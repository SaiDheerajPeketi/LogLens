from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class AnalysisStatus(StrEnum):
    QUEUED = "queued"
    PARSING = "parsing"
    SCORING = "scoring"
    EXPLAINING = "explaining"
    COMPLETE = "complete"
    FAILED = "failed"
    EXPIRED = "expired"


class CauseClass(StrEnum):
    DATABASE_TIMEOUT = "database_timeout"
    AUTHENTICATION_FAILURE = "authentication_failure"
    CONNECTION_POOL_EXHAUSTION = "connection_pool_exhaustion"
    DISK_PRESSURE = "disk_pressure"
    NETWORK_DNS_FAILURE = "network_dns_failure"
    UNKNOWN = "unknown"


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "loglens-api"
    version: str
    model_ready: bool
    checked_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ScenarioSummary(BaseModel):
    id: str
    name: str
    description: str
    expected_cause: CauseClass
    line_count: int
    synthetic: bool = True


class ModelCardSummary(BaseModel):
    version: str
    anomaly_dataset: str
    root_cause_dataset: str
    anomaly_metrics: dict[str, float]
    root_cause_metrics: dict[str, float]
    limitations: list[str]


class AnalysisAccepted(BaseModel):
    id: str
    status: AnalysisStatus
    created_at: datetime
    updated_at: datetime
    expires_at: datetime


class SourceSummary(BaseModel):
    kind: str
    name: str
    line_count: int
    raw_retained: bool = False
    synthetic: bool = False


class EvidenceLine(BaseModel):
    id: str
    line_no: int
    text: str
    event_template: str
    severity: str


class WindowResult(BaseModel):
    id: str
    strategy: str
    start_line: int
    end_line: int
    anomaly_score: float = Field(ge=0, le=1)
    is_anomaly: bool
    cause: CauseClass
    confidence: float = Field(ge=0, le=1)
    evidence_line_ids: list[str]
    caveats: list[str] = Field(default_factory=list)


class ExplanationResult(BaseModel):
    summary: str
    probable_cause: CauseClass
    confidence: float = Field(ge=0, le=1)
    citations: list[str]
    source: str
    caveat: str | None = None


class AnalysisError(BaseModel):
    code: str
    message: str
    retryable: bool
    action: str


class AnalysisDetail(AnalysisAccepted):
    source: SourceSummary
    model_versions: dict[str, str] = Field(default_factory=dict)
    windows: list[WindowResult] = Field(default_factory=list)
    explanation: ExplanationResult | None = None
    caveats: list[str] = Field(default_factory=list)
    error: AnalysisError | None = None


class EventsPage(BaseModel):
    items: list[EvidenceLine]
    next_cursor: str | None
