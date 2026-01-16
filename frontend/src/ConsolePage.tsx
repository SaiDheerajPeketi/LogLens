import {
  AlertTriangle,
  ArrowRight,
  Check,
  ChevronRight,
  CircleDot,
  Database,
  FileLock2,
  FileUp,
  Gauge,
  LoaderCircle,
  Play,
  RefreshCw,
  Search,
  ShieldCheck,
  Sparkles,
  TerminalSquare,
} from "lucide-react";
import { type ChangeEvent, type KeyboardEvent, useEffect, useMemo, useState } from "react";

import { causeLabels, percent, shortTime, statusLabels } from "./format";
import type {
  AnalysisAccepted,
  AnalysisDetail,
  AnalysisStatus,
  EvidenceLine,
  Scenario,
  WindowResult,
} from "./types";

interface ConsolePageProps {
  scenarios: Scenario[];
  analysis: AnalysisDetail | null;
  pending: AnalysisAccepted | null;
  events: EvidenceLine[];
  nextCursor: string | null;
  busy: boolean;
  error: string | null;
  onRunScenario: (scenarioId: string) => void;
  onUpload: (file: File) => void;
  onRetry?: () => void;
  onLoadMore: () => void;
}

const PHASES: AnalysisStatus[] = ["queued", "parsing", "scoring", "explaining", "complete"];

function SourceRail({
  scenarios,
  selected,
  busy,
  onSelect,
  onRun,
  onUpload,
}: {
  scenarios: Scenario[];
  selected: string;
  busy: boolean;
  onSelect: (id: string) => void;
  onRun: () => void;
  onUpload: (file: File) => void;
}) {
  const handleFile = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.currentTarget.files?.[0];
    if (file) onUpload(file);
    event.currentTarget.value = "";
  };
  return (
    <aside className="source-rail" aria-labelledby="source-heading">
      <div className="rail-heading">
        <p className="eyebrow">Input channel</p>
        <h2 id="source-heading">Incident source</h2>
      </div>
      <div className="source-status">
        <Database size={18} aria-hidden="true" />
        <div><strong>Synthetic flight data</strong><span>Safe to replay locally</span></div>
        <span className="status-lamp" aria-hidden="true" />
      </div>
      <fieldset className="scenario-fieldset">
        <legend>Built-in scenarios</legend>
        {scenarios.map((scenario, index) => (
          <button
            type="button"
            className={scenario.id === selected ? "scenario-option selected" : "scenario-option"}
            aria-pressed={scenario.id === selected}
            onClick={() => onSelect(scenario.id)}
            key={scenario.id}
          >
            <span>{String(index + 1).padStart(2, "0")}</span>
            <div><strong>{scenario.name}</strong><small>{scenario.line_count} redacted lines</small></div>
            <ChevronRight size={15} aria-hidden="true" />
          </button>
        ))}
      </fieldset>
      <button className="primary-action" type="button" onClick={onRun} disabled={!selected || busy}>
        {busy ? <LoaderCircle className="spin" size={16} /> : <Play size={16} fill="currentColor" />}
        Run incident replay
      </button>
      <div className="rail-divider"><span>or inspect your own data</span></div>
      <label className="upload-control">
        <FileUp size={18} aria-hidden="true" />
        <span><strong>Upload log</strong><small>.log or .txt · 5 MB max</small></span>
        <input type="file" accept=".log,.txt,text/plain" onChange={handleFile} />
      </label>
      <div className="privacy-note">
        <FileLock2 size={16} aria-hidden="true" />
        <p><strong>Raw input is never stored.</strong> Results remain redacted and expire after 24 hours.</p>
      </div>
    </aside>
  );
}

function SignalStrip({ anomaly, seed = 0 }: { anomaly: boolean; seed?: number }) {
  return (
    <span className={anomaly ? "signal-strip anomaly" : "signal-strip"} aria-hidden="true">
      {Array.from({ length: 52 }, (_, index) => {
        const center = 1 - Math.min(1, Math.abs(index - 27) / 18);
        const base = 14 + Math.abs(Math.sin((index + seed) * 1.71)) * 22;
        const height = anomaly ? base + center * 35 : base;
        return <i style={{ height: `${height}%` }} key={index} />;
      })}
    </span>
  );
}

