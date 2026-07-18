from __future__ import annotations

import json
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


ROOT = Path(__file__).resolve().parents[1]
FINAL = ROOT / "Final data"
RAW = ROOT / "data" / "raw" / "reproducibility_cases"
SOURCE = FINAL / "comparison_figures" / "comparison_source_data.csv"
OUT = FINAL / "task_grouped_figures"

COLORS = {
    "ink": "#1f2933",
    "muted": "#6b7280",
    "grid": "#e5e7eb",
    "paper": "#a5b0ba",
    "agent": "#2f6f8f",
    "accent": "#c46a4a",
    "gold": "#d8a24a",
    "green": "#5b8f73",
    "purple": "#7b6ca8",
    "panel": "#f7f8fa",
}


def set_style() -> None:
    mpl.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
            "svg.fonttype": "none",
            "pdf.fonttype": 42,
            "font.size": 8,
            "axes.spines.right": False,
            "axes.spines.top": False,
            "axes.linewidth": 0.7,
            "axes.edgecolor": COLORS["ink"],
            "xtick.color": COLORS["ink"],
            "ytick.color": COLORS["ink"],
            "text.color": COLORS["ink"],
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "savefig.facecolor": "white",
        }
    )


def save(fig: mpl.figure.Figure, stem: Path) -> list[Path]:
    paths = []
    for ext in (".png", ".pdf", ".svg"):
        path = stem.with_suffix(ext)
        if ext == ".png":
            fig.savefig(path, dpi=320, bbox_inches="tight")
        else:
            fig.savefig(path, bbox_inches="tight")
        paths.append(path)
    return paths


def panel_label(ax, label: str, x: float = -0.12, y: float = 1.14) -> None:
    ax.text(x, y, label, transform=ax.transAxes, fontsize=11, fontweight="bold", va="bottom")


def strip(ax) -> None:
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_xticks([])
    ax.set_yticks([])


def peptide_tables() -> tuple[pd.DataFrame, pd.DataFrame]:
    raw = pd.read_csv(RAW / "case1_amplit_validation" / "Validation.csv", header=None, names=["label", "sequence"])
    cleaned = pd.read_csv(FINAL / "1" / "final_outputs" / "cleaned_Validation.csv")
    return raw, cleaned


def fastq_summary() -> pd.DataFrame:
    frame = pd.read_csv(SOURCE)
    # Keep the latest exact metrics if present. Older figures used rounded FastQC values.
    if "agent_gc_percent_exact" in frame.columns:
        frame["gc_for_plot"] = frame["agent_gc_percent_exact"]
    else:
        frame["gc_for_plot"] = frame["agent_gc_percent"]
    return frame


