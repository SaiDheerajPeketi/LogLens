# Engineering Decision Journal

This journal records the decisions that materially shape LogLens. Each entry states what was decided, why it was chosen, what it costs, and what evidence would justify revisiting it.

## 001 — Build a portfolio MVP before a production pilot

- **Context:** The project must be achievable, deployable, and useful in interviews without pretending to be a production observability platform.
- **Options considered:** notebook-only research demo; four-week portfolio MVP; multi-user production pilot.
- **Decision:** Build a four-week portfolio MVP with a polished application, reproducible evaluation, and explicit non-goals.
- **Why:** It demonstrates ML, API, product, evaluation, and delivery skills while keeping the scope finishable.
- **Tradeoffs:** Authentication, streaming ingestion, distributed queues, and durable cloud workspaces are deferred.
- **Evidence:** The project blueprint prioritizes a deployed, evaluated first project over a broader unfinished system.
- **Revisit when:** Real users require saved workspaces, sustained throughput, or integrations.
- **Implementation:** Product foundation; `docs: record the initial product decisions`.

## 002 — Keep anomaly and root-cause evidence separate

- **Context:** HDFS_v1 provides trace-level anomaly labels but not root-cause categories.
- **Options considered:** imply root-cause labels exist; make the entire dataset synthetic; combine real anomaly data with disclosed synthetic RCA data.
- **Decision:** Evaluate anomaly detection on HDFS_v1 and root-cause classification on a separately disclosed synthetic corpus.
- **Why:** It preserves external validity for anomaly detection without inventing labels.
- **Tradeoffs:** Metrics cannot be collapsed into one end-to-end score, and synthetic RCA performance has narrower claims.
- **Evidence:** The official HDFS_v1 documentation describes normal/anomaly labels only.
- **Revisit when:** A legally usable, incident-level dataset with reliable cause labels becomes available.
- **Implementation:** Dataset and evaluation pipeline; `docs: record the initial product decisions`.

## 003 — Use React with a FastAPI analysis service

- **Context:** The project must demonstrate both ML engineering and a credible operational interface.
- **Options considered:** Streamlit monolith; Streamlit with FastAPI; React with FastAPI.
- **Decision:** Use React/TypeScript and FastAPI.
- **Why:** It cleanly separates the analysis contract from the interface and demonstrates production-oriented full-stack engineering.
- **Tradeoffs:** More code, build tooling, and test surface than Streamlit.
- **Evidence:** The portfolio goal values product engineering breadth, while Docker keeps local setup bounded.
- **Revisit when:** A research-only branch is needed for rapid experiment review.
- **Implementation:** Application scaffold; `docs: record the initial product decisions`.

## 004 — Design explanations as an optional adapter

- **Context:** Plain-English explanations improve usability, but the analysis must remain reproducible without credentials or network access.
- **Options considered:** require an external model; use templates only; optional API with deterministic fallback.
- **Decision:** Put the external explanation service behind an interface and validate all citations, with a deterministic fallback for every failure mode.
- **Why:** The core result stays available, safe, and testable while still demonstrating structured model integration.
- **Tradeoffs:** Two explanation paths must be maintained and tested.
- **Evidence:** Citation integrity matters more than prose quality for an audit-oriented tool.
- **Revisit when:** A local model can meet the same latency and faithfulness requirements within the deployment budget.
- **Implementation:** Explanation service; `docs: record the initial product decisions`.

## 005 — Deliver locally before selecting a cloud host

- **Context:** A public URL was requested initially, then explicitly deferred.
- **Options considered:** deploy immediately; temporary tunnel; verified local Docker deployment with a cloud runbook.
- **Decision:** Verify Docker Compose locally and document a direct cloud path without claiming a live public deployment.
- **Why:** It honors the latest delivery boundary and keeps the portfolio honest.
- **Tradeoffs:** The live-demo checklist remains open until hosting is authorized.
- **Evidence:** The selected scope explicitly defers public cloud hosting.
- **Revisit when:** A hosting account and acceptable cost/cold-start policy are chosen.
- **Implementation:** Delivery tooling; `docs: record the initial product decisions`.

## 006 — Use a flight-recorder operating model

- **Context:** The interface must make anomaly, cause, and evidence relationships understandable during triage.
- **Options considered:** generic observability dashboard; forensic case file; seismic station; flight recorder.
- **Decision:** Organize the workspace around a replayable incident timeline with synchronized evidence.
- **Why:** It makes time, anomaly markers, and post-incident inspection part of one coherent interaction.
- **Tradeoffs:** Dense timeline behavior requires careful responsive and keyboard design.
- **Evidence:** The selected concept directly supports the product's evidence-first mechanism.
- **Revisit when:** User testing shows the timeline slows down rather than accelerates first-pass triage.
- **Implementation:** Web interface; `docs: record the initial product decisions`.