function PipelineState({ status }: { status: AnalysisStatus }) {
  const current = Math.max(0, PHASES.indexOf(status));
  return (
    <section className="process-state" aria-labelledby="process-title">
      <LoaderCircle className="spin" size={24} aria-hidden="true" />
      <p className="eyebrow">Local pipeline active</p>
      <h2 id="process-title">{statusLabels[status]}</h2>
      <p>Raw bytes have left memory. Every later stage operates on redacted lines.</p>
      <ol>
        {PHASES.slice(0, -1).map((phase, index) => (
          <li className={index <= current ? "reached" : ""} key={phase}>
            <span>{index < current ? <Check size={13} /> : index === current ? <CircleDot size={13} /> : index + 1}</span>
            {statusLabels[phase]}
          </li>
        ))}
      </ol>
    </section>
  );
}

function FirstRun({ onStart }: { onStart: () => void }) {
  return (
    <section className="first-run" aria-labelledby="first-run-title">
      <div className="recorder-glyph" aria-hidden="true"><Gauge size={32} /></div>
      <p className="eyebrow">Flight recorder ready</p>
      <h1 id="first-run-title">Replay the failure.<br />Inspect the evidence.</h1>
      <p>
        LogLens finds suspicious time windows, proposes a supported cause, and ties every
        explanation to exact redacted log lines.
      </p>
      <button className="primary-action wide" type="button" onClick={onStart}>
        <Play size={16} fill="currentColor" /> Start with database timeout
      </button>
      <div className="first-run-contract">
        <span><ShieldCheck size={15} /> Redact first</span>
        <span><TerminalSquare size={15} /> Cite exact lines</span>
        <span><Sparkles size={15} /> Explain last</span>
      </div>
    </section>
  );
}

function Timeline({
  windows,
  selectedId,
  onSelect,
}: {
  windows: WindowResult[];
  selectedId: string;
  onSelect: (window: WindowResult) => void;
}) {
  const handleKeys = (event: KeyboardEvent<HTMLButtonElement>, index: number) => {
    if (!['ArrowLeft', 'ArrowRight'].includes(event.key)) return;
    event.preventDefault();
    const direction = event.key === 'ArrowRight' ? 1 : -1;
    const next = Math.min(windows.length - 1, Math.max(0, index + direction));
    onSelect(windows[next]);
    document.getElementById(`window-${windows[next].id}`)?.focus();
  };
  return (
    <section className="timeline-panel" aria-labelledby="timeline-title">
      <div className="panel-heading">
        <div><p className="eyebrow">Incident replay</p><h2 id="timeline-title">Anomaly timeline</h2></div>
        <div className="legend" aria-label="Timeline legend">
          <span><i className="normal-dot" /> Normal</span>
          <span><i className="anomaly-dot" /> Anomaly</span>
        </div>
      </div>
      <div className="master-signal"><SignalStrip anomaly={windows.some((window) => window.is_anomaly)} seed={8} /></div>
      <div className="window-grid" role="group" aria-label="Analysis windows">
        {windows.map((window, index) => (
          <button
            id={`window-${window.id}`}
            type="button"
            className={window.id === selectedId ? "window-cell selected" : "window-cell"}
            aria-pressed={window.id === selectedId}
            aria-label={`Window ${index + 1}, lines ${window.start_line} to ${window.end_line}, ${percent(window.anomaly_score)} anomaly score`}
            onClick={() => onSelect(window)}
            onKeyDown={(event) => handleKeys(event, index)}
            key={window.id}
          >
            <span className="window-number">{String(index + 1).padStart(2, "0")}</span>
            <strong>{window.is_anomaly ? "Anomalous" : "Nominal"}</strong>
            <small>Lines {window.start_line}–{window.end_line}</small>
            <SignalStrip anomaly={window.is_anomaly} seed={index * 4} />
            <span className="window-score"><b>{percent(window.anomaly_score)}</b> anomaly score</span>
          </button>
        ))}
      </div>
      <p className="keyboard-hint">Use ← → to replay adjacent windows</p>
    </section>
  );
}