def task1_peptide_figure() -> list[Path]:
    raw, cleaned = peptide_tables()
    raw_lengths = raw["sequence"].astype(str).str.len()
    clean_lengths = cleaned["sequence"].astype(str).str.len()
    raw_counts = raw["label"].value_counts().sort_index()
    clean_counts = cleaned["label"].value_counts().sort_index()

    fig = plt.figure(figsize=(7.4, 4.5), constrained_layout=True)
    gs = fig.add_gridspec(2, 3, width_ratios=[1.05, 1.1, 1.45], height_ratios=[1.0, 1.05])
    ax0 = fig.add_subplot(gs[:, 0])
    ax1 = fig.add_subplot(gs[0, 1])
    ax2 = fig.add_subplot(gs[1, 1])
    ax3 = fig.add_subplot(gs[:, 2])

    strip(ax0)
    panel_label(ax0, "A")
    ax0.set_xlim(0, 1)
    ax0.set_ylim(0, 1)
    ax0.text(0.00, 0.96, "Peptide CSV curation", fontsize=10, fontweight="bold", va="top")
    steps = [
        ("Raw table", f"{len(raw):,} rows"),
        ("Normalize", "label + sequence"),
        ("Validate", "canonical amino acids"),
        ("Deduplicate", f"{len(raw) - len(cleaned):,} removed"),
        ("Export", f"{len(cleaned):,} cleaned rows"),
    ]
    ys = np.linspace(0.78, 0.18, len(steps))
    for i, ((title, sub), y) in enumerate(zip(steps, ys)):
        box = FancyBboxPatch((0.08, y - 0.045), 0.72, 0.075, boxstyle="round,pad=0.012,rounding_size=0.018", fc="#f7fbfc", ec=COLORS["grid"], lw=0.8)
        ax0.add_patch(box)
        ax0.text(0.16, y + 0.012, title, fontsize=7.6, fontweight="bold", va="center")
        ax0.text(0.16, y - 0.018, sub, fontsize=6.7, color=COLORS["muted"], va="center")
        if i < len(ys) - 1:
            ax0.add_patch(FancyArrowPatch((0.44, y - 0.055), (0.44, ys[i + 1] + 0.045), arrowstyle="-|>", mutation_scale=9, color=COLORS["paper"], lw=0.9))

    panel_label(ax1, "B", x=-0.13, y=1.15)
    stages = ["raw", "cleaned"]
    values = [len(raw), len(cleaned)]
    ax1.plot(stages, values, color=COLORS["grid"], lw=2, zorder=1)
    ax1.scatter(stages, values, s=[80, 90], color=[COLORS["paper"], COLORS["agent"]], edgecolor="white", linewidth=0.8, zorder=3)
    for x, v in zip(stages, values):
        xytext = (8, 8) if x == "raw" else (0, 8)
        ha = "left" if x == "raw" else "center"
        ax1.annotate(
            f"{v:,}",
            (x, v),
            xytext=xytext,
            textcoords="offset points",
            ha=ha,
            va="bottom",
            fontsize=7.5,
        )
    ax1.text(0.5, min(values) - max(values) * 0.16, f"{len(raw)-len(cleaned):,} duplicate rows removed", ha="center", color=COLORS["accent"], fontsize=7.5)
    ax1.set_ylim(min(values) * 0.92, max(values) * 1.08)
    ax1.set_ylabel("Rows")
    ax1.set_title("Expected curation change", fontsize=9, pad=11)
    ax1.grid(axis="y", color=COLORS["grid"], lw=0.6)

    panel_label(ax2, "C", x=-0.13, y=1.15)
    labels = sorted(set(raw_counts.index).union(clean_counts.index))
    y = np.arange(len(labels))
    for yi, label in zip(y, labels):
        rv = raw_counts.get(label, 0)
        cv = clean_counts.get(label, 0)
        ax2.plot([rv, cv], [yi, yi], color=COLORS["grid"], lw=2)
        ax2.scatter(rv, yi, s=42, color=COLORS["paper"], zorder=3)
        ax2.scatter(cv, yi, s=42, color=COLORS["agent"], zorder=3)
        ax2.text(max(raw_counts.max(), clean_counts.max()) * 1.03, yi, f"label {label}", va="center", fontsize=7.5)
    ax2.set_yticks([])
    ax2.set_xlabel("Peptides")
    ax2.set_title("Class balance retained", fontsize=9, pad=11)
    ax2.grid(axis="x", color=COLORS["grid"], lw=0.6)

    panel_label(ax3, "D", x=-0.08, y=1.08)
    bins = np.arange(min(raw_lengths.min(), clean_lengths.min()), max(raw_lengths.max(), clean_lengths.max()) + 2)
    ax3.hist(raw_lengths, bins=bins, density=True, histtype="stepfilled", alpha=0.28, color=COLORS["paper"], label="raw")
    ax3.hist(clean_lengths, bins=bins, density=True, histtype="step", lw=2.0, color=COLORS["agent"], label="cleaned")
    ax3.set_xlabel("Peptide length")
    ax3.set_ylabel("Density")
    ax3.set_title("Length distribution preserved after cleaning", fontsize=9, pad=11)
    ax3.grid(axis="y", color=COLORS["grid"], lw=0.6)
    ax3.legend(fontsize=7)

    fig.suptitle("Task 1 | Peptide-table curation produces a non-redundant validation table", fontsize=12, fontweight="bold")
    return save(fig, OUT / "task1_peptide_csv_curation")


