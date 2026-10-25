import { lazy, Suspense, useEffect, useMemo, useRef, useState } from "react";
import type { ReactNode } from "react";
import { t } from "./labels";
import { FEATURE_ORDER, factorLabel, formatArea, formatFactor, formatScore, summarize } from "./model";
import type { Cell, Dashboard, Language, MapView, Summary } from "./types";

const CellMap = lazy(() => import("./CellMap").then((module) => ({ default: module.CellMap })));
const INITIAL_THRESHOLD = 0.5;

function DeferredMap({ render }: { render: () => ReactNode }) {
  const host = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const target = host.current;
    if (!target || visible) return;
    const observer = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting) {
        setVisible(true);
        observer.disconnect();
      }
    }, { rootMargin: "120px" });
    observer.observe(target);
    return () => observer.disconnect();
  }, [visible]);

  return (
    <div ref={host} className="map-viewport">
      {visible
        ? render()
        : <div className="map-loading" aria-label="Interactive map loading"><span>H / 2050</span></div>}
    </div>
  );
}

function useDashboard(retryKey: number) {
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    fetch("/api/dashboard", { signal: controller.signal })
      .then(async (response) => {
        if (!response.ok) {
          const body = await response.json().catch(() => ({}));
          throw new Error(typeof body.error === "string" ? body.error : `HTTP ${response.status}`);
        }
        return await response.json() as Dashboard;
      })
      .then((value) => {
        if (!Array.isArray(value.cells) || value.cells.length === 0) {
          throw new Error("The model API returned an empty grid.");
        }
        setDashboard(value);
      })
      .catch((cause: unknown) => {
        if (cause instanceof DOMException && cause.name === "AbortError") return;
        setError(cause instanceof Error ? cause.message : "Unknown connection error");
      })
      .finally(() => setLoading(false));
    return () => controller.abort();
  }, [retryKey]);

  return { dashboard, error, loading };
}

function changeLabel(cell: Cell, threshold: number, language: Language): string {
  const now = cell.suitability_current >= threshold;
  const later = cell.suitability_2050 >= threshold;
  if (now && later) return t(language, "classPersistent");
  if (now) return t(language, "classLost");
  if (later) return t(language, "classGained");
  return t(language, "classUnsuitable");
}

function metricValue(value: number, language: Language): string {
  return `${formatArea(value, language)} km²`;
}

function MetricCard({
  label,
  value,
  sub,
  tone,
}: {
  label: string;
  value: string;
  sub: string;
  tone?: string;
}) {
  return (
    <article className={`metric-card${tone ? ` ${tone}` : ""}`}>
      <p className="metric-label">{label}</p>
      <p className="metric-value">{value}</p>
      <p className="metric-sub">{sub}</p>
    </article>
  );
}

