import Plotly from "plotly.js-dist-min";
import createPlotlyComponent from "react-plotly.js/factory";
import type { ColorScale, Config, Data, Layout, PlotMouseEvent } from "plotly.js";
import type { Cell, Language, MapView } from "./types";
import { t } from "./labels";

const Plot = createPlotlyComponent(Plotly);

interface Props {
  cells: Cell[];
  view: MapView;
  threshold: number;
  selectedId: string;
  language: Language;
  showPresence: boolean;
  showExtrapolation: boolean;
  onSelect: (id: string) => void;
}

const suitabilityScale: ColorScale = [
  [0, "#e8e9df"],
  [0.25, "#c4d2af"],
  [0.5, "#82a987"],
  [0.75, "#3f7860"],
  [1, "#173f34"],
];
const changeScale: ColorScale = [
  [0, "#ad564b"],
  [0.5, "#f0eee5"],
  [1, "#24877b"],
];
const classColors = ["#377d60", "#c65b4d", "#389da0", "#e5e8df"];
const classScale: ColorScale = [
  [0, classColors[0]], [0.25, classColors[0]],
  [0.25, classColors[1]], [0.5, classColors[1]],
  [0.5, classColors[2]], [0.75, classColors[2]],
  [0.75, classColors[3]], [1, classColors[3]],
];

export function CellMap({
  cells,
  view,
  threshold,
  selectedId,
  language,
  showPresence,
  showExtrapolation,
  onSelect,
}: Props) {
  const longitudes = [...new Set(cells.map((cell) => cell.lon))].sort((a, b) => a - b);
  const latitudes = [...new Set(cells.map((cell) => cell.lat))].sort((a, b) => a - b);
  const byCoordinate = new Map(cells.map((cell) => [`${cell.lat}:${cell.lon}`, cell]));
  const rows = latitudes.map((latitude) =>
    longitudes.map((longitude) => byCoordinate.get(`${latitude}:${longitude}`)),
  );
  const selected = cells.find((cell) => cell.grid_id === selectedId);

  if (longitudes.length === 0 || latitudes.length === 0) {
    return <div className="map-error">No grid cells are available.</div>;
  }

  const heatValues = rows.map((row) => row.map((cell) => {
    if (!cell) return null;
    if (view === "current") return cell.suitability_current;
    if (view === "future") return cell.suitability_2050;
    if (view === "change") return cell.delta_suitability;
    const current = cell.suitability_current >= threshold;
    const future = cell.suitability_2050 >= threshold;
    if (current && future) return 0;
    if (current) return 1;
    if (future) return 2;
    return 3;
  }));
  const customdata = rows.map((row) =>
    row.map((cell) => cell?.grid_id ?? ""),
  );
  const isChange = view === "change";
  const isClasses = view === "classes";
  const selectedShapes = selected ? [{
    type: "rect" as const,
    x0: selected.lon - 1 / 24,
    x1: selected.lon + 1 / 24,
    y0: selected.lat - 1 / 24,
    y1: selected.lat + 1 / 24,
    line: { color: "#dfa93f", width: 2.5 },
    fillcolor: "rgba(0,0,0,0)",
  }] : [];
  const data: Data[] = [{
    type: "heatmap",
    x: longitudes,
    y: latitudes,
    z: heatValues,
    customdata,
    zmin: isChange ? -1 : isClasses ? -0.5 : 0,
    zmax: isChange ? 1 : isClasses ? 3.5 : 1,
    colorscale: isChange ? changeScale : isClasses ? classScale : suitabilityScale,
    zsmooth: false,
    xgap: 1,
    ygap: 1,
    showscale: false,
    hovertemplate: "<b>%{customdata}</b><extra></extra>",
  }];

  if (showPresence) {
    const points = cells.filter((cell) => cell.recorded_presence);
    data.push({
      type: "scatter",
      mode: "markers",
      x: points.map((cell) => cell.lon),
      y: points.map((cell) => cell.lat),
      customdata: points.map((cell) => [cell.grid_id]),
      marker: { size: 7, color: "#e8bc58", line: { width: 1, color: "#3b5541" } },
      name: t(language, "occurrenceToggle"),
      hovertemplate: "%{customdata[0]}<extra></extra>",
    });
  }

  if (showExtrapolation && !isClasses) {
    const points = cells.filter((cell) =>
      view === "current" ? cell.extrapolated_current : cell.extrapolated_2050,
    );
    data.push({
      type: "scatter",
      mode: "markers",
      x: points.map((cell) => cell.lon),
      y: points.map((cell) => cell.lat),
      customdata: points.map((cell) => [cell.grid_id]),
      marker: { size: 5, symbol: "x", color: "#8e4e79" },
      name: t(language, "extrapolationToggle"),
      hovertemplate: "%{customdata[0]}<extra></extra>",
    });
  }

  const layout: Partial<Layout> = {
    autosize: true,
    height: 470,
    margin: { l: 42, r: 20, t: 16, b: 64 },
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor: "rgba(0,0,0,0)",
    font: {
      family: "DM Sans, Noto Sans SC, sans-serif",
      color: "#526456",
      size: 10,
      shadow: "none",
      weight: 400,
    },
    xaxis: {
      title: { text: language === "zh" ? "经度 / Longitude" : "Longitude (E)", font: { size: 9 } },
      range: [98.5 - 1 / 24, 103 + 1 / 24],
      tickvals: [99, 100, 101, 102, 103],
      showgrid: false,
      zeroline: false,
      fixedrange: false,
    },
    yaxis: {
      title: { text: language === "zh" ? "纬度 / Latitude" : "Latitude (N)", font: { size: 9 } },
      range: [26 - 1 / 24, 29.5 + 1 / 24],
      tickvals: [26, 27, 28, 29],
      showgrid: false,
      zeroline: false,
      scaleanchor: "x",
      scaleratio: 1 / Math.cos((27.75 * Math.PI) / 180),
      fixedrange: false,
    },
    showlegend: false,
    shapes: selectedShapes,
    clickmode: "event",
    hoverlabel: { bgcolor: "#fdfcf8", bordercolor: "#d9ded3", font: { color: "#334b3b", size: 11 } },
    uirevision: `habitat-map-${view}`,
  };
  const config: Partial<Config> = {
    displaylogo: false,
    scrollZoom: false,
    responsive: true,
    doubleClick: "reset" as const,
    modeBarButtonsToRemove: ["lasso2d", "select2d"],
  };

  function selectPoint(event: PlotMouseEvent) {
    const point = event.points[0];
    const data = point?.customdata;
    const id = Array.isArray(data) ? data[0] : data;
    if (typeof id === "string" && id) onSelect(id);
  }

  return (
    <div className="plotly-map" aria-label={language === "zh" ? "交互式适宜度地图" : "Interactive suitability map"}>
      <Plot
        data={data}
        layout={layout}
        config={config}
        useResizeHandler
        style={{ width: "100%", height: "100%" }}
        onClick={selectPoint}
      />
    </div>
  );
}
