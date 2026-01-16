# Product notes

## Who it is for

LogLens is built for support and SRE engineers doing a first pass on an unfamiliar incident. The desktop layout favors investigation speed, while the mobile layout keeps the same reading path for review and sharing.

## Goal

LogLens shortens first-pass log triage. It identifies unusual windows, proposes a probable root cause, and explains the conclusion with links to exact redacted log lines. Success means an engineer can move from an unfamiliar log to an auditable working hypothesis without treating a model output as unquestionable truth.

Most anomaly demos stop at a score. LogLens connects that score to a probable cause and to the lines that support it. It also keeps real anomaly evaluation separate from synthetic root-cause evaluation so the numbers remain interpretable.

## Typical workflow

Users inspect a bundled incident or upload a small plain-text log. They move across an incident timeline, select a suspicious window, inspect competing evidence, and read the underlying redacted transcript. The public demo is not intended for confidential production logs.

## Boundaries

- HDFS_v1 supplies real normal/anomaly traces; it does not supply root-cause labels.
- A synthetic corpus supplies root-cause training and evaluation data.
- Uploads are limited to 5 MB or 50,000 lines and are deleted after processing.
- Raw log content is never persisted or sent to an external explanation service.
- An external explanation API is optional; deterministic cited explanations are always available.
- The current deployment target is a single local Docker service. A Render configuration is included for later hosting.
- Authentication, saved workspaces, real-time streaming, distributed workers, and an LSTM are outside the MVP.

## Voice and visual direction

The name is LogLens. The product voice is calm, exact, and candid about uncertainty. The interface uses the metaphor of a flight recorder: replayable time, marked anomalies, and evidence that can be inspected after the fact.

## Data used

- Public HDFS_v1 log data and binary labels from LogHub.
- Synthetic incident scenarios created and labeled in this repository.
- No customer testimonials, production deployment claims, or Oracle/customer data.

## Product principles

1. Evidence before eloquence.
2. Separate what was measured from what was simulated.
3. Make uncertainty visible and actionable.
4. Keep the demo safe to run and straightforward to reproduce.
5. Prefer a strong, inspectable baseline over an opaque model added for novelty.

## Accessibility and inclusion

Target WCAG AA contrast, full keyboard operation, visible focus, reduced-motion support, semantic status announcements, and status cues that never rely on color alone.
