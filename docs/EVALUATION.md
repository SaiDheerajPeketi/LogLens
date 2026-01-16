# LogLens Evaluation

These are measured results from the committed training pipeline, not projected targets.

## Anomaly detection — LogHub HDFS_v1

- PR-AUC: **0.9994**
- Precision: **0.9926**
- Recall: **0.9985**
- F1: **0.9956**
- False-positive rate: **0.0002**
- Cost-weighted score (missed anomaly = 10× false alarm): **0.9995**
- Validation-selected decision threshold: **0.65**
- Held-out test traces: **115,013**

The dataset is split by block trace. The threshold is selected on validation data and reported once on the held-out test traces.

| Actual \ Predicted | Normal | Anomaly |
| --- | ---: | ---: |
| Normal | 111,620 | 25 |
| Anomaly | 5 | 3,363 |

## Root-cause classification — disclosed synthetic incidents

- Macro F1: **1.0000**
- Weighted F1: **1.0000**
- Held-out test incidents: **150**
- Held-out scenario families: **6**

Each cause keeps one wording family completely outside training. These numbers measure generalization across authored templates, not real-world RCA accuracy.

The held-out confusion matrix contains 150 correct predictions out of 150 incidents.

## Explanation integrity

Citation validation is structural: the service rejects any explanation whose line IDs are not present in the evidence supplied to the explainer. Deterministic fallback covers every invalid or unavailable API response.

## Limitations

- HDFS labels normal/anomaly traces; it does not validate the root-cause classifier.
- Synthetic RCA metrics cannot be interpreted as production incident accuracy.
- Uploaded formats outside the known patterns may fall back to coarse line windows.

## Machine-readable artifacts

- `artifacts/evaluation/metrics.json`
- `artifacts/evaluation/anomaly_confusion.csv`
- `artifacts/evaluation/anomaly_precision_recall.csv`
- `artifacts/evaluation/root_cause_confusion.csv`
- `artifacts/evaluation/synthetic_manifest.json`

## Reproduce

```bash
python -m loglens.cli download-data
python -m loglens.cli train \
  --structured data/downloads/hdfs_v1/Event_occurrence_matrix.csv \
  --labels data/downloads/hdfs_v1/anomaly_label.csv
```
