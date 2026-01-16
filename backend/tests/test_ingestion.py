import pytest
from loglens.ingestion import (
    UploadValidationError,
    build_windows,
    event_template,
    parse_lines,
    redact_text,
    validate_upload,
)


def test_upload_accepts_utf8_log() -> None:
    lines = validate_upload(
        "incident.log",
        b"2026-09-16 12:00:00 INFO service ready\n",
        max_bytes=1024,
        max_lines=10,
    )

    assert lines == ["2026-09-16 12:00:00 INFO service ready"]


@pytest.mark.parametrize("filename", ["incident.zip", "incident.csv", "incident.exe"])
def test_upload_rejects_unsupported_extensions(filename: str) -> None:
    with pytest.raises(UploadValidationError, match="plain-text"):
        validate_upload(filename, b"log", max_bytes=1024, max_lines=10)


def test_upload_rejects_binary_and_line_overflow() -> None:
    with pytest.raises(UploadValidationError, match="Binary"):
        validate_upload("incident.log", b"abc\x00def", max_bytes=1024, max_lines=10)
    with pytest.raises(UploadValidationError, match="line limit"):
        validate_upload("incident.txt", b"a\nb\nc", max_bytes=1024, max_lines=2)


def test_redaction_is_stable_within_analysis_and_changes_across_analyses() -> None:
    source = "user_id=sai email=sai@example.com ip=10.1.2.3 token=super-secret"

    first = redact_text(source, salt="analysis-a")
    repeat = redact_text(source, salt="analysis-a")
    second = redact_text(source, salt="analysis-b")

    assert first == repeat
    assert first != second
    assert "sai@example.com" not in first
    assert "10.1.2.3" not in first
    assert "super-secret" not in first
    assert "[SECRET]" in first


def test_event_template_keeps_error_codes_but_normalizes_parameters() -> None:
    template = event_template("ERROR AUTH-401 request 812 took 230.5ms from [IP:12ab34cd]")

    assert "AUTH-401" in template
    assert "812" not in template
    assert "230.5" not in template
    assert "<REDACTED>" in template


def test_windowing_prefers_correlation_ids() -> None:
    lines = parse_lines(
        [
            "12:00:00 INFO blk_1 opened",
            "12:00:01 ERROR blk_2 failed",
            "12:00:02 INFO blk_1 closed",
        ],
        salt="analysis",
    )

    windows = build_windows(lines)

    assert [window.strategy for window in windows] == ["correlation_id", "correlation_id"]
    assert [line.line_no for line in windows[0].lines] == [1, 3]


def test_windowing_uses_time_when_correlation_coverage_is_low() -> None:
    lines = parse_lines(
        [
            "2026-09-16 12:00:00 INFO started",
            "2026-09-16 12:01:00 WARN slow",
            "2026-09-16 12:06:00 ERROR timeout",
        ],
        salt="analysis",
    )

    windows = build_windows(lines)

    assert len(windows) == 2
    assert all(window.strategy == "timestamp" for window in windows)