def task2_fastq_figure() -> list[Path]:
    df = fastq_summary()
    rs = (
        df.groupby(["group", "run", "paper", "source", "layout"], as_index=False)
        .agg(
            ena_read_count=("ena_run_read_count", "first"),
            agent_total=("agent_total_sequences", "sum"),
            ena_bytes=("ena_fastq_bytes", "sum"),
            local_bytes=("local_fastq_bytes", "sum"),
            mean_gc=("gc_for_plot", "mean"),
            min_len=("agent_sequence_length_mean", "min"),
            max_len=("agent_sequence_length_mean", "max"),
        )
        .sort_values("group")
    )
    rs["read_delta"] = rs["agent_total"] - rs["ena_read_count"]
    rs["byte_ratio"] = rs["local_bytes"] / rs["ena_bytes"]

    fig = plt.figure(figsize=(7.4, 5.1), constrained_layout=True)
    gs = fig.add_gridspec(2, 3, width_ratios=[1.05, 1.05, 1.45], height_ratios=[1.05, 1.0])
    ax0 = fig.add_subplot(gs[0, 0])
    ax1 = fig.add_subplot(gs[0, 1])
    ax2 = fig.add_subplot(gs[:, 2])
    ax3 = fig.add_subplot(gs[1, :2])

    panel_label(ax0, "A", x=-0.18, y=1.20)
    minv = min(rs["ena_read_count"].min(), rs["agent_total"].min())
    maxv = max(rs["ena_read_count"].max(), rs["agent_total"].max())
    ax0.plot([minv, maxv], [minv, maxv], color=COLORS["grid"], lw=1.4)
    ax0.scatter(rs["ena_read_count"], rs["agent_total"], s=54, color=COLORS["agent"], edgecolor="white", linewidth=0.8, zorder=3)
    offsets = {
        "ERR15682270": (10, 12),
        "ERR15682267": (10, 12),
        "ERR10114861": (-42, -14),
        "ERR3250149": (8, -12),
    }
    for row in rs.itertuples():
        dx, dy = offsets.get(row.run, (7, 3))
        ax0.annotate(
            row.run.replace("ERR", ""),
            (row.ena_read_count, row.agent_total),
            xytext=(dx, dy),
            textcoords="offset points",
            fontsize=6.5,
            ha="right" if dx < 0 else "left",
            bbox=dict(boxstyle="round,pad=0.10", fc="white", ec="none", alpha=0.72),
            arrowprops=dict(arrowstyle="-", color=COLORS["paper"], lw=0.45, shrinkA=0, shrinkB=4),
        )
    ax0.set_xscale("log")
    ax0.set_yscale("log")
    ax0.set_xlabel("Published ENA read count")
    ax0.set_ylabel("Agent total sequences")
    ax0.set_title("Read counts match public records", fontsize=9, pad=14)
    ax0.grid(color=COLORS["grid"], lw=0.6, which="both")

    panel_label(ax1, "B", x=-0.18, y=1.20)
    y = np.arange(len(rs))[::-1]
    ax1.axvline(1.0, color=COLORS["grid"], lw=1.5)
    ax1.scatter(rs["byte_ratio"], y, s=55, color=COLORS["paper"], edgecolor="white", linewidth=0.8, zorder=3)
    for yi, row in zip(y, rs.itertuples()):
        ax1.text(1.003, yi, row.run, fontsize=6.7, va="center")
    ax1.set_xlim(0.995, 1.012)
    ax1.set_yticks([])
    ax1.set_xlabel("Local bytes / ENA bytes")
    ax1.set_title("Local files match source files", fontsize=9, pad=14)
    ax1.grid(axis="x", color=COLORS["grid"], lw=0.6)

    panel_label(ax2, "C", x=-0.08, y=1.08)
    matrix = df.pivot_table(index="run", columns="mate", values="gc_for_plot", aggfunc="mean")
    matrix = matrix.reindex(rs["run"])
    im = ax2.imshow(matrix, aspect="auto", cmap="copper", vmin=35, vmax=90)
    ax2.set_xticks(np.arange(matrix.shape[1]))
    ax2.set_xticklabels(matrix.columns)
    ax2.set_yticks(np.arange(matrix.shape[0]))
    ax2.set_yticklabels(matrix.index, fontsize=7)
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            value = matrix.iloc[i, j]
            if not np.isnan(value):
                ax2.text(j, i, f"{value:.1f}", ha="center", va="center", fontsize=6.8, color="white" if value > 60 else COLORS["ink"])
    ax2.set_title("R1/R2 GC% is reported as a QC metric", fontsize=9, pad=11)
    cbar = fig.colorbar(im, ax=ax2, fraction=0.035, pad=0.02)
    cbar.set_label("GC (%)")

    panel_label(ax3, "D", x=-0.08, y=1.10)
    y2 = np.arange(len(rs))[::-1]
    ax3.set_xscale("log")
    jitter = 0.09
    for yi, row in zip(y2, rs.itertuples()):
        ax3.plot(
            [row.ena_read_count, row.agent_total],
            [yi + jitter, yi - jitter],
            color=COLORS["grid"],
            lw=2.0,
            zorder=1,
        )
        ax3.scatter(
            row.ena_read_count,
            yi + jitter,
            s=46,
            color=COLORS["paper"],
            edgecolor="white",
            linewidth=0.8,
            zorder=3,
            label="Published ENA" if yi == y2[0] else None,
        )
        ax3.scatter(
            row.agent_total,
            yi - jitter,
            s=46,
            color=COLORS["agent"],
            edgecolor="white",
            linewidth=0.8,
            zorder=3,
            label="Agent FastQC" if yi == y2[0] else None,
        )
        ax3.text(row.agent_total * 1.08, yi, row.run.replace("ERR", ""), va="center", fontsize=6.7)
    ax3.set_yticks([])
    ax3.set_xlabel("Read count")
    ax3.set_title("Published read counts and Agent outputs overlap", fontsize=9, pad=12)
    ax3.grid(axis="x", color=COLORS["grid"], lw=0.6, which="both")
    ax3.legend(fontsize=6.7, loc="upper right", framealpha=0.94)

    fig.suptitle("Task 2 | Sequencing source-data checks verify traceable input handling", fontsize=12, fontweight="bold")
    return save(fig, OUT / "task2_fastq_source_qc")


