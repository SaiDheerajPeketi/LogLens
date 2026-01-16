from __future__ import annotations

import json
from pathlib import Path

from .schemas import ModelCardSummary


def load_model_card(model_dir: Path) -> ModelCardSummary:
    manifest_path = model_dir / "manifest.json"
    if not manifest_path.exists():
        return ModelCardSummary(
            version="unavailable",
            anomaly_dataset="LogHub HDFS_v1",
            root_cause_dataset="LogLens disclosed synthetic incident corpus",
            anomaly_metrics={},
            root_cause_metrics={},
            limitations=["Packaged models are not available in the configured model directory."],
        )
    manifest = json.loads(manifest_path.read_text())
    metrics = manifest["metrics"]
    return ModelCardSummary(
        version=manifest["version"],
        anomaly_dataset="LogHub HDFS_v1 — 575,061 block traces",
        root_cause_dataset="LogLens disclosed synthetic incident corpus",
        anomaly_metrics={
            name: float(metrics["anomaly"][name])
            for name in ("pr_auc", "f1", "false_positive_rate", "threshold")
        },
        root_cause_metrics={
            "macro_f1": float(metrics["root_cause"]["macro_f1"]),
            "held_out_families": float(metrics["root_cause"]["held_out_families"]),
        },
        limitations=[
            "HDFS evaluates binary anomaly detection, not root-cause classification.",
            "Root-cause metrics use synthetic incidents and do not imply production accuracy.",
            (
                "Generic uploads use a deterministic severity-and-rarity anomaly score because "
                "their event vocabulary differs from HDFS."
            ),
        ],
    )
