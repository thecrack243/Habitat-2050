"""Create a self-describing results bundle without changing source data."""

from io import BytesIO
import json
from zipfile import ZipFile, ZIP_DEFLATED

from habitat2050.data import Dataset
from habitat2050.modeling import Results, classify_change, summarize
from habitat2050.paths import DATASET_ROOT
from habitat2050.visualization import as_geojson


def build_export(dataset: Dataset, results: Results, threshold: float) -> bytes:
    classified = classify_change(results.predictions, threshold)
    metadata = {
        **results.metadata,
        "export_summary": summarize(results.predictions, threshold),
        "class_rule": "Suitable when score >= selected threshold.",
    }
    buffer = BytesIO()
    with ZipFile(buffer, "w", compression=ZIP_DEFLATED) as archive:
        tables = {
            "predictions.csv": classified,
            "occurrence_audit.csv": dataset.audit,
            "sample_split.csv": results.split,
            "validation_predictions.csv": results.validation,
            "permutation_importance.csv": results.importance,
        }
        for name, table in tables.items():
            archive.writestr(name, table.to_csv(index=False).encode("utf-8-sig"))
        archive.writestr("evaluation.json", json.dumps(metadata, indent=2, ensure_ascii=False, allow_nan=False))
        archive.writestr("cells.geojson", json.dumps(as_geojson(classified), ensure_ascii=False, allow_nan=False))
        archive.writestr("source_notes.txt", (DATASET_ROOT / "数据来源与合规说明.txt").read_bytes())
        archive.writestr("README.txt", (
            "Habitat 2050 | Educational competition demonstration\n"
            "One fixed training-only random forest; preliminary random holdout validation.\n"
            "Relative suitability is not occupancy probability. Background is not verified absence.\n"
            "Current climate: 1970-2000. Future: SSP2-4.5, MPI-ESM1-2-HR, 2041-2060.\n"
            "Vegetation is held static. No dispersal or population projection.\n"
            "See evaluation.json for parameters, versions, hashes, threshold, and limitations.\n"
            "GeoJSON coordinates are longitude/latitude (WGS84); areas use WGS84 ellipsoid integration.\n"
            "Not for conservation planning, land use, or policy decisions.\n"
        ))
    return buffer.getvalue()
