#!/usr/bin/env python3
"""Create the manuscript benchmark figure from retained v3-v5 summaries."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "Final data" / "manuscript_figures" / "benchmark_v5"
BASE = OUT / "figure2_paleorigor_v5_benchmark"

BLUE = "#2F6F92"
BLUE_DARK = "#214F69"
BLUE_LIGHT = "#B8D2E1"
GRAY = "#8A949E"
GRAY_LIGHT = "#DCE1E5"
GREEN = "#3F8A68"
GREEN_LIGHT = "#E7F2EC"
TEXT = "#202A35"
GRID = "#E5E8EB"


def load_summary(version: str) -> dict:
    return json.loads(
        (ROOT / "analysis" / f"benchmark_{version}" / "results" / "summary.json").read_text(
            encoding="utf-8"
        )
    )


def write_source_data(summaries: dict[str, dict]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []
    for version, summary in summaries.items():
        for arm, values in summary["arms"].items():
            rows.append(
                {
                    "record_type": "version",
                    "version": version,
                    "scenario": "overall",
                    "task_class": "all",
                    "arm": arm,
                    "successes": values["successes"],
                    "total": values["total"],
                    "rate": values["rate"],
                    "wilson_low": values["wilson_95"][0],
                    "wilson_high": values["wilson_95"][1],
                }
            )
    v5 = summaries["v5"]
    for scenario, arms in v5["by_scenario"].items():
        task_class = "supported" if "-S" in scenario else "boundary"
        for arm, values in arms.items():
            rows.append(
                {
                    "record_type": "scenario",
                    "version": "v5",
                    "scenario": scenario,
                    "task_class": task_class,
                    "arm": arm,
                    "successes": values["successes"],
                    "total": values["total"],
                    "rate": values["rate"],
                    "wilson_low": "",
                    "wilson_high": "",
                }
            )
    with (OUT / "figure2_source_data.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def panel_label(ax, label: str) -> None:
    ax.text(-0.10, 1.08, label, transform=ax.transAxes, fontsize=11, fontweight="bold", va="top")


def main() -> None:
    summaries = {version: load_summary(version) for version in ("v3", "v4", "v5")}
    write_source_data(summaries)

    mpl.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
            "svg.fonttype": "none",
            "pdf.fonttype": 42,
            "font.size": 8.2,
            "axes.labelcolor": TEXT,
            "axes.edgecolor": TEXT,
            "axes.linewidth": 0.8,
            "xtick.color": TEXT,
            "ytick.color": TEXT,
            "text.color": TEXT,
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )

    fig = plt.figure(figsize=(7.2, 5.15), facecolor="white")
    gs = fig.add_gridspec(2, 2, width_ratios=[1.22, 0.78], height_ratios=[0.95, 1.15], hspace=0.56, wspace=0.42)
    ax_a = fig.add_subplot(gs[0, 0])
    ax_b = fig.add_subplot(gs[0, 1])
    ax_c = fig.add_subplot(gs[1, :])

    # A: version history. V3/V4 are visibly development-stage; V5 is the final held-out release test.
    versions = ["v3", "v4", "v5"]
    x = np.arange(3)
    paleo = np.array([summaries[v]["arms"]["paleorigor"]["rate"] * 100 for v in versions])
    raw = np.array([summaries[v]["arms"]["raw_llm"]["rate"] * 100 for v in versions])
    ax_a.axvspan(-0.38, 1.38, color="#F3F4F5", zorder=0)
    ax_a.axvspan(1.62, 2.38, color=GREEN_LIGHT, zorder=0)
    ax_a.axhline(90, color="#7A838B", lw=1, ls=(0, (4, 3)), zorder=1)
    ax_a.plot(x, raw, color=GRAY, marker="o", ms=5, lw=1.6, label="Raw-model control", zorder=3)
    ax_a.plot(x, paleo, color=BLUE, marker="o", ms=5.5, lw=2.0, label="PaleoRigor", zorder=4)
    ax_a.text(0, 72.9, "18/24 both", ha="center", va="top", color="#616B74", fontsize=7.2)
    for xi, yi, count in zip(x[1:], paleo[1:], ("18/24", "23/24")):
        ax_a.text(xi, yi + 2.0, count, ha="center", va="bottom", color=BLUE_DARK, fontsize=7.5, fontweight="bold")
    for xi, yi, count in zip(x[1:], raw[1:], ("21/24", "19/24")):
        ax_a.text(xi, yi + 2.0, count, ha="center", va="bottom", color="#616B74", fontsize=7.2)
    ax_a.text(0.5, 103.0, "development qualification", ha="center", va="bottom", color="#68727B", fontsize=7.4)
    ax_a.text(2, 103.0, "final held-out", ha="center", va="bottom", color=GREEN, fontsize=7.4, fontweight="bold")
    ax_a.text(-0.38, 90.7, "prespecified 90% threshold", ha="left", va="bottom", fontsize=6.9, color="#68727B", bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.82, "pad": 0.8})
    ax_a.set(title="Versioned strict-success trajectory", ylabel="Strict success (%)", xticks=x, xticklabels=["v3", "v4", "v5"], ylim=(68, 107), xlim=(-0.45, 2.45))
    ax_a.set_yticks([70, 80, 90, 100])
    ax_a.grid(axis="y", color=GRID, lw=0.8)
    ax_a.legend(
        loc="upper left",
        bbox_to_anchor=(0.01, 0.84),
        frameon=False,
        fontsize=6.9,
        handlelength=2.0,
        ncol=2,
        columnspacing=1.3,
    )
    panel_label(ax_a, "A")

    # B: final overall comparison with Wilson intervals.
    labels = ["PaleoRigor", "Raw model"]
    arms = ["paleorigor", "raw_llm"]
    colors = [BLUE, GRAY]
    y = np.array([1, 0])
    for yi, arm, color in zip(y, arms, colors):
        values = summaries["v5"]["arms"][arm]
        rate = values["rate"] * 100
        lo, hi = (value * 100 for value in values["wilson_95"])
        ax_b.errorbar(rate, yi, xerr=[[rate - lo], [hi - rate]], fmt="o", ms=7, color=color, ecolor=color, elinewidth=2, capsize=3, zorder=3)
        ax_b.text(rate, yi + 0.18, f'{values["successes"]}/{values["total"]} ({rate:.1f}%)', ha="center", va="bottom", fontsize=7.4, color=TEXT, fontweight="bold" if arm == "paleorigor" else "normal")
    ax_b.axvline(90, color="#7A838B", lw=1, ls=(0, (4, 3)))
    ax_b.set(title="Final v5 evaluation", xlabel="Strict success (%)", yticks=y, yticklabels=labels, xlim=(50, 103), ylim=(-0.55, 1.55))
    ax_b.set_xticks([50, 60, 70, 80, 90, 100])
    ax_b.grid(axis="x", color=GRID, lw=0.8)
    ax_b.text(0.03, 0.055, "Difference +16.7 pp\nexact McNemar p = 0.219", transform=ax_b.transAxes, fontsize=6.9, color="#59636C", va="bottom")
    panel_label(ax_b, "B")

    # C: scenario-level results expose where the remaining failures occurred.
    scenario_order = ["H5-S1", "H5-S2", "H5-S3", "H5-S4", "H5-B1", "H5-B2", "H5-B3", "H5-B4"]
    scenario_labels = ["FASTA\ncuration", "Paired\nFASTQ QC", "Peptide\ntable", "Sample\nsheet", "Format\nmismatch", "Missing\nreference", "Unsupported\nclaim", "Missing\nmate"]
    matrix = np.array(
        [
            [summaries["v5"]["by_scenario"][s]["paleorigor"]["rate"] for s in scenario_order],
            [summaries["v5"]["by_scenario"][s]["raw_llm"]["rate"] for s in scenario_order],
        ]
    )
    cmap = LinearSegmentedColormap.from_list("audit_blue", ["#F1F3F4", BLUE_LIGHT, BLUE_DARK])
    ax_c.imshow(matrix, vmin=0, vmax=1, cmap=cmap, aspect="auto")
    for row in range(matrix.shape[0]):
        for col in range(matrix.shape[1]):
            success = round(matrix[row, col] * 3)
            color = "white" if matrix[row, col] >= 0.83 else TEXT
            ax_c.text(col, row, f"{success}/3", ha="center", va="center", color=color, fontsize=8.2, fontweight="bold")
    ax_c.axvline(3.5, color="white", lw=4)
    ax_c.axvline(3.5, color="#AEB6BD", lw=0.8)
    ax_c.text(1.5, -0.64, "supported workflows", ha="center", va="bottom", fontsize=7.5, color="#59636C")
    ax_c.text(5.5, -0.64, "boundary decisions", ha="center", va="bottom", fontsize=7.5, color="#59636C")
    ax_c.set(title="Final v5 performance by scenario", xticks=np.arange(8), xticklabels=scenario_labels, yticks=[0, 1], yticklabels=["PaleoRigor", "Raw model"])
    ax_c.tick_params(axis="x", length=0, pad=5)
    ax_c.tick_params(axis="y", length=0, pad=6)
    for spine in ax_c.spines.values():
        spine.set_visible(False)
    panel_label(ax_c, "C")

    fig.subplots_adjust(left=0.095, right=0.985, top=0.935, bottom=0.11)
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(BASE.with_suffix(".svg"), bbox_inches="tight")
    fig.savefig(BASE.with_suffix(".pdf"), bbox_inches="tight")
    fig.savefig(BASE.with_suffix(".png"), dpi=400, bbox_inches="tight")
    fig.savefig(BASE.with_suffix(".tiff"), dpi=600, bbox_inches="tight", pil_kwargs={"compression": "tiff_lzw"})
    plt.close(fig)


if __name__ == "__main__":
    main()
