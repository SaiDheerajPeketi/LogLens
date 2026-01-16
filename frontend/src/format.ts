import type { AnalysisStatus, CauseClass } from "./types";

export const causeLabels: Record<CauseClass, string> = {
  database_timeout: "Database timeout",
  authentication_failure: "Authentication failure",
  connection_pool_exhaustion: "Connection-pool exhaustion",
  disk_pressure: "Disk pressure",
  network_dns_failure: "Network / DNS failure",
  unknown: "Unknown — needs human review",
};

export const statusLabels: Record<AnalysisStatus, string> = {
  queued: "Queued for local analysis",
  parsing: "Parsing redacted events",
  scoring: "Scoring anomaly windows",
  explaining: "Linking explanation to evidence",
  complete: "Analysis complete",
  failed: "Analysis failed",
  expired: "Analysis expired",
};

export function percent(value: number, digits = 0): string {
  return `${(value * 100).toFixed(digits)}%`;
}

export function metric(value: number | undefined, digits = 4): string {
  return typeof value === "number" ? value.toFixed(digits) : "—";
}

export function shortTime(value: string): string {
  return new Intl.DateTimeFormat(undefined, {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  }).format(new Date(value));
}
