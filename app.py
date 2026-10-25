"""Bilingual Habitat 2050 Streamlit application."""

from pathlib import Path
import json
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd
import streamlit as st

from habitat2050.data import load_dataset, source_fingerprint
from habitat2050.exports import build_export
from habitat2050.modeling import MODEL_VERSION, classify_change, fit_and_predict, summarize
from habitat2050.paths import DATASET_ROOT, FEATURE_COLUMNS
from habitat2050.visualization import (
    CLASS_COLORS, CLASS_LABELS, CLASS_ORDER, FEATURE_LABELS, importance_figure, map_figure,
)


st.set_page_config(page_title="Habitat 2050 | 栖息地2050", layout="wide")
st.markdown(f"<style>{(ROOT / 'src/habitat2050/theme.css').read_text(encoding='utf-8')}</style>",
            unsafe_allow_html=True)

with st.sidebar:
    st.markdown('<div class="side-brand">HABITAT / 2050</div>'
                '<div class="side-small">云南 · YUNNAN<br>Climate & biodiversity explorer</div>',
                unsafe_allow_html=True)
    language = st.radio("语言 / Language", ["中文", "English"], horizontal=True, key="ui_language")

zh = language == "中文"
lang = "zh" if zh else "en"


def tr(chinese: str, english: str) -> str:
    return chinese if zh else english


@st.cache_data(show_spinner=False)
def compute(fingerprint: tuple, pipeline_version: str):
    data = load_dataset()
    return data, fit_and_predict(data)


@st.cache_data(show_spinner=False)
def export_bytes(fingerprint: tuple, pipeline_version: str, threshold: float):
    data, result = compute(fingerprint, pipeline_version)
    return build_export(data, result, threshold)


def select_map_cell():
    event = st.session_state.get("habitat_map", {})
    points = event.get("selection", {}).get("points", [])
    if points:
        custom = points[-1].get("customdata")
        if isinstance(custom, (list, tuple)) and custom and custom[0] in st.session_state.get("grid_options", []):
            st.session_state["grid_id"] = custom[0]


with st.sidebar:
    st.divider()
    st.markdown("### " + tr("探索设置", "Explorer settings"))
    threshold = st.slider(
        tr("适宜度阈值", "Suitability threshold"), 0.1, 0.9, 0.5, 0.05, key="threshold",
        help=tr("仅作敏感性探索；0.5 不是经生态验证的边界。阈值不改变模型。",
                "Sensitivity exploration only. 0.5 is not an ecological boundary; this does not retrain the model."),
    )
    show_records = st.toggle(tr("显示出现记录", "Show recorded cells"), value=True, key="records")
    show_outside = st.toggle(tr("标出训练范围外网格", "Flag extrapolation"), value=False, key="extrapolation")
    st.markdown('<div class="step">' + tr(
        "01 · 对比两个时期<br>02 · 探索变化区域<br>03 · 查看证据与局限",
        "01 · Compare the two periods<br>02 · Explore changing conditions<br>03 · Inspect evidence & limits",
    ) + "</div>", unsafe_allow_html=True)
    st.divider()
    st.caption(tr("单一情景 · SSP2-4.5\n\nMPI-ESM1-2-HR\n\n未来气候：2041–2060\n\n植被保持不变",
                  "One scenario · SSP2-4.5\n\nMPI-ESM1-2-HR\n\nFuture climate: 2041–2060\n\nVegetation held fixed"))

st.markdown('<div class="eyebrow">HABITAT ATLAS / 气候与生境</div>', unsafe_allow_html=True)
st.title(tr("栖息地 2050", "Habitat 2050"))
st.markdown('<div class="intro">' + tr(
    "滇金丝猴，未来何处适宜？探索滇西北及邻区的环境变化，理解模型的预测，也看见它的局限。",
    "Where could suitable conditions persist for the Yunnan snub-nosed monkey? Explore northwest Yunnan, "
    "compare environmental change, and see the evidence behind the model.",
) + "</div>", unsafe_allow_html=True)
st.markdown(
    '<span class="tag">Rhinopithecus bieti</span>'
    '<span class="tag">SSP2-4.5 · 2050</span>'
    '<span class="tag">' + tr("本地运行 · 无需在线底图", "Local-first · No online basemap") + "</span>",
    unsafe_allow_html=True,
)

