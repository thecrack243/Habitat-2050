"""Rebuild the measured results and write the default-threshold evidence bundle."""

from pathlib import Path
import json
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from habitat2050.data import load_dataset
from habitat2050.exports import build_export
from habitat2050.modeling import DEFAULT_THRESHOLD, fit_and_predict, summarize
from habitat2050.paths import ARTIFACTS_ROOT


def main():
    data = load_dataset()
    results = fit_and_predict(data)
    summary = summarize(results.predictions, DEFAULT_THRESHOLD)
    ARTIFACTS_ROOT.mkdir(exist_ok=True)
    (ARTIFACTS_ROOT / "habitat-2050-evidence.zip").write_bytes(
        build_export(data, results, DEFAULT_THRESHOLD)
    )
    report = {**results.metadata, "default_summary": summary}
    (ARTIFACTS_ROOT / "evaluation.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8"
    )
    print(json.dumps({
        "roc_auc": results.metadata["validation_roc_auc"],
        "summary": summary, "output": "artifacts/habitat-2050-evidence.zip",
    }, indent=2))


if __name__ == "__main__":
    main()
