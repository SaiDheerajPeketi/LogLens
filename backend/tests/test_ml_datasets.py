from collections import Counter

from loglens.ml.datasets import generate_synthetic_incidents
from loglens.schemas import CauseClass


def test_synthetic_dataset_is_balanced_and_family_disjoint() -> None:
    incidents = generate_synthetic_incidents(samples_per_family=4)

    counts = Counter(incident.cause for incident in incidents)
    assert set(counts) == set(CauseClass)
    assert len(set(counts.values())) == 1

    split_families = {
        split: {incident.family for incident in incidents if incident.split == split}
        for split in ("train", "validation", "test")
    }
    assert split_families["train"].isdisjoint(split_families["validation"])
    assert split_families["train"].isdisjoint(split_families["test"])
    assert split_families["validation"].isdisjoint(split_families["test"])


def test_every_synthetic_incident_has_repeated_cause_evidence() -> None:
    incidents = generate_synthetic_incidents(samples_per_family=2)

    assert all(incident.text.count("ERROR") >= 2 for incident in incidents)

