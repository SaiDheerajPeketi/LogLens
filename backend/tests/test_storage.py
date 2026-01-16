from pathlib import Path

from loglens.schemas import AnalysisStatus
from loglens.storage import AnalysisStore


def test_expiry_removes_redacted_derived_data(tmp_path: Path) -> None:
    store = AnalysisStore(f"sqlite:///{tmp_path / 'expiry.sqlite3'}", ttl_hours=0)
    store.initialize()
    created = store.create(
        source_kind="upload",
        source_name="incident.log",
        redacted_lines=["ERROR token=[SECRET]"],
        retryable=False,
    )

    expired = store.get(created.id)

    assert expired is not None
    assert expired.status == AnalysisStatus.EXPIRED
    assert expired.redacted_lines is None
    assert expired.result is None
    store.close()


def test_startup_marks_interrupted_work_failed(tmp_path: Path) -> None:
    database_url = f"sqlite:///{tmp_path / 'restart.sqlite3'}"
    first = AnalysisStore(database_url, ttl_hours=24)
    first.initialize()
    created = first.create(
        source_kind="scenario",
        source_name="Database timeout",
        scenario_id="db-timeout-checkout",
        redacted_lines=["ERROR query timed out"],
        retryable=True,
    )
    first.close()

    restarted = AnalysisStore(database_url, ttl_hours=24)
    restarted.initialize()
    recovered = restarted.get(created.id)

    assert recovered is not None
    assert recovered.status == AnalysisStatus.FAILED
    assert recovered.error is not None
    assert recovered.error["code"] == "interrupted"
    restarted.close()
