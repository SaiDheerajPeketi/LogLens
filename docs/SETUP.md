# LogLens Setup Guide

This guide covers the verified Docker demo, native development, data acquisition, training, testing, configuration, and common failures.

## Prerequisites

- Python 3.12
- [uv](https://docs.astral.sh/uv/) for the locked Python environment
- Node.js 22 and npm
- Docker Engine and Docker Compose for the packaged demo
- About 1 GB of free disk space if you download and train on full HDFS_v1

## Fastest path: Docker Compose

From the repository root:

```bash
docker compose up --build
```

Open:

- Application: `http://localhost:8080`
- API documentation: `http://localhost:8080/docs`
- Health: `http://localhost:8080/api/v1/health`

Some installations expose Compose as a standalone command. Use this equivalent form when needed:

```bash
docker-compose up --build
```

The verified local build used Docker 29.5.2, Docker Compose 5.2.0, and the standalone command. The container runs as a non-root user and stores only redacted derived state in the `loglens-runtime` named volume.

To stop the service without deleting results:

```bash
docker compose down
```

To also delete the local redacted-result volume:

```bash
docker compose down --volumes
```

The second command is intentionally destructive for retained local results.

## Native development

Install the locked Python and frontend dependencies:

```bash
uv sync --extra dev --frozen
npm ci --prefix frontend
cp .env.example .env
```

Run the API in one terminal:

```bash
uv run uvicorn loglens.main:app --reload --host 127.0.0.1 --port 8000
```

Run the interface in another:

```bash
npm run dev --prefix frontend
```

Open `http://localhost:5173`. The Vite development server proxies `/api` to the API on port 8000.

## Environment variables

| Variable | Default | Meaning |
| --- | --- | --- |
| `LOGLENS_DATABASE_URL` | `sqlite:///./data/runtime/loglens.sqlite3` | SQLAlchemy database URL |
| `LOGLENS_RESULT_TTL_HOURS` | `24` | Redacted result lifetime |
| `LOGLENS_MAX_UPLOAD_BYTES` | `5242880` | Upload byte limit |
| `LOGLENS_MAX_LOG_LINES` | `50000` | Upload line limit |
| `LOGLENS_QUEUE_CAPACITY` | `8` | Maximum queued analyses |
| `LOGLENS_OPENAI_MODEL` | `gpt-5-mini` | Optional explanation model |
| `OPENAI_API_KEY` | unset | Enables the optional Responses API adapter |

Do not commit `.env`. Without `OPENAI_API_KEY`, the application remains fully functional and labels its deterministic explanation mode in the interface.

## Datasets and training

Download the official HDFS_v1 archive and extract the required preprocessed assets:

```bash
uv run loglens download-data
```

The command downloads the checksum-pinned LogHub archive, verifies the archive, extracts the event-occurrence matrix and labels, and verifies both files. Downloaded data stays under `data/downloads/` and is ignored by Git.

Train both models and regenerate the evaluation bundle:

```bash
uv run loglens train \
  --structured data/downloads/hdfs_v1/Event_occurrence_matrix.csv \
  --labels data/downloads/hdfs_v1/anomaly_label.csv
```

Training:

1. splits HDFS traces by block ID;
2. selects the XGBoost threshold only on validation data;
3. evaluates once on held-out test traces;
4. generates the synthetic cause corpus with family-disjoint splits;
5. trains and calibrates the linear cause model;
6. packages model metadata and checksums;
7. runs runtime citation and privacy integrity evaluation.

Re-run only the fast runtime integrity evaluation with:

```bash
uv run loglens evaluate-runtime
```

## Tests and quality checks

Backend:

```bash
uv run ruff check backend
uv run mypy backend/loglens
uv run pytest
```

Frontend:

```bash
npm test --prefix frontend
npm run build --prefix frontend
npm audit --prefix frontend --omit=dev
```

End to end against the Docker service:

```bash
npm --prefix frontend exec playwright install chromium
docker compose up --detach --build
npm run test:e2e --prefix frontend
```

The Playwright suite expects `http://127.0.0.1:8080` by default. Override it with `LOGLENS_E2E_URL` when testing another authorized environment.

## Clean production verification

```bash
docker compose up --detach --build
curl --fail http://127.0.0.1:8080/api/v1/health
docker compose ps
```

Expected health fields include `"status":"ok"` and `"model_ready":true`.

## Troubleshooting

### Docker cannot connect to an engine

Start Docker Desktop, Colima, or another Docker-compatible engine, then retry. A Compose client alone is not enough.

### Port 8080 is already in use

Change only the published side in `docker-compose.yml`, for example `"8081:8080"`, then open port 8081.

### The model health flag is false

Confirm `artifacts/models/manifest.json`, `anomaly_bundle.joblib`, and `rca_bundle.joblib` are present. Run the model artifact tests to verify their checksums.

### An upload is rejected

Use UTF-8 plain text with a `.log` or `.txt` extension. Archives, binary content, files over 5 MB, and logs over 50,000 lines are rejected before analysis.

### Explanations always use the deterministic fallback

That is expected when `OPENAI_API_KEY` is absent. When a key is present, timeouts, refusals, malformed structured output, or citations outside supplied evidence also trigger the fallback by design.

### A previous analysis shows as interrupted

The queue lives in one process. Work interrupted by restart is marked failed. Built-in scenarios can be retried; uploads must be resubmitted because raw bytes are not retained.

## Later cloud deployment

See [the deployment runbook](DEPLOYMENT.md). The project currently claims only the verified local deployment.
