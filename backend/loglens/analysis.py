from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from collections.abc import Callable
from pathlib import Path
from typing import Any

import joblib

from .explainers import DeterministicExplainer, Explainer, validate_citations
from .ingestion import LogWindow, ParsedLine, build_windows, parse_lines
from .schemas import (
    AnalysisStatus,
    CauseClass,
    EvidenceLine,
    WindowResult,
)

StatusCallback = Callable[[AnalysisStatus], None]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class AnalysisEngine:
    def __init__(self, *, model_dir: Path, explainer: Explainer) -> None:
        manifest_path = model_dir / "manifest.json"
        self.manifest: dict[str, Any] = json.loads(manifest_path.read_text())
        anomaly_path = model_dir / str(self.manifest["anomaly_model"])
        root_cause_path = model_dir / str(self.manifest["root_cause_model"])
        checksums = self.manifest["checksums"]
        if _sha256(anomaly_path) != checksums["anomaly_bundle_sha256"]:
            raise ValueError("Anomaly model checksum does not match its manifest.")
        if _sha256(root_cause_path) != checksums["root_cause_bundle_sha256"]:
            raise ValueError("Root-cause model checksum does not match its manifest.")
        self.root_cause_model: Any = joblib.load(root_cause_path)
        self.explainer = explainer

    @staticmethod
    def _anomaly_score(window: LogWindow, template_counts: Counter[str]) -> float:
        severity_weight = {
            "FATAL": 1.0,
            "ERROR": 0.75,
            "WARN": 0.30,
        }
        signal = sum(severity_weight.get(line.severity, 0.0) for line in window.lines)
        rare_failure_boost = sum(
            0.12
            for line in window.lines
            if line.severity in {"FATAL", "ERROR"} and template_counts[line.event_template] <= 2
        )
        density = (signal + rare_failure_boost) / math.sqrt(max(1, len(window.lines)))
        return min(0.99, 1 - math.exp(-density))

    def _classify_cause(self, window: LogWindow) -> tuple[CauseClass, float]:
        text = "\n".join(line.text for line in window.lines)
        probabilities = self.root_cause_model.predict_proba([text])[0]
        classes = list(self.root_cause_model.classes_)
        best_index = int(probabilities.argmax())
        predicted = CauseClass(classes[best_index])
        confidence = float(probabilities[best_index])
        if predicted == CauseClass.UNKNOWN:
            return predicted, min(confidence, 0.49)
        if confidence < 0.58:
            return CauseClass.UNKNOWN, confidence
        return predicted, confidence

    def _select_evidence(
        self,
        window: LogWindow,
        cause: CauseClass,
        *,
        limit: int = 5,
    ) -> list[EvidenceLine]:
        line_text = [line.text for line in window.lines]
        probabilities = self.root_cause_model.predict_proba(line_text)
        classes = list(self.root_cause_model.classes_)
        class_index = classes.index(cause.value)
        severity_weight = {"FATAL": 1.0, "ERROR": 0.8, "WARN": 0.35}
        ranked = sorted(
            zip(window.lines, probabilities[:, class_index], strict=True),
            key=lambda item: (severity_weight.get(item[0].severity, 0) + float(item[1])),
            reverse=True,
        )
        selected = [line for line, _ in ranked if line.severity != "DEBUG"][:limit]
        return [self._evidence_line(line) for line in selected]

    @staticmethod
    def _evidence_line(line: ParsedLine) -> EvidenceLine:
        return EvidenceLine(
            id=f"line-{line.line_no}",
            line_no=line.line_no,
            text=line.text,
            event_template=line.event_template,
            severity=line.severity,
        )

    def analyze(
        self,
        *,
        redacted_lines: list[str],
        analysis_id: str,
        status: StatusCallback,
    ) -> dict[str, object]:
        status(AnalysisStatus.PARSING)
        parsed = parse_lines(redacted_lines, salt=analysis_id)
        windows = build_windows(parsed)
        template_counts = Counter(line.event_template for line in parsed)

        status(AnalysisStatus.SCORING)
        window_results: list[WindowResult] = []
        evidence_by_window: dict[str, list[EvidenceLine]] = {}
        for window in windows:
            score = self._anomaly_score(window, template_counts)
            is_anomaly = score >= 0.55
            cause = CauseClass.UNKNOWN
            confidence = 0.0
            caveats: list[str] = []
            evidence: list[EvidenceLine] = []
            if is_anomaly:
                cause, confidence = self._classify_cause(window)
                evidence = self._select_evidence(window, cause)
                if cause == CauseClass.UNKNOWN:
                    caveats.append("Unknown—needs human review; evidence was not class-specific.")
            evidence_by_window[window.id] = evidence
            window_results.append(
                WindowResult(
                    id=window.id,
                    strategy=window.strategy,
                    start_line=window.start_line,
                    end_line=window.end_line,
                    anomaly_score=round(score, 4),
                    is_anomaly=is_anomaly,
                    cause=cause,
                    confidence=round(confidence, 4),
                    evidence_line_ids=[line.id for line in evidence],
                    caveats=caveats,
                )
            )

        status(AnalysisStatus.EXPLAINING)
        anomalous = [window for window in window_results if window.is_anomaly]
        if anomalous:
            primary = max(anomalous, key=lambda window: window.anomaly_score)
            evidence = evidence_by_window[primary.id]
            explanation = self.explainer.explain(
                cause=primary.cause,
                confidence=primary.confidence,
                evidence=evidence,
            )
            validate_citations(explanation.citations, evidence)
        else:
            explanation = DeterministicExplainer().explain(
                cause=CauseClass.UNKNOWN,
                confidence=0,
                evidence=[],
            )

        model_version = str(self.manifest["version"])
        events = [self._evidence_line(line).model_dump(mode="json") for line in parsed]
        return {
            "model_versions": {
                "evaluation_bundle": model_version,
                "runtime_anomaly": "generic-severity-rarity-v1",
                "root_cause": model_version,
            },
            "windows": [window.model_dump(mode="json") for window in window_results],
            "explanation": explanation.model_dump(mode="json"),
            "events": events,
            "caveats": [
                (
                    "Generic uploads use a deterministic severity-and-rarity anomaly score; "
                    "the reported HDFS metric applies only to HDFS block traces."
                ),
                "Root-cause accuracy is measured on disclosed synthetic template families.",
            ],
        }