## 007 — Use a single Python package at the repository root

- **Context:** Training, evaluation, and serving need to share schemas and feature logic without publishing several internal packages.
- **Options considered:** separate packages for API and ML; an unstructured scripts directory; one installable package with offline CLI commands.
- **Decision:** Use one installable `loglens` Python package and keep the web application as a separate frontend workspace.
- **Why:** It prevents train/serve drift while leaving the user interface independently buildable.
- **Tradeoffs:** Optional ML and API dependencies install together in the MVP.
- **Evidence:** The deployment is one Docker service and the planned model footprint is intentionally small.
- **Revisit when:** Training requires a materially different runtime or deployment cadence.
- **Implementation:** Python project and service scaffold; `chore: scaffold the analysis service`.

## 008 — Redact before parsing, persistence, or explanation

- **Context:** Log lines can contain secrets and personal or infrastructure identifiers, while parsing still needs stable relationships within one analysis.
- **Options considered:** reject all uploads; redact only before external API calls; redact immediately with stable per-analysis aliases.
- **Decision:** Validate and redact each line before feature extraction, persistence, or explanation, using salted aliases that remain stable only within one analysis.
- **Why:** The pipeline preserves useful recurrence without retaining original sensitive values.
- **Tradeoffs:** Redaction can remove features that might help a classifier and cannot guarantee detection of every proprietary secret format.
- **Evidence:** The public demo explicitly warns against confidential logs and treats redaction as defense in depth.
- **Revisit when:** A production pilot supplies a formal data-classification policy or requires an on-premises-only mode.
- **Implementation:** Ingestion pipeline; `feat: validate and redact uploaded logs`.

## 009 — Select windows by evidence available in the log

- **Context:** HDFS has block identifiers, many application logs have request IDs or timestamps, and some logs have neither.
- **Options considered:** fixed line windows only; require a configured parser; use a deterministic precedence order.
- **Decision:** Prefer correlation identifiers when they cover at least half the lines, then five-minute timestamp windows, then 200-line windows with 50-line overlap.
- **Why:** It uses the strongest available grouping while keeping generic uploads analyzable.
- **Tradeoffs:** Mixed-format logs may fall back to coarse windows, and overlapping windows require result deduplication.
- **Evidence:** The precedence is deterministic and directly testable across representative formats.
- **Revisit when:** Format-specific adapters or streaming sessions provide stronger boundaries.
- **Implementation:** Ingestion pipeline; `feat: validate and redact uploaded logs`.

## 010 — Use XGBoost for anomaly detection and a calibrated linear RCA model

- **Context:** The anomaly task has compact event-count features and severe imbalance; the RCA task must map evidence back to readable log lines.
- **Options considered:** one opaque sequence model; two XGBoost models; XGBoost for anomaly plus calibrated linear text classification for RCA.
- **Decision:** Use class-weighted XGBoost on HDFS event counts and calibrated logistic regression on synthetic incident TF-IDF features.
- **Why:** The anomaly model captures nonlinear event interactions, while the RCA model keeps class evidence inspectable and confidence calibratable.
- **Tradeoffs:** The models do not share a representation, and TF-IDF will miss unseen semantic paraphrases.
- **Evidence:** On the full HDFS_v1 trace matrix, the anomaly model reached 0.9994 PR-AUC and 0.9956 F1; the held-out synthetic-family RCA test reached 1.0000 macro-F1.
- **Revisit when:** A sequence or embedding model produces a meaningful held-out gain without breaking latency or evidence mapping.
- **Implementation:** Offline ML pipeline; `feat: train reproducible anomaly and cause models`.

## 012 — Evaluate on the complete HDFS_v1 trace matrix

- **Context:** The 100,000-line convenience subset contains only 7,940 traces and the first baseline reached 0.5081 PR-AUC, far below the acceptance target.
- **Options considered:** tune against the small subset; report the small-subset limitation; use the official complete HDFS_v1 preprocessed trace matrix.
- **Decision:** Download the checksum-pinned LogHub HDFS_v1 archive and evaluate on its 575,061 block-level traces.
- **Why:** It matches the dataset named in the project scope and supplies enough anomaly diversity for a credible held-out evaluation.
- **Tradeoffs:** The download is 186 MB compressed, the extracted assets are excluded from Git, and initial setup takes longer.
- **Evidence:** Without changing the test threshold after inspection, the complete trace matrix produced 0.9994 PR-AUC, 0.9956 F1, and a 0.0002 false-positive rate on 115,013 held-out traces.
- **Revisit when:** LogHub publishes a corrected version, or a deployment-specific labeled corpus is available.
- **Implementation:** Dataset acquisition and offline evaluation; `feat: train reproducible anomaly and cause models`.

