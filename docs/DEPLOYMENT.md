# Cloud Deployment Runbook

## Current status

Public hosting is deferred. No live URL is claimed for this release.

This runbook defines a concrete later path on Render because the repository already produces one health-checked Docker web service. It is a readiness document, not evidence that the service has been deployed.

## Proposed Render topology

- One Docker web service built from the repository root
- One 1 GB persistent disk mounted at `/app/data/runtime`
- SQLite at `/app/data/runtime/loglens.sqlite3`
- HTTP health check at `/api/v1/health`
- One application instance only
- Optional `OPENAI_API_KEY` secret; the deterministic fallback remains valid without it

The committed `render.yaml` captures that topology. Render can build from a repository Dockerfile, configure an HTTP health-check path, and attach a persistent disk. A disk is available only to one service instance, prevents horizontal scaling, and disables zero-downtime deploys. Those constraints match the current bounded in-process queue but are not the target architecture for sustained traffic.

Official references: [Docker services](https://render.com/docs/docker), [web services](https://render.com/docs/web-services), [health checks](https://render.com/docs/health-checks), [persistent disks](https://render.com/docs/disks), and the [Blueprint specification](https://render.com/docs/blueprint-spec).

## Pre-deployment checklist

1. Confirm CI is green on the exact commit.
2. Build and run the image from a clean checkout.
3. Verify `/api/v1/health` reports `model_ready: true`.
4. Run the five Playwright workflows against the local production image.
5. Review the privacy warning and confirm only synthetic or non-confidential demo input will be accepted.
6. Review current Render compute and disk pricing. A persistent disk requires a paid service.
7. Choose a region before creation; Render does not allow changing a service region later.

## Deployment procedure

1. In Render, create a new Blueprint and connect `SaiDheerajPeketi/LogLens`.
2. Review the resources parsed from `render.yaml`; do not deploy automatically without confirming the plan and disk cost.
3. Keep the repository Dockerfile and `CMD`. The container listens on `0.0.0.0:8080`, which Render can detect.
4. Confirm the disk mount is `/app/data/runtime` and the health path is `/api/v1/health`.
5. Optionally add `OPENAI_API_KEY` as a secret environment variable. Never place it in `render.yaml` or Git.
6. Create the service and wait for the HTTP health check to pass.
7. Record the deployed Git commit and the model version returned by `/api/v1/model-card`.

## Post-deployment smoke test

Replace the placeholder host with the assigned Render hostname:

```bash
curl --fail https://YOUR-SERVICE.onrender.com/api/v1/health
curl --fail https://YOUR-SERVICE.onrender.com/api/v1/scenarios
curl --fail \
  --header 'Content-Type: application/json' \
  --data '{"scenario_id":"db-timeout-checkout"}' \
  https://YOUR-SERVICE.onrender.com/api/v1/analyses
```

Then run the browser suite against that authorized environment:

```bash
LOGLENS_E2E_URL=https://YOUR-SERVICE.onrender.com npm run test:e2e --prefix frontend
```

Do not publish a live-demo link until the health check, all five browser workflows, privacy review, and a retention-expiry check pass on the hosted service.

## Storage and operations

- Only `/app/data/runtime` persists. The rest of the container filesystem is replaceable.
- The application stores redacted derived results for 24 hours; raw upload bytes are never written.
- A persistent disk can attach to only one instance, so keep the replica count at one.
- Deploys with the disk have a short interruption because Render cannot perform a zero-downtime instance swap with a single attached disk.
- Treat the SQLite volume as disposable demo state. There is no promise of long-term incident history.
- Monitor container memory, request latency, queue-full responses, analysis failures, and disk usage.

## Rollback

1. Select the last healthy deploy in the Render dashboard.
2. Redeploy that commit.
3. Confirm the health endpoint and model version.
4. Re-run one built-in scenario and the deterministic-fallback browser workflow.

The SQLite schema is intentionally small and currently has no forward-only migrations. If that changes, add a tested backup and migration rollback procedure before public deployment.

## Path beyond a single demo instance

Move from the proposed topology when availability, concurrency, or durable work matters:

1. Replace SQLite with managed Postgres for analysis metadata and redacted results.
2. Replace the in-process queue with a durable broker and separate worker service.
3. Keep the API stateless so multiple replicas can serve reads and submissions.
4. Add authentication, per-user authorization, request quotas, and an explicit deletion API.
5. Add structured observability without logging uploaded or redacted line content.
6. Re-run evaluation and privacy probes against the deployed build.
