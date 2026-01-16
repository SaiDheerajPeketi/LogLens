import { useEffect, useMemo, useState } from "react";
import { Activity, BookOpenText, ChartNoAxesCombined, RadioTower } from "lucide-react";

import { ApiError, api } from "./api";
import { ConsolePage } from "./ConsolePage";
import { metric, statusLabels } from "./format";
import type {
  AnalysisAccepted,
  AnalysisDetail,
  EvidenceLine,
  ModelCard,
  Scenario,
} from "./types";

type Page = "console" | "evaluation" | "methodology";
type SystemStatus = "checking" | "healthy" | "unavailable";

function pageFromHash(): Page {
  const value = window.location.hash.replace("#", "");
  return value === "evaluation" || value === "methodology" ? value : "console";
}

function Header({
  page,
  systemStatus,
  onNavigate,
}: {
  page: Page;
  systemStatus: SystemStatus;
  onNavigate: (page: Page) => void;
}) {
  const tabs: { id: Page; label: string; icon: typeof Activity }[] = [
    { id: "console", label: "Console", icon: Activity },
    { id: "evaluation", label: "Evaluation", icon: ChartNoAxesCombined },
    { id: "methodology", label: "Methodology", icon: BookOpenText },
  ];
  const systemLabel = {
    checking: "Checking local system",
    healthy: "Local system healthy",
    unavailable: "Local system unavailable",
  }[systemStatus];
  return (
    <header className="topbar">
      <button className="brand" type="button" onClick={() => onNavigate("console")}>
        <span className="brand-mark" aria-hidden="true">
          <RadioTower size={18} strokeWidth={1.8} />
        </span>
        <span>LogLens</span>
        <small>Evidence before inference</small>
      </button>
      <nav aria-label="Primary navigation">
        {tabs.map(({ id, label, icon: Icon }) => (
          <button
            className={page === id ? "nav-item active" : "nav-item"}
            type="button"
            aria-current={page === id ? "page" : undefined}
            onClick={() => onNavigate(id)}
            key={id}
          >
            <Icon size={15} aria-hidden="true" />
            {label}
          </button>
        ))}
      </nav>
      <div className={`system-state ${systemStatus}`} aria-label={systemLabel} aria-live="polite">
        <span className="status-lamp" aria-hidden="true" />
        {systemLabel}
      </div>
    </header>
  );
}