function Evidence({
  dashboard,
  language,
}: {
  dashboard: Dashboard;
  language: Language;
}) {
  const translate = (key: string) => t(language, key);
  const audit = dashboard.audit_counts;
  const total = Object.values(audit).reduce((sum, count) => sum + count, 0);
  const maxImportance = Math.max(
    0.001,
    ...dashboard.feature_importance.map((item) => Math.abs(item.auc_drop)),
  );

  return (
    <section className="evidence-section" id="evidence">
      <div className="section-heading">
        <span className="eyebrow">{t(language, "evidence")}</span>
        <h2>{t(language, "evidenceTitle")}</h2>
      </div>
      <div className="evidence-grid">
        <article className="surface evidence-panel">
          <div className="panel-topline">
            <div>
              <span className="panel-kicker">{t(language, "validationLabel")}</span>
              <h3>ROC-AUC <span className="info-dot" title={t(language, "aucTooltip")}>i</span></h3>
            </div>
            <span className="auc-score">{dashboard.evaluation.validation_roc_auc.toFixed(3)}</span>
          </div>
          <div className="auc-track">
            <span style={{ width: `${dashboard.evaluation.validation_roc_auc * 100}%` }} />
          </div>
          <div className="stat-pair">
            <span>{t(language, "train")} <b>{dashboard.evaluation.train_cells}</b></span>
            <span>{t(language, "validation")} <b>{dashboard.evaluation.validation_cells}</b></span>
          </div>
          <p className="evidence-copy">
            {dashboard.evaluation.validation_presence_cells} {t(language, "presenceOf")}{" "}
            {dashboard.evaluation.validation_background_cells} {t(language, "backgroundCells")}
          </p>
          <p className="fine-print">{t(language, "validationWarning")}</p>
        </article>

        <article className="surface evidence-panel">
          <div className="panel-topline">
            <div>
              <span className="panel-kicker">{t(language, "variableNote")}</span>
              <h3>{t(language, "variableTitle")}</h3>
            </div>
            <span className="panel-index">01</span>
          </div>
          <div className="importance-list">
            {dashboard.feature_importance.map((item, index) => (
              <div className="importance-row" key={item.feature}>
                <span className="importance-rank">0{index + 1}</span>
                <span className="importance-name">
                  {factorLabel(item.feature as (typeof FEATURE_ORDER)[number], translate)}
                </span>
                <span className="importance-track">
                  <span
                    className="importance-fill"
                    style={{ width: `${Math.max(2, (Math.abs(item.auc_drop) / maxImportance) * 100)}%` }}
                  />
                </span>
                <span className="importance-value">{item.auc_drop.toFixed(3)}</span>
              </div>
            ))}
          </div>
          <p className="fine-print">{t(language, "importanceWarning")}</p>
        </article>

        <article className="surface evidence-panel audit-panel">
          <div className="panel-topline">
            <div>
              <span className="panel-kicker">{t(language, "dataAudit")}</span>
              <h3>{total} {t(language, "sourceRows")}</h3>
            </div>
            <span className="panel-index">02</span>
          </div>
          <div className="audit-list">
            <AuditLine label={t(language, "retained")} count={audit.retained ?? 0} accent />
            <AuditLine label={t(language, "duplicate")} count={audit.duplicate_grid ?? 0} />
            <AuditLine label={t(language, "unmatched")} count={audit.outside_or_unmatched_grid ?? 0} />
            <AuditLine label={t(language, "missing")} count={audit.missing_or_invalid_coordinates ?? 0} />
          </div>
          <p className="fine-print">{t(language, "auditWarning")}</p>
        </article>

        <article className="surface evidence-panel limitations-panel">
          <div className="panel-topline">
            <div>
              <span className="panel-kicker">{t(language, "limitations")}</span>
              <h3>{t(language, "scenario")}</h3>
            </div>
            <span className="panel-index">03</span>
          </div>
          <div className="scenario-row">
            <span>{t(language, "pathway")}</span><b>{dashboard.scenario.pathway}</b>
          </div>
          <div className="scenario-row">
            <span>{t(language, "climateModel")}</span><b>{dashboard.scenario.gcm}</b>
          </div>
          <div className="scenario-row">
            <span>{t(language, "futurePeriod")}</span><b>{dashboard.scenario.future_period}</b>
          </div>
          <p className="fine-print">{t(language, "scenarioWarning")}</p>
        </article>
      </div>
      <details className="source-details">
        <summary>{t(language, "source")}</summary>
        <div className="source-body">
          <p>{t(language, "sourceCredits")}</p>
          <p>{t(language, "sourceBaseline")}</p>
          <p>{t(language, "sourceLimit")}</p>
          <p>{t(language, "sourceUse")}</p>
        </div>
      </details>
    </section>
  );
}

function AuditLine({ label, count, accent = false }: { label: string; count: number; accent?: boolean }) {
  return (
    <div className="audit-row">
      <span className={accent ? "audit-dot accent" : "audit-dot"} />
      <span>{label}</span>
      <b>{count}</b>
    </div>
  );
}