try:
    fingerprint = source_fingerprint()
    with st.spinner(tr("正在校验数据并生成可复现的模型结果…", "Validating data and preparing reproducible model results…")):
        dataset, results = compute(fingerprint, MODEL_VERSION)
except (ValueError, OSError, ImportError) as exc:
    st.error(tr("无法加载数据或模型，请检查完整数据包和依赖。", "Unable to load data or model. Check the full dataset and dependencies."))
    st.code(str(exc))
    st.stop()

predictions = classify_change(results.predictions, threshold)
summary = summarize(results.predictions, threshold)
st.session_state["grid_options"] = predictions["grid_id"].tolist()
if st.session_state.get("grid_id") not in st.session_state["grid_options"]:
    st.session_state["grid_id"] = dataset.presence_ids[0]

metric_columns = st.columns(4)
metric_columns[0].metric(tr("当前适宜面积", "Current suitable area"), f"{summary['current_area_km2']:,.0f} km²")
metric_columns[1].metric(tr("2050 适宜面积", "2050 suitable area"), f"{summary['future_area_km2']:,.0f} km²")
percent = summary["delta_percent"]
metric_columns[2].metric(
    tr("适宜面积净变化", "Net area change"), f"{summary['delta_area_km2']:+,.0f} km²",
    (f"{percent:+.1f}%" if percent is not None else tr("当前面积为零", "Zero baseline area")),
    delta_color="off",
)
metric_columns[3].metric(tr("两期持续适宜面积", "Persistent suitable area"),
                         f"{summary['class_areas_km2']['stable_suitable']:,.0f} km²")
st.caption(tr(
    f"按阈值 {threshold:.2f} 划分的模型面积，非实测栖息地。当前气候基线为 1970–2000 年；面积按 WGS84 椭球计算。",
    f"Modeled area at threshold {threshold:.2f}, not observed habitat. Current climate baseline: 1970–2000. Areas use the WGS84 ellipsoid.",
))

map_col, detail_col = st.columns([3, 1.45], gap="large")
with map_col:
    with st.container(border=True):
        st.subheader(tr("环境适宜度地图", "Explore habitat suitability"))
        view_labels = {
            "current": tr("当前", "Current"),
            "future": "2050",
            "change": tr("适宜度变化", "Score change"),
            "classes": tr("区域分类", "Area classes"),
        }
        view = st.radio(
            tr("地图视图", "Map view"), list(view_labels), format_func=view_labels.get,
            horizontal=True, label_visibility="collapsed", key="map_view",
        )
        figure = map_figure(
            predictions, view, st.session_state["grid_id"], show_records, show_outside, lang,
        )
        st.plotly_chart(
            figure, width="stretch", key="habitat_map", on_select=select_map_cell,
            selection_mode="points",
            config={"displaylogo": False, "scrollZoom": False,
                    "modeBarButtonsToRemove": ["lasso2d", "select2d"]},
        )
        if view == "classes":
            st.markdown("".join(
                f'<span class="legend-item"><span class="swatch" style="background:{color}"></span>'
                f'{CLASS_LABELS[name][0 if zh else 1]}</span>'
                for name, color in zip(CLASS_ORDER, CLASS_COLORS)
            ), unsafe_allow_html=True)
        st.caption(tr(
            "悬停查看数值；点击网格中心或使用右侧编号选择网格。双击地图恢复视野。每格约 5 角分，非精确物种位置。",
            "Hover for scores; click a cell center or use the cell selector. Double-click to reset zoom. "
            "Cells are 5 arc-minutes, not precise species locations.",
        ))

