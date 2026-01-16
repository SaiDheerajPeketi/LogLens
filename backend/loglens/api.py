from fastapi import APIRouter

from . import __version__
from .catalog import MODEL_CARD, SCENARIOS
from .config import get_settings
from .schemas import HealthResponse, ModelCardSummary, ScenarioSummary

router = APIRouter(prefix="/api/v1")


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    settings = get_settings()
    model_ready = (settings.model_dir / "manifest.json").exists()
    return HealthResponse(version=__version__, model_ready=model_ready)


@router.get("/scenarios", response_model=list[ScenarioSummary])
def list_scenarios() -> list[ScenarioSummary]:
    return SCENARIOS


@router.get("/model-card", response_model=ModelCardSummary)
def model_card() -> ModelCardSummary:
    return MODEL_CARD

