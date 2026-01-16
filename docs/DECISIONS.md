# Engineering decisions

This document records the choices that are easiest to misunderstand when reading the code. It is intentionally short; implementation details belong beside the implementation.

## Keep anomaly detection and root-cause evaluation separate

LogHub HDFS_v1 has reliable normal/anomaly labels, but it does not have root-cause labels. LogLens therefore uses HDFS only for anomaly evaluation and a separate synthetic dataset for root-cause classification. The UI and documentation never present the synthetic score as production accuracy.

## Split HDFS data by block ID

Rows from one HDFS block trace are kept in the same train, validation, or test split. This prevents events from the same incident appearing on both sides of the evaluation boundary.

The anomaly threshold is selected on validation data under a 5% false-positive-rate ceiling, then measured once on the test set.

## Hold out complete wording families for root-cause tests

Randomly splitting individual synthetic lines would make the root-cause task too easy. Each cause keeps one full wording family outside training so the test measures generalization to unseen phrasing.

## Use two runtime scoring paths

The packaged XGBoost model expects the HDFS event vocabulary and is used for the HDFS benchmark. Arbitrary uploads use a generic score based on severity density and event-template rarity. This avoids applying the HDFS model to unrelated logs while still providing a useful ranking.

## Prefer correlation IDs, then timestamps, then line windows

LogLens groups events using the strongest structure available:

1. correlation or block identifiers when they cover most lines;
2. five-minute timestamp windows;
3. overlapping 200-line windows as a deterministic fallback.

## Redact before parsing or persistence

Raw uploads are processed in memory. Redaction happens before parsing, model input, persistence, or any optional external explanation call. Only redacted derived results are stored, and they expire after 24 hours.

## Treat generated prose as an untrusted presentation layer

The explanation step receives a predicted cause and a small set of selected, redacted evidence lines. It cannot choose new evidence. Its output follows a strict schema, and every citation is checked locally. Missing credentials, timeouts, malformed output, and invalid citations all fall back to a deterministic explanation.

## Use calibrated linear classification for causes

TF-IDF with calibrated logistic regression gives useful probabilities and direct feature contributions for evidence ranking. A more complex model would be harder to inspect without improving the current synthetic benchmark.

## Keep runtime state simple

SQLite stores redacted results and one bounded worker processes analyses. That is enough for local use and a single demo instance. Multiple replicas would require Postgres, a durable queue, authentication, and per-user authorization.

## Ship one production container

The frontend is compiled in a Node build stage and served by FastAPI from a non-root Python container. One service keeps local setup simple and matches the current single-instance storage model.

## Test the user-visible workflow in a browser

Playwright covers built-in analysis, uploads, no-anomaly results, low-confidence results, deterministic explanation fallback, keyboard navigation, and citation focus against the production container.

## Keep the interface evidence-first

The main screen keeps source selection, scored windows, diagnosis, and the transcript together. Selecting a window updates every dependent view, and following a citation moves focus to the corresponding transcript line.