function EvaluationPage({ model }: { model: ModelCard | null }) {
  return (
    <article className="document-page" aria-labelledby="evaluation-title">
      <header className="document-lede">
        <h1 id="evaluation-title">Model evaluation</h1>
        <p>
          Two separate benchmarks answer two separate questions. HDFS measures binary anomaly
          detection; disclosed synthetic incidents measure cause classification.
        </p>
      </header>
      <section className="metric-band" aria-label="Evaluation highlights">
        <div>
          <span>HDFS PR-AUC</span>
          <strong>{metric(model?.anomaly_metrics.pr_auc)}</strong>
          <small>115,013 held-out block traces</small>
        </div>
        <div>
          <span>HDFS F1</span>
          <strong>{metric(model?.anomaly_metrics.f1)}</strong>
          <small>Threshold selected on validation</small>
        </div>
        <div>
          <span>False-positive rate</span>
          <strong>{metric(model?.anomaly_metrics.false_positive_rate)}</strong>
          <small>Target ≤ 0.0500</small>
        </div>
        <div>
          <span>Synthetic RCA macro-F1</span>
          <strong>{metric(model?.root_cause_metrics.macro_f1)}</strong>
          <small>Six held-out wording families</small>
        </div>
      </section>
      <div className="document-grid">
        <section>
          <h2>Block-level HDFS split</h2>
          <p>
            The full LogHub HDFS_v1 event-occurrence matrix is split by block ID into 60% train,
            20% validation, and 20% test. The 0.65 threshold maximizes validation F1 while holding
            false positives below 5%.
          </p>
          <dl className="definition-rows">
            <div><dt>Dataset</dt><dd>{model?.anomaly_dataset ?? "Loading…"}</dd></div>
            <div><dt>Classifier</dt><dd>Class-weighted XGBoost</dd></div>
            <div><dt>Test confusion</dt><dd>111,620 TN · 25 FP · 5 FN · 3,363 TP</dd></div>
          </dl>
        </section>
        <section>
          <h2>Family-disjoint synthetic split</h2>
          <p>
            Each supported cause reserves one wording family for test. The perfect score is useful
            evidence that known template families separate cleanly—not a claim about production
            incident accuracy.
          </p>
          <dl className="definition-rows">
            <div><dt>Dataset</dt><dd>{model?.root_cause_dataset ?? "Loading…"}</dd></div>
            <div><dt>Classifier</dt><dd>Calibrated linear TF-IDF</dd></div>
            <div><dt>Test set</dt><dd>150 incidents · 25 per cause</dd></div>
          </dl>
        </section>
      </div>
      <section className="limitations-strip">
        <h2>What these numbers do not prove</h2>
        <ul>
          {(model?.limitations ?? ["Loading documented limitations…"]).map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>
    </article>
  );
}

function MethodologyPage() {
  const steps = [
    "Validate plain text and enforce byte and line limits",
    "Redact credentials, people, and infrastructure identifiers",
    "Parse timestamps, severity, correlation IDs, and event templates",
    "Build correlation, time, or overlapping line windows",
    "Score anomalies and classify a supported cause",
    "Select exact redacted evidence lines",
    "Generate prose, validate every citation, then persist for 24 hours",
  ];
  return (
    <article className="document-page" aria-labelledby="methodology-title">
      <header className="document-lede">
        <h1 id="methodology-title">A deliberately narrow trust boundary</h1>
        <p>
          LogLens proposes a first-pass diagnosis. It does not replace a postmortem, and it never
          asks prose generation to discover evidence that the pipeline has not already selected.
        </p>
      </header>
      <ol className="pipeline-list">
        {steps.map((step, index) => (
          <li key={step}>
            <span>{String(index + 1).padStart(2, "0")}</span>
            <p>{step}</p>
          </li>
        ))}
      </ol>
      <div className="document-grid methodology-grid">
        <section>
          <h2>Redact before meaning</h2>
          <p>
            Raw uploads remain in request memory only. Redaction happens before parsing,
            persistence, model input, or optional external explanation. Derived redacted results
            expire after 24 hours.
          </p>
        </section>
        <section>
          <h2>Citations are executable constraints</h2>
          <p>
            The optional explanation adapter receives only selected redacted evidence. Storage is
            disabled, output follows a strict schema, and any unknown line ID triggers the local
            deterministic fallback.
          </p>
        </section>
      </div>
      <aside className="privacy-warning">
        <strong>Public demo rule</strong>
        <p>Use synthetic or non-confidential logs. Automated redaction is defense in depth, not a guarantee.</p>
      </aside>
    </article>
  );
}

export default function App() {
  const [page, setPage] = useState<Page>(pageFromHash);
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [modelCard, setModelCard] = useState<ModelCard | null>(null);
  const [analysis, setAnalysis] = useState<AnalysisDetail | AnalysisAccepted | null>(null);
  const [events, setEvents] = useState<EvidenceLine[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [eventsState, setEventsState] = useState<"idle" | "loading" | "ready">("idle");
  const [systemStatus, setSystemStatus] = useState<SystemStatus>("checking");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    api.health()
      .then((health) => {
        if (active) setSystemStatus(health.status === "ok" && health.model_ready ? "healthy" : "unavailable");
      })
      .catch(() => {
        if (active) setSystemStatus("unavailable");
      });
    Promise.all([api.scenarios(), api.modelCard()])
      .then(([scenarioData, modelData]) => {
        if (!active) return;
        setScenarios(scenarioData);
        setModelCard(modelData);
      })
      .catch((reason: unknown) => {
        if (active) setError(reason instanceof Error ? reason.message : "Unable to load LogLens.");
      });
    const onHashChange = () => setPage(pageFromHash());
    window.addEventListener("hashchange", onHashChange);
    return () => {
      active = false;
      window.removeEventListener("hashchange", onHashChange);
    };
  }, []);

  const status = analysis?.status;
  useEffect(() => {
    if (!analysis || !["queued", "parsing", "scoring", "explaining"].includes(analysis.status)) {
      return;
    }
    let active = true;
    const timer = window.setTimeout(() => {
      api.analysis(analysis.id)
        .then((detail) => {
          if (active) setAnalysis(detail);
        })
        .catch((reason: unknown) => {
          if (active) setError(reason instanceof Error ? reason.message : "Analysis polling failed.");
        });
    }, 280);
    return () => {
      active = false;
      window.clearTimeout(timer);
    };
  }, [analysis, status]);

  useEffect(() => {
    if (analysis?.status !== "complete") return;
    let active = true;
    setEventsState("loading");
    api.events(analysis.id)
      .then((result) => {
        if (!active) return;
        setEvents(result.items);
        setNextCursor(result.next_cursor);
        setEventsState("ready");
      })
      .catch((reason: unknown) => {
        if (active) {
          setEventsState("ready");
          setError(reason instanceof Error ? reason.message : "Unable to load events.");
        }
      });
    return () => {
      active = false;
    };
  }, [analysis?.id, analysis?.status]);

  const detail = analysis && "windows" in analysis ? analysis : null;
  const announcement = useMemo(() => {
    if (error) return `Error: ${error}`;
    return status ? statusLabels[status] : "Choose a scenario or upload a log to begin.";
  }, [error, status]);

  const navigate = (destination: Page) => {
    window.location.hash = destination === "console" ? "" : destination;
    setPage(destination);
  };

  const begin = async (operation: () => Promise<AnalysisAccepted>) => {
    setBusy(true);
    setError(null);
    setEvents([]);
    setNextCursor(null);
    setEventsState("idle");
    try {
      setAnalysis(await operation());
    } catch (reason) {
      setError(reason instanceof ApiError ? reason.message : "The analysis could not be started.");
    } finally {
      setBusy(false);
    }
  };

  const loadMoreEvents = async () => {
    if (!analysis || !nextCursor) return;
    const pageResult = await api.events(analysis.id, nextCursor);
    setEvents((current) => [...current, ...pageResult.items]);
    setNextCursor(pageResult.next_cursor);
  };

  return (
    <div className="app-shell">
      <a className="skip-link" href="#main-content">Skip to main content</a>
      <Header page={page} systemStatus={systemStatus} onNavigate={navigate} />
      <main id="main-content" tabIndex={-1}>
        {page === "console" && (
          <ConsolePage
            scenarios={scenarios}
            analysis={detail}
            pending={analysis && !detail ? analysis : null}
            events={events}
            eventsLoading={eventsState === "loading"}
            nextCursor={nextCursor}
            busy={busy}
            error={error}
            onRunScenario={(id) => begin(() => api.createScenario(id))}
            onUpload={(file) => begin(() => api.createUpload(file))}
            onRetry={analysis ? () => begin(() => api.retry(analysis.id)) : undefined}
            onLoadMore={loadMoreEvents}
          />
        )}
        {page === "evaluation" && <EvaluationPage model={modelCard} />}
        {page === "methodology" && <MethodologyPage />}
      </main>
      <p className="sr-only" aria-live="polite" aria-atomic="true">
        {announcement}
      </p>
    </div>
  );
}
