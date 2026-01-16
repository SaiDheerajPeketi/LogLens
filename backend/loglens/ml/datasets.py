from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from loglens.schemas import CauseClass

HDFS_ARCHIVE_URL = "https://zenodo.org/records/8196385/files/HDFS_v1.zip?download=1"
HDFS_ARCHIVE_SHA256 = "04f919f2185821f23f045dca611a7586429bdabc601bd7b43f30005f8e289b01"
HDFS_MATRIX_SHA256 = "59ab8b8a6d12f18f41b35e9eb0113655825b9bf9d9787c1a6f72fface7cc01a7"
HDFS_LABELS_SHA256 = "1c711ed6c8848fc3243fb4d092f172f31d128c8a6ec7f26ebba72ab931885ed8"


@dataclass(frozen=True, slots=True)
class SyntheticIncident:
    id: str
    cause: CauseClass
    family: str
    split: str
    text: str


_BASELINES = (
    "INFO request accepted by gateway",
    "INFO health probe completed status=200",
    "DEBUG worker heartbeat recorded",
    "INFO metrics batch flushed",
    "DEBUG configuration cache hit",
)

_CAUSE_MARKERS: dict[CauseClass, str] = {
    CauseClass.DATABASE_TIMEOUT: "WARN subsystem=database dependency=db-primary degraded",
    CauseClass.AUTHENTICATION_FAILURE: "WARN subsystem=identity auth-gateway degraded",
    CauseClass.CONNECTION_POOL_EXHAUSTION: (
        "WARN subsystem=database resource=connection-pool saturated"
    ),
    CauseClass.DISK_PRESSURE: "WARN subsystem=storage volume=data degraded",
    CauseClass.NETWORK_DNS_FAILURE: "WARN subsystem=network resolver=service-dns degraded",
    CauseClass.UNKNOWN: "WARN subsystem=unclassified signature=unsupported",
}

_CAUSE_TEMPLATES: dict[CauseClass, tuple[tuple[str, ...], ...]] = {
    CauseClass.DATABASE_TIMEOUT: (
        ("WARN database latency above threshold", "ERROR query timed out after {ms}ms"),
        ("WARN slow SQL execution detected", "ERROR database deadline exceeded"),
        ("WARN replica response delayed", "ERROR transaction timed out"),
        ("WARN datastore round trip degraded", "ERROR DB_TIMEOUT while reading orders"),
        ("WARN query queue depth={count}", "ERROR statement cancelled by timeout"),
        ("WARN persistence layer is slow", "ERROR deadline reached awaiting database response"),
    ),
    CauseClass.AUTHENTICATION_FAILURE: (
        ("WARN token verification failed", "ERROR AUTH-401 invalid bearer token"),
        ("WARN signing key expired", "ERROR request rejected as unauthenticated"),
        ("WARN session signature mismatch", "ERROR access denied for principal"),
        ("WARN identity provider rejected assertion", "ERROR authentication failed"),
        ("WARN JWT audience mismatch", "ERROR credential validation denied"),
        ("WARN login proof could not be verified", "ERROR caller identity is invalid"),
    ),
    CauseClass.CONNECTION_POOL_EXHAUSTION: (
        ("WARN connection pool utilization=100", "ERROR no connection available"),
        ("WARN checkout waiters={count}", "ERROR pool acquisition timed out"),
        ("WARN active connections reached max", "ERROR connection lease unavailable"),
        ("WARN database pool queue growing", "ERROR POOL-503 capacity exhausted"),
        ("WARN idle connections=0", "ERROR timed out waiting for pooled resource"),
        ("WARN every connection is leased", "ERROR could not acquire database handle"),
    ),
    CauseClass.DISK_PRESSURE: (
        ("WARN disk usage={percent}%", "ERROR no space left on device"),
        ("WARN filesystem capacity critical", "ERROR write failed ENOSPC"),
        ("WARN volume free bytes below threshold", "ERROR journal append rejected"),
        ("WARN storage watermark exceeded", "ERROR DISK-507 insufficient storage"),
        ("WARN inode availability low", "ERROR temporary file could not be created"),
        ("WARN data volume is full", "ERROR persistence failed for lack of disk space"),
    ),
    CauseClass.NETWORK_DNS_FAILURE: (
        ("WARN DNS lookup latency high", "ERROR host name could not be resolved"),
        ("WARN upstream connection reset", "ERROR network route unavailable"),
        ("WARN resolver retry={count}", "ERROR NXDOMAIN from nameserver"),
        ("WARN packet loss detected", "ERROR NET-502 upstream unreachable"),
        ("WARN socket handshake timed out", "ERROR connection refused by peer"),
        ("WARN service discovery returned no address", "ERROR endpoint resolution failed"),
    ),
    CauseClass.UNKNOWN: (
        ("WARN cache eviction rate increased", "ERROR operation failed for unclassified reason"),
        ("WARN response payload changed", "ERROR downstream returned unexpected status"),
        ("WARN scheduler delay detected", "ERROR task ended without a known cause"),
        ("WARN feature flag mismatch", "ERROR UNKNOWN-520 generic service failure"),
        ("WARN dependency reported degraded", "ERROR failure signature is unsupported"),
        ("WARN anomaly lacks a recognized signature", "ERROR human review is required"),
    ),
}


def _render_incident(cause: CauseClass, cause_lines: tuple[str, ...], seed: int) -> str:
    rng = random.Random(seed)
    lines = [rng.choice(_BASELINES) for _ in range(rng.randint(8, 14))]
    inserts = [_CAUSE_MARKERS[cause]] + [
        line.format(
            ms=rng.choice((750, 1200, 2500, 5000)),
            count=rng.randint(12, 80),
            percent=rng.randint(91, 100),
        )
        for line in cause_lines
    ]
    position = rng.randint(2, max(2, len(lines) - 2))
    lines[position:position] = inserts * rng.randint(2, 4)
    return "\n".join(lines)


def generate_synthetic_incidents(samples_per_family: int = 25) -> list[SyntheticIncident]:
    incidents: list[SyntheticIncident] = []
    for cause_index, (cause, families) in enumerate(_CAUSE_TEMPLATES.items()):
        for family_index, family_lines in enumerate(families):
            split = "train" if family_index < 4 else "validation" if family_index == 4 else "test"
            family_name = f"{cause.value}-{family_index}"
            for sample_index in range(samples_per_family):
                seed = cause_index * 10_000 + family_index * 100 + sample_index
                incidents.append(
                    SyntheticIncident(
                        id=f"syn-{seed:05d}",
                        cause=cause,
                        family=family_name,
                        split=split,
                        text=_render_incident(cause, family_lines, seed),
                    )
                )
    return incidents


def verify_sha256(path: Path, expected: str) -> None:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != expected:
        raise ValueError(f"Checksum mismatch for {path}: expected {expected}, got {digest}")


def load_hdfs_features(structured_path: Path, labels_path: Path) -> tuple[pd.DataFrame, pd.Series]:
    verify_sha256(structured_path, HDFS_MATRIX_SHA256)
    verify_sha256(labels_path, HDFS_LABELS_SHA256)

    occurrence = pd.read_csv(structured_path).set_index("BlockId")
    labels = pd.read_csv(labels_path).set_index("BlockId")["Label"]
    features = occurrence.drop(columns=["Label", "Type"], errors="ignore").astype(float)
    features["trace:length"] = features.sum(axis=1)
    features["trace:unique_events"] = (features > 0).sum(axis=1)
    target = features.index.to_series().map(labels).map({"Normal": 0, "Anomaly": 1})
    valid = target.notna()
    return features.loc[valid], target.loc[valid].astype(int)
