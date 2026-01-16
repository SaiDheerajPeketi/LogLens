from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import zipfile
from pathlib import Path
from urllib.request import urlopen

from .ml.datasets import (
    HDFS_ARCHIVE_SHA256,
    HDFS_ARCHIVE_URL,
    HDFS_LABELS_SHA256,
    HDFS_MATRIX_SHA256,
    verify_sha256,
)
from .ml.training import train_all


def _download(url: str, destination: Path, expected_sha256: str) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    with urlopen(url) as response, destination.open("wb") as target:  # noqa: S310
        while chunk := response.read(1024 * 1024):
            target.write(chunk)
            digest.update(chunk)
    if digest.hexdigest() != expected_sha256:
        destination.unlink(missing_ok=True)
        raise RuntimeError(f"Checksum mismatch for {destination.name}")


def _extract_hdfs_assets(archive_path: Path, destination: Path) -> None:
    members = {
        "preprocessed/Event_occurrence_matrix.csv": "Event_occurrence_matrix.csv",
        "preprocessed/anomaly_label.csv": "anomaly_label.csv",
        "preprocessed/HDFS.log_templates.csv": "HDFS.log_templates.csv",
    }
    destination.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive_path) as archive:
        for member, filename in members.items():
            with archive.open(member) as source, (destination / filename).open("wb") as target:
                shutil.copyfileobj(source, target)
    verify_sha256(destination / "Event_occurrence_matrix.csv", HDFS_MATRIX_SHA256)
    verify_sha256(destination / "anomaly_label.csv", HDFS_LABELS_SHA256)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="loglens")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("download-data", help="Download the official LogHub HDFS_v1 data")
    train = subparsers.add_parser("train", help="Train and evaluate both LogLens models")
    train.add_argument(
        "--structured",
        type=Path,
        default=Path("data/downloads/hdfs_v1/Event_occurrence_matrix.csv"),
    )
    train.add_argument(
        "--labels",
        type=Path,
        default=Path("data/downloads/hdfs_v1/anomaly_label.csv"),
    )
    train.add_argument("--model-dir", type=Path, default=Path("artifacts/models"))
    train.add_argument("--evaluation-dir", type=Path, default=Path("artifacts/evaluation"))
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "download-data":
        archive_path = Path("data/downloads/HDFS_v1.zip")
        _download(HDFS_ARCHIVE_URL, archive_path, HDFS_ARCHIVE_SHA256)
        _extract_hdfs_assets(archive_path, Path("data/downloads/hdfs_v1"))
        print("Downloaded, extracted, and verified the HDFS_v1 evaluation assets.")
        return
    metrics = train_all(
        args.structured,
        args.labels,
        model_dir=args.model_dir,
        evaluation_dir=args.evaluation_dir,
    )
    print(json.dumps(metrics, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