function Diagnosis({
  analysis,
  selected,
  events,
  onEvidence,
}: {
  analysis: AnalysisDetail;
  selected: WindowResult;
  events: EvidenceLine[];
  onEvidence: (lineId: string) => void;
}) {
  const evidence = selected.evidence_line_ids
    .map((id) => events.find((line) => line.id === id))
    .filter((line): line is EvidenceLine => Boolean(line));
  const explanation = analysis.explanation;
  return (
    <aside className="diagnosis-panel" aria-labelledby="diagnosis-title">
      <div className="diagnosis-icon" aria-hidden="true">
        {selected.is_anomaly ? <AlertTriangle size={20} /> : <Check size={20} />}
      </div>
      <p className="eyebrow">Probable cause</p>
      <h2 id="diagnosis-title">
        {selected.is_anomaly ? causeLabels[selected.cause] : "No anomaly detected"}
      </h2>
      <div className="confidence-row">
        <strong>{percent(selected.confidence)}</strong>
        <span>classifier confidence</span>
      </div>
      <div
        className="confidence-track"
        role="progressbar"
        aria-label="Classifier confidence"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={Math.round(selected.confidence * 100)}
      >
        <span style={{ width: `${selected.confidence * 100}%` }} />
      </div>
      {explanation && (
        <div className="explanation-copy">
          <p>{explanation.summary}</p>
          <span className="explanation-mode">
            {explanation.source === "deterministic" ? <TerminalSquare size={13} /> : <Sparkles size={13} />}
            {explanation.source === "deterministic" ? "Deterministic fallback" : "Structured explanation"}
          </span>
        </div>
      )}
      <div className="evidence-heading">
        <h3>Evidence</h3><span>{evidence.length} cited lines</span>
      </div>
      {evidence.length ? (
        <ol className="evidence-list">
          {evidence.map((line, index) => (
            <li key={line.id}>
              <button type="button" onClick={() => onEvidence(line.id)}>
                <span>{index + 1}</span>
                <p><strong>Line {line.line_no} · {line.severity}</strong><small>{line.text}</small></p>
                <ArrowRight size={14} aria-hidden="true" />
              </button>
            </li>
          ))}
        </ol>
      ) : (
        <p className="empty-evidence">No cited failure lines in this window.</p>
      )}
      <div className="caveat-block">
        <h3>Caveats</h3>
        <ul>
          {[...selected.caveats, ...analysis.caveats].slice(0, 3).map((caveat) => <li key={caveat}>{caveat}</li>)}
        </ul>
      </div>
    </aside>
  );
}

