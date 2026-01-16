import type {
  AnalysisAccepted,
  AnalysisDetail,
  EventsPage,
  ModelCard,
  Scenario,
} from "./types";

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, init);
  if (!response.ok) {
    let message = `Request failed with status ${response.status}.`;
    try {
      const payload = (await response.json()) as { detail?: string };
      if (payload.detail) message = payload.detail;
    } catch {
      // Keep the status-based fallback when the server does not return JSON.
    }
    throw new ApiError(message, response.status);
  }
  return (await response.json()) as T;
}

export const api = {
  scenarios: () => request<Scenario[]>("/api/v1/scenarios"),
  modelCard: () => request<ModelCard>("/api/v1/model-card"),
  createScenario: (scenarioId: string) =>
    request<AnalysisAccepted>("/api/v1/analyses", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ scenario_id: scenarioId }),
    }),
  createUpload: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<AnalysisAccepted>("/api/v1/analyses", {
      method: "POST",
      body: form,
    });
  },
  analysis: (analysisId: string) =>
    request<AnalysisDetail>(`/api/v1/analyses/${analysisId}`),
  events: (analysisId: string, cursor?: string | null) => {
    const query = new URLSearchParams({ limit: "500" });
    if (cursor) query.set("cursor", cursor);
    return request<EventsPage>(`/api/v1/analyses/${analysisId}/events?${query}`);
  },
  retry: (analysisId: string) =>
    request<AnalysisAccepted>(`/api/v1/analyses/${analysisId}/retry`, {
      method: "POST",
    }),
};
