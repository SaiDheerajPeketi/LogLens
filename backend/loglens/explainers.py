from __future__ import annotations

import json
import os
from typing import Protocol

from openai import OpenAI

from .schemas import CauseClass, EvidenceLine, ExplanationResult


class CitationValidationError(ValueError):
    """Raised when an explanation cites evidence it was not given."""


class Explainer(Protocol):
    def explain(
        self,
        *,
        cause: CauseClass,
        confidence: float,
        evidence: list[EvidenceLine],
    ) -> ExplanationResult: ...


def validate_citations(citations: list[str], evidence: list[EvidenceLine]) -> None:
    allowed = {line.id for line in evidence}
    if not citations or any(citation not in allowed for citation in citations):
        raise CitationValidationError("Every citation must reference supplied evidence.")


class DeterministicExplainer:
    _CAUSE_NAMES = {
        CauseClass.DATABASE_TIMEOUT: "database timeouts",
        CauseClass.AUTHENTICATION_FAILURE: "authentication failures",
        CauseClass.CONNECTION_POOL_EXHAUSTION: "connection-pool exhaustion",
        CauseClass.DISK_PRESSURE: "disk pressure",
        CauseClass.NETWORK_DNS_FAILURE: "network or DNS failure",
        CauseClass.UNKNOWN: "an unsupported or ambiguous cause",
    }

    def explain(
        self,
        *,
        cause: CauseClass,
        confidence: float,
        evidence: list[EvidenceLine],
    ) -> ExplanationResult:
        citations = [line.id for line in evidence[:3]]
        if citations:
            summary = (
                f"The suspicious window is most consistent with {self._CAUSE_NAMES[cause]}. "
                "The cited redacted lines contain the strongest repeated failure signals."
            )
        else:
            summary = "No anomalous window was detected in the supplied log."
        return ExplanationResult(
            summary=summary,
            probable_cause=cause,
            confidence=confidence,
            citations=citations,
            source="deterministic",
            caveat=(
                "Generated locally from the classifier result and selected evidence; "
                "no external explanation service was used."
            ),
        )


class OpenAIExplainer:
    def __init__(self, *, model: str, api_key: str, timeout_seconds: float = 12.0) -> None:
        self.model = model
        self.client = OpenAI(api_key=api_key, timeout=timeout_seconds)

    def explain(
        self,
        *,
        cause: CauseClass,
        confidence: float,
        evidence: list[EvidenceLine],
    ) -> ExplanationResult:
        payload = {
            "classifier": {"cause": cause.value, "confidence": round(confidence, 4)},
            "evidence": [
                {"line_id": line.id, "severity": line.severity, "text": line.text}
                for line in evidence
            ],
        }
        response = self.client.responses.create(
            model=self.model,
            store=False,
            instructions=(
                "Explain the classifier result using only the supplied redacted evidence. "
                "Be concise, state uncertainty, and cite only supplied line_id values."
            ),
            input=json.dumps(payload),
            max_output_tokens=300,
            text={
                "format": {
                    "type": "json_schema",
                    "name": "loglens_explanation",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "summary": {"type": "string"},
                            "citations": {
                                "type": "array",
                                "items": {"type": "string"},
                                "minItems": 1,
                                "uniqueItems": True,
                            },
                        },
                        "required": ["summary", "citations"],
                        "additionalProperties": False,
                    },
                }
            },
        )
        if response.status != "completed" or not response.output_text:
            raise ValueError("The explanation response was incomplete or refused.")
        generated = json.loads(response.output_text)
        summary = generated.get("summary")
        citations = generated.get("citations")
        if not isinstance(summary, str) or not isinstance(citations, list):
            raise ValueError("The explanation response did not match the expected shape.")
        if not all(isinstance(citation, str) for citation in citations):
            raise CitationValidationError("Citation values must be line identifiers.")
        validate_citations(citations, evidence)
        return ExplanationResult(
            summary=summary,
            probable_cause=cause,
            confidence=confidence,
            citations=citations,
            source="openai",
        )


class FallbackExplainer:
    def __init__(self, primary: Explainer | None) -> None:
        self.primary = primary
        self.fallback = DeterministicExplainer()

    def explain(
        self,
        *,
        cause: CauseClass,
        confidence: float,
        evidence: list[EvidenceLine],
    ) -> ExplanationResult:
        if self.primary:
            try:
                explanation = self.primary.explain(
                    cause=cause,
                    confidence=confidence,
                    evidence=evidence,
                )
                validate_citations(explanation.citations, evidence)
                return explanation
            except Exception:
                pass
        return self.fallback.explain(cause=cause, confidence=confidence, evidence=evidence)


def build_explainer(*, model: str) -> FallbackExplainer:
    api_key = os.getenv("OPENAI_API_KEY")
    primary = OpenAIExplainer(model=model, api_key=api_key) if api_key else None
    return FallbackExplainer(primary)