## 013 — Separate benchmark scoring from generic-upload scoring

- **Context:** The HDFS model consumes 29 HDFS event IDs, while arbitrary uploaded logs have unrelated event-template vocabularies.
- **Options considered:** force generic templates into the HDFS feature slots; claim the HDFS metric applies to uploads; use a disclosed generic severity-and-rarity score while keeping HDFS evaluation separate.
- **Decision:** Use XGBoost for HDFS block traces and a deterministic severity-density plus template-rarity score for generic runtime windows.
- **Why:** It avoids a silent train/serve schema mismatch and keeps the public claim bounded to the data actually evaluated.
- **Tradeoffs:** The generic anomaly score is heuristic and does not inherit the HDFS PR-AUC or F1.
- **Evidence:** Feature inspection showed that HDFS has a fixed E1–E29 vocabulary, whereas scenario and upload templates are open-ended text.
- **Revisit when:** A representative labeled cross-application log corpus supports training a portable event-template model.
- **Implementation:** Runtime analysis engine and model card; `feat: process analyses through the cited evidence API`.

## 014 — Use SQLite with one bounded in-process worker

- **Context:** The local demo needs asynchronous status, restart handling, and bounded resource use without operating external infrastructure.
- **Options considered:** synchronous requests; Redis and Celery; SQLite plus a bounded single-worker queue.
- **Decision:** Persist redacted state in SQLite for 24 hours and process jobs with one bounded worker thread.
- **Why:** It demonstrates the lifecycle contract while keeping Docker setup to one service and preventing concurrent model spikes.
- **Tradeoffs:** Work does not survive as queued work across process loss, one process is required, and horizontal scaling needs a real broker.
- **Evidence:** Integration tests cover queued acceptance, completion, restart interruption, expiry deletion, and retry boundaries.
- **Revisit when:** Throughput or availability requires multiple application processes or durable queue semantics.
- **Implementation:** Analysis store, service, and public API; `feat: process analyses through the cited evidence API`.

## 015 — Treat external prose as an untrusted rendering step

- **Context:** An external explanation can improve readability but must not invent evidence, change the classifier outcome, or retain uploaded data.
- **Options considered:** free-form generation; require the external service; strict structured output with local validation and fallback.
- **Decision:** Send only selected redacted evidence and derived prediction metadata through the Responses API with storage disabled, enforce a strict schema, validate every citation locally, and fall back deterministically on any failure.
- **Why:** The evidence relationship remains testable and the product still works without credentials or network access.
- **Tradeoffs:** Generated prose is constrained, and invalid but otherwise useful responses are discarded.
- **Evidence:** Tests reject out-of-set citations, verify storage is disabled, and prove malformed primary output resolves to cited deterministic prose.
- **Revisit when:** A local explanation model can meet the same faithfulness and latency requirements.
- **Implementation:** Explanation adapter and citation guard; `feat: process analyses through the cited evidence API`.

## 016 — Make evidence navigation the primary interface action

- **Context:** A conventional dashboard can show scores but leaves the operator to reconnect a prediction with the source lines manually.
- **Options considered:** card-based analytics dashboard; separate result and raw-log pages; flight-recorder workspace with synchronized timeline, diagnosis, and transcript.
- **Decision:** Use a compact left source rail, central replay timeline, right diagnosis rail, and lower transcript, with every evidence item acting as a direct focus link to its cited line.
- **Why:** The layout exposes the product's differentiator—the relationship between anomaly, cause, and exact evidence—without requiring page changes.
- **Tradeoffs:** Dense desktop information architecture needs a separate stacked mobile order and horizontal window replay.
- **Evidence:** Desktop and 390-pixel visual checks preserve source selection, anomaly replay, diagnosis, and cited transcript reading; interaction tests cover arrow-key windows and focus transfer to evidence.
- **Revisit when:** Operator testing shows a different first action or the diagnosis rail obscures rather than accelerates triage.
- **Implementation:** Flight-recorder React interface; `feat: build the flight recorder analysis console`.

## 011 — Tune the anomaly threshold on validation data

