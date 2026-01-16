export type AnalysisStatus =
  | "queued"
  | "parsing"
  | "scoring"
  | "explaining"
  | "complete"
  | "failed"
  | "expired";

export type CauseClass =
  | "database_timeout"
  | "authentication_failure"
  | "connection_pool_exhaustion"
  | "disk_pressure"
  | "network_dns_failure"
  | "unknown";

export interface Scenario {
  id: string;
  name: string;
  description: string;
  expected_cause: CauseClass;
  line_count: number;
  synthetic: boolean;
}

export interface AnalysisAccepted {
  id: string;
  status: AnalysisStatus;
  created_at: string;
  updated_at: string;
  expires_at: string;
}

export interface SourceSummary {
  kind: "scenario" | "upload";
  name: string;
  line_count: number;
  raw_retained: boolean;
  synthetic: boolean;
}

export interface EvidenceLine {
  id: string;
  line_no: number;
  text: string;
  event_template: string;
  severity: string;
}

export interface WindowResult {
  id: string;
  strategy: string;
  start_line: number;
  end_line: number;
  anomaly_score: number;
  is_anomaly: boolean;
  cause: CauseClass;
  confidence: number;
  evidence_line_ids: string[];
  caveats: string[];
}

export interface Explanation {
  summary: string;
  probable_cause: CauseClass;
  confidence: number;
  citations: string[];
  source: "openai" | "deterministic";
  caveat: string | null;
}

export interface AnalysisError {
  code: string;
  message: string;
  retryable: boolean;
  action: string;
}

export interface AnalysisDetail extends AnalysisAccepted {
  source: SourceSummary;
  model_versions: Record<string, string>;
  windows: WindowResult[];
  explanation: Explanation | null;
  caveats: string[];
  error: AnalysisError | null;
}

export interface EventsPage {
  items: EvidenceLine[];
  next_cursor: string | null;
}

export interface ModelCard {
  version: string;
  anomaly_dataset: string;
  root_cause_dataset: string;
  anomaly_metrics: Record<string, number>;
  root_cause_metrics: Record<string, number>;
  limitations: string[];
}

