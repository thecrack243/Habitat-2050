"""Resolve bundled resources independently of the terminal working directory."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = PROJECT_ROOT / "题四_栖息地2050_气候变化下的物种适生区预测"
DATASET_ROOT = SOURCE_ROOT / "【发放给参赛队伍】物种适生区数据包"
PROCESSED_ROOT = PROJECT_ROOT / "data" / "processed"
ARTIFACTS_ROOT = PROJECT_ROOT / "artifacts"

DATA_FILES = (
    "occurrence_records.csv",
    "env_factors.csv",
    "env_scenario_2050.csv",
    "truth_auc.csv",
    "数据来源与合规说明.txt",
)

FEATURE_COLUMNS = (
    "elevation_m",
    "bio1_annual_mean_temp_degC",
    "bio12_annual_precip_mm",
    "ndvi_growing_season",
    "forest_cover_pct",
)