function Transcript({
  events,
  selected,
  evidenceIds,
  highlightedId,
  nextCursor,
  onLoadMore,
}: {
  events: EvidenceLine[];
  selected: WindowResult;
  evidenceIds: string[];
  highlightedId: string | null;
  nextCursor: string | null;
  onLoadMore: () => void;
}) {
  const [query, setQuery] = useState("");
  const [severity, setSeverity] = useState("ALL");
  const rows = useMemo(() => events.filter((event) => {
    const inWindow = event.line_no >= selected.start_line && event.line_no <= selected.end_line;
    const matchesSeverity = severity === "ALL" || event.severity === severity;
    const matchesQuery = event.text.toLowerCase().includes(query.toLowerCase());
    return inWindow && matchesSeverity && matchesQuery;
  }), [events, query, selected.end_line, selected.start_line, severity]);
  return (
    <section className="transcript-panel" aria-labelledby="transcript-title">
      <div className="transcript-toolbar">
        <div><p className="eyebrow">Synchronized record</p><h2 id="transcript-title">Redacted transcript</h2></div>
        <label className="search-field"><Search size={15} /><span className="sr-only">Search transcript</span><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search redacted lines" /></label>
        <label className="severity-field"><span className="sr-only">Filter by severity</span><select value={severity} onChange={(event) => setSeverity(event.target.value)}><option>ALL</option><option>ERROR</option><option>WARN</option><option>INFO</option><option>DEBUG</option></select></label>
      </div>
      <div className="table-scroll">
        <table>
          <thead><tr><th scope="col">Line</th><th scope="col">Level</th><th scope="col">Redacted message</th></tr></thead>
          <tbody>
            {rows.map((line) => {
              const cited = evidenceIds.includes(line.id);
              return (
                <tr
                  id={`event-${line.id}`}
                  tabIndex={-1}
                  className={`${cited ? "cited" : ""} ${highlightedId === line.id ? "highlighted" : ""}`}
                  key={line.id}
                >
                  <td data-label="Line">{String(line.line_no).padStart(5, "0")}{cited && <span className="citation-mark">CITED</span>}</td>
                  <td data-label="Level"><span className={`severity severity-${line.severity.toLowerCase()}`}>{line.severity}</span></td>
                  <td data-label="Message">{line.text}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
        {!rows.length && <p className="empty-table">No lines match this window and filter.</p>}
      </div>
      {nextCursor && <button className="load-more" type="button" onClick={onLoadMore}>Load more redacted lines</button>}
    </section>
  );
}

export function ConsolePage({
  scenarios,
  analysis,
  pending,
  events,
  nextCursor,
  busy,
  error,
  onRunScenario,
  onUpload,
  onRetry,
  onLoadMore,
}: ConsolePageProps) {
  const [selectedScenario, setSelectedScenario] = useState("db-timeout-checkout");
  const [selectedWindowId, setSelectedWindowId] = useState("");
  const [highlightedLine, setHighlightedLine] = useState<string | null>(null);

  useEffect(() => {
    if (!analysis?.windows.length) return;
    const primary = [...analysis.windows]
      .sort((left, right) => right.anomaly_score - left.anomaly_score)[0];
    setSelectedWindowId(primary.id);
  }, [analysis?.id, analysis?.windows]);

  const selectedWindow = analysis?.windows.find((window) => window.id === selectedWindowId)
    ?? analysis?.windows[0];
  const currentStatus = analysis?.status ?? pending?.status;

  const goToEvidence = (lineId: string) => {
    setHighlightedLine(lineId);
    window.requestAnimationFrame(() => {
      const target = document.getElementById(`event-${lineId}`);
      target?.scrollIntoView({ block: "center", behavior: "smooth" });
      target?.focus({ preventScroll: true });
    });
  };

  return (
    <div className="console-layout">
      <SourceRail
        scenarios={scenarios}
        selected={selectedScenario}
        busy={busy}
        onSelect={setSelectedScenario}
        onRun={() => onRunScenario(selectedScenario)}
        onUpload={onUpload}
      />
      <div className="console-main">
        {error && <div className="error-banner" role="alert"><AlertTriangle size={17} /><span>{error}</span></div>}
        {!currentStatus && <FirstRun onStart={() => onRunScenario(selectedScenario)} />}
        {currentStatus && ["queued", "parsing", "scoring", "explaining"].includes(currentStatus) && (
          <PipelineState status={currentStatus} />
        )}
        {analysis && ["failed", "expired"].includes(analysis.status) && (
          <section className="failure-state" role="alert">
            <AlertTriangle size={24} />
            <p className="eyebrow">{analysis.status === "expired" ? "Retention window ended" : "Pipeline stopped"}</p>
            <h2>{analysis.error?.message ?? statusLabels[analysis.status]}</h2>
            <p>{analysis.error?.action}</p>
            {analysis.error?.retryable && onRetry && <button className="primary-action" type="button" onClick={onRetry}><RefreshCw size={15} /> Retry analysis</button>}
          </section>
        )}
        {analysis?.status === "complete" && selectedWindow && (
          <>
            <div className="analysis-meta">
              <div><span>Source</span><strong>{analysis.source.name}</strong></div>
              <div><span>Created</span><strong>{shortTime(analysis.created_at)}</strong></div>
              <div><span>Retention</span><strong>Expires {shortTime(analysis.expires_at)}</strong></div>
              <div><span>Raw data</span><strong className="safe-value"><ShieldCheck size={13} /> Not retained</strong></div>
            </div>
            <div className="replay-grid">
              <Timeline windows={analysis.windows} selectedId={selectedWindow.id} onSelect={(window) => { setSelectedWindowId(window.id); setHighlightedLine(null); }} />
              <Diagnosis analysis={analysis} selected={selectedWindow} events={events} onEvidence={goToEvidence} />
              <Transcript events={events} selected={selectedWindow} evidenceIds={selectedWindow.evidence_line_ids} highlightedId={highlightedLine} nextCursor={nextCursor} onLoadMore={onLoadMore} />
            </div>
          </>
        )}
      </div>
    </div>
  );
}
