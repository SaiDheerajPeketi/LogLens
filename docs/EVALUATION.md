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

The committed precision-recall artifact contains 132 measured operating points. The cost-weighted score assigns a missed anomaly 10 times the cost of a false alarm, then normalizes against the worst possible cost for the held-out set.

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

- Citation validity: **100%** (15 of 15 returned citations)
- Completed runtime cases: **6 of 6**
- Invalid citation trials rejected: **1 of 1**
- Raw upload files retained: **0**
- Raw sensitive markers found in SQLite: **0**

The runtime evaluator exercises all five built-in scenarios plus a redaction-sensitive upload through the queue, models, evidence selection, explanation, and temporary SQLite store. A citation passes only when its line ID belongs to the primary window's supplied evidence. The evaluator also injects an out-of-set citation and confirms it is rejected.

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
- `artifacts/evaluation/runtime_integrity.json`

## Reproduce

```bash
python -m loglens.cli download-data
python -m loglens.cli train \
  --structured data/downloads/hdfs_v1/Event_occurrence_matrix.csv \
  --labels data/downloads/hdfs_v1/anomaly_label.csv
python -m loglens.cli evaluate-runtime
```
