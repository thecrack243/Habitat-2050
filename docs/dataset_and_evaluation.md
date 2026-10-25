# Dataset and evaluation boundaries

## Bundled inputs

Authoritative source directory:
`题四_栖息地2050_气候变化下的物种适生区预测/【发放给参赛队伍】物种适生区数据包/`.

Treat these files as read-only. No raw cleaning edits are permitted.

| File | Role |
| --- | --- |
| occurrence_records.csv | 128 coarse species occurrence records |
| env_factors.csv | 2,268 current environmental grid cells |
| env_scenario_2050.csv | 2,268 future environmental grid cells |
| truth_auc.csv | Reference AUC interval and importance rankings only |
| 数据来源与合规说明.txt | Supplied provenance, field meanings, usage limits |

The study grid spans 98.5-103.0 E and 26.0-29.5 N, with 54 columns and 42
rows at 1/12 degree resolution. Coordinates are cell centers. Build cell bounds
using half the angular resolution, not a presumed kilometer size.

The five predictors are elevation_m, bio1_annual_mean_temp_degC,
bio12_annual_precip_mm, ndvi_growing_season, and forest_cover_pct.

Current climate is the 1970-2000 average. Future climate is MPI-ESM1-2-HR,
SSP2-4.5, averaged over 2041-2060. Elevation, NDVI, and forest cover are held
unchanged. The source notes identify NDVI as 2024 and forest cover as 2021,
so these layers do not represent one simultaneous observation date.

## Setup inspection

Measured from this bundled copy on 2026-10-25, without fitting a model:

- 128 occurrence rows; 15 have missing coordinates.
- 113 rows have both coordinates, representing 39 distinct coordinate pairs.
- 108 rows match an environmental center when rounded to six decimal places.
- Those matched rows represent only **34 unique grid cells**.
- Five rows lie outside the environmental grid: REC0054, REC0072, REC0074,
  REC0077, and REC0093.
- 15 rows have a missing year. Missing year alone need not exclude a usable
  location, but the policy must be documented.

The future cleaner must use an explicit numeric tolerance and exclusion
audit, rather than relying on string formatting or silently changing records.

## Documentation discrepancies

1. Source notes describe north-to-south grid numbering. The actual first row
   has latitude 26.041667 and the final row 29.458333: row latitude increases
   south-to-north. Use coordinates to prevent a flipped map.
2. Notes describe a 2025 GBIF query, but eight occurrence rows have year 2026.
   Preserve and flag this inconsistency; do not invent its explanation.
3. The supplied GBIF DOI is a wildcard (`https://doi.org/10.15468/dl.*`), not
   a resolvable record-specific download citation. A verified DOI remains
   missing. Do not turn it into a fabricated source.
4. NDVI is named/described as a seasonal mean in the field description, while
   the processing notes describe maximum-value compositing. Preserve this
   ambiguity; refer to it as the supplied growing-season NDVI layer.

The package's provenance claims have not been independently verified.

## Evaluation protocol

1. Filter missing/out-of-grid positions with an audit trail.
2. Match centers, then deduplicate by grid_id before splitting.
3. Sample background from cells without a retained occurrence. Background
   labels are a modeling device, not confirmed species absences.
4. Freeze seed 42 initially, record sampled cells and disjoint split IDs, and
   fit one random forest using the five predictors only.
5. Fit any learned preprocessing on training data only.
6. Measure held-out ROC-AUC with both classes represented; show split sizes,
   design, and warnings. With only 34 positive cells, precision is limited.
7. Mark random held-out validation as preliminary. Add spatially separated
   validation and background-sampling sensitivity when feasible.
8. Apply the same model and feature order to both aligned scenarios. Flag
   future environmental values outside the training range.
9. Report a common classification threshold and how it was chosen. Do not
   optimize it on held-out evaluation data. A fixed 0.5 cutoff, if used, is an
   illustrative classifier threshold, not a biologically validated boundary.

The reference AUC range is 0.45-0.90. It is not measured performance of this
project and must not be used as a tuning target, test labels, or pass criterion.
Out-of-range scores warrant investigation, not data manipulation.

Global feature importance does not establish causation or explain a specific
cell by itself. Relative suitability is not occupancy probability. Do not infer
verified refugia, migration corridors, or protection priorities from this MVP.

## Attribution and conservation

Preserve the complete bundled source notes. They name GBIF/public records,
the cited 2003 literature, WorldClim 2.1, CMIP6, NOAA CDR NDVI, and ESA
WorldCover. Consult original providers for precise license and citation
requirements before wider publication.

Never recover or expose locations finer than the supplied grid. Retain an
educational-use disclaimer: outputs are not a basis for conservation planning,
land use, or policy. Do not claim future vegetation, population size, dispersal,
or species survival has been modeled.

## Checks still needed after implementation

Test cleaner exclusions, tolerance boundaries, no duplicate positives or split
overlap, no occurrence/background overlap, reproducibility, feature order,
scenario joins, finite scores, change classes, map orientation, area math,
offline visualization, app startup, and interactive controls.

Scaffold checks are not model validation.

## Implemented baseline

The first MVP implements the exclusion audit, numeric matching with 0.000002
degree tolerance, grid deduplication, fixed 3:1 background sampling, and a
25% stratified random holdout. The forest has 300 trees, maximum depth 6,
minimum leaf size 3, balanced class weights, and seed 42.

Training contains 102 cells; validation contains 34 cells (8 presence and
26 background). The same training-only model generates both scenario maps.
Locked-runtime ROC-AUC is 0.8173076923. Current suitable area is 26,720.58 km2;
future suitable area is 24,819.75 km2 at threshold 0.50.

Areas integrate WGS84 ellipsoid surface strips between grid-cell latitude
parallels and longitude meridians. They are neither square degrees nor fixed
81 km2 cells. Future extrapolation flags identify 221 cells outside at least
one training predictor's min/max range.

The score and area outputs differ with scikit-learn version even under the
same seed. Use requirements.lock.txt and record versions with every export.
Preinstalled-library trial results (ROC-AUC 0.837 and approximately -4% area)
were superseded by the locked-runtime baseline (0.817 and -7.1%), not selected
by optimizing performance. Do not mix results from these environments.

Spatial validation, independent testing, calibration, and sampling sensitivity
remain unimplemented and explicitly disclosed in the UI.