with detail_col:
    with st.container(border=True):
        st.subheader(tr("网格观察窗", "Cell inspector"))
        grid_id = st.selectbox(tr("选择网格", "Select a cell"), st.session_state["grid_options"], key="grid_id")
        row = predictions.set_index("grid_id").loc[grid_id]
        current = dataset.current.set_index("grid_id").loc[grid_id]
        future = dataset.future.set_index("grid_id").loc[grid_id]
        st.caption(f"{row['lon']:.4f}°E · {row['lat']:.4f}°N")
        st.markdown("**" + CLASS_LABELS[row["change_class"]][0 if zh else 1] + "**")
        st.markdown(
            '<div class="score-row"><div><small>' + tr("当前", "Current")
            + f'</small><strong>{row["suitability_current"]:.3f}</strong></div>'
            + f'<div><small>2050</small><strong>{row["suitability_2050"]:.3f}</strong></div></div>',
            unsafe_allow_html=True,
        )
        st.caption(tr("相对适宜度，不是出现概率", "Relative suitability, not occupancy probability"))
        units = ["m", "°C", "mm", "", "%"]
        details = ""
        for feature, unit in zip(FEATURE_COLUMNS, units):
            details += (
                '<div class="env-row"><span>' + FEATURE_LABELS[feature][0 if zh else 1]
                + f'</span><div>{current[feature]:.2f} → {future[feature]:.2f} {unit}</div></div>'
            )
        st.markdown(details, unsafe_allow_html=True)
        if row["recorded_presence"]:
            st.caption(tr("该网格有保留的出现记录。", "This cell has a retained occurrence record."))
        if row["extrapolated_2050"] or row["extrapolated_current"]:
            st.warning(tr(
                "至少一个时期的环境值超出训练样本范围，需谨慎解释。",
                "Environmental values in at least one period exceed the training range. Interpret cautiously.",
            ))
        st.caption(tr(
            "这里只比较输入条件，不能据此认定某个变量造成了适宜度变化。",
            "These are input comparisons, not proof that one variable caused the score change.",
        ))

st.info(tr(
    "适宜不等于一定出现。模型不模拟迁徙、种群数量或未来植被；仅供教学与赛事演示，不用于保护规划或政策决策。",
    "Suitable does not mean occupied. Dispersal, population size, and future vegetation are not modeled. "
    "Educational demonstration only, not a conservation or policy decision tool.",
))

evidence, quality, sources, downloads = st.tabs([
    tr("模型证据", "Model evidence"), tr("数据质量", "Data quality"),
    tr("来源与局限", "Sources & limits"), tr("导出结果", "Export results"),
])
with evidence:
    a, b = st.columns([1.7, 1])
    with a:
        st.subheader(tr("哪些变量影响模型表现？", "Which inputs matter to the model?"))
        st.plotly_chart(importance_figure(results.importance, lang), width="stretch", key="importance_chart")
        st.caption(tr(
            "验证集置换重要性：打乱变量后的 AUC 降幅。误差线为 10 次置换的标准差，非置信区间；重要性不代表因果。",
            "Held-out permutation importance: AUC decrease after shuffling a feature. Bars show standard deviation "
            "across 10 repeats, not confidence intervals. Importance is not causation.",
        ))
    with b:
        st.subheader(tr("初步验证，不是准确率承诺", "Preliminary validation"))
        st.metric("ROC-AUC", f"{results.metadata['validation_roc_auc']:.3f}")
        st.write(tr(
            f"训练 {results.metadata['train_cells']} 格；验证 {results.metadata['validation_cells']} 格"
            f"（出现 {results.metadata['validation_presence_cells']}，背景 {results.metadata['validation_background_cells']}）。",
            f"{results.metadata['train_cells']} training cells; {results.metadata['validation_cells']} validation cells "
            f"({results.metadata['validation_presence_cells']} presence, "
            f"{results.metadata['validation_background_cells']} background).",
        ))
        st.warning(tr(
            "随机留出验证，尚未进行空间分块。空间自相关与样本量小可能使结果过于乐观。背景点不是已证实的缺失点。",
            "Random holdout, not spatially blocked. Spatial autocorrelation and few presence cells can make "
            "performance optimistic. Background cells are not verified absences.",
        ))
        st.caption(tr("随机种子 42 · 300 棵树 · 仅 5 个环境变量 · 无 LLM",
                      "Seed 42 · 300 trees · 5 environmental predictors · No LLM"))