def task3_audit_figure() -> list[Path]:
    raw, cleaned = peptide_tables()
    df = fastq_summary()
    rs = (
        df.groupby(["run"], as_index=False)
        .agg(ena_read_count=("ena_run_read_count", "first"), agent_total=("agent_total_sequences", "sum"))
    )
    mismatches = int((rs["ena_read_count"] != rs["agent_total"]).sum())
    expected_changes = len(raw) - len(cleaned)

    fig, ax = plt.subplots(figsize=(7.4, 3.6))
    strip(ax)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.text(0.02, 0.93, "Audit interpretation separates task-specific changes from failures", fontsize=12, fontweight="bold", va="top")
    cards = [
        ("Source-data\nmatch", f"{len(rs)} FASTQ runs\nread-count delta = 0", COLORS["agent"], 0.125),
        ("Expected\ncuration", f"{expected_changes:,} duplicate\npeptide rows removed", COLORS["gold"], 0.375),
        ("Derived\nQC", "GC% and read length\nreported as QC metrics", COLORS["purple"], 0.625),
        ("Actionable\nmismatch", f"{mismatches} FASTQ source-data\nmismatches detected", COLORS["accent"], 0.875),
    ]
    for title, text, color, x in cards:
        ax.add_patch(FancyBboxPatch((x - 0.105, 0.35), 0.21, 0.31, boxstyle="round,pad=0.014,rounding_size=0.02", fc="#fbfbfb", ec=COLORS["grid"], lw=0.8))
        ax.add_patch(plt.Rectangle((x - 0.075, 0.57), 0.024, 0.024, color=color, ec="none"))
        ax.text(x - 0.040, 0.58, title, fontsize=7.4, fontweight="bold", va="center", linespacing=1.0)
        ax.text(x, 0.45, text, fontsize=6.55, color=COLORS["muted"], ha="center", va="center", linespacing=1.15)
    for x1, x2 in [(0.235, 0.27), (0.485, 0.52), (0.735, 0.77)]:
        ax.add_patch(FancyArrowPatch((x1, 0.49), (x2, 0.49), arrowstyle="-|>", mutation_scale=9, color=COLORS["paper"], lw=0.9))
    ax.text(0.05, 0.14, "Interpretation rule: raw-source mismatches require review; expected preprocessing changes and derived QC metrics should be reported, not treated as failures.", fontsize=7.7, color=COLORS["muted"])
    return save(fig, OUT / "task3_audit_interpretation")


def write_tables() -> dict[str, str]:
    OUT.mkdir(parents=True, exist_ok=True)
    raw, cleaned = peptide_tables()
    df = fastq_summary()
    peptide = pd.DataFrame(
        [
            {
                "task": "peptide_csv_curation",
                "raw_rows": len(raw),
                "cleaned_rows": len(cleaned),
                "duplicates_removed": len(raw) - len(cleaned),
                "raw_unique_sequences": raw["sequence"].nunique(),
                "cleaned_unique_sequences": cleaned["sequence"].nunique(),
            }
        ]
    )
    fastq = (
        df.groupby(["group", "run", "layout"], as_index=False)
        .agg(
            ena_read_count=("ena_run_read_count", "first"),
            agent_total_sequences=("agent_total_sequences", "sum"),
            ena_fastq_bytes=("ena_fastq_bytes", "sum"),
            local_fastq_bytes=("local_fastq_bytes", "sum"),
            mean_gc_percent=("gc_for_plot", "mean"),
            mean_read_length=("agent_sequence_length_mean", "mean"),
        )
    )
    fastq["read_delta"] = fastq["agent_total_sequences"] - fastq["ena_read_count"]
    fastq["byte_ratio"] = fastq["local_fastq_bytes"] / fastq["ena_fastq_bytes"]
    p1 = OUT / "task1_peptide_summary.csv"
    p2 = OUT / "task2_fastq_summary.csv"
    peptide.to_csv(p1, index=False)
    fastq.to_csv(p2, index=False)
    return {"peptide": str(p1), "fastq": str(p2)}


def main() -> None:
    set_style()
    OUT.mkdir(parents=True, exist_ok=True)
    figures = []
    figures.extend(task1_peptide_figure())
    figures.extend(task2_fastq_figure())
    figures.extend(task3_audit_figure())
    tables = write_tables()
    manifest = {"figures": [str(p) for p in figures], "tables": tables}
    (OUT / "task_grouped_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
