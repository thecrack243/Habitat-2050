"""Build JSON dashboard data from the existing Python model pipeline."""

from functools import lru_cache
import math
from threading import Lock

import pandas as pd

from habitat2050.data import Dataset, load_dataset, source_fingerprint
from habitat2050.modeling import Results, classify_change, fit_and_predict, summarize
from habitat2050.paths import FEATURE_COLUMNS


_MODEL_LOCK = Lock()


@lru_cache(maxsize=1)
def _model_results(fingerprint: tuple[tuple[str, str], ...]) -> tuple[Dataset, Results]:
    dataset = load_dataset()
    if tuple(sorted(dataset.source_hashes.items())) != fingerprint:
        raise ValueError("Dataset changed while the model results were being loaded.")
    return dataset, fit_and_predict(dataset)


def model_results() -> tuple[Dataset, Results]:
    with _MODEL_LOCK:
        return _model_results(tuple(sorted(source_fingerprint())))


def build_dashboard_payload(threshold: float = 0.5) -> dict:
    if isinstance(threshold, bool) or not isinstance(threshold, (int, float)):
        raise ValueError("Threshold must be a number between 0 and 1.")
    if not math.isfinite(threshold) or not 0 <= threshold <= 1:
        raise ValueError("Threshold must be a finite number between 0 and 1.")

    dataset, results = model_results()
    current = dataset.current.set_index("grid_id")
    future = dataset.future.set_index("grid_id")
    classified = classify_change(results.predictions, float(threshold))
    cells = []
    for row in classified.to_dict("records"):
        grid_id = row["grid_id"]
        cells.append({
            "grid_id": grid_id,
            "lon": float(row["lon"]),
            "lat": float(row["lat"]),
            "suitability_current": float(row["suitability_current"]),
            "suitability_2050": float(row["suitability_2050"]),
            "delta_suitability": float(row["delta_suitability"]),
            "extrapolated_current": bool(row["extrapolated_current"]),
            "extrapolated_2050": bool(row["extrapolated_2050"]),
            "recorded_presence": bool(row["recorded_presence"]),
            "area_km2": float(row["area_km2"]),
            "change_class": row["change_class"],
            "current_factors": {
                name: float(current.at[grid_id, name]) for name in FEATURE_COLUMNS
            },
            "future_factors": {
                name: float(future.at[grid_id, name]) for name in FEATURE_COLUMNS
            },
        })

    metadata = results.metadata
    return {
        "threshold": float(threshold),
        "summary": summarize(results.predictions, float(threshold)),
        "cells": cells,
        "evaluation": {
            "validation_roc_auc": float(metadata["validation_roc_auc"]),
            "validation_average_precision": float(metadata["validation_average_precision"]),
            "train_cells": int(metadata["train_cells"]),
            "validation_cells": int(metadata["validation_cells"]),
            "validation_presence_cells": int(metadata["validation_presence_cells"]),
            "validation_background_cells": int(metadata["validation_background_cells"]),
            "presence_cells": int(metadata["presence_cells"]),
            "background_cells": int(metadata["background_cells"]),
            "seed": int(metadata["seed"]),
            "model": str(metadata["model"]),
            "parameters": metadata["parameters"],
            "split_method": str(metadata["split_method"]),
            "limitations": list(metadata["limitations"]),
        },
        "audit_counts": metadata["audit_counts"],
        "feature_importance": [
            {
                "feature": str(row["feature"]),
                "auc_drop": float(row["auc_drop"]),
                "std": float(row["std"]),
            }
            for row in results.importance.to_dict("records")
        ],
        "scenario": metadata["scenario"],
        "source_sha256": metadata["source_sha256"],
    }


def build_evidence_export(threshold: float) -> bytes:
    if isinstance(threshold, bool) or not isinstance(threshold, (int, float)):
        raise ValueError("Threshold must be a number between 0 and 1.")
    if not math.isfinite(threshold) or not 0 <= threshold <= 1:
        raise ValueError("Threshold must be a finite number between 0 and 1.")
    dataset, results = model_results()
    from habitat2050.exports import build_export

    return build_export(dataset, results, float(threshold))
