from __future__ import annotations

import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from loglens.config import Settings
from loglens.main import create_app

PROJECT_ROOT = Path(__file__).parents[2]


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    settings = Settings(
        database_url=f"sqlite:///{tmp_path / 'loglens.sqlite3'}",
        model_dir=PROJECT_ROOT / "artifacts" / "models",
    )
    with TestClient(create_app(settings)) as test_client:
        yield test_client


def _wait_for_completion(client: TestClient, analysis_id: str) -> dict[str, object]:
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        response = client.get(f"/api/v1/analyses/{analysis_id}")
        assert response.status_code == 200
        payload = response.json()
        if payload["status"] in {"complete", "failed"}:
            return payload
        time.sleep(0.01)
    raise AssertionError("analysis did not finish")


def test_builtin_scenario_returns_cited_evidence(client: TestClient) -> None:
    accepted = client.post(
        "/api/v1/analyses",
        json={"scenario_id": "db-timeout-checkout"},
    )
    assert accepted.status_code == 202

    detail = _wait_for_completion(client, accepted.json()["id"])
    assert detail["status"] == "complete"
    assert detail["source"]["raw_retained"] is False
    anomalous = [window for window in detail["windows"] if window["is_anomaly"]]
    assert anomalous
    assert anomalous[0]["cause"] == "database_timeout"
    assert detail["explanation"]["source"] == "deterministic"

    events_response = client.get(
        f"/api/v1/analyses/{detail['id']}/events",
        params={"limit": 7},
    )
    assert events_response.status_code == 200
    events = events_response.json()
    assert len(events["items"]) == 7
    assert events["next_cursor"]

    all_events = client.get(f"/api/v1/analyses/{detail['id']}/events", params={"limit": 100})
    event_ids = {item["id"] for item in all_events.json()["items"]}
    assert set(detail["explanation"]["citations"]).issubset(event_ids)


def test_upload_is_redacted_and_cannot_be_retried(client: TestClient) -> None:
    upload = "\n".join(
        [
            "2026-04-18T09:00:00 INFO request accepted user_id=alice@example.com",
            "2026-04-18T09:01:00 WARN subsystem=network resolver=service-dns degraded",
            "2026-04-18T09:02:00 ERROR DNS lookup failed host=10.1.2.3",
            "2026-04-18T09:03:00 ERROR NXDOMAIN token=top-secret",
            "2026-04-18T09:04:00 ERROR endpoint resolution failed",
        ]
    )
    accepted = client.post(
        "/api/v1/analyses",
        files={"file": ("incident.log", upload, "text/plain")},
    )
    assert accepted.status_code == 202

    detail = _wait_for_completion(client, accepted.json()["id"])
    assert detail["status"] == "complete"
    events = client.get(f"/api/v1/analyses/{detail['id']}/events").text
    assert "alice@example.com" not in events
    assert "10.1.2.3" not in events
    assert "top-secret" not in events
    assert "[SECRET]" in events

    retry = client.post(f"/api/v1/analyses/{detail['id']}/retry")
    assert retry.status_code == 409
    assert "upload" in retry.json()["detail"].lower()


@pytest.mark.parametrize("scenario_id", ["healthy-checkout", "ambiguous-degradation"])
def test_non_actionable_scenarios_are_explicit(
    client: TestClient,
    scenario_id: str,
) -> None:
    accepted = client.post("/api/v1/analyses", json={"scenario_id": scenario_id})
    detail = _wait_for_completion(client, accepted.json()["id"])

    if scenario_id == "healthy-checkout":
        assert not any(window["is_anomaly"] for window in detail["windows"])
        assert detail["explanation"]["confidence"] == 0
    else:
        anomalous = [window for window in detail["windows"] if window["is_anomaly"]]
        assert anomalous[0]["cause"] == "unknown"
        assert anomalous[0]["confidence"] < 0.5
        assert "human review" in anomalous[0]["caveats"][0].lower()


def test_invalid_upload_and_unknown_scenario_are_rejected(client: TestClient) -> None:
    binary = client.post(
        "/api/v1/analyses",
        files={"file": ("archive.zip", b"PK\x00\x01", "application/zip")},
    )
    missing = client.post("/api/v1/analyses", json={"scenario_id": "missing"})

    assert binary.status_code == 422
    assert missing.status_code == 404
