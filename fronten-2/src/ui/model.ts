import type { Cell, Language, Summary } from "./types";

export const FEATURE_ORDER = [
  "elevation_m",
  "bio1_annual_mean_temp_degC",
  "bio12_annual_precip_mm",
  "ndvi_growing_season",
  "forest_cover_pct",
] as const;

export const FEATURE_LABEL_KEYS: Record<(typeof FEATURE_ORDER)[number], string> = {
  elevation_m: "elevation",
  bio1_annual_mean_temp_degC: "temperature",
  bio12_annual_precip_mm: "rainfall",
  ndvi_growing_season: "ndvi",
  forest_cover_pct: "forest",
};

export const FEATURE_UNITS: Record<(typeof FEATURE_ORDER)[number], string> = {
  elevation_m: "m",
  bio1_annual_mean_temp_degC: "°C",
  bio12_annual_precip_mm: "mm",
  ndvi_growing_season: "",
  forest_cover_pct: "%",
};

export function summarize(cells: Cell[], threshold: number): Summary {
  let current = 0;
  let future = 0;
  let persistent = 0;
  let gained = 0;
  let lost = 0;
  let extrapolated = 0;

  for (const cell of cells) {
    const now = cell.suitability_current >= threshold;
    const later = cell.suitability_2050 >= threshold;
    if (now) current += cell.area_km2;
    if (later) future += cell.area_km2;
    if (now && later) persistent += cell.area_km2;
    else if (now) lost += cell.area_km2;
    else if (later) gained += cell.area_km2;
    if (cell.extrapolated_2050) extrapolated += 1;
  }

  return {
    current,
    future,
    delta: future - current,
    changePercent: current > 0 ? (future / current - 1) * 100 : null,
    persistent,
    gained,
    lost,
    extrapolated,
  };
}

export function formatArea(value: number, language: Language): string {
  return new Intl.NumberFormat(language === "zh" ? "zh-CN" : "en", {
    maximumFractionDigits: 0,
  }).format(value);
}

export function formatScore(value: number): string {
  return value.toFixed(3);
}

export function formatFactor(value: number, feature: string): string {
  const digits = feature === "ndvi_growing_season" ? 2 : 1;
  const formatted = new Intl.NumberFormat("en", {
    maximumFractionDigits: digits,
    minimumFractionDigits: digits,
  }).format(value);
  const unit = FEATURE_UNITS[feature as (typeof FEATURE_ORDER)[number]];
  return unit ? `${formatted} ${unit}` : formatted;
}

export function cellColor(score: number): string {
  const stops = [
    [0, "#e8e9df"],
    [0.25, "#c4d2af"],
    [0.5, "#82a987"],
    [0.75, "#3f7860"],
    [1, "#173f34"],
  ] as const;
  return rampColor(score, stops);
}

export function changeColor(value: number): string {
  const normalized = (value + 1) / 2;
  const stops = [
    [0, "#ad564b"],
    [0.5, "#f0eee5"],
    [1, "#24877b"],
  ] as const;
  return rampColor(normalized, stops);
}

function rampColor(value: number, stops: readonly (readonly [number, string])[]): string {
  const v = Math.max(0, Math.min(1, value));
  for (let i = 1; i < stops.length; i += 1) {
    if (v <= stops[i][0]) {
      const [lower, start] = stops[i - 1];
      const [upper, end] = stops[i];
      const amount = (v - lower) / (upper - lower);
      const startRgb = hexRgb(start);
      const endRgb = hexRgb(end);
      return `rgb(${startRgb.map((channel, index) => Math.round(channel + (endRgb[index] - channel) * amount)).join(",")})`;
    }
  }
  return stops[stops.length - 1][1];
}

function hexRgb(color: string): number[] {
  return color.match(/[a-f\d]{2}/gi)!.map((channel) => Number.parseInt(channel, 16));
}

export function cellFill(
  cell: Cell,
  view: "current" | "future" | "change" | "classes",
  threshold: number,
): string {
  if (view === "current") return cellColor(cell.suitability_current);
  if (view === "future") return cellColor(cell.suitability_2050);
  if (view === "change") return changeColor(cell.delta_suitability);
  const now = cell.suitability_current >= threshold;
  const later = cell.suitability_2050 >= threshold;
  if (now && later) return "#377d60";
  if (now) return "#c65b4d";
  if (later) return "#389da0";
  return "#e5e8df";
}

export function factorLabel(
  key: (typeof FEATURE_ORDER)[number],
  translate: (key: string) => string,
): string {
  return translate(FEATURE_LABEL_KEYS[key]);
}
