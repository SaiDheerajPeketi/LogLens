from __future__ import annotations

import json
import os
import subprocess
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from xgboost import XGBClassifier

from .datasets import (
    HDFS_LABELS_SHA256,
    HDFS_MATRIX_SHA256,
    SyntheticIncident,
    generate_synthetic_incidents,
    load_hdfs_features,
)

RANDOM_STATE = 42


def _false_positive_rate(target: np.ndarray, predicted: np.ndarray) -> float:
    tn, fp, _, _ = confusion_matrix(target, predicted, labels=[0, 1]).ravel()
    return float(fp / max(1, fp + tn))


def _cost_weighted_score(target: np.ndarray, predicted: np.ndarray) -> float:
    tn, fp, fn, tp = confusion_matrix(target, predicted, labels=[0, 1]).ravel()
    total_cost = 10 * fn + fp
    worst_cost = 10 * (fn + tp) + fp + tn
    return float(1 - total_cost / max(1, worst_cost))


def _select_threshold(target: np.ndarray, scores: np.ndarray) -> float:
    candidates: list[tuple[float, float, float]] = []
    for threshold in np.linspace(0.05, 0.95, 91):
        predicted = (scores >= threshold).astype(int)
        candidates.append(
            (
                float(threshold),
                float(f1_score(target, predicted, zero_division=0)),
                _false_positive_rate(target, predicted),
            )
        )
    within_budget = [candidate for candidate in candidates if candidate[2] <= 0.05]
    pool = within_budget or candidates
    return max(pool, key=lambda candidate: (candidate[1], -candidate[2]))[0]


def train_anomaly_model(
    structured_path: Path,
    labels_path: Path,
) -> tuple[dict[str, Any], dict[str, float], pd.DataFrame, pd.DataFrame]:
    features, target = load_hdfs_features(structured_path, labels_path)
    train_x, remainder_x, train_y, remainder_y = train_test_split(
        features,
        target,
        test_size=0.4,
        stratify=target,
        random_state=RANDOM_STATE,
    )
    validation_x, test_x, validation_y, test_y = train_test_split(
        remainder_x,
        remainder_y,
        test_size=0.5,
        stratify=remainder_y,
        random_state=RANDOM_STATE,
    )
    positive = int(train_y.sum())
    negative = int(len(train_y) - positive)
    model = XGBClassifier(
        n_estimators=180,
        max_depth=4,
        learning_rate=0.06,
        subsample=0.9,
        colsample_bytree=0.9,
        min_child_weight=2,
        reg_lambda=1.5,
        eval_metric="logloss",
        scale_pos_weight=negative / max(1, positive),
        random_state=RANDOM_STATE,
        n_jobs=2,
    )
    model.fit(train_x, train_y)
    threshold = _select_threshold(validation_y.to_numpy(), model.predict_proba(validation_x)[:, 1])
    scores = model.predict_proba(test_x)[:, 1]
    predicted = (scores >= threshold).astype(int)
    matrix = confusion_matrix(test_y, predicted, labels=[0, 1])
    true_negative, false_positive, false_negative, true_positive = matrix.ravel()
    metrics = {
        "pr_auc": float(average_precision_score(test_y, scores)),
        "precision": float(precision_score(test_y, predicted, zero_division=0)),
        "recall": float(recall_score(test_y, predicted, zero_division=0)),
        "f1": float(f1_score(test_y, predicted, zero_division=0)),
        "false_positive_rate": _false_positive_rate(test_y.to_numpy(), predicted),
        "cost_weighted_score": _cost_weighted_score(test_y.to_numpy(), predicted),
        "threshold": threshold,
        "train_traces": float(len(train_y)),
        "validation_traces": float(len(validation_y)),
        "test_traces": float(len(test_y)),
        "true_negative": float(true_negative),
        "false_positive": float(false_positive),
        "false_negative": float(false_negative),
        "true_positive": float(true_positive),
    }
    confusion = pd.DataFrame(
        matrix,
        index=["actual_normal", "actual_anomaly"],
        columns=["predicted_normal", "predicted_anomaly"],
    )
    curve_precision, curve_recall, curve_thresholds = precision_recall_curve(test_y, scores)
    precision_recall = pd.DataFrame(
        {
            "precision": curve_precision,
            "recall": curve_recall,
            "threshold": np.append(curve_thresholds, np.nan),
        }
    )
    bundle = {
        "model": model,
        "feature_names": list(features.columns),
        "threshold": threshold,
        "dataset": "LogHub HDFS_v1 (Zenodo record 8196385)",
        "random_state": RANDOM_STATE,
    }
    return bundle, metrics, confusion, precision_recall


