from pathlib import Path

from loglens.runtime_evaluation import evaluate_runtime

PROJECT_ROOT = Path(__file__).parents[2]


def test_runtime_evaluation_meets_integrity_targets() -> None:
    metrics = evaluate_runtime(PROJECT_ROOT / "artifacts" / "models")
    summary = metrics["summary"]

    assert summary["analyses"] == 6
    assert summary["cases_passed"] == 6
    assert summary["citation_validity_rate"] == 1.0
    assert summary["invalid_citations_rejected"] == 1
    assert summary["raw_upload_files_retained"] == 0
    assert summary["raw_markers_found_in_persistence"] == 0