with quality:
    st.subheader(tr("从 128 条记录到 34 个独立出现网格", "From 128 records to 34 unique presence cells"))
    counts = dataset.audit["status"].value_counts()
    status_labels = {
        "retained": tr("保留网格", "Retained cells"),
        "duplicate_grid": tr("重复网格记录", "Duplicate-grid records"),
        "missing_or_invalid_coordinates": tr("缺失或无效坐标", "Missing / invalid coordinates"),
        "outside_or_unmatched_grid": tr("区外或未匹配", "Outside / unmatched"),
    }
    for col, status in zip(st.columns(4), status_labels):
        col.metric(status_labels[status], int(counts.get(status, 0)))
    st.caption(tr(
        "按网格去重后再划分训练与验证；缺失年份单独标记，不补造坐标。审计表保留每条记录的处理原因。",
        "Grid deduplication happens before splitting. Missing years do not invent locations. "
        "The audit preserves the handling reason for every record.",
    ))
    audit_view = dataset.audit.copy()
    audit_view["status"] = audit_view["status"].map(status_labels)
    st.dataframe(audit_view, hide_index=True, width="stretch", height=260)

with sources:
    st.subheader(tr("清楚说明模型没有回答什么", "Be clear about what the model cannot answer"))
    st.write(tr(
        "只有一种未来气候情景；海拔、NDVI 与林地覆盖不变。训练区间外标记仅表示外推，不是完整的不确定性估计。"
        "目前没有独立测试集、概率校准或背景采样敏感性分析。",
        "Only one future climate scenario; elevation, NDVI, and forest cover remain fixed. Extrapolation flags "
        "are not comprehensive uncertainty estimates. There is no independent test set, probability calibration, "
        "or background-sampling sensitivity analysis.",
    ))
    st.markdown(tr(
        "- 当前气候：WorldClim 2.1，1970–2000\n"
        "- 未来气候：CMIP6 / MPI-ESM1-2-HR / SSP2-4.5，2041–2060\n"
        "- 植被：NOAA CDR NDVI（2024）；ESA WorldCover（2021）\n"
        "- 出现记录：数据包所述 GBIF、公众科学与公开文献",
        "- Current climate: WorldClim 2.1, 1970–2000\n"
        "- Future climate: CMIP6 / MPI-ESM1-2-HR / SSP2-4.5, 2041–2060\n"
        "- Vegetation: NOAA CDR NDVI (2024); ESA WorldCover (2021)\n"
        "- Occurrences: GBIF, citizen science, and literature as described by the supplied package",
    ))
    st.warning(tr(
        "来源说明存在待核实项：网格行序与文字描述相反；2025 查询说明包含 2026 记录；GBIF DOI 为通配符；"
        "NDVI 均值与最大值合成描述不一致。未擅自修正或补造来源。",
        "Unresolved source issues: reversed documented grid row order; 2026 records despite a stated 2025 query; "
        "a wildcard GBIF DOI; inconsistent NDVI mean/max-composite descriptions. No provenance was invented.",
    ))
    with st.expander(tr("阅读随包原始说明（中文）", "Read original supplied notes (Chinese)")):
        st.text((DATASET_ROOT / "数据来源与合规说明.txt").read_text(encoding="utf-8"))
    st.caption(tr(
        "truth_auc.csv 仅是参考，不参与训练、选阈值或调参。来源与许可请以原提供方要求为准。",
        "truth_auc.csv is reference-only and is not used to train, select thresholds, or tune parameters. "
        "Original providers' licensing and citation requirements apply.",
    ))

with downloads:
    st.subheader(tr("带走结果，也带走证据", "Take the results and the evidence"))
    st.write(tr(
        "下载包含网格预测、GeoJSON、记录审计、样本划分、验证分数、变量重要性与来源说明的 ZIP。"
        "元数据保留随机种子、阈值、参数、依赖版本与输入哈希。",
        "Download a ZIP with predictions, GeoJSON, the occurrence audit, sample split, validation scores, "
        "importance, and source notes. Metadata includes the seed, threshold, parameters, versions, and input hashes.",
    ))
    st.download_button(
        tr("下载完整结果包", "Download evidence bundle"),
        data=export_bytes(fingerprint, MODEL_VERSION, threshold),
        file_name=f"habitat-2050-threshold-{threshold:.2f}.zip",
        mime="application/zip", type="primary", key="download_bundle",
    )
    with st.expander(tr("查看模型元数据", "Inspect model metadata")):
        st.json(json.dumps(results.metadata, ensure_ascii=False))

st.markdown('<div class="footnote">' + tr(
    "栖息地 2050 · AI × 生态 · 让预测可探索，让局限可见。仅供教学与赛事训练。",
    "Habitat 2050 · AI × Ecology · Explore the prediction. Keep its limits visible. Educational use only.",
) + "</div>", unsafe_allow_html=True)
