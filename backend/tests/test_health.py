from fastapi.testclient import TestClient
from loglens.main import create_app

client = TestClient(create_app())


def test_health_reports_service_version() -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["service"] == "loglens-api"
    assert payload["version"] == "0.1.0"


def test_scenarios_are_disclosed_as_synthetic() -> None:
    response = client.get("/api/v1/scenarios")

    assert response.status_code == 200
    scenarios = response.json()
    assert len(scenarios) >= 3
    assert all(scenario["synthetic"] is True for scenario in scenarios)


def test_model_card_separates_datasets() -> None:
    response = client.get("/api/v1/model-card")

    assert response.status_code == 200
    payload = response.json()
    assert "HDFS" in payload["anomaly_dataset"]
    assert "synthetic" in payload["root_cause_dataset"].lower()