def _sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _build_commit() -> str:
    if supplied := os.getenv("LOGLENS_BUILD_COMMIT"):
        return supplied
    result = subprocess.run(  # noqa: S603
        ["git", "rev-parse", "HEAD"],
        capture_output=True,
        check=False,
        text=True,
    )
    return result.stdout.strip() if result.returncode == 0 else "unavailable"


def _incidents_for_split(
    incidents: list[SyntheticIncident], split: str
) -> tuple[list[str], list[str]]:
    selected = [incident for incident in incidents if incident.split == split]
    return [incident.text for incident in selected], [incident.cause.value for incident in selected]


def train_root_cause_model() -> tuple[
    Pipeline,
    dict[str, float],
    pd.DataFrame,
    list[dict[str, str]],
]:
    incidents = generate_synthetic_incidents()
    train_text, train_target = _incidents_for_split(incidents, "train")
    validation_text, validation_target = _incidents_for_split(incidents, "validation")
    test_text, test_target = _incidents_for_split(incidents, "test")
    train_text += validation_text
    train_target += validation_target

    base = LogisticRegression(
        class_weight="balanced",
        max_iter=2_000,
        random_state=RANDOM_STATE,
        solver="lbfgs",
    )
    model = Pipeline(
        [
            ("vectorizer", TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=8_000)),
            ("classifier", CalibratedClassifierCV(base, method="sigmoid", cv=3)),
        ]
    )
    model.fit(train_text, train_target)
    predicted = model.predict(test_text)
    metrics = {
        "macro_f1": float(f1_score(test_target, predicted, average="macro")),
        "weighted_f1": float(f1_score(test_target, predicted, average="weighted")),
        "test_incidents": float(len(test_target)),
        "correct_incidents": float(
            sum(
                actual == guess
                for actual, guess in zip(test_target, predicted, strict=True)
            )
        ),
        "held_out_families": float(
            len({incident.family for incident in incidents if incident.split == "test"})
        ),
    }
    labels = sorted(set(test_target))
    confusion = pd.DataFrame(
        confusion_matrix(test_target, predicted, labels=labels),
        index=[f"actual_{label}" for label in labels],
        columns=[f"predicted_{label}" for label in labels],
    )
    disclosure = [
        {
            "id": incident.id,
            "cause": incident.cause.value,
            "family": incident.family,
            "split": incident.split,
            "sha256": __import__("hashlib").sha256(incident.text.encode()).hexdigest(),
        }
        for incident in incidents
    ]
    return model, metrics, confusion, disclosure


