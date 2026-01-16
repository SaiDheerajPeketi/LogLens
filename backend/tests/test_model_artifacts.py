import hashlib
import json
from pathlib import Path

import joblib

PROJECT_ROOT = Path(__file__).parents[2]
MODEL_DIR = PROJECT_ROOT / "artifacts" / "models"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_packaged_models_match_manifest_checksums() -> None:
    manifest = json.loads((MODEL_DIR / "manifest.json").read_text())

    anomaly_path = MODEL_DIR / manifest["anomaly_model"]
    root_cause_path = MODEL_DIR / manifest["root_cause_model"]
    assert _sha256(anomaly_path) == manifest["checksums"]["anomaly_bundle_sha256"]
    assert _sha256(root_cause_path) == manifest["checksums"]["root_cause_bundle_sha256"]


def test_packaged_models_are_loadable() -> None:
    anomaly = joblib.load(MODEL_DIR / "anomaly_bundle.joblib")
    root_cause = joblib.load(MODEL_DIR / "rca_bundle.joblib")

    assert 0 < anomaly["threshold"] < 1
    assert anomaly["feature_names"]
    assert set(root_cause.named_steps) == {"vectorizer", "classifier"}
