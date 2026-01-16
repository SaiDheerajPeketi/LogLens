from __future__ import annotations

import base64
import binascii
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request, status
from starlette.datastructures import UploadFile

from . import __version__
from .catalog import load_model_card
from .scenarios import list_scenario_summaries
from .schemas import (
    AnalysisAccepted,
    AnalysisDetail,
    AnalysisError,
    AnalysisStatus,
    EventsPage,
    EvidenceLine,
    ExplanationResult,
    HealthResponse,
    ModelCardSummary,
    ScenarioSummary,
    SourceSummary,
    WindowResult,
)
from .service import (
    AnalysisService,
    QueueCapacityError,
    RetryNotAvailableError,
    ScenarioNotFoundError,
    UploadValidationError,
)
from .storage import AnalysisRecord

router = APIRouter(prefix="/api/v1")


def _service(request: Request) -> AnalysisService:
    service: AnalysisService | None = getattr(request.app.state, "analysis_service", None)
    if not service:
        raise HTTPException(status_code=503, detail="Analysis service is starting.")
    return service


def _accepted(record: AnalysisRecord) -> AnalysisAccepted:
    return AnalysisAccepted(
        id=record.id,
        status=record.status,
        created_at=record.created_at,
        updated_at=record.updated_at,
        expires_at=record.expires_at,
    )


def _detail(record: AnalysisRecord) -> AnalysisDetail:
    result = record.result or {}
    raw_versions = result.get("model_versions")
    model_versions = (
        {str(key): str(value) for key, value in raw_versions.items()}
        if isinstance(raw_versions, dict)
        else {}
    )
    raw_windows = result.get("windows")
    windows = raw_windows if isinstance(raw_windows, list) else []
    raw_explanation = result.get("explanation")
    raw_caveats = result.get("caveats")
    caveats = [str(item) for item in raw_caveats] if isinstance(raw_caveats, list) else []
    return AnalysisDetail(
        **_accepted(record).model_dump(),
        source=SourceSummary(
            kind=record.source_kind,
            name=record.source_name,
            line_count=record.line_count,
            synthetic=record.source_kind == "scenario",
        ),
        model_versions=model_versions,
        windows=[WindowResult.model_validate(item) for item in windows],
        explanation=(
            ExplanationResult.model_validate(raw_explanation) if raw_explanation else None
        ),
        caveats=caveats,
        error=AnalysisError.model_validate(record.error) if record.error else None,
    )


def _encode_cursor(offset: int) -> str:
    return base64.urlsafe_b64encode(str(offset).encode()).decode().rstrip("=")


def _decode_cursor(cursor: str | None) -> int:
    if not cursor:
        return 0
    try:
        padded = cursor + "=" * (-len(cursor) % 4)
        offset = int(base64.urlsafe_b64decode(padded).decode())
    except (ValueError, UnicodeDecodeError, binascii.Error) as exc:
        raise HTTPException(status_code=422, detail="Invalid events cursor.") from exc
    if offset < 0:
        raise HTTPException(status_code=422, detail="Invalid events cursor.")
    return offset


@router.get("/health", response_model=HealthResponse)
def health(request: Request) -> HealthResponse:
    settings = request.app.state.settings
    model_ready = (settings.model_dir / "manifest.json").exists()
    return HealthResponse(version=__version__, model_ready=model_ready)


@router.get("/scenarios", response_model=list[ScenarioSummary])
def list_scenarios() -> list[ScenarioSummary]:
    return list_scenario_summaries()


@router.get("/model-card", response_model=ModelCardSummary)
def model_card(request: Request) -> ModelCardSummary:
    return load_model_card(request.app.state.settings.model_dir)


@router.post(
    "/analyses",
    response_model=AnalysisAccepted,
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_analysis(request: Request) -> AnalysisAccepted:
    service = _service(request)
    content_type = request.headers.get("content-type", "").lower()
    try:
        if content_type.startswith("multipart/form-data"):
            form = await request.form()
            upload = form.get("file")
            if not isinstance(upload, UploadFile):
                raise HTTPException(
                    status_code=422,
                    detail="Multipart uploads require a file field.",
                )
            content = await upload.read(service.settings.max_upload_bytes + 1)
            record = service.submit_upload(
                filename=upload.filename or "upload.log",
                content=content,
            )
        elif content_type.startswith("application/json"):
            body: Any = await request.json()
            scenario_id = body.get("scenario_id") if isinstance(body, dict) else None
            if not isinstance(scenario_id, str):
                raise HTTPException(status_code=422, detail="JSON requests require scenario_id.")
            record = service.submit_scenario(scenario_id)
        else:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="Use multipart/form-data or application/json.",
            )
    except UploadValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ScenarioNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Scenario not found.") from exc
    except QueueCapacityError as exc:
        raise HTTPException(status_code=503, detail="The analysis queue is full.") from exc
    return _accepted(record)


@router.get("/analyses/{analysis_id}", response_model=AnalysisDetail)
def get_analysis(analysis_id: str, request: Request) -> AnalysisDetail:
    record = _service(request).get(analysis_id)
    if not record:
        raise HTTPException(status_code=404, detail="Analysis not found.")
    return _detail(record)


@router.get("/analyses/{analysis_id}/events", response_model=EventsPage)
def get_events(
    analysis_id: str,
    request: Request,
    cursor: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
) -> EventsPage:
    record = _service(request).get(analysis_id)
    if not record:
        raise HTTPException(status_code=404, detail="Analysis not found.")
    if record.status == AnalysisStatus.EXPIRED:
        raise HTTPException(status_code=410, detail="Analysis result has expired.")
    if record.status != AnalysisStatus.COMPLETE or not record.result:
        raise HTTPException(status_code=409, detail="Analysis events are not ready.")
    events = record.result.get("events", [])
    if not isinstance(events, list):
        raise HTTPException(status_code=500, detail="Stored events are malformed.")
    offset = _decode_cursor(cursor)
    page = events[offset : offset + limit]
    next_offset = offset + len(page)
    next_cursor = _encode_cursor(next_offset) if next_offset < len(events) else None
    return EventsPage(
        items=[EvidenceLine.model_validate(item) for item in page],
        next_cursor=next_cursor,
    )


@router.post(
    "/analyses/{analysis_id}/retry",
    response_model=AnalysisAccepted,
    status_code=status.HTTP_202_ACCEPTED,
)
def retry_analysis(analysis_id: str, request: Request) -> AnalysisAccepted:
    service = _service(request)
    if not service.get(analysis_id):
        raise HTTPException(status_code=404, detail="Analysis not found.")
    try:
        record = service.retry(analysis_id)
    except RetryNotAvailableError as exc:
        raise HTTPException(
            status_code=409,
            detail="The raw upload was deleted; upload the source log again.",
        ) from exc
    except QueueCapacityError as exc:
        raise HTTPException(status_code=503, detail="The analysis queue is full.") from exc
    return _accepted(record)
