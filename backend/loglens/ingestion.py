from __future__ import annotations

import hashlib
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path


class UploadValidationError(ValueError):
    """Raised when an uploaded log cannot be analyzed safely."""


@dataclass(frozen=True, slots=True)
class ParsedLine:
    line_no: int
    text: str
    event_template: str
    severity: str
    timestamp: datetime | None
    correlation_id: str | None


@dataclass(frozen=True, slots=True)
class LogWindow:
    id: str
    strategy: str
    start_line: int
    end_line: int
    lines: tuple[ParsedLine, ...]


_EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
_IPV4_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
_IPV6_RE = re.compile(r"(?<![\w:])(?:[A-F0-9]{1,4}:){3,7}[A-F0-9]{1,4}(?![\w:])", re.IGNORECASE)
_SECRET_RE = re.compile(
    r"(?i)\b(password|passwd|secret|token|api[_-]?key|authorization)\b\s*([=:])\s*([^\s,;]+)"
)
_USER_RE = re.compile(r"(?i)\b(user(?:_?id)?|uid)\b\s*([=:])\s*([A-Z0-9._@-]+)")
_UUID_RE = re.compile(
    r"\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b",
    re.IGNORECASE,
)
_HEX_RE = re.compile(r"\b0x[0-9a-f]+\b", re.IGNORECASE)
_NUMBER_RE = re.compile(r"(?<![A-Z])\b\d+(?:\.\d+)?\b")
_ERROR_CODE_RE = re.compile(r"\b[A-Z]{2,}-\d{2,}\b")
_SPACE_RE = re.compile(r"\s+")
_CORRELATION_PATTERNS = (
    re.compile(r"\bblk_-?\d+\b"),
    re.compile(r"(?i)\b(?:trace|request|correlation)[_-]?id[=: ]+([A-Z0-9._-]+)"),
)
_TIMESTAMP_PATTERNS = (
    (re.compile(r"\b\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?Z?\b"), "%Y-%m-%dT%H:%M:%S"),
    (re.compile(r"\b\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\b"), "%Y-%m-%d %H:%M:%S"),
    (re.compile(r"\b\d{2}:\d{2}:\d{2}\b"), "%H:%M:%S"),
)


def validate_upload(
    filename: str,
    content: bytes,
    *,
    max_bytes: int,
    max_lines: int,
) -> list[str]:
    suffix = Path(filename).suffix.lower()
    if suffix not in {".log", ".txt"}:
        raise UploadValidationError("Upload a plain-text .log or .txt file.")
    if not content:
        raise UploadValidationError("The uploaded log is empty.")
    if len(content) > max_bytes:
        raise UploadValidationError(f"The uploaded log exceeds the {max_bytes} byte limit.")
    if b"\x00" in content:
        raise UploadValidationError("Binary files are not supported.")
    try:
        decoded = content.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise UploadValidationError("The uploaded log must use UTF-8 encoding.") from exc
    lines = decoded.splitlines()
    if len(lines) > max_lines:
        raise UploadValidationError(f"The uploaded log exceeds the {max_lines} line limit.")
    if not any(line.strip() for line in lines):
        raise UploadValidationError("The uploaded log contains no readable entries.")
    return lines


def _alias(kind: str, value: str, salt: str) -> str:
    digest = hashlib.sha256(f"{salt}:{kind}:{value.lower()}".encode()).hexdigest()[:8]
    return f"[{kind}:{digest}]"


def redact_text(text: str, *, salt: str) -> str:
    redacted = _SECRET_RE.sub(lambda match: f"{match.group(1)}{match.group(2)}[SECRET]", text)
    redacted = _EMAIL_RE.sub(lambda match: _alias("EMAIL", match.group(0), salt), redacted)
    redacted = _IPV4_RE.sub(lambda match: _alias("IP", match.group(0), salt), redacted)
    redacted = _IPV6_RE.sub(lambda match: _alias("IP", match.group(0), salt), redacted)
    return _USER_RE.sub(
        lambda match: f"{match.group(1)}{match.group(2)}{_alias('USER', match.group(3), salt)}",
        redacted,
    )


def _parse_timestamp(text: str) -> datetime | None:
    for pattern, date_format in _TIMESTAMP_PATTERNS:
        match = pattern.search(text)
        if not match:
            continue
        candidate = match.group(0).removesuffix("Z")
        if "T" in candidate and "." in candidate:
            candidate = candidate.split(".", maxsplit=1)[0]
        try:
            return datetime.strptime(candidate, date_format)
        except ValueError:
            continue
    return None


