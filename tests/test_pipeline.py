"""Scientific invariants and reproducibility of the MVP pipeline."""

from io import BytesIO
import json
import unittest
from zipfile import ZipFile

import numpy as np
import pandas as pd

from habitat2050.data import (
    MATCH_TOLERANCE, align_scenarios, audit_occurrences, load_dataset, validate_environment,
)
from habitat2050.exports import build_export
from habitat2050.modeling import cell_area_km2, classify_change, fit_and_predict, summarize
from habitat2050.paths import FEATURE_COLUMNS
from habitat2050.visualization import as_geojson, cell_polygon, map_figure


class PipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dataset = load_dataset()
        cls.results = fit_and_predict(cls.dataset)

    def test_actual_audit_counts(self):
        self.assertEqual(self.dataset.audit["status"].value_counts().to_dict(), {
            "duplicate_grid": 74, "retained": 34,
            "missing_or_invalid_coordinates": 15, "outside_or_unmatched_grid": 5,
        })
        self.assertEqual(len(self.dataset.presence_ids), 34)

    def test_matching_tolerance_and_missing(self):
        row = self.dataset.current.iloc[0]
        records = pd.DataFrame({
            "record_id": ["a", "b", "c", "d", "e"],
            "longitude": [row.lon, row.lon + MATCH_TOLERANCE / 2,
                          row.lon + MATCH_TOLERANCE * 2, np.nan, 104],
            "latitude": [row.lat] * 5, "year": [None] * 5, "source_type": ["test"] * 5,
        })
        audit = audit_occurrences(records, self.dataset.current)
        self.assertEqual(audit["status"].tolist(), [
            "retained", "duplicate_grid", "outside_or_unmatched_grid",
            "missing_or_invalid_coordinates", "outside_or_unmatched_grid",
        ])

    def test_bad_environment_is_rejected(self):
        for column, value in (("forest_cover_pct", 101), ("lon", np.nan),
                              ("bio12_annual_precip_mm", -1)):
            bad = self.dataset.current.copy()
            bad.loc[0, column] = value
            with self.assertRaises(ValueError):
                validate_environment(bad)
        duplicated = pd.concat([self.dataset.current, self.dataset.current.iloc[[0]]])
        with self.assertRaises(ValueError):
            validate_environment(duplicated)

    def test_scenario_alignment_is_by_id(self):
        shuffled = self.dataset.future.sample(frac=1, random_state=9)
        aligned = align_scenarios(self.dataset.current, shuffled)
        pd.testing.assert_frame_equal(aligned, self.dataset.future)
        bad = self.dataset.future.copy()
        bad.loc[0, "forest_cover_pct"] += 1
        with self.assertRaises(ValueError):
            align_scenarios(self.dataset.current, bad)
        with self.assertRaises(ValueError):
            align_scenarios(self.dataset.current, self.dataset.future.iloc[1:])

    def test_sample_and_split_disjointness(self):
        split = self.results.split
        self.assertFalse(split["grid_id"].duplicated().any())
        train = set(split.loc[split["split"].eq("train"), "grid_id"])
        validation = set(split.loc[split["split"].eq("validation"), "grid_id"])
        background = set(split.loc[split["label"].eq(0), "grid_id"])
        self.assertFalse(train & validation)
        self.assertFalse(background & set(self.dataset.presence_ids))
        self.assertEqual((len(train), len(validation), len(background)), (102, 34, 102))
        self.assertEqual(set(self.results.validation["label"]), {0, 1})

    def test_features_and_reference_separation(self):
        self.assertEqual(self.results.metadata["features"], list(FEATURE_COLUMNS))
        self.assertNotIn("truth_auc.csv", self.results.metadata["source_sha256"])
        self.assertEqual(self.results.metadata["seed"], 42)

    def test_scores_and_change_are_finite(self):
        p = self.results.predictions
        self.assertEqual(len(p), 2268)
        for column in ("suitability_current", "suitability_2050"):
            self.assertTrue(p[column].between(0, 1).all())
        np.testing.assert_allclose(p["delta_suitability"],
                                   p["suitability_2050"] - p["suitability_current"])
        self.assertTrue(0 <= self.results.metadata["validation_roc_auc"] <= 1)

    def test_threshold_boundary_and_zero_baseline(self):
        tiny = pd.DataFrame({
            "suitability_current": [0.5, 0.6, 0.2, 0.1],
            "suitability_2050": [0.5, 0.3, 0.7, 0.2],
            "area_km2": [1.0] * 4, "extrapolated_2050": [False] * 4,
        })
        self.assertEqual(classify_change(tiny, 0.5)["change_class"].tolist(),
                         ["stable_suitable", "lost", "gained", "stable_unsuitable"])
        self.assertIsNone(summarize(tiny, 1)["delta_percent"])
        for invalid in (-0.1, 1.1, np.nan):
            with self.assertRaises(ValueError):
                classify_change(tiny, invalid)

    def test_area_accounting_and_latitude(self):
        areas = cell_area_km2([0, 26, 29])
        self.assertGreater(areas[0], areas[1])
        self.assertGreater(areas[1], areas[2])
        self.assertAlmostEqual(areas[0], 85.479661, delta=0.002)
        report = summarize(self.results.predictions, 0.5)
        self.assertAlmostEqual(sum(report["class_areas_km2"].values()),
                               self.results.predictions["area_km2"].sum(), places=6)
        self.assertAlmostEqual(report["delta_area_km2"],
                               report["class_areas_km2"]["gained"] - report["class_areas_km2"]["lost"])

    def test_extrapolation_against_training_range(self):
        train_ids = self.results.split.loc[self.results.split["split"].eq("train"), "grid_id"]
        train = self.dataset.current.set_index("grid_id").loc[train_ids, list(FEATURE_COLUMNS)]
        outside = (self.dataset.future[list(FEATURE_COLUMNS)].lt(train.min()) |
                   self.dataset.future[list(FEATURE_COLUMNS)].gt(train.max())).any(axis=1)
        np.testing.assert_array_equal(outside, self.results.predictions["extrapolated_2050"])

    def test_reproducibility(self):
        repeated = fit_and_predict(self.dataset)
        pd.testing.assert_frame_equal(repeated.predictions, self.results.predictions)
        pd.testing.assert_frame_equal(repeated.split, self.results.split)
        self.assertEqual(repeated.metadata, self.results.metadata)

    def test_geometry_and_offline_map(self):
        polygon = cell_polygon(100, 27)
        self.assertEqual(polygon[0], polygon[-1])
        self.assertLess(polygon[0][0], polygon[1][0])
        self.assertGreater(polygon[2][1], polygon[1][1])
        frame = classify_change(self.results.predictions, 0.5)
        for view in ("current", "future", "change", "classes"):
            fig = map_figure(frame, view, frame.iloc[0]["grid_id"], True, True, "en")
            payload = fig.to_json()
            self.assertNotIn("https://", payload)
            self.assertEqual(len(fig.data[0].x), 55)
            self.assertEqual(len(fig.data[0].y), 43)
            self.assertLess(fig.data[0].y[0], fig.data[0].y[-1])
        features = as_geojson(frame.iloc[:2])["features"]
        self.assertEqual(len(features), 2)
        self.assertEqual(features[0]["geometry"]["type"], "Polygon")

    def test_evidence_bundle(self):
        content = build_export(self.dataset, self.results, 0.65)
        with ZipFile(BytesIO(content)) as archive:
            metadata = json.loads(archive.read("evaluation.json"))
            self.assertEqual(metadata["export_summary"]["threshold"], 0.65)
            self.assertEqual(len(json.loads(archive.read("cells.geojson"))["features"]), 2268)
            predictions = pd.read_csv(BytesIO(archive.read("predictions.csv")))
            self.assertEqual(len(predictions), 2268)
            self.assertEqual(len(pd.read_csv(BytesIO(archive.read("sample_split.csv")))), 136)
            self.assertIn(b"Educational", archive.read("README.txt"))
