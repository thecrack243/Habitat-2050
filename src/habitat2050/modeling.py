"""Reproducible presence/background classification and scenario projection."""

from dataclasses import dataclass
from importlib.metadata import version

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance
from sklearn.metrics import average_precision_score, confusion_matrix, roc_auc_score
from sklearn.model_selection import train_test_split

from habitat2050.data import CELL_SIZE, Dataset
from habitat2050.paths import FEATURE_COLUMNS


SEED = 42
MODEL_VERSION = "1.0.0"
BACKGROUND_RATIO = 3
DEFAULT_THRESHOLD = 0.5
CLASS_ORDER = ("stable_suitable", "lost", "gained", "stable_unsuitable")


@dataclass
class Results:
    predictions: pd.DataFrame
    importance: pd.DataFrame
    metadata: dict
    split: pd.DataFrame
    validation: pd.DataFrame


def cell_area_km2(latitude, size: float = CELL_SIZE) -> np.ndarray:
    """WGS84 ellipsoid area between cell meridians and latitude parallels."""
    a = 6378.137
    e2 = 6.69437999014e-3
    e = np.sqrt(e2)
    latitude = np.asarray(latitude, dtype=float)

    def primitive(phi):
        u = np.sin(np.deg2rad(phi))
        return (u / (1 - e2 * u**2) + np.arctanh(e * u) / e) / 2

    return a**2 * (1 - e2) * np.deg2rad(size) * (
        primitive(latitude + size / 2) - primitive(latitude - size / 2)
    )


def classify_change(predictions: pd.DataFrame, threshold: float) -> pd.DataFrame:
    if not np.isfinite(threshold) or not 0 <= threshold <= 1:
        raise ValueError("Threshold must be between 0 and 1.")
    result = predictions.copy()
    now = result["suitability_current"].ge(threshold)
    future = result["suitability_2050"].ge(threshold)
    result["change_class"] = np.select(
        [now & future, now & ~future, ~now & future],
        CLASS_ORDER[:3], default="stable_unsuitable",
    )
    return result


def summarize(predictions: pd.DataFrame, threshold: float) -> dict:
    classified = classify_change(predictions, threshold)
    areas = {
        name: float(classified.loc[classified["change_class"].eq(name), "area_km2"].sum())
        for name in CLASS_ORDER
    }
    current = areas["stable_suitable"] + areas["lost"]
    future = areas["stable_suitable"] + areas["gained"]
    return {
        "threshold": float(threshold),
        "current_area_km2": current,
        "future_area_km2": future,
        "delta_area_km2": future - current,
        "delta_percent": (future / current - 1) * 100 if current > 0 else None,
        "class_areas_km2": areas,
        "future_extrapolated_cells": int(predictions["extrapolated_2050"].sum()),
    }


