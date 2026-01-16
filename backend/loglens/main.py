from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .api import router
from .config import Settings, get_settings
from .explainers import Explainer
from .service import AnalysisService


def create_app(
    settings: Settings | None = None,
    *,
    explainer: Explainer | None = None,
) -> FastAPI:
    active_settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        service = AnalysisService(active_settings, explainer=explainer)
        app.state.analysis_service = service
        service.start()
        try:
            yield
        finally:
            service.stop()

    app = FastAPI(
        title=active_settings.app_name,
        version="0.1.0",
        description="Evidence-first log anomaly detection and root-cause analysis.",
        lifespan=lifespan,
    )
    app.state.settings = active_settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://localhost:8080"],
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )
    app.include_router(router)
    if active_settings.static_dir.exists():
        assets_dir = active_settings.static_dir / "assets"
        if assets_dir.exists():
            app.mount("/assets", StaticFiles(directory=assets_dir), name="frontend-assets")

        @app.get("/{path:path}", include_in_schema=False)
        def frontend(path: str) -> FileResponse:
            if path.startswith("api/"):
                raise HTTPException(status_code=404, detail="API route not found.")
            return FileResponse(active_settings.static_dir / "index.html")

    return app


app = create_app()
