export type Language = "zh" | "en";
export type MapView = "current" | "future" | "change" | "classes";

export type Factors = Record<string, number>;

export interface Cell {
  grid_id: string;
  lon: number;
  lat: number;
  suitability_current: number;
  suitability_2050: number;
  delta_suitability: number;
  extrapolated_current: boolean;
  extrapolated_2050: boolean;
  recorded_presence: boolean;
  area_km2: number;
  change_class: string;
  current_factors: Factors;
  future_factors: Factors;
}

export interface FeatureImportance {
  feature: string;
  auc_drop: number;
  std: number;
}

export interface Dashboard {
  threshold: number;
  cells: Cell[];
  evaluation: {
    validation_roc_auc: number;
    validation_average_precision: number;
    train_cells: number;
    validation_cells: number;
    validation_presence_cells: number;
    validation_background_cells: number;
    presence_cells: number;
    background_cells: number;
    seed: number;
    model: string;
    parameters: Record<string, number | string | boolean | null>;
    split_method: string;
    limitations: string[];
  };
  audit_counts: Record<string, number>;
  feature_importance: FeatureImportance[];
  scenario: {
    pathway: string;
    gcm: string;
    future_period: string;
    current_climate_period: string;
    static_layers: string[];
  };
}

export interface Summary {
  current: number;
  future: number;
  delta: number;
  changePercent: number | null;
  persistent: number;
  gained: number;
  lost: number;
  extrapolated: number;
}