- **Context:** The default probability threshold does not encode the product's false-alarm budget, and selecting on test data would leak evaluation information.
- **Options considered:** fixed 0.5 threshold; maximize test F1; scan validation thresholds under a 5% false-positive constraint.
- **Decision:** Select the highest-validation-F1 threshold among candidates with false-positive rate at or below 5%, then evaluate it once on held-out test traces.
- **Why:** It ties the classifier to an operational cost while preserving the test set for honest reporting.
- **Tradeoffs:** The selected threshold depends on the demo subset's prevalence and must be recalibrated for a new environment.
- **Evidence:** The evaluation report records threshold, FPR, PR-AUC, F1, and a 10:1 missed-anomaly cost score.
- **Revisit when:** Pilot data supplies a different base rate or explicit incident costs.
- **Implementation:** Offline ML pipeline; `feat: train reproducible anomaly and cause models`.

## 017 — Ship one CPU-only production container

- **Context:** The local demo needs one reproducible command, durable SQLite state, production frontend assets, and the trained models without requiring GPU support.
- **Options considered:** separate frontend and API containers; a development-server composition; one multi-stage image that serves the compiled interface from FastAPI.
- **Decision:** Build the React interface in a Node stage, install the Python service with the official CPU-only XGBoost distribution on Linux, and run one non-root FastAPI container with a named SQLite volume.
- **Why:** One service keeps the portfolio demo and later single-service cloud deployment understandable while preserving the same API boundary used in development.
- **Benefits:** The container has an explicit health check, persists only redacted derived state, and avoids shipping unused GPU libraries.
- **Tradeoffs:** Frontend and backend releases are coupled, the SQLite volume constrains horizontal scaling, and local hot reload still uses the native development commands.
- **Evidence:** A clean Compose build served the production interface and completed a database-timeout analysis at port 8080; the healthy CPU-only image measured 178,490,743 bytes.
- **Reconsideration trigger:** Split the services and replace SQLite when independent scaling, a CDN, or multiple application replicas become necessary.
- **Related implementation:** Dockerfile, Compose service, static asset routing, and CI; `chore: package the local demo with Docker`.

## 018 — Exercise the product contract in a real browser

- **Context:** Component and API tests can pass while focus transfer, uploads, polling, responsive layout, or the production asset bundle fails at the browser boundary.
- **Options considered:** rely on unit tests; keep a manual QA checklist; run Playwright against the composed production service.
- **Decision:** Cover the built-in incident, uploaded log, no-anomaly result, low-confidence human-review result, and forced deterministic fallback in Chromium against the Docker URL.
- **Why:** These are the five user-visible paths where the API, queue, models, evidence navigation, and interface must work together.
- **Benefits:** The same harness produces reproducible desktop and mobile screenshots from measured product states and verifies keyboard focus reaches a cited transcript row.
- **Tradeoffs:** CI downloads a browser and the suite depends on the container reaching health first.
- **Evidence:** All five workflows passed against the production image; captured views cover 1440-pixel desktop and 390-pixel mobile layouts.
- **Reconsideration trigger:** Add browsers or visual-regression baselines when cross-browser support becomes a stated product requirement.
- **Related implementation:** Playwright configuration, end-to-end suite, CI Docker job, and product screenshots; `test: verify complete analysis workflows`.

## 019 — Measure integrity through the persisted runtime path

- **Context:** Unit tests prove individual guards, but the acceptance claims require a concrete denominator for citation validity and proof that an upload is not written raw during normal processing.
- **Options considered:** report test coverage qualitatively; count only deterministic explainer output; run all scenarios and a sensitive upload through the queue, models, and temporary database.
- **Decision:** Provide an offline runtime evaluator that checks every returned citation against the selected evidence, injects one invalid citation, scans persistence for raw markers, and counts raw log files.
- **Why:** It turns privacy and citation claims into repeatable measurements without sending data externally or retaining evaluation input.
- **Benefits:** The result is machine-readable, fast enough for CI, and exercises the same service and SQLite path as the application.
- **Tradeoffs:** Six authored cases do not estimate real-world explanation usefulness, and marker scanning cannot prove redaction catches every possible sensitive format.
- **Evidence:** Six of six analyses passed, all 15 returned citations were valid, the invalid citation was rejected, and zero raw files or raw markers remained.
- **Reconsideration trigger:** Expand the corpus and privacy probes when representative customer formats or a formal data-classification standard become available.
- **Related implementation:** Runtime evaluation command, CI integrity step, and evaluation artifact; `test: measure runtime citation integrity`.
