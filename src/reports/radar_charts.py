"""
src/reports/radar_charts.py

Day 19 — Radar / polar charts. 8 axes: ROE, ROCE, NPM, D/E, FCF score,
PAT CAGR 5yr, Revenue CAGR 5yr, Composite Score (all 0-100 normalised
scores, computed by src.screener.composite). Company = filled polygon,
peer group average = dashed outline overlay. Companies with no peer group
get a standalone chart against the Nifty 100 average instead.

Exported as reports/radar_charts/<company_id>_radar.png
"""

from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.screener.composite import scale_0_100

AXES = ["ROE", "ROCE", "NPM", "D/E", "FCF Score", "PAT CAGR 5yr", "Revenue CAGR 5yr", "Composite Score"]


def _axis_values(row: pd.Series) -> list[float]:
    def g(col):
        v = row.get(col)
        return 0.0 if pd.isna(v) else float(v)
    return [
        g("roe_score"), g("roce_score"), g("npm_score"), g("de_score"),
        g("fcf_score"), g("pat_cagr_score"), g("revenue_cagr_score"), g("composite_score"),
    ]


def prepare_scored_df(snapshot_df: pd.DataFrame) -> pd.DataFrame:
    """Adds the fcf_score column (missing from composite.add_component_scores) used only for radar axes."""
    df = snapshot_df.copy()
    df["fcf_score"] = scale_0_100(df["free_cash_flow_cr"])
    return df


def _draw_radar(ax, company_values: list[float], overlay_values: list[float], overlay_label: str,
                 title: str) -> None:
    n = len(AXES)
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False).tolist()
    angles += angles[:1]

    cv = company_values + company_values[:1]
    ov = overlay_values + overlay_values[:1]

    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(AXES, fontsize=9)
    ax.set_ylim(0, 100)
    ax.set_yticks([25, 50, 75, 100])
    ax.set_yticklabels(["25", "50", "75", "100"], fontsize=7)

    ax.plot(angles, cv, color="#1F4E78", linewidth=2)
    ax.fill(angles, cv, color="#1F4E78", alpha=0.25)

    ax.plot(angles, ov, color="#B22222", linewidth=1.5, linestyle="--")

    ax.set_title(title, fontsize=11, fontweight="bold", pad=20)
    ax.legend(["Company", overlay_label], loc="upper right", bbox_to_anchor=(1.3, 1.1), fontsize=8)


def generate_radar_chart(company_id: str, scored_df: pd.DataFrame, out_dir: Path) -> Path:
    row = scored_df[scored_df["company_id"] == company_id].iloc[0]
    peer_group = row.get("peer_group_name", "No peer group assigned")

    if peer_group != "No peer group assigned":
        peers = scored_df[scored_df["peer_group_name"] == peer_group]
        overlay_values = [
            peers[c].mean(skipna=True) if pd.notna(peers[c].mean(skipna=True)) else 0.0
            for c in ["roe_score", "roce_score", "npm_score", "de_score", "fcf_score",
                      "pat_cagr_score", "revenue_cagr_score", "composite_score"]
        ]
        overlay_label = f"{peer_group} avg"
    else:
        overlay_values = [
            scored_df[c].mean(skipna=True) if pd.notna(scored_df[c].mean(skipna=True)) else 0.0
            for c in ["roe_score", "roce_score", "npm_score", "de_score", "fcf_score",
                      "pat_cagr_score", "revenue_cagr_score", "composite_score"]
        ]
        overlay_label = "Nifty 100 avg"

    company_values = _axis_values(row)

    fig = plt.figure(figsize=(6, 6))
    ax = fig.add_subplot(111, polar=True)
    _draw_radar(ax, company_values, overlay_values, overlay_label,
                f"{row.get('company_name', company_id)} ({company_id})")

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{company_id}_radar.png"
    fig.tight_layout()
    fig.savefig(out_path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return out_path


def generate_all_radar_charts(scored_df: pd.DataFrame, out_dir: Path) -> list[Path]:
    scored_df = prepare_scored_df(scored_df)
    paths = []
    for cid in scored_df["company_id"].unique():
        paths.append(generate_radar_chart(cid, scored_df, out_dir))
    return paths