def _correlation_id(text: str) -> str | None:
    for pattern in _CORRELATION_PATTERNS:
        match = pattern.search(text)
        if match:
            return match.group(1) if match.lastindex else match.group(0)
    return None


def _severity(text: str) -> str:
    upper = text.upper()
    for severity in ("FATAL", "ERROR", "WARN", "INFO", "DEBUG", "TRACE"):
        if re.search(rf"\b{severity}(?:ING)?\b", upper):
            return severity
    return "UNKNOWN"


def event_template(text: str) -> str:
    protected_codes: list[str] = []

    def protect_code(match: re.Match[str]) -> str:
        protected_codes.append(match.group(0))
        return f"<ERRORCODE{len(protected_codes) - 1}>"

    template = _ERROR_CODE_RE.sub(protect_code, text)
    template = _UUID_RE.sub("<UUID>", template)
    template = _HEX_RE.sub("<HEX>", template)
    template = re.sub(r"\[(?:EMAIL|IP|USER):[0-9a-f]{8}\]", "<REDACTED>", template)
    template = _NUMBER_RE.sub("<NUM>", template)
    for index, code in enumerate(protected_codes):
        template = template.replace(f"<ERRORCODE{index}>", code)
    return _SPACE_RE.sub(" ", template).strip()


def parse_lines(lines: list[str], *, salt: str) -> list[ParsedLine]:
    parsed: list[ParsedLine] = []
    for index, raw in enumerate(lines, start=1):
        text = redact_text(raw.rstrip(), salt=salt)
        parsed.append(
            ParsedLine(
                line_no=index,
                text=text,
                event_template=event_template(text),
                severity=_severity(text),
                timestamp=_parse_timestamp(text),
                correlation_id=_correlation_id(text),
            )
        )
    return parsed


def _correlation_windows(lines: list[ParsedLine]) -> list[LogWindow]:
    grouped: dict[str, list[ParsedLine]] = defaultdict(list)
    for line in lines:
        if line.correlation_id:
            grouped[line.correlation_id].append(line)
    return [
        LogWindow(
            id=f"corr-{index:03d}",
            strategy="correlation_id",
            start_line=group[0].line_no,
            end_line=group[-1].line_no,
            lines=tuple(group),
        )
        for index, group in enumerate(grouped.values(), start=1)
    ]


def _timestamp_windows(lines: list[ParsedLine], minutes: int = 5) -> list[LogWindow]:
    timed = [line for line in lines if line.timestamp]
    assert timed and timed[0].timestamp is not None
    origin = timed[0].timestamp
    grouped: dict[int, list[ParsedLine]] = defaultdict(list)
    for line in timed:
        assert line.timestamp is not None
        delta = line.timestamp - origin
        bucket = max(0, int(delta / timedelta(minutes=minutes)))
        grouped[bucket].append(line)
    return [
        LogWindow(
            id=f"time-{bucket:03d}",
            strategy="timestamp",
            start_line=group[0].line_no,
            end_line=group[-1].line_no,
            lines=tuple(group),
        )
        for bucket, group in sorted(grouped.items())
    ]


def _line_windows(lines: list[ParsedLine], size: int = 200, overlap: int = 50) -> list[LogWindow]:
    if not lines:
        return []
    step = max(1, size - overlap)
    windows: list[LogWindow] = []
    for index, start in enumerate(range(0, len(lines), step), start=1):
        group = lines[start : start + size]
        if not group:
            break
        windows.append(
            LogWindow(
                id=f"line-{index:03d}",
                strategy="line_count",
                start_line=group[0].line_no,
                end_line=group[-1].line_no,
                lines=tuple(group),
            )
        )
        if start + size >= len(lines):
            break
    return windows


def build_windows(lines: list[ParsedLine]) -> list[LogWindow]:
    if not lines:
        return []
    correlation_coverage = sum(line.correlation_id is not None for line in lines) / len(lines)
    if correlation_coverage >= 0.5:
        return _correlation_windows(lines)
    timestamp_coverage = sum(line.timestamp is not None for line in lines) / len(lines)
    if timestamp_coverage >= 0.5:
        return _timestamp_windows(lines)
    return _line_windows(lines)
