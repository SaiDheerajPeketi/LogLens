from __future__ import annotations

import queue
import secrets
import threading
from functools import partial

from .analysis import AnalysisEngine
from .config import Settings
from .explainers import Explainer, build_explainer
from .ingestion import UploadValidationError, redact_text, validate_upload
from .scenarios import SCENARIO_CATALOG
from .storage import AnalysisRecord, AnalysisStore


class QueueCapacityError(RuntimeError):
    """Raised when the bounded analysis queue cannot accept more work."""


class ScenarioNotFoundError(KeyError):
    """Raised when a requested built-in scenario does not exist."""


class RetryNotAvailableError(RuntimeError):
    """Raised when a source must be resubmitted instead of retried."""


class AnalysisService:
    def __init__(self, settings: Settings, *, explainer: Explainer | None = None) -> None:
        self.settings = settings
        self.store = AnalysisStore(
            settings.database_url,
            ttl_hours=settings.result_ttl_hours,
        )
        self.engine = AnalysisEngine(
            model_dir=settings.model_dir,
            explainer=explainer or build_explainer(model=settings.openai_model),
        )
        self.queue: queue.Queue[str | None] = queue.Queue(maxsize=settings.queue_capacity)
        self.worker = threading.Thread(
            target=self._run,
            name="loglens-analysis-worker",
            daemon=True,
        )

    def start(self) -> None:
        self.store.initialize()
        self.worker.start()

    def stop(self) -> None:
        try:
            self.queue.put_nowait(None)
        except queue.Full:
            self.queue.put(None, timeout=2)
        self.worker.join(timeout=5)
        self.store.close()

    def _enqueue(self, record: AnalysisRecord) -> AnalysisRecord:
        try:
            self.queue.put_nowait(record.id)
        except queue.Full as exc:
            self.store.fail(
                record.id,
                code="queue_full",
                message="The local analysis queue is full.",
                retryable=record.retryable,
                action="Wait for the current analysis to finish, then try again.",
            )
            raise QueueCapacityError from exc
        return record

    def submit_scenario(self, scenario_id: str) -> AnalysisRecord:
        scenario = SCENARIO_CATALOG.get(scenario_id)
        if not scenario:
            raise ScenarioNotFoundError(scenario_id)
        redacted = [redact_text(line, salt=scenario_id) for line in scenario.lines]
        record = self.store.create(
            source_kind="scenario",
            source_name=scenario.summary.name,
            scenario_id=scenario_id,
            redacted_lines=redacted,
            retryable=True,
        )
        return self._enqueue(record)

    def submit_upload(self, *, filename: str, content: bytes) -> AnalysisRecord:
        lines = validate_upload(
            filename,
            content,
            max_bytes=self.settings.max_upload_bytes,
            max_lines=self.settings.max_log_lines,
        )
        salt = secrets.token_hex(16)
        redacted = [redact_text(line, salt=salt) for line in lines]
        record = self.store.create(
            source_kind="upload",
            source_name=filename,
            redacted_lines=redacted,
            retryable=False,
        )
        return self._enqueue(record)

    def retry(self, analysis_id: str) -> AnalysisRecord:
        current = self.store.get(analysis_id)
        if not current or current.source_kind != "scenario" or not current.scenario_id:
            raise RetryNotAvailableError
        scenario = SCENARIO_CATALOG[current.scenario_id]
        redacted = [redact_text(line, salt=current.scenario_id) for line in scenario.lines]
        reset = self.store.reset_scenario(analysis_id, redacted)
        if not reset:
            raise RetryNotAvailableError
        return self._enqueue(reset)

    def get(self, analysis_id: str) -> AnalysisRecord | None:
        return self.store.get(analysis_id)

    def _run(self) -> None:
        while True:
            analysis_id = self.queue.get()
            if analysis_id is None:
                self.queue.task_done()
                return
            record = self.store.get(analysis_id)
            if not record or not record.redacted_lines:
                self.queue.task_done()
                continue
            try:
                current_id = record.id
                result = self.engine.analyze(
                    redacted_lines=record.redacted_lines,
                    analysis_id=current_id,
                    status=partial(self.store.update_status, current_id),
                )
                self.store.complete(record.id, result)
            except Exception:
                self.store.fail(
                    record.id,
                    code="analysis_failed",
                    message="The analysis pipeline could not complete this source.",
                    retryable=record.retryable,
                    action=(
                        "Retry the built-in scenario."
                        if record.retryable
                        else "Upload the source log again."
                    ),
                )
            finally:
                self.queue.task_done()


__all__ = [
    "AnalysisService",
    "QueueCapacityError",
    "RetryNotAvailableError",
    "ScenarioNotFoundError",
    "UploadValidationError",
]
