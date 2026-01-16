from __future__ import annotations

import time
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from .config import Settings
from .explainers import CitationValidationError, DeterministicExplainer, validate_citations
from .scenarios import SCENARIO_CATALOG
from .schemas import AnalysisStatus, EvidenceLine, ExplanationResult, WindowResult
from .service import AnalysisService
from .storage import AnalysisRecord

_UPLOAD_NAME = "runtime-evaluation.log"
_UPLOAD_LINES = (
    "2026-04-18T09:00:00 INFO request accepted user_id=alice@example.com",
    "2026-04-18T09:01:00 WARN subsystem=network resolver=service-dns degraded",
    "2026-04-18T09:02:00 ERROR DNS lookup failed host=10.1.2.3",
    "2026-04-18T09:03:00 ERROR NXDOMAIN token=top-secret",
    "2026-04-18T09:04:00 ERROR endpoint resolution failed",
)
_RAW_MARKERS = (b"alice@example.com", b"10.1.2.3", b"top-secret")


def _wait_for_result(service: AnalysisService, analysis_id: str) -> AnalysisRecord:
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        record = service.get(analysis_id)
        if record and record.status in {AnalysisStatus.COMPLETE, AnalysisStatus.FAILED}:
            return record
        time.sleep(0.01)
    raise RuntimeError(f"Analysis {analysis_id} did not finish within 10 seconds.")


def _evaluate_record(record: AnalysisRecord) -> tuple[dict[str, object], int, int]:
    if record.status != AnalysisStatus.COMPLETE or not record.result:
        raise RuntimeError(f"Runtime evaluation failed for {record.source_name}.")
    raw_windows = record.result.get("windows")
    raw_explanation = record.result.get("explanation")
    if not isinstance(raw_windows, list) or not isinstance(raw_explanation, dict):
        raise RuntimeError(f"Runtime result was malformed for {record.source_name}.")

    windows = [WindowResult.model_validate(item) for item in raw_windows]
    explanation = ExplanationResult.model_validate(raw_explanation)
    anomalous = [window for window in windows if window.is_anomaly]
    primary = max(anomalous, key=lambda item: item.anomaly_score) if anomalous else None
    allowed = set(primary.evidence_line_ids if primary else [])
    valid_citations = sum(citation in allowed for citation in explanation.citations)
    passed = valid_citations == len(explanation.citations)
    if anomalous and not explanation.citations:
        passed = False

    return (
        {
            "source": record.source_name,
            "source_kind": record.source_kind,
            "anomalous_windows": len(anomalous),
            "citations_checked": len(explanation.citations),
            "valid_citations": valid_citations,
            "passed": passed,
        },
        len(explanation.citations),
        valid_citations,
    )


def evaluate_runtime(model_dir: Path) -> dict[str, Any]:
    with TemporaryDirectory(prefix="loglens-runtime-evaluation-") as temp_dir:
        root = Path(temp_dir)
        database_path = root / "runtime.sqlite3"
        service = AnalysisService(
            Settings(
                database_url=f"sqlite:///{database_path}",
                model_dir=model_dir,
                queue_capacity=len(SCENARIO_CATALOG) + 2,
            ),
            explainer=DeterministicExplainer(),
        )
        service.start()
        try:
            submitted = [service.submit_scenario(scenario_id) for scenario_id in SCENARIO_CATALOG]
            submitted.append(
                service.submit_upload(
                    filename=_UPLOAD_NAME,
                    content="\n".join(_UPLOAD_LINES).encode(),
                )
            )
            records = [_wait_for_result(service, record.id) for record in submitted]
        finally:
            service.stop()

        cases: list[dict[str, object]] = []
        citations_checked = 0
        valid_citations = 0
        for record in records:
            case, case_citations, case_valid = _evaluate_record(record)
            cases.append(case)
            citations_checked += case_citations
            valid_citations += case_valid

        invalid_citation_rejected = False
        try:
            validate_citations(
                ["line-not-supplied"],
                [
                    EvidenceLine(
                        id="line-supplied",
                        line_no=1,
                        text="ERROR redacted evaluation line",
                        event_template="ERROR redacted evaluation line",
                        severity="ERROR",
                    )
                ],
            )
        except CitationValidationError:
            invalid_citation_rejected = True

        database_bytes = database_path.read_bytes()
        raw_markers_found = sum(marker in database_bytes for marker in _RAW_MARKERS)
        raw_upload_files = [
            path
            for path in root.rglob("*")
            if path.is_file() and path.suffix.lower() in {".log", ".txt"}
        ]
        cases_passed = sum(bool(case["passed"]) for case in cases)
        return {
            "evaluation": "runtime_integrity",
            "model_version": service.engine.manifest["version"],
            "cases": cases,
            "summary": {
                "analyses": len(cases),
                "cases_passed": cases_passed,
                "citations_checked": citations_checked,
                "valid_citations": valid_citations,
                "citation_validity_rate": (
                    valid_citations / citations_checked if citations_checked else 1.0
                ),
                "invalid_citation_trials": 1,
                "invalid_citations_rejected": int(invalid_citation_rejected),
                "raw_upload_files_retained": len(raw_upload_files),
                "raw_markers_found_in_persistence": raw_markers_found,
            },
        }