def fit_and_predict(dataset: Dataset) -> Results:
    grid = dataset.current.set_index("grid_id")
    positives = dataset.presence_ids
    available = sorted(set(grid.index) - set(positives))
    count = min(len(available), len(positives) * BACKGROUND_RATIO)
    if count < 8:
        raise ValueError("Insufficient non-presence cells for background sampling.")
    background = sorted(np.random.default_rng(SEED).choice(available, count, replace=False))
    sample_ids = np.array(positives + background)
    labels = np.array([1] * len(positives) + [0] * count)
    train_idx, valid_idx = train_test_split(
        np.arange(len(labels)), test_size=0.25, random_state=SEED, stratify=labels
    )
    features = list(FEATURE_COLUMNS)
    x = grid.loc[sample_ids, features]
    model = RandomForestClassifier(
        n_estimators=300, max_depth=6, min_samples_leaf=3,
        class_weight="balanced", random_state=SEED, n_jobs=1,
    )
    model.fit(x.iloc[train_idx], labels[train_idx])
    valid_score = model.predict_proba(x.iloc[valid_idx])[:, 1]
    y_valid = labels[valid_idx]
    auc = float(roc_auc_score(y_valid, valid_score))
    importance = permutation_importance(
        model, x.iloc[valid_idx], y_valid, scoring="roc_auc",
        n_repeats=10, random_state=SEED, n_jobs=1,
    )
    importance_frame = pd.DataFrame({
        "feature": features, "auc_drop": importance.importances_mean,
        "std": importance.importances_std,
    }).sort_values("auc_drop", ascending=False).reset_index(drop=True)
    predictions = dataset.current[["grid_id", "lon", "lat"]].copy()
    predictions["suitability_current"] = model.predict_proba(dataset.current[features])[:, 1]
    predictions["suitability_2050"] = model.predict_proba(dataset.future[features])[:, 1]
    predictions["delta_suitability"] = (
        predictions["suitability_2050"] - predictions["suitability_current"]
    )
    lower, upper = x.iloc[train_idx].min(), x.iloc[train_idx].max()
    for suffix, frame in (("current", dataset.current), ("2050", dataset.future)):
        outside = frame[features].lt(lower) | frame[features].gt(upper)
        predictions[f"extrapolated_{suffix}"] = outside.any(axis=1)
    predictions["area_km2"] = cell_area_km2(predictions["lat"])
    predictions["recorded_presence"] = predictions["grid_id"].isin(positives)
    split = pd.DataFrame({"grid_id": sample_ids, "label": labels, "split": "train"})
    split.loc[valid_idx, "split"] = "validation"
    validation = pd.DataFrame({
        "grid_id": sample_ids[valid_idx], "label": y_valid, "score": valid_score,
    })
    metadata = {
        "model_version": MODEL_VERSION,
        "model": "RandomForestClassifier",
        "parameters": model.get_params(),
        "seed": SEED,
        "features": features,
        "source_sha256": dataset.source_hashes,
        "background_policy": "Uniform unique non-presence grid cells; not verified absences.",
        "background_ratio": BACKGROUND_RATIO,
        "presence_cells": len(positives),
        "background_cells": count,
        "train_cells": len(train_idx),
        "validation_cells": len(valid_idx),
        "validation_presence_cells": int(y_valid.sum()),
        "validation_background_cells": int((y_valid == 0).sum()),
        "split_method": "Stratified random holdout, 25%; no spatial blocking.",
        "validation_roc_auc": auc,
        "validation_average_precision": float(average_precision_score(y_valid, valid_score)),
        "validation_confusion_at_0_5": confusion_matrix(
            y_valid, valid_score >= DEFAULT_THRESHOLD, labels=[0, 1]
        ).tolist(),
        "threshold_policy": "Illustrative default 0.5; user sensitivity control; never tuned on validation.",
        "projection_model": "Same training-only model as evaluated; no refit on validation.",
        "scenario": {
            "pathway": "SSP2-4.5", "gcm": "MPI-ESM1-2-HR",
            "future_period": "2041-2060", "current_climate_period": "1970-2000",
            "static_layers": ["elevation_m", "ndvi_growing_season", "forest_cover_pct"],
        },
        "importance_method": "Held-out permutation ROC-AUC decrease; 10 repeats; not causal.",
        "extrapolation_method": "Any predictor outside training-set min/max; not a confidence interval.",
        "area_method": "WGS84 ellipsoid integration along meridians and parallels.",
        "audit_counts": {str(k): int(v) for k, v in dataset.audit["status"].value_counts().items()},
        "limitations": [
            "Preliminary non-spatial validation; spatial autocorrelation may inflate metrics.",
            "Only 34 unique matched presence cells in the supplied package.",
            "Background labels are not verified absences; scores are relative suitability.",
            "One climate scenario; vegetation is static and dispersal is not modeled.",
            "No independent test set, calibration, or background-sampling sensitivity study.",
            "Not for conservation, land-use, or policy decisions.",
        ],
        "versions": {name: version(name) for name in (
            "streamlit", "pandas", "numpy", "scikit-learn", "plotly"
        )},
    }
    return Results(predictions, importance_frame, metadata, split, validation)
