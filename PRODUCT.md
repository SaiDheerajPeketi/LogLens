# LogLens Product Record

## Platform

Web application, optimized for desktop incident triage with a complete mobile reading flow.

## Stack

React and TypeScript for the interface; FastAPI, SQLite, pandas, scikit-learn, and XGBoost for the analysis service; Docker Compose for local delivery.

## Users

- Primary: support and SRE engineers performing the first pass on an unfamiliar incident.
- Secondary: engineering interviewers evaluating whether the project demonstrates production-minded ML engineering rather than a tutorial clone.

## Product purpose

LogLens shortens first-pass log triage. It identifies unusual windows, proposes a probable root cause, and explains the conclusion with links to exact redacted log lines. Success means an engineer can move from an unfamiliar log to an auditable working hypothesis without treating a model output as unquestionable truth.

## Positioning

Most portfolio anomaly detectors stop at a score. LogLens joins anomaly detection, calibrated root-cause classification, and citation-validated explanations while keeping real anomaly evaluation separate from synthetic root-cause evaluation.

## Operating context

Users inspect a bundled incident or upload a small plain-text log. They move across an incident timeline, select a suspicious window, inspect competing evidence, and read the underlying redacted transcript. The public demo is not intended for confidential production logs.

## Capabilities and constraints

- HDFS_v1 supplies real normal/anomaly traces; it does not supply root-cause labels.
- A disclosed synthetic corpus supplies root-cause training and evaluation data.
- Uploads are limited to 5 MB or 50,000 lines and are deleted after processing.
- Raw log content is never persisted or sent to an external explanation service.
- An external explanation API is optional; deterministic cited explanations are always available.
- Public cloud hosting is deferred. The current delivery target is a verified local Docker deployment plus a cloud runbook.
- Authentication, saved workspaces, real-time streaming, distributed workers, and an LSTM are outside the MVP.

## Brand commitments

The name is LogLens. The product voice is calm, exact, and candid about uncertainty. The interface uses the metaphor of a flight recorder: replayable time, marked anomalies, and evidence that can be inspected after the fact.

## Evidence on hand

- Public HDFS_v1 log data and binary labels from LogHub.
- Synthetic incident scenarios authored and labeled within this repository.
- No customer testimonials, production deployment claims, or Oracle/customer data.

## Product principles

1. Evidence before eloquence.
2. Separate what was measured from what was simulated.
3. Make uncertainty visible and actionable.
4. Keep the demo safe to run and straightforward to reproduce.
5. Prefer a strong, inspectable baseline over an opaque model added for novelty.

## Accessibility and inclusion

Target WCAG AA contrast, full keyboard operation, visible focus, reduced-motion support, semantic status announcements, and status cues that never rely on color alone.
