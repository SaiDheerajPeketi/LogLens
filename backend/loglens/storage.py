from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

from sqlalchemy import String, Text, create_engine, select, update
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from .schemas import AnalysisStatus


class Base(DeclarativeBase):
    pass


class AnalysisRow(Base):
    __tablename__ = "analyses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    status: Mapped[str] = mapped_column(String(24), index=True)
    source_kind: Mapped[str] = mapped_column(String(24))
    source_name: Mapped[str] = mapped_column(String(255))
    scenario_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    line_count: Mapped[int]
    retryable: Mapped[bool]
    created_at: Mapped[str] = mapped_column(String(40))
    updated_at: Mapped[str] = mapped_column(String(40))
    expires_at: Mapped[str] = mapped_column(String(40), index=True)
    redacted_lines_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    result_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_json: Mapped[str | None] = mapped_column(Text, nullable=True)


@dataclass(frozen=True, slots=True)
class AnalysisRecord:
    id: str
    status: AnalysisStatus
    source_kind: str
    source_name: str
    scenario_id: str | None
    line_count: int
    retryable: bool
    created_at: datetime
    updated_at: datetime
    expires_at: datetime
    redacted_lines: list[str] | None
    result: dict[str, object] | None
    error: dict[str, object] | None


def _now() -> datetime:
    return datetime.now(UTC)


def _iso(value: datetime) -> str:
    return value.astimezone(UTC).isoformat()


def _from_iso(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _json_load(value: str | None) -> object | None:
    return json.loads(value) if value else None


def _record(row: AnalysisRow) -> AnalysisRecord:
    lines = _json_load(row.redacted_lines_json)
    result = _json_load(row.result_json)
    error = _json_load(row.error_json)
    return AnalysisRecord(
        id=row.id,
        status=AnalysisStatus(row.status),
        source_kind=row.source_kind,
        source_name=row.source_name,
        scenario_id=row.scenario_id,
        line_count=row.line_count,
        retryable=row.retryable,
        created_at=_from_iso(row.created_at),
        updated_at=_from_iso(row.updated_at),
        expires_at=_from_iso(row.expires_at),
        redacted_lines=lines if isinstance(lines, list) else None,
        result=result if isinstance(result, dict) else None,
        error=error if isinstance(error, dict) else None,
    )


class AnalysisStore:
    def __init__(self, database_url: str, *, ttl_hours: int) -> None:
        if database_url.startswith("sqlite:///"):
            path = Path(database_url.removeprefix("sqlite:///"))
            path.parent.mkdir(parents=True, exist_ok=True)
        self.engine = create_engine(
            database_url,
            connect_args={"check_same_thread": False} if database_url.startswith("sqlite") else {},
        )
        self.sessions = sessionmaker(self.engine, expire_on_commit=False)
        self.ttl_hours = ttl_hours

    def initialize(self) -> None:
        Base.metadata.create_all(self.engine)
        now = _iso(_now())
        interrupted = [
            AnalysisStatus.QUEUED.value,
            AnalysisStatus.PARSING.value,
            AnalysisStatus.SCORING.value,
            AnalysisStatus.EXPLAINING.value,
        ]
        error = {
            "code": "interrupted",
            "message": "Analysis stopped when the service restarted.",
            "retryable": True,
            "action": "Retry the built-in scenario or upload the source log again.",
        }
        with self.sessions.begin() as session:
            session.execute(
                update(AnalysisRow)
                .where(AnalysisRow.status.in_(interrupted))
                .values(
                    status=AnalysisStatus.FAILED.value,
                    updated_at=now,
                    error_json=json.dumps(error),
                )
            )

    def create(
        self,
        *,
        source_kind: str,
        source_name: str,
        redacted_lines: list[str],
        scenario_id: str | None = None,
        retryable: bool,
    ) -> AnalysisRecord:
        created = _now()
        row = AnalysisRow(
            id=str(uuid4()),
            status=AnalysisStatus.QUEUED.value,
            source_kind=source_kind,
            source_name=source_name,
            scenario_id=scenario_id,
            line_count=len(redacted_lines),
            retryable=retryable,
            created_at=_iso(created),
            updated_at=_iso(created),
            expires_at=_iso(created + timedelta(hours=self.ttl_hours)),
            redacted_lines_json=json.dumps(redacted_lines),
        )
        with self.sessions.begin() as session:
            session.add(row)
        return _record(row)

    def get(self, analysis_id: str) -> AnalysisRecord | None:
        self.expire_due()
        with self.sessions() as session:
            row = session.get(AnalysisRow, analysis_id)
            return _record(row) if row else None

    def update_status(self, analysis_id: str, status: AnalysisStatus) -> None:
        with self.sessions.begin() as session:
            session.execute(
                update(AnalysisRow)
                .where(AnalysisRow.id == analysis_id)
                .values(status=status.value, updated_at=_iso(_now()))
            )

    def complete(self, analysis_id: str, result: dict[str, object]) -> None:
        with self.sessions.begin() as session:
            session.execute(
                update(AnalysisRow)
                .where(AnalysisRow.id == analysis_id)
                .values(
                    status=AnalysisStatus.COMPLETE.value,
                    updated_at=_iso(_now()),
                    result_json=json.dumps(result),
                    error_json=None,
                )
            )

    def fail(
        self,
        analysis_id: str,
        *,
        code: str,
        message: str,
        retryable: bool,
        action: str,
    ) -> None:
        error = {
            "code": code,
            "message": message,
            "retryable": retryable,
            "action": action,
        }
        with self.sessions.begin() as session:
            session.execute(
                update(AnalysisRow)
                .where(AnalysisRow.id == analysis_id)
                .values(
                    status=AnalysisStatus.FAILED.value,
                    updated_at=_iso(_now()),
                    error_json=json.dumps(error),
                )
            )

    def reset_scenario(self, analysis_id: str, redacted_lines: list[str]) -> AnalysisRecord | None:
        current = self.get(analysis_id)
        if not current or not current.retryable or current.source_kind != "scenario":
            return None
        now = _now()
        with self.sessions.begin() as session:
            session.execute(
                update(AnalysisRow)
                .where(AnalysisRow.id == analysis_id)
                .values(
                    status=AnalysisStatus.QUEUED.value,
                    updated_at=_iso(now),
                    expires_at=_iso(now + timedelta(hours=self.ttl_hours)),
                    redacted_lines_json=json.dumps(redacted_lines),
                    result_json=None,
                    error_json=None,
                )
            )
        return self.get(analysis_id)

    def expire_due(self) -> int:
        now = _iso(_now())
        with self.sessions.begin() as session:
            rows = session.scalars(
                select(AnalysisRow).where(
                    AnalysisRow.expires_at <= now,
                    AnalysisRow.status != AnalysisStatus.EXPIRED.value,
                )
            ).all()
            for row in rows:
                row.status = AnalysisStatus.EXPIRED.value
                row.updated_at = now
                row.redacted_lines_json = None
                row.result_json = None
                row.error_json = json.dumps(
                    {
                        "code": "expired",
                        "message": "The retained redacted result has expired.",
                        "retryable": row.source_kind == "scenario",
                        "action": (
                            "Run the scenario again."
                            if row.source_kind == "scenario"
                            else "Upload the source log again."
                        ),
                    }
                )
            return len(rows)

    def close(self) -> None:
        self.engine.dispose()
