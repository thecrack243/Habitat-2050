"""Integrity checks for the supplied copy, not tests of an implemented model."""

import csv
import hashlib
import json
import math
import re
import tomllib
import unittest

from habitat2050.paths import (
    ARTIFACTS_ROOT,
    DATA_FILES,
    DATASET_ROOT,
    FEATURE_COLUMNS,
    PROCESSED_ROOT,
    PROJECT_ROOT,
    SOURCE_ROOT,
)


def read_csv(name):
    with (DATASET_ROOT / name).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


class ScaffoldTests(unittest.TestCase):
    def test_paths_are_internal_and_present(self):
        for path in (SOURCE_ROOT, DATASET_ROOT, PROCESSED_ROOT, ARTIFACTS_ROOT):
            self.assertTrue(path.is_relative_to(PROJECT_ROOT))
            self.assertTrue(path.is_dir())
        self.assertEqual(
            {p.name for p in DATASET_ROOT.iterdir() if p.is_file()},
            set(DATA_FILES),
        )

    def test_original_dataset_hashes(self):
        manifest = json.loads(
            (PROJECT_ROOT / "docs" / "source_manifest.json").read_text(
                encoding="utf-8-sig"
            )
        )
        expected = {
            path.relative_to(PROJECT_ROOT).as_posix()
            for path in SOURCE_ROOT.rglob("*") if path.is_file()
        }
        self.assertEqual(set(manifest), expected)
        self.assertEqual(len(manifest), 5)
        for relative, digest in manifest.items():
            self.assertEqual(
                hashlib.sha256((PROJECT_ROOT / relative).read_bytes()).hexdigest(),
                digest,
                relative,
            )

    def test_environment_schema_and_ranges(self):
        expected = {"grid_id", "lon", "lat", *FEATURE_COLUMNS}
        for name in ("env_factors.csv", "env_scenario_2050.csv"):
            rows = read_csv(name)
            self.assertEqual(len(rows), 2268)
            self.assertEqual(set(rows[0]), expected)
            self.assertEqual(len({r["grid_id"] for r in rows}), 2268)
            for row in rows:
                for column in expected - {"grid_id"}:
                    self.assertTrue(math.isfinite(float(row[column])))
                self.assertTrue(-1 <= float(row["ndvi_growing_season"]) <= 1)
                self.assertTrue(0 <= float(row["forest_cover_pct"]) <= 100)
                self.assertGreaterEqual(float(row["bio12_annual_precip_mm"]), 0)

    def test_scenario_alignment_and_static_layers(self):
        current = {r["grid_id"]: r for r in read_csv("env_factors.csv")}
        future = {r["grid_id"]: r for r in read_csv("env_scenario_2050.csv")}
        self.assertEqual(set(current), set(future))
        for grid_id, row in current.items():
            for column in (
                "lon", "lat", "elevation_m",
                "ndvi_growing_season", "forest_cover_pct",
            ):
                self.assertEqual(float(row[column]), float(future[grid_id][column]))

    def test_grid_geometry_observations(self):
        rows = read_csv("env_factors.csv")
        longitude = sorted({float(r["lon"]) for r in rows})
        latitude = sorted({float(r["lat"]) for r in rows})
        self.assertEqual((len(longitude), len(latitude)), (54, 42))
        self.assertEqual(len({(r["lon"], r["lat"]) for r in rows}), 2268)
        for values in (longitude, latitude):
            for left, right in zip(values, values[1:]):
                self.assertAlmostEqual(right - left, 1 / 12, places=5)
        self.assertTrue(98.5 < longitude[0] < longitude[-1] < 103.0)
        self.assertTrue(26.0 < latitude[0] < latitude[-1] < 29.5)
        # Records the supplied ordering discrepancy, not a rendering algorithm.
        self.assertLess(float(rows[0]["lat"]), float(rows[-1]["lat"]))

    def test_occurrence_audit_observations(self):
        rows = read_csv("occurrence_records.csv")
        self.assertEqual(len(rows), 128)
        self.assertEqual(
            set(rows[0]), {"record_id", "longitude", "latitude", "year", "source_type"}
        )
        self.assertEqual(len({r["record_id"] for r in rows}), 128)
        valid = [r for r in rows if r["longitude"] and r["latitude"]]
        key = lambda x, y: (round(float(x), 6), round(float(y), 6))
        centers = {
            key(r["lon"], r["lat"]) for r in read_csv("env_factors.csv")
        }
        matched = [
            r for r in valid if key(r["longitude"], r["latitude"]) in centers
        ]
        self.assertEqual(len(rows) - len(valid), 15)
        self.assertEqual(len({key(r["longitude"], r["latitude"]) for r in valid}), 39)
        self.assertEqual(len(matched), 108)
        self.assertEqual(len({key(r["longitude"], r["latitude"]) for r in matched}), 34)
        self.assertEqual(sum(not r["year"] for r in rows), 15)

    def test_project_metadata(self):
        with (PROJECT_ROOT / "pyproject.toml").open("rb") as handle:
            config = tomllib.load(handle)
        self.assertEqual(config["project"]["name"], "habitat-2050")
        self.assertEqual(config["project"]["requires-python"], ">=3.11")
        names = {
            re.split(r"[<>=!~\[]", item)[0]
            for item in config["project"]["dependencies"]
        }
        self.assertEqual(
            names, {"streamlit", "pandas", "numpy", "scikit-learn", "plotly"}
        )
        self.assertEqual(config["tool"]["setuptools"]["packages"]["find"]["where"], ["src"])

    def test_skill_frontmatter_and_references(self):
        folder = PROJECT_ROOT / ".trae" / "skills" / "habitat-2050-workflow"
        text = (folder / "SKILL.md").read_text(encoding="utf-8")
        sections = text.split("---", 2)
        self.assertEqual(sections[0], "")
        self.assertEqual(len(sections), 3)
        fields = {}
        # The authored format intentionally uses only two simple YAML scalars.
        for line in sections[1].strip().splitlines():
            name, value = line.split(": ", 1)
            fields[name] = value
        self.assertEqual(set(fields), {"name", "description"})
        self.assertEqual(fields["name"], folder.name)
        self.assertRegex(fields["name"], r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
        self.assertTrue(2 <= len(fields["name"]) <= 64)
        description = fields["description"]
        self.assertFalse(description.startswith(("'", '"')))
        for forbidden in (": ", "<", ">", "TODO"):
            self.assertNotIn(forbidden, description)
        self.assertIn("Use for", description)
        self.assertTrue(sections[2].strip())
        self.assertLess(len(text.splitlines()), 500)
        for relative in (
            "AGENTS.md", "docs/project_status.md", "docs/architecture.md",
            "docs/dataset_and_evaluation.md", "src/habitat2050/paths.py",
            "scripts/verify_scaffold.py",
        ):
            self.assertTrue((PROJECT_ROOT / relative).is_file(), relative)

    def test_always_on_rule_and_streamlit_decision(self):
        rule = (PROJECT_ROOT / ".trae/rules/project_rules.md").read_text(
            encoding="utf-8"
        )
        self.assertTrue(rule.startswith("---\nalwaysApply: true\n---\n"))
        for relative in (
            "README.md", "AGENTS.md", ".trae/rules/project_rules.md",
            ".trae/skills/habitat-2050-workflow/SKILL.md",
            "docs/project_status.md",
        ):
            self.assertIn(
                "Streamlit", (PROJECT_ROOT / relative).read_text(encoding="utf-8")
            )

    def test_reference_auc_is_not_a_feature(self):
        self.assertEqual(len(FEATURE_COLUMNS), 5)
        self.assertNotIn("grid_id", FEATURE_COLUMNS)
        self.assertNotIn("longitude", FEATURE_COLUMNS)
        self.assertFalse(any("auc" in column for column in FEATURE_COLUMNS))
        reference = {
            r["item"]: r["value"] for r in read_csv("truth_auc.csv")
            if r["item"].startswith("auc_interval_")
        }
        self.assertEqual(float(reference["auc_interval_lower"]), 0.45)
        self.assertEqual(float(reference["auc_interval_upper"]), 0.90)
