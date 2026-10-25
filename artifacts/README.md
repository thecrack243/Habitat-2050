# Model artifacts

`habitat-2050-evidence.zip` contains the measured default-threshold results:
predictions, cell GeoJSON, occurrence audit, train/validation split,
validation scores, permutation importance, evaluation metadata, and source notes.

`evaluation.json` provides a readable copy of the metadata and area summary.
These files were generated with the locked Python 3.11 runtime and threshold
0.50. The app can export the same evidence at a different selected threshold.

Regenerate using `python -B scripts/export_results.py` after installing
`requirements.lock.txt`. No serialized model is loaded; the fixed-seed forest
is rebuilt from source. Do not substitute unmeasured scores or dummy outputs.
