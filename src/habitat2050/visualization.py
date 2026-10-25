"""Offline Plotly grid maps and portable GeoJSON geometry."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from habitat2050.data import CELL_SIZE
from habitat2050.modeling import CLASS_ORDER


SUITABILITY_COLORS = [
    [0, "#eff0e6"], [0.25, "#d3dfc2"], [0.5, "#92b891"],
    [0.75, "#3e8066"], [1, "#123e35"],
]
CHANGE_COLORS = [[0, "#af5545"], [0.5, "#f3f2ea"], [1, "#218b83"]]
CLASS_COLORS = ["#276a52", "#bc614c", "#349ca0", "#e3e7df"]
FEATURE_LABELS = {
    "elevation_m": ("海拔", "Elevation"),
    "bio1_annual_mean_temp_degC": ("年均温", "Annual temperature"),
    "bio12_annual_precip_mm": ("年降水量", "Annual rainfall"),
    "ndvi_growing_season": ("生长季 NDVI", "Growing-season NDVI"),
    "forest_cover_pct": ("林地覆盖率", "Forest cover"),
}
CLASS_LABELS = {
    "stable_suitable": ("持续适宜", "Persistent suitable"),
    "lost": ("转为不适宜", "Lost suitability"),
    "gained": ("转为适宜", "Gained suitability"),
    "stable_unsuitable": ("持续不适宜", "Persistent unsuitable"),
}


def cell_polygon(lon: float, lat: float) -> list[list[float]]:
    half = CELL_SIZE / 2
    west, east, south, north = lon - half, lon + half, lat - half, lat + half
    return [[west, south], [east, south], [east, north], [west, north], [west, south]]


def as_geojson(frame: pd.DataFrame) -> dict:
    features = []
    for row in frame.to_dict("records"):
        properties = {
            key: (value.item() if isinstance(value, np.generic) else value)
            for key, value in row.items()
        }
        features.append({
            "type": "Feature", "id": row["grid_id"], "properties": properties,
            "geometry": {"type": "Polygon", "coordinates": [cell_polygon(row["lon"], row["lat"])]},
        })
    return {"type": "FeatureCollection", "features": features}


def map_figure(
    frame: pd.DataFrame, view: str, selected: str,
    show_occurrences: bool, show_extrapolation: bool, language: str,
) -> go.Figure:
    zh = language == "zh"
    frame = frame.copy()
    column = {
        "current": "suitability_current", "future": "suitability_2050",
        "change": "delta_suitability", "classes": "class_code",
    }[view]
    frame["class_code"] = frame["change_class"].map(dict(zip(CLASS_ORDER, range(4))))
    xs, ys = np.sort(frame["lon"].unique()), np.sort(frame["lat"].unique())
    indexed = frame.set_index(["lat", "lon"])
    index = pd.MultiIndex.from_product([ys, xs], names=["lat", "lon"])
    ordered = indexed.reindex(index)
    z = ordered[column].to_numpy().reshape(len(ys), len(xs))
    fields = ["grid_id", "suitability_current", "suitability_2050", "delta_suitability"]
    custom = ordered[fields].to_numpy().reshape(len(ys), len(xs), len(fields))
    if view == "change":
        colors, lower, upper = CHANGE_COLORS, -1, 1
        legend = "适宜度变化" if zh else "Suitability change"
    elif view == "classes":
        colors = []
        for i, color in enumerate(CLASS_COLORS):
            colors.extend([[i / 4, color], [(i + 1) / 4, color]])
        lower, upper, legend = -0.5, 3.5, ""
    else:
        colors, lower, upper = SUITABILITY_COLORS, 0, 1
        legend = "相对适宜度" if zh else "Relative suitability"
    hover = (
        "<b>%{customdata[0]}</b><br>"
        + ("当前" if zh else "Current") + ": %{customdata[1]:.3f}<br>"
        + "2050: %{customdata[2]:.3f}<br>"
        + ("变化" if zh else "Change") + ": %{customdata[3]:+.3f}<extra></extra>"
    )
    # Explicit cell edges make the heatmap a rectangular grid, not an interpolated surface.
    x_edges = np.r_[xs - CELL_SIZE / 2, xs[-1] + CELL_SIZE / 2]
    y_edges = np.r_[ys - CELL_SIZE / 2, ys[-1] + CELL_SIZE / 2]
    fig = go.Figure(go.Heatmap(
        x=x_edges, y=y_edges, z=z, customdata=custom,
        zmin=lower, zmax=upper, colorscale=colors, zsmooth=False,
        hovertemplate=hover, xgap=0.5, ygap=0.5,
        showscale=view != "classes",
        colorbar=dict(title=dict(text=legend, side="bottom"), orientation="h",
                      x=0.5, xanchor="center", y=-0.22, thickness=9, len=0.8, outlinewidth=0),
    ))
    # Plotly selection events come from scatter centers; the heatmap supplies cell fills.
    fig.add_trace(go.Scatter(
        x=frame["lon"], y=frame["lat"], mode="markers",
        marker=dict(size=8, color="rgba(0,0,0,0.005)"),
        customdata=frame[["grid_id"]].to_numpy(),
        hoverinfo="skip", showlegend=False,
        selected=dict(marker=dict(opacity=0.1)),
        unselected=dict(marker=dict(opacity=0.005)),
    ))
    if show_occurrences:
        points = frame[frame["recorded_presence"]]
        fig.add_trace(go.Scatter(
            x=points["lon"], y=points["lat"], mode="markers",
            marker=dict(size=6, color="#dfb756", line=dict(width=1, color="#243e30")),
            name="出现记录" if zh else "Recorded cells",
            customdata=points[["grid_id"]].to_numpy(),
            hovertemplate="%{customdata[0]}<extra></extra>",
        ))
    if show_extrapolation:
        flag = "extrapolated_current" if view == "current" else "extrapolated_2050"
        points = frame[frame[flag]]
        fig.add_trace(go.Scatter(
            x=points["lon"], y=points["lat"], mode="markers",
            marker=dict(size=5, symbol="x", color="#8a456c"),
            name="训练范围外" if zh else "Outside training range",
            customdata=points[["grid_id"]].to_numpy(),
            hovertemplate="%{customdata[0]}<extra></extra>",
        ))
    point = frame.loc[frame["grid_id"].eq(selected)].iloc[0]
    border = cell_polygon(float(point["lon"]), float(point["lat"]))
    fig.add_trace(go.Scatter(
        x=[p[0] for p in border], y=[p[1] for p in border],
        mode="lines", line=dict(color="#e0a728", width=3),
        hoverinfo="skip", showlegend=False,
    ))
    fig.update_layout(
        height=490, margin=dict(l=12, r=12, t=24, b=80),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#f5f5ed",
        font=dict(family="Arial, Microsoft YaHei, sans-serif", color="#36524b", size=12),
        xaxis=dict(title="经度 / Longitude" if zh else "Longitude (E)",
                   range=[98.45, 103.05], showgrid=False, zeroline=False, constrain="domain"),
        yaxis=dict(title="纬度 / Latitude" if zh else "Latitude (N)",
                   range=[25.95, 29.55], showgrid=False, zeroline=False, constrain="domain",
                   scaleanchor="x", scaleratio=1 / np.cos(np.deg2rad(27.75))),
        legend=dict(orientation="h", y=1.06, x=0),
        clickmode="event+select", dragmode="pan",
        uirevision=f"habitat-map-{view}", selectionrevision=selected,
    )
    return fig


def importance_figure(importance: pd.DataFrame, language: str) -> go.Figure:
    index = 0 if language == "zh" else 1
    data = importance.iloc[::-1]
    fig = go.Figure(go.Bar(
        x=data["auc_drop"], y=[FEATURE_LABELS[f][index] for f in data["feature"]],
        orientation="h", marker_color="#3e8066",
        error_x=dict(type="data", array=data["std"], color="#9ab4a5"),
        hovertemplate="%{y}<br>%{x:.3f}<extra></extra>",
    ))
    fig.update_layout(
        height=270, margin=dict(l=0, r=20, t=8, b=0),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#36524b"),
        xaxis=dict(title="AUC 降幅" if index == 0 else "Decrease in held-out ROC-AUC",
                   gridcolor="#e6eae3", zerolinecolor="#b6c5b9"),
    )
    return fig
