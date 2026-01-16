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