def _write_evaluation_markdown(path: Path, metrics: dict[str, Any]) -> None:
    anomaly = metrics["anomaly"]
    root_cause = metrics["root_cause"]
    path.write_text(
        "\n".join(
            [
                "# LogLens Evaluation",
                "",
                (
                    "These are measured results from the committed training pipeline, "
                    "not projected targets."
                ),
                "",
                "## Anomaly detection — LogHub HDFS_v1",
                "",
                f"- PR-AUC: **{anomaly['pr_auc']:.4f}**",
                f"- Precision: **{anomaly['precision']:.4f}**",
                f"- Recall: **{anomaly['recall']:.4f}**",
                f"- F1: **{anomaly['f1']:.4f}**",
                f"- False-positive rate: **{anomaly['false_positive_rate']:.4f}**",
                (
                    "- Cost-weighted score (missed anomaly = 10× false alarm): "
                    f"**{anomaly['cost_weighted_score']:.4f}**"
                ),
                f"- Validation-selected decision threshold: **{anomaly['threshold']:.2f}**",
                f"- Held-out test traces: **{int(anomaly['test_traces']):,}**",
                "",
                (
                    "The dataset is split by block trace. The threshold is selected on "
                    "validation data and reported once on the held-out test traces."
                ),
                "",
                "| Actual \\ Predicted | Normal | Anomaly |",
                "| --- | ---: | ---: |",
                (
                    f"| Normal | {int(anomaly['true_negative']):,} | "
                    f"{int(anomaly['false_positive']):,} |"
                ),
                (
                    f"| Anomaly | {int(anomaly['false_negative']):,} | "
                    f"{int(anomaly['true_positive']):,} |"
                ),
                "",
                "## Root-cause classification — disclosed synthetic incidents",
                "",
                f"- Macro F1: **{root_cause['macro_f1']:.4f}**",
                f"- Weighted F1: **{root_cause['weighted_f1']:.4f}**",
                f"- Held-out test incidents: **{int(root_cause['test_incidents'])}**",
                f"- Held-out scenario families: **{int(root_cause['held_out_families'])}**",
                "",
                (
                    "Each cause keeps one wording family completely outside training. "
                    "These numbers measure generalization across authored templates, "
                    "not real-world RCA accuracy."
                ),
                "",
                (
                    f"The held-out confusion matrix contains "
                    f"{int(root_cause['correct_incidents'])} correct predictions out of "
                    f"{int(root_cause['test_incidents'])} incidents."
                ),
                "",
                "## Explanation integrity",
                "",
                (
                    "Citation validation is structural: the service rejects any explanation "
                    "whose line IDs are not present in the evidence supplied to the "
                    "explainer. Deterministic fallback covers every invalid or unavailable "
                    "API response."
                ),
                "",
                "## Limitations",
                "",
                (
                    "- HDFS labels normal/anomaly traces; it does not validate the "
                    "root-cause classifier."
                ),
                "- Synthetic RCA metrics cannot be interpreted as production incident accuracy.",
                (
                "- Uploaded formats outside the known patterns may fall back to "
                    "coarse line windows."
                ),
                "",
                "## Machine-readable artifacts",
                "",
                "- `artifacts/evaluation/metrics.json`",
                "- `artifacts/evaluation/anomaly_confusion.csv`",
                "- `artifacts/evaluation/anomaly_precision_recall.csv`",
                "- `artifacts/evaluation/root_cause_confusion.csv`",
                "- `artifacts/evaluation/synthetic_manifest.json`",
                "",
                "## Reproduce",
                "",
                "```bash",
                "python -m loglens.cli download-data",
                "python -m loglens.cli train \\",
                "  --structured data/downloads/hdfs_v1/Event_occurrence_matrix.csv \\",
                "  --labels data/downloads/hdfs_v1/anomaly_label.csv",
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )


def train_all(
    structured_path: Path,
    labels_path: Path,
    *,
    model_dir: Path,
    evaluation_dir: Path,
) -> dict[str, Any]:
    model_dir.mkdir(parents=True, exist_ok=True)
    evaluation_dir.mkdir(parents=True, exist_ok=True)

    anomaly_bundle, anomaly_metrics, anomaly_confusion, precision_recall = (
        train_anomaly_model(structured_path, labels_path)
    )
    root_cause_model, root_cause_metrics, rca_confusion, disclosure = train_root_cause_model()
    anomaly_path = model_dir / "anomaly_bundle.joblib"
    root_cause_path = model_dir / "rca_bundle.joblib"
    joblib.dump(anomaly_bundle, anomaly_path)
    joblib.dump(root_cause_model, root_cause_path)

    metrics: dict[str, Any] = {
        "generated_at": datetime.now(UTC).isoformat(),
        "random_state": RANDOM_STATE,
        "anomaly": anomaly_metrics,
        "root_cause": root_cause_metrics,
    }
    (evaluation_dir / "metrics.json").write_text(
        json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    anomaly_confusion.to_csv(evaluation_dir / "anomaly_confusion.csv")
    precision_recall.to_csv(evaluation_dir / "anomaly_precision_recall.csv", index=False)
    rca_confusion.to_csv(evaluation_dir / "root_cause_confusion.csv")
    (evaluation_dir / "synthetic_manifest.json").write_text(
        json.dumps(disclosure, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    manifest = {
        "version": "hdfsv1-synthetic-rca-v1",
        "generated_at": metrics["generated_at"],
        "anomaly_model": "anomaly_bundle.joblib",
        "root_cause_model": "rca_bundle.joblib",
        "metrics": metrics,
        "feature_schema": (
            "HDFS event-count vectors plus trace length and unique-event count; "
            "synthetic incident word/bigram TF-IDF"
        ),
        "dataset": {
            "name": "LogHub HDFS_v1",
            "version": "Zenodo record 8196385",
            "event_matrix_sha256": HDFS_MATRIX_SHA256,
            "labels_sha256": HDFS_LABELS_SHA256,
        },
        "build_commit": _build_commit(),
        "checksums": {
            "anomaly_bundle_sha256": _sha256_file(anomaly_path),
            "root_cause_bundle_sha256": _sha256_file(root_cause_path),
        },
        "random_state": RANDOM_STATE,
    }
    (model_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    _write_evaluation_markdown(Path("docs/EVALUATION.md"), metrics)
    return metrics
