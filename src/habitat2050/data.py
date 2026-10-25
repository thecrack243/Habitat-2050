"""Read-only source validation and auditable occurrence-to-grid matching."""

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

import numpy as np
import pandas as pd

from habitat2050.paths import DATASET_ROOT, FEATURE_COLUMNS


CELL_SIZE = 1 / 12
MATCH_TOLERANCE = 0.000002  # Degrees; permits source rounding, not arbitrary snapping.
INPUT_FILES = ("env_factors.csv", "env_scenario_2050.csv", "occurrence_records.csv")


@dataclass
class Dataset:
    current: pd.DataFrame
    future: pd.DataFrame
    audit: pd.DataFrame
    presence_ids: list[str]
    source_hashes: dict[str, str]


def source_fingerprint(root: Path = DATASET_ROOT) -> tuple[tuple[str, str], ...]:
    return tuple((name, sha256((root / name).read_bytes()).hexdigest()) for name in INPUT_FILES)


def validate_environment(frame: pd.DataFrame) -> pd.DataFrame:
    required = ["grid_id", "lon", "lat", *FEATURE_COLUMNS]
    if not set(required).issubset(frame.columns):
        raise ValueError("Missing environmental columns.")
    data = frame[required].copy()
    if data.empty or data["grid_id"].isna().any() or data["grid_id"].duplicated().any():
        raise ValueError("Environmental grid IDs must be present and unique.")
    numeric = ["lon", "lat", *FEATURE_COLUMNS]
    data[numeric] = data[numeric].apply(pd.to_numeric, errors="raise")
    if not np.isfinite(data[numeric].to_numpy()).all():
        raise ValueError("Environmental values must be finite.")
    if data.duplicated(["lon", "lat"]).any():
        raise ValueError("Grid centers must be unique.")
    if not (data["lon"].between(98.5, 103.0) & data["lat"].between(26.0, 29.5)).all():
        raise ValueError("Environmental cells fall outside the study extent.")
    for column, lower, upper in (
        ("ndvi_growing_season", -1, 1), ("forest_cover_pct", 0, 100),
    ):
        if not data[column].between(lower, upper).all():
            raise ValueError(f"Invalid range for {column}.")
    if (data["bio12_annual_precip_mm"] < 0).any():
        raise ValueError("Rainfall must be non-negative.")
    return data.sort_values("grid_id").reset_index(drop=True)


def align_scenarios(current: pd.DataFrame, future: pd.DataFrame) -> pd.DataFrame:
    if set(current["grid_id"]) != set(future["grid_id"]):
        raise ValueError("Current and future grid IDs differ.")
    aligned = future.set_index("grid_id").loc[current["grid_id"]].reset_index()
    static = ["lon", "lat", "elevation_m", "ndvi_growing_season", "forest_cover_pct"]
    if not np.allclose(current[static], aligned[static], rtol=0, atol=1e-9):
        raise ValueError("Coordinates or static layers changed between scenarios.")
    return aligned


def audit_occurrences(records: pd.DataFrame, grid: pd.DataFrame) -> pd.DataFrame:
    required = {"record_id", "longitude", "latitude", "year", "source_type"}
    if not required.issubset(records.columns):
        raise ValueError("Missing occurrence columns.")
    if records["record_id"].isna().any() or records["record_id"].duplicated().any():
        raise ValueError("Occurrence record IDs must be present and unique.")
    audit = records.copy()
    audit["longitude"] = pd.to_numeric(audit["longitude"], errors="coerce")
    audit["latitude"] = pd.to_numeric(audit["latitude"], errors="coerce")
    audit["grid_id"] = ""
    audit["status"] = ""
    centers = grid[["lon", "lat"]].to_numpy()
    seen = set()
    # Stable record order makes duplicate retention deterministic.
    for idx, row in audit.sort_values("record_id").iterrows():
        xy = np.array([row["longitude"], row["latitude"]], dtype=float)
        if not np.isfinite(xy).all():
            audit.at[idx, "status"] = "missing_or_invalid_coordinates"
            continue
        distances = np.max(np.abs(centers - xy), axis=1)
        candidates = np.flatnonzero(distances <= MATCH_TOLERANCE)
        if len(candidates) != 1:
            audit.at[idx, "status"] = "outside_or_unmatched_grid"
            continue
        grid_id = str(grid.iloc[candidates[0]]["grid_id"])
        audit.at[idx, "grid_id"] = grid_id
        audit.at[idx, "status"] = "duplicate_grid" if grid_id in seen else "retained"
        seen.add(grid_id)
    return audit


def load_dataset(root: Path = DATASET_ROOT) -> Dataset:
    read = lambda name: pd.read_csv(root / name, encoding="utf-8-sig")
    current = validate_environment(read("env_factors.csv"))
    future = align_scenarios(current, validate_environment(read("env_scenario_2050.csv")))
    audit = audit_occurrences(read("occurrence_records.csv"), current)
    presence_ids = sorted(audit.loc[audit["status"].eq("retained"), "grid_id"].tolist())
    if len(presence_ids) < 8:
        raise ValueError("At least eight unique matched presence cells are required.")
    return Dataset(current, future, audit, presence_ids, dict(source_fingerprint(root)))