export function App() {
  const [language, setLanguage] = useState<Language>("zh");
  const [view, setView] = useState<MapView>("current");
  const [threshold, setThreshold] = useState(INITIAL_THRESHOLD);
  const [selectedId, setSelectedId] = useState("");
  const [showPresence, setShowPresence] = useState(true);
  const [showExtrapolation, setShowExtrapolation] = useState(false);
  const [retryKey, setRetryKey] = useState(0);
  const [exporting, setExporting] = useState(false);
  const [exportError, setExportError] = useState(false);
  const { dashboard, error, loading } = useDashboard(retryKey);
  const translate = (key: string) => t(language, key);

  const cells = dashboard?.cells ?? [];
  const selectedCell = cells.find((cell) => cell.grid_id === selectedId) ?? cells[0];
  const summary: Summary | null = useMemo(
    () => dashboard ? summarize(dashboard.cells, threshold) : null,
    [dashboard, threshold],
  );

  useEffect(() => {
    if (cells.length > 0 && !cells.some((cell) => cell.grid_id === selectedId)) {
      setSelectedId(cells.find((cell) => cell.recorded_presence)?.grid_id ?? cells[0].grid_id);
    }
  }, [cells, selectedId]);

  async function exportEvidence() {
    setExporting(true);
    setExportError(false);
    try {
      const response = await fetch("/api/export", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ threshold }),
      });
      if (!response.ok) throw new Error(`Export failed: ${response.status}`);
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = "habitat-2050-evidence.zip";
      document.body.append(link);
      link.click();
      window.setTimeout(() => {
        URL.revokeObjectURL(url);
        link.remove();
      }, 1000);
    } catch {
      setExportError(true);
    } finally {
      setExporting(false);
    }
  }

  const views: MapView[] = ["current", "future", "change", "classes"];
  const viewKeys: Record<MapView, string> = {
    current: "viewCurrent",
    future: "viewFuture",
    change: "viewChange",
    classes: "viewClasses",
  };

  if (loading && !dashboard) {
    return (
      <main className="loading-screen">
        <div className="loading-mark">H / 2050</div>
        <div className="loading-orbit"><span /></div>
        <h1>{t(language, "loading")}</h1>
        <p>{t(language, "loadingNote")}</p>
      </main>
    );
  }

  if (error && !dashboard) {
    return (
      <main className="error-screen">
        <div className="brand-mark">H<span>/</span>2050</div>
        <span className="panel-kicker">{t(language, "localModel")}</span>
        <h1>{t(language, "apiUnavailable")}</h1>
        <p>{error}</p>
        <button className="primary-button" onClick={() => setRetryKey((value) => value + 1)}>
          {t(language, "retry")}
        </button>
        <LanguageToggle language={language} setLanguage={setLanguage} translate={translate} />
      </main>
    );
  }

  if (!dashboard || !summary) return null;

  const thresholdText = threshold.toFixed(2);
  const thresholdNote = t(language, "modeledArea").replace("{threshold}", thresholdText);
  const signedDelta = summary.delta < 0 ? "−" : "+";
  const deltaPercent = summary.changePercent === null
    ? "—"
    : `${summary.changePercent < 0 ? "−" : "+"}${Math.abs(summary.changePercent).toFixed(1)}%`;

  return (
    <div className={language === "zh" ? "app-shell chinese" : "app-shell"}>
      <header className="topbar">
        <a className="brand-mark" href="#" aria-label="Habitat 2050">H<span>/</span>2050</a>
        <div className="topbar-location">
          <span className="location-dot" />
          <span>{t(language, "location")}</span>
        </div>
        <nav className="topnav">
          <a href="#explore">{t(language, "mapTitle")}</a>
          <a href="#evidence">{t(language, "evidence")}</a>
          <button
            className="language-switch"
            onClick={() => setLanguage((value) => value === "zh" ? "en" : "zh")}
            aria-label={t(language, "languageLabel")}
          >
            {t(language, "languageLabel")}
          </button>
        </nav>
      </header>

      <main className="main-content">
        <section className="hero">
          <div className="hero-copy">
            <span className="eyebrow"><span className="eyebrow-mark">✳</span>{t(language, "kicker")}</span>
            <h1>{t(language, "title")}</h1>
            <p className="hero-intro">{t(language, "introduction")}</p>
            <div className="species-line">
              <span className="species-english">{t(language, "species")}</span>
              <i>{t(language, "speciesLatin")}</i>
              <span className="species-separator">/</span>
              <span className="scenario-pill">{dashboard.scenario.pathway} · 2050</span>
            </div>
          </div>
          <div className="hero-art" aria-hidden="true">
            <div className="hero-glow" />
            <div className="hero-orbit orbit-one" />
            <div className="hero-orbit orbit-two" />
            <div className="hero-contour contour-one" />
            <div className="hero-contour contour-two" />
            <div className="hero-contour contour-three" />
            <span className="hero-coordinate">27°45'N<br />101°31'E</span>
            <span className="hero-period">MODEL / 2050</span>
          </div>
        </section>

        <section className="metrics-grid" aria-label={t(language, "areaOverview")}>
          <MetricCard
            label={t(language, "currentArea")}
            value={metricValue(summary.current, language)}
            sub={t(language, "currentBaseline")}
          />
          <MetricCard
            label={t(language, "futureArea")}
            value={metricValue(summary.future, language)}
            sub={`${dashboard.scenario.gcm} · ${dashboard.scenario.future_period}`}
          />
          <MetricCard
            label={t(language, "netChange")}
            value={`${signedDelta}${metricValue(Math.abs(summary.delta), language)}`}
            sub={deltaPercent}
            tone={summary.delta <= 0 ? "tone-rust" : "tone-teal"}
          />
          <MetricCard
            label={t(language, "persistent")}
            value={metricValue(summary.persistent, language)}
            sub={t(language, "persistentSub")}
            tone="tone-forest"
          />
          <p className="metrics-footnote"><span>i</span>{thresholdNote}</p>
        </section>

        <section className="explorer-section" id="explore">
          <div className="section-heading explorer-heading">
            <div>
              <span className="eyebrow"><span className="eyebrow-mark">01</span>{t(language, "exploreEyebrow")}</span>
              <h2>{t(language, "mapTitle")}</h2>
              <p>{t(language, "mapDescription")}</p>
            </div>
            <button className="export-button" onClick={exportEvidence} disabled={exporting}>
              <span className="export-icon">↥</span>
              {exporting ? t(language, "exporting") : t(language, "export")}
            </button>
          </div>

          <div className="explorer-grid">
            <section className="surface map-panel">
              <div className="map-toolbar">
                <div className="view-tabs" role="tablist" aria-label={t(language, "views")}>
                  {views.map((key) => (
                    <button
                      key={key}
                      role="tab"
                      aria-selected={view === key}
                      className={view === key ? "view-tab active" : "view-tab"}
                      onClick={() => setView(key)}
                    >
                      {t(language, viewKeys[key])}
                    </button>
                  ))}
                </div>
                <span className="grid-count">{cells.length.toLocaleString(language === "zh" ? "zh-CN" : "en")} CELLS</span>
              </div>
              <div className="map-stage">
                <DeferredMap render={() => (
                  <Suspense fallback={<div className="map-loading"><span>H / 2050</span></div>}>
                    <CellMap
                      cells={cells}
                      view={view}
                      threshold={threshold}
                      selectedId={selectedCell.grid_id}
                      language={language}
                      showPresence={showPresence}
                      showExtrapolation={showExtrapolation}
                      onSelect={setSelectedId}
                    />
                  </Suspense>
                )} />
                <div className="map-north" aria-hidden="true"><span>↑</span>N</div>
              </div>
              <div className="map-footer">
                <div className="legend">
                  <span>{t(language, view === "change" ? "declining" : view === "classes" ? "classPersistent" : "legendLow")}</span>
                  <span className={view === "classes" ? "class-legend" : "gradient-legend"} />
                  <span>{t(language, view === "change" ? "improving" : view === "classes" ? "classUnsuitable" : "legendHigh")}</span>
                </div>
                <span className="map-hint">{t(language, "mapHint")}</span>
              </div>
              <div className="map-toggles">
                <label className="toggle-label">
                  <input type="checkbox" checked={showPresence} onChange={(event) => setShowPresence(event.target.checked)} />
                  <span className="toggle-track" />
                  <span>{t(language, "occurrenceToggle")}</span>
                </label>
                <label className="toggle-label">
                  <input type="checkbox" checked={showExtrapolation} onChange={(event) => setShowExtrapolation(event.target.checked)} />
                  <span className="toggle-track" />
                  <span>{t(language, "extrapolationToggle")}</span>
                </label>
              </div>
              {exportError && <p className="inline-error" role="alert">{t(language, "exportError")}</p>}
            </section>

            <aside className="surface inspector-panel">
              <div className="inspector-header">
                <span className="panel-kicker">{t(language, "inspector")}</span>
                <span className="selected-id">{selectedCell.grid_id}</span>
              </div>
              <label className="select-label" htmlFor="cell-select">{t(language, "selectCell")}</label>
              <select id="cell-select" value={selectedCell.grid_id} onChange={(event) => setSelectedId(event.target.value)}>
                {cells.map((cell) => (
                  <option key={cell.grid_id} value={cell.grid_id}>
                    {cell.grid_id} · {cell.lon.toFixed(3)}°E, {cell.lat.toFixed(3)}°N
                  </option>
                ))}
              </select>
              <p className="coordinates">{selectedCell.lon.toFixed(4)}° E <span>/</span> {selectedCell.lat.toFixed(4)}° N</p>

              <div className="suitability-pair">
                <div>
                  <span>{t(language, "currentSuitability")}</span>
                  <strong>{formatScore(selectedCell.suitability_current)}</strong>
                </div>
                <div>
                  <span>{t(language, "futureSuitability")}</span>
                  <strong>{formatScore(selectedCell.suitability_2050)}</strong>
                </div>
              </div>
              <div className="status-line">
                <span className={`status-dot ${selectedCell.recorded_presence ? "status-amber" : "status-green"}`} />
                <span>{changeLabel(selectedCell, threshold, language)}</span>
              </div>
              {selectedCell.recorded_presence && <p className="micro-badge presence-badge">● {t(language, "presenceBadge")}</p>}
              {((view === "current" && selectedCell.extrapolated_current) || selectedCell.extrapolated_2050) &&
                <p className="micro-badge extrapolation-badge">↗ {t(language, "outsideBadge")}</p>}
              <p className="score-notice">{t(language, "scoreNotice")}</p>

              <div className="factor-heading">
                <span>{t(language, "factors")}</span>
                <span>{t(language, "currentColumn")} <i>→</i> {t(language, "futureColumn")}</span>
              </div>
              <div className="factor-list">
                {FEATURE_ORDER.map((key) => (
                  <div className="factor-row" key={key}>
                    <span>{factorLabel(key, translate)}</span>
                    <b>{formatFactor(selectedCell.current_factors[key], key)}</b>
                    <span className="factor-arrow">→</span>
                    <b>{formatFactor(selectedCell.future_factors[key], key)}</b>
                  </div>
                ))}
              </div>
              <div className="inspector-note">
                <span className="note-glyph">↗</span>
                <p>{t(language, "inspectorNote")}</p>
              </div>
            </aside>
          </div>
          <div className="privacy-strip"><span>◈</span>{t(language, "privacy")}</div>
        </section>

        <section className="threshold-section">
          <div className="threshold-copy">
            <span className="eyebrow"><span className="eyebrow-mark">02</span>{t(language, "sensitivity")}</span>
            <h2>{t(language, "thresholdTitle")}</h2>
            <p>{t(language, "thresholdNote")}</p>
          </div>
          <div className="threshold-control surface">
            <div className="threshold-value"><span>{t(language, "threshold")}</span><b>{thresholdText}</b></div>
            <input
              aria-label={t(language, "threshold")}
              type="range"
              min="0.1"
              max="0.9"
              step="0.05"
              value={threshold}
              onChange={(event) => setThreshold(Number(event.target.value))}
            />
            <div className="threshold-scale"><span>0.10</span><span>0.50</span><span>0.90</span></div>
            <div className="class-summary">
              <div><span className="class-dot class-persistent" />{t(language, "classPersistent")} <b>{metricValue(summary.persistent, language)}</b></div>
              <div><span className="class-dot class-lost" />{t(language, "classLost")} <b>{metricValue(summary.lost, language)}</b></div>
              <div><span className="class-dot class-gained" />{t(language, "classGained")} <b>{metricValue(summary.gained, language)}</b></div>
            </div>
          </div>
        </section>

        <Evidence dashboard={dashboard} language={language} />
        <footer className="page-footer">
          <span>{t(language, "footer")}</span>
          <span>{dashboard.evaluation.model} · seed {dashboard.evaluation.seed}</span>
          <button className="footer-language" onClick={() => setLanguage((value) => value === "zh" ? "en" : "zh")}>
            {t(language, "languageLabel")}
          </button>
        </footer>
      </main>
    </div>
  );
}

function LanguageToggle({
  language,
  setLanguage,
  translate,
}: {
  language: Language;
  setLanguage: (value: Language) => void;
  translate: (key: string) => string;
}) {
  return (
    <button className="language-switch error-language" onClick={() => setLanguage(language === "zh" ? "en" : "zh")}>
      {translate("languageLabel")}
    </button>
  );
}
