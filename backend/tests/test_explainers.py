import json
from typing import Any

import pytest
from loglens.explainers import (
    CitationValidationError,
    FallbackExplainer,
    OpenAIExplainer,
    validate_citations,
)
from loglens.schemas import CauseClass, EvidenceLine, ExplanationResult


def _evidence() -> list[EvidenceLine]:
    return [
        EvidenceLine(
            id="line-7",
            line_no=7,
            text="ERROR token=[SECRET] database deadline exceeded",
            event_template="ERROR token=[SECRET] database deadline exceeded",
            severity="ERROR",
        )
    ]


def test_invalid_citation_is_rejected() -> None:
    with pytest.raises(CitationValidationError):
        validate_citations(["line-999"], _evidence())


class InvalidPrimary:
    def explain(self, **_: object) -> ExplanationResult:
        return ExplanationResult(
            summary="Unsupported citation.",
            probable_cause=CauseClass.DATABASE_TIMEOUT,
            confidence=0.9,
            citations=["line-999"],
            source="openai",
        )


def test_invalid_primary_explanation_uses_deterministic_fallback() -> None:
    result = FallbackExplainer(InvalidPrimary()).explain(
        cause=CauseClass.DATABASE_TIMEOUT,
        confidence=0.9,
        evidence=_evidence(),
    )

    assert result.source == "deterministic"
    assert result.citations == ["line-7"]


class FakeResponse:
    status = "completed"
    output_text = json.dumps(
        {
            "summary": "The database deadline was exceeded.",
            "citations": ["line-7"],
        }
    )


class FakeResponses:
    def __init__(self) -> None:
        self.kwargs: dict[str, Any] = {}

    def create(self, **kwargs: Any) -> FakeResponse:
        self.kwargs = kwargs
        return FakeResponse()


class FakeClient:
    def __init__(self) -> None:
        self.responses = FakeResponses()


def test_openai_adapter_disables_storage_and_sends_only_redacted_evidence() -> None:
    adapter = OpenAIExplainer(model="test-model", api_key="test-key")
    fake = FakeClient()
    adapter.client = fake  # type: ignore[assignment]

    result = adapter.explain(
        cause=CauseClass.DATABASE_TIMEOUT,
        confidence=0.9,
        evidence=_evidence(),
    )

    assert result.source == "openai"
    assert fake.responses.kwargs["store"] is False
    transmitted = fake.responses.kwargs["input"]
    assert "[SECRET]" in transmitted
    assert "test-key" not in transmitted
