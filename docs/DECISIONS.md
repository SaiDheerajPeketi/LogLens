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
