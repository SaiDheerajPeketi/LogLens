import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import App from "./App";
import type { AnalysisDetail, EvidenceLine, ModelCard, Scenario } from "./types";

const scenarios: Scenario[] = [
  {
    id: "db-timeout-checkout",
    name: "Checkout database timeout",
    description: "Database latency rises.",
    expected_cause: "database_timeout",
    line_count: 10,
    synthetic: true,
  },
  {
    id: "healthy-checkout",
    name: "Healthy checkout traffic",
    description: "No incident.",
    expected_cause: "unknown",
    line_count: 10,
    synthetic: true,
  },
];

const modelCard: ModelCard = {
  version: "hdfsv1-synthetic-rca-v1",
  anomaly_dataset: "LogHub HDFS_v1 — 575,061 block traces",
  root_cause_dataset: "LogLens disclosed synthetic incident corpus",
  anomaly_metrics: { pr_auc: 0.9994, f1: 0.9956, false_positive_rate: 0.0002 },
  root_cause_metrics: { macro_f1: 1 },
  limitations: ["Synthetic RCA is not production accuracy."],
};

const evidence: EvidenceLine[] = [
  {
    id: "line-7",
    line_no: 7,
    text: "ERROR database deadline exceeded",
    event_template: "ERROR database deadline exceeded",
    severity: "ERROR",
  },
  {
    id: "line-8",
    line_no: 8,
    text: "WARN database latency above threshold",
    event_template: "WARN database latency above threshold",
    severity: "WARN",
  },
];

function detail(overrides: Partial<AnalysisDetail> = {}): AnalysisDetail {
  return {
    id: "analysis-1",
    status: "complete",
    created_at: "2026-04-18T09:00:00Z",
    updated_at: "2026-04-18T09:00:01Z",
    expires_at: "2026-04-19T09:00:00Z",
    source: {
      kind: "scenario",
      name: "Checkout database timeout",
      line_count: 10,
      raw_retained: false,
      synthetic: true,
    },
    model_versions: { evaluation_bundle: "hdfsv1-synthetic-rca-v1" },
    windows: [
      {
        id: "time-000",
        strategy: "timestamp",
        start_line: 1,
        end_line: 5,
        anomaly_score: 0.05,
        is_anomaly: false,
        cause: "unknown",
        confidence: 0,
        evidence_line_ids: [],
        caveats: [],
      },
      {
        id: "time-001",
        strategy: "timestamp",
        start_line: 6,
        end_line: 10,
        anomaly_score: 0.91,
        is_anomaly: true,
        cause: "database_timeout",
        confidence: 0.91,
        evidence_line_ids: ["line-7", "line-8"],
        caveats: [],
      },
    ],
    explanation: {
      summary: "The window is most consistent with database timeouts.",
      probable_cause: "database_timeout",
      confidence: 0.91,
      citations: ["line-7", "line-8"],
      source: "deterministic",
      caveat: "Generated locally.",
    },
    caveats: ["HDFS metrics apply only to HDFS traces."],
    error: null,
    ...overrides,
  };
}

function jsonResponse(payload: unknown, status = 200): Response {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function installFetch(analysis = detail()): void {
  vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    if (url === "/api/v1/scenarios") return jsonResponse(scenarios);
    if (url === "/api/v1/model-card") return jsonResponse(modelCard);
    if (url === "/api/v1/analyses" && init?.method === "POST") {
      return jsonResponse({
        id: analysis.id,
        status: "queued",
        created_at: analysis.created_at,
        updated_at: analysis.updated_at,
        expires_at: analysis.expires_at,
      }, 202);
    }
    if (url === `/api/v1/analyses/${analysis.id}`) return jsonResponse(analysis);
    if (url.startsWith(`/api/v1/analyses/${analysis.id}/events`)) {
      return jsonResponse({ items: evidence, next_cursor: null });
    }
    return jsonResponse({ detail: "Not found" }, 404);
  }));
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  window.location.hash = "";
});

describe("LogLens console", () => {
  it("moves from first-run state to synchronized cited evidence", async () => {
    installFetch();
    const user = userEvent.setup();
    render(<App />);

    expect(await screen.findByRole("heading", { name: /replay the failure/i })).toBeVisible();
    await user.click(screen.getByRole("button", { name: /run incident replay/i }));

    expect(await screen.findByRole("heading", { name: "Database timeout" })).toBeVisible();
    const evidenceButton = screen.getByRole("button", { name: /line 7/i });
    await user.click(evidenceButton);
    await waitFor(() => expect(document.getElementById("event-line-7")).toHaveFocus());
    expect(document.getElementById("event-line-7")).toHaveClass("cited");
    expect(screen.getByText("Deterministic fallback")).toBeVisible();
  });

  it("supports arrow-key replay across windows", async () => {
    installFetch();
    const user = userEvent.setup();
    render(<App />);
    await user.click(await screen.findByRole("button", { name: /run incident replay/i }));

    const anomaly = await screen.findByRole("button", { name: /window 2/i });
    await waitFor(() => expect(anomaly).toHaveAttribute("aria-pressed", "true"));
    anomaly.focus();
    await user.keyboard("{ArrowLeft}");
    expect(screen.getByRole("button", { name: /window 1/i })).toHaveAttribute("aria-pressed", "true");
  });

  it("renders low-confidence unknown as a human-review outcome", async () => {
    const ambiguous = detail({
      windows: [
        {
          id: "time-000",
          strategy: "timestamp",
          start_line: 1,
          end_line: 10,
          anomaly_score: 0.72,
          is_anomaly: true,
          cause: "unknown",
          confidence: 0.42,
          evidence_line_ids: ["line-7"],
          caveats: ["Unknown—needs human review; evidence was not class-specific."],
        },
      ],
      explanation: {
        summary: "The cause is not supported by a known class.",
        probable_cause: "unknown",
        confidence: 0.42,
        citations: ["line-7"],
        source: "deterministic",
        caveat: "Generated locally.",
      },
    });
    installFetch(ambiguous);
    const user = userEvent.setup();
    render(<App />);
    await user.click(await screen.findByRole("button", { name: /run incident replay/i }));

    expect(await screen.findByRole("heading", { name: /unknown.*human review/i })).toBeVisible();
    expect(screen.getByText(/evidence was not class-specific/i)).toBeVisible();
  });

  it("announces and displays invalid-upload failures", async () => {
    installFetch();
    const fetchMock = vi.mocked(fetch);
    fetchMock.mockImplementation(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url === "/api/v1/scenarios") return jsonResponse(scenarios);
      if (url === "/api/v1/model-card") return jsonResponse(modelCard);
      if (url === "/api/v1/analyses" && init?.method === "POST") {
        return jsonResponse({ detail: "Upload a plain-text .log or .txt file." }, 422);
      }
      return jsonResponse({}, 404);
    });
    const user = userEvent.setup();
    render(<App />);
    const input = await screen.findByLabelText(/upload log/i);
    await user.upload(input, new File(["\0binary"], "bad.log", { type: "text/plain" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("plain-text .log or .txt");
  });
});

describe("documentation pages", () => {
  it("reports measured metrics and navigates without a router dependency", async () => {
    installFetch();
    const user = userEvent.setup();
    render(<App />);
    await user.click(screen.getByRole("button", { name: "Evaluation" }));

    expect(await screen.findByRole("heading", { name: "Model evaluation" })).toBeVisible();
    expect(screen.getByText("0.9994")).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Methodology" }));
    expect(screen.getByRole("heading", { name: /narrow trust boundary/i })).toBeVisible();
  });
});
