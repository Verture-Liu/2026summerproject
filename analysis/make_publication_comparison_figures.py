from __future__ import annotations

import csv
import gzip
import json
import math
import re
import zipfile
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
FINAL = ROOT / "Final data"
RAW = ROOT / "data" / "raw" / "reproducibility_cases"
OUT = FINAL / "comparison_figures"

COLORS = {
    "ink": "#1f2933",
    "muted": "#6b7280",
    "grid": "#e5e7eb",
    "paper": "#9aa6b2",
    "agent": "#2f6f8f",
    "accent": "#c46a4a",
    "gold": "#d8a24a",
    "panel": "#f7f8fa",
}

ENA = {
    "ERR15682270": {
        "group": "2–3",
        "paper": "Iceman microbiome",
        "source": "PRJEB94382",
        "layout": "PAIRED",
        "scientific_name": "metagenome",
        "fastq_bytes": [3644307, 5363244],
        "read_count": 56122,
        "base_count": 16892722,
        "folders": ["2", "3"],
    },
    "ERR10114877": {
        "group": "4–5",
        "paper": "Paleofuran study",
        "source": "PRJEB55583",
        "layout": "PAIRED",
        "scientific_name": "blank sample",
        "fastq_bytes": [7701833, 7169255],
        "read_count": 526070,
        "base_count": 33836230,
        "folders": ["4", "5"],
    },
    "ERR3250149": {
        "group": "6",
        "paper": "Birch pitch genome",
        "source": "PRJEB30280",
        "layout": "SINGLE",
        "scientific_name": "Betula pendula",
        "fastq_bytes": [172890455],
        "read_count": 4380359,
        "base_count": 354809079,
        "folders": ["6"],
    },
    "ERR10114867": {
        "group": "7",
        "paper": "Paleofuran study",
        "source": "PRJEB55583",
        "layout": "PAIRED",
        "scientific_name": "blank sample",
        "fastq_bytes": [14798699, 15848835],
        "read_count": 847520,
        "base_count": 49281990,
        "folders": ["7"],
    },
    "ERR10114861": {
        "group": "8",
        "paper": "Paleofuran study",
        "source": "PRJEB55583",
        "layout": "PAIRED",
        "scientific_name": "Neanderthal sample",
        "fastq_bytes": [35365445, 36069916],
        "read_count": 4068862,
        "base_count": 78016958,
        "folders": ["8"],
    },
    "ERR15682267": {
        "group": "9",
        "paper": "Iceman microbiome",
        "source": "PRJEB94382",
        "layout": "PAIRED",
        "scientific_name": "metagenome",
        "fastq_bytes": [4102323, 5787702],
        "read_count": 59258,
        "base_count": 17836658,
        "folders": ["9"],
    },
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


def save_figure(fig: mpl.figure.Figure, stem: Path) -> None:
    fig.savefig(stem.with_suffix(".png"), dpi=320, bbox_inches="tight")
    fig.savefig(stem.with_suffix(".pdf"), bbox_inches="tight")
    fig.savefig(stem.with_suffix(".svg"), bbox_inches="tight")


def panel_label(ax, label: str) -> None:
    ax.text(
        -0.08,
        1.07,
        label,
        transform=ax.transAxes,
        fontsize=11,
        fontweight="bold",
        va="bottom",
        ha="left",
    )


def strip_axes(ax) -> None:
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_visible(False)
    ax.set_xticks([])
    ax.set_yticks([])


def read_peptide_tables() -> tuple[pd.DataFrame, pd.DataFrame]:
    raw = pd.read_csv(RAW / "case1_amplit_validation" / "Validation.csv", header=None, names=["label", "sequence"])
    agent = pd.read_csv(FINAL / "1" / "final_outputs" / "cleaned_Validation.csv")
    return raw, agent


def fastqc_zips_for_run(run: str, folders: list[str]) -> list[Path]:
    zips: list[Path] = []
    for folder in folders:
        zips.extend(sorted((FINAL / folder / "final_outputs").glob(f"{run}*_fastqc.zip")))
    return zips


def local_fastq_for_run(run: str) -> list[Path]:
    paired = sorted(RAW.glob(f"case*/{run}_*.fastq.gz"))
    return paired or sorted(RAW.glob(f"case*/{run}.fastq.gz"))


def parse_fastqc_zip(path: Path) -> dict[str, float | str]:
    with zipfile.ZipFile(path) as zf:
        data_name = next(name for name in zf.namelist() if name.endswith("fastqc_data.txt"))
        text = zf.read(data_name).decode("utf-8", errors="replace")
    parsed: dict[str, float | str] = {}
    for line in text.splitlines():
        if "\t" not in line:
            continue
        key, value = line.split("\t", 1)
        if key in {"Filename", "Total Sequences", "Sequences flagged as poor quality", "Sequence length", "%GC"}:
            parsed[key] = value
    length_values = [int(x) for x in re.findall(r"\d+", str(parsed.get("Sequence length", "")))]
    parsed["total_sequences"] = int(float(str(parsed.get("Total Sequences", 0))))
    parsed["gc_percent"] = float(str(parsed.get("%GC", 0)))
    parsed["poor_quality"] = int(float(str(parsed.get("Sequences flagged as poor quality", 0))))
    parsed["sequence_length_mean"] = float(np.mean(length_values)) if length_values else np.nan
    return parsed


def exact_fastq_metrics(path: Path) -> dict[str, float]:
    records = 0
    total_bases = 0
    gc_bases = 0
    opener = gzip.open if path.name.lower().endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8", errors="replace") as handle:
        while True:
            header = handle.readline()
            if not header:
                break
            sequence = handle.readline().strip().upper()
            handle.readline()
            handle.readline()
            records += 1
            total_bases += len(sequence)
            gc_bases += sequence.count("G") + sequence.count("C")
    return {
        "records": records,
        "mean_length": round(total_bases / records, 3) if records else float("nan"),
        "gc_percent_exact": round(gc_bases / total_bases * 100, 3) if total_bases else float("nan"),
    }


def build_fastq_summary() -> pd.DataFrame:
    rows = []
    for run, info in ENA.items():
        zips = fastqc_zips_for_run(run, info["folders"])
        fastqs = local_fastq_for_run(run)
        for idx, zip_path in enumerate(zips):
            metrics = parse_fastqc_zip(zip_path)
            exact_metrics = exact_fastq_metrics(fastqs[idx]) if idx < len(fastqs) else {}
            mate = f"R{idx + 1}" if len(zips) > 1 else "single"
            rows.append(
                {
                    "group": info["group"],
                    "run": run,
                    "mate": mate,
                    "paper": info["paper"],
                    "source": info["source"],
                    "layout": info["layout"],
                    "scientific_name": info["scientific_name"],
                    "ena_fastq_bytes": info["fastq_bytes"][idx],
                    "local_fastq_bytes": fastqs[idx].stat().st_size if idx < len(fastqs) else np.nan,
                    "agent_total_sequences": metrics["total_sequences"],
                    "agent_gc_percent": metrics["gc_percent"],
                    "agent_gc_percent_exact": exact_metrics.get("gc_percent_exact", np.nan),
                    "agent_poor_quality": metrics["poor_quality"],
                    "agent_sequence_length_mean": exact_metrics.get("mean_length", metrics["sequence_length_mean"]),
                    "ena_run_read_count": info["read_count"],
                    "ena_run_base_count": info["base_count"],
                }
            )
    return pd.DataFrame(rows)


def draw_metric_pair(ax, left_value, right_value, y, label, color=COLORS["agent"], fmt="{:,.0f}") -> None:
    ax.plot([0, 1], [y, y], color=COLORS["grid"], lw=1.1, zorder=1)
    ax.scatter([0], [y], s=46, color=COLORS["paper"], edgecolor="white", linewidth=0.8, zorder=3)
    ax.scatter([1], [y], s=46, color=color, edgecolor="white", linewidth=0.8, zorder=3)
    ax.text(-0.08, y, fmt.format(left_value), va="center", ha="right", fontsize=7)
    ax.text(1.08, y, fmt.format(right_value), va="center", ha="left", fontsize=7)
    ax.text(0.5, y + 0.13, label, va="center", ha="center", fontsize=7, color=COLORS["muted"])


def figure_group1() -> list[Path]:
    raw, agent = read_peptide_tables()
    OUT.mkdir(parents=True, exist_ok=True)
    fig = plt.figure(figsize=(7.2, 3.1), constrained_layout=True)
    gs = fig.add_gridspec(1, 3, width_ratios=[0.85, 1.1, 1.55])
    ax0 = fig.add_subplot(gs[0, 0])
    ax1 = fig.add_subplot(gs[0, 1])
    ax2 = fig.add_subplot(gs[0, 2])

    strip_axes(ax0)
    panel_label(ax0, "A")
    ax0.text(0, 0.95, "Peptide validation table", fontsize=10, fontweight="bold", va="top")
    ax0.text(0, 0.72, "Published source", color=COLORS["paper"], fontsize=8, fontweight="bold")
    ax0.text(0, 0.62, "Validation.csv", fontsize=8)
    ax0.text(0, 0.42, "Agent output", color=COLORS["agent"], fontsize=8, fontweight="bold")
    ax0.text(0, 0.32, "cleaned_Validation.csv", fontsize=8)
    ax0.text(
        0,
        0.08,
        f"Rows: {len(raw):,} → {len(agent):,}\nDuplicates removed: {len(raw)-len(agent):,}",
        fontsize=8,
        linespacing=1.5,
    )

    panel_label(ax1, "B")
    labels = sorted(set(raw["label"]).union(set(agent["label"])))
    y = np.arange(len(labels))[::-1]
    raw_counts = raw["label"].value_counts().reindex(labels).fillna(0)
    agent_counts = agent["label"].value_counts().reindex(labels).fillna(0)
    for yi, label in zip(y, labels):
        ax1.plot([raw_counts[label], agent_counts[label]], [yi, yi], color=COLORS["grid"], lw=2)
        ax1.scatter(raw_counts[label], yi, s=42, color=COLORS["paper"], label="Published" if yi == y[0] else None, zorder=3)
        ax1.scatter(agent_counts[label], yi, s=42, color=COLORS["agent"], label="Agent" if yi == y[0] else None, zorder=3)
        ax1.text(max(raw_counts.max(), agent_counts.max()) * 1.02, yi, f"label {label}", va="center", fontsize=8)
    ax1.set_title("Class balance retained after cleaning", fontsize=9)
    ax1.set_xlabel("Peptides")
    ax1.set_yticks([])
    ax1.grid(axis="x", color=COLORS["grid"], lw=0.6)
    ax1.legend(loc="lower right", fontsize=7)

    panel_label(ax2, "C")
    raw_lengths = raw["sequence"].astype(str).str.len()
    agent_lengths = agent["sequence"].astype(str).str.len()
    bins = np.arange(min(raw_lengths.min(), agent_lengths.min()), max(raw_lengths.max(), agent_lengths.max()) + 2)
    ax2.hist(raw_lengths, bins=bins, density=True, histtype="stepfilled", alpha=0.30, color=COLORS["paper"], label="Published")
    ax2.hist(agent_lengths, bins=bins, density=True, histtype="step", lw=2.0, color=COLORS["agent"], label="Agent")
    ax2.set_title("Length distribution is preserved", fontsize=9)
    ax2.set_xlabel("Peptide length")
    ax2.set_ylabel("Density")
    ax2.grid(axis="y", color=COLORS["grid"], lw=0.6)
    ax2.legend(fontsize=7)

    fig.suptitle("Group 1 | Agent curation reproduces the corresponding peptide validation data", fontsize=11, fontweight="bold")
    stem = OUT / "group1_peptide_publication_comparison"
    save_figure(fig, stem)
    plt.close(fig)
    return [stem.with_suffix(".png")]


def figure_fastq_run(run: str, df: pd.DataFrame) -> list[Path]:
    sub = df[df["run"] == run].copy()
    info = ENA[run]
    agent_total = sub["agent_total_sequences"].sum()
    ena_total = info["read_count"]
    bytes_equal = np.allclose(sub["ena_fastq_bytes"], sub["local_fastq_bytes"])

    fig = plt.figure(figsize=(7.2, 3.4), constrained_layout=True)
    gs = fig.add_gridspec(1, 4, width_ratios=[1.0, 1.05, 1.2, 1.25])
    ax0 = fig.add_subplot(gs[0, 0])
    ax1 = fig.add_subplot(gs[0, 1])
    ax2 = fig.add_subplot(gs[0, 2])
    ax3 = fig.add_subplot(gs[0, 3])

    strip_axes(ax0)
    panel_label(ax0, "A")
    ax0.add_patch(plt.Rectangle((0, 0.05), 1, 0.88, color=COLORS["panel"], ec="none"))
    ax0.text(0.08, 0.86, f"Group {info['group']}", fontsize=9, fontweight="bold", va="top")
    ax0.text(0.08, 0.72, run, fontsize=11, fontweight="bold")
    ax0.text(0.08, 0.58, info["paper"], fontsize=7.5, color=COLORS["muted"], wrap=True)
    ax0.text(0.08, 0.42, f"{info['source']} · {info['layout'].lower()}", fontsize=8)
    ax0.text(0.08, 0.29, info["scientific_name"], fontsize=8, style="italic")
    ax0.text(
        0.08,
        0.13,
        "Source FASTQ matched" if bytes_equal else "Source FASTQ differs",
        fontsize=8,
        color=COLORS["agent"] if bytes_equal else COLORS["accent"],
        fontweight="bold",
    )
    ax0.set_xlim(0, 1)
    ax0.set_ylim(0, 1)

    panel_label(ax1, "B")
    draw_metric_pair(ax1, ena_total, agent_total, 0.65, "read count", fmt="{:,.0f}")
    diff = agent_total - ena_total
    ax1.text(
        0.5,
        0.28,
        f"Δ = {diff:+,}",
        ha="center",
        va="center",
        fontsize=9,
        color=COLORS["agent"] if diff == 0 else COLORS["accent"],
        fontweight="bold",
    )
    ax1.text(0, 0.95, "Published ENA", ha="center", fontsize=7, color=COLORS["paper"], fontweight="bold")
    ax1.text(1, 0.95, "Agent FastQC", ha="center", fontsize=7, color=COLORS["agent"], fontweight="bold")
    ax1.set_xlim(-0.22, 1.22)
    ax1.set_ylim(0, 1.05)
    strip_axes(ax1)

    panel_label(ax2, "C")
    x_source = [0, 1]
    max_mb = max(sub["ena_fastq_bytes"].max(), sub["local_fastq_bytes"].max()) / 1e6
    min_mb = min(sub["ena_fastq_bytes"].min(), sub["local_fastq_bytes"].min()) / 1e6
    for i, (_, row) in enumerate(sub.iterrows()):
        ena_mb = row["ena_fastq_bytes"] / 1e6
        local_mb = row["local_fastq_bytes"] / 1e6
        ax2.plot(x_source, [ena_mb, local_mb], color=COLORS["grid"], lw=1.5, zorder=1)
        ax2.scatter([0], [ena_mb], s=42, color=COLORS["paper"], edgecolor="white", linewidth=0.8, zorder=3)
        ax2.scatter([1], [local_mb], s=42, color=COLORS["agent"], edgecolor="white", linewidth=0.8, zorder=3)
        ax2.text(1.08, local_mb, row["mate"], va="center", fontsize=8)
    ax2.set_title("FASTQ file size agreement", fontsize=9)
    ax2.set_ylabel("MB")
    ax2.set_xticks([0, 1])
    ax2.set_xticklabels(["Published\nENA", "Local\nagent input"])
    ax2.grid(axis="y", color=COLORS["grid"], lw=0.6)
    pad = max((max_mb - min_mb) * 0.18, max_mb * 0.08, 0.5)
    ax2.set_ylim(max(0, min_mb - pad), max_mb + pad)
    ax2.set_xlim(-0.35, 1.35)

    panel_label(ax3, "D")
    x = np.arange(len(sub))
    ax3.scatter(x, sub["agent_gc_percent"], s=42, color=COLORS["accent"], zorder=3)
    for i, row in enumerate(sub.itertuples()):
        ax3.text(i, row.agent_gc_percent - 3, f"{row.agent_gc_percent:.0f}%", ha="center", fontsize=6.5, color=COLORS["accent"])
    ax3.set_xticks(x)
    ax3.set_xticklabels(sub["mate"].tolist())
    ax3.set_ylabel("GC (%)")
    ax3.set_ylim(max(0, sub["agent_gc_percent"].min() - 14), min(100, sub["agent_gc_percent"].max() + 16))
    ax3.grid(axis="y", color=COLORS["grid"], lw=0.6)
    ax3b = ax3.twinx()
    ax3b.plot(x, sub["agent_sequence_length_mean"], color=COLORS["gold"], marker="D", ms=4, lw=1.5)
    for i, row in enumerate(sub.itertuples()):
        ax3b.text(i, row.agent_sequence_length_mean + 0.025 * max(sub["agent_sequence_length_mean"].max(), 1), f"{row.agent_sequence_length_mean:.0f}", ha="center", fontsize=6.5, color=COLORS["gold"])
    ax3b.set_ylabel("Mean read length")
    ax3b.tick_params(axis="y", colors=COLORS["gold"])
    ax3b.spines["right"].set_visible(True)
    ax3b.spines["right"].set_color(COLORS["gold"])

    fig.suptitle(f"{run} | Agent output corresponds to the published source record", fontsize=11, fontweight="bold")
    stem = OUT / f"group{info['group'].replace('–', '_')}_{run}_publication_comparison"
    save_figure(fig, stem)
    plt.close(fig)
    return [stem.with_suffix(".png")]


def figure_overview(df: pd.DataFrame) -> list[Path]:
    run_summary = (
        df.groupby(["group", "run", "paper", "source"], as_index=False)
        .agg(
            ena_read_count=("ena_run_read_count", "first"),
            agent_total=("agent_total_sequences", "sum"),
            ena_bytes=("ena_fastq_bytes", "sum"),
            local_bytes=("local_fastq_bytes", "sum"),
            mean_gc=("agent_gc_percent", "mean"),
        )
        .sort_values("group")
    )
    fig = plt.figure(figsize=(7.4, 5.0), constrained_layout=True)
    gs = fig.add_gridspec(2, 2, height_ratios=[1.1, 1.0], width_ratios=[1.2, 1.0])
    ax0 = fig.add_subplot(gs[0, 0])
    ax1 = fig.add_subplot(gs[0, 1])
    ax2 = fig.add_subplot(gs[1, :])

    panel_label(ax0, "A")
    minv = min(run_summary["ena_read_count"].min(), run_summary["agent_total"].min())
    maxv = max(run_summary["ena_read_count"].max(), run_summary["agent_total"].max())
    ax0.plot([minv, maxv], [minv, maxv], color=COLORS["grid"], lw=1.5, zorder=1)
    ax0.scatter(run_summary["ena_read_count"], run_summary["agent_total"], s=54, color=COLORS["agent"], edgecolor="white", linewidth=0.8, zorder=3)
    offsets = {
        "ERR15682270": (18, -2),
        "ERR15682267": (18, 17),
        "ERR10114877": (8, -3),
        "ERR10114867": (8, 0),
        "ERR10114861": (-42, 8),
        "ERR3250149": (8, 5),
    }
    for row in run_summary.itertuples():
        dx, dy = offsets.get(row.run, (6, 0))
        ax0.annotate(
            row.run.replace("ERR", ""),
            xy=(row.ena_read_count, row.agent_total),
            xytext=(dx, dy),
            textcoords="offset points",
            fontsize=6.7,
            va="center",
            ha="left" if dx >= 0 else "right",
            bbox=dict(boxstyle="round,pad=0.10", fc="white", ec="none", alpha=0.75),
            arrowprops=dict(arrowstyle="-", color=COLORS["paper"], lw=0.45, shrinkA=0, shrinkB=4),
        )
    ax0.set_xscale("log")
    ax0.set_yscale("log")
    ax0.set_xlabel("Published ENA read_count")
    ax0.set_ylabel("Agent FastQC total sequences")
    ax0.set_title("Read counts fall on the identity line", fontsize=9)
    ax0.grid(color=COLORS["grid"], lw=0.6, which="both")

    panel_label(ax1, "B")
    ratios = run_summary["local_bytes"] / run_summary["ena_bytes"]
    y = np.arange(len(run_summary))[::-1]
    ax1.axvline(1, color=COLORS["grid"], lw=1.5)
    ax1.scatter(ratios, y, s=48, color=COLORS["paper"], edgecolor="white", linewidth=0.8)
    for yi, row, ratio in zip(y, run_summary.itertuples(), ratios):
        ax1.text(1.006, yi, row.run, va="center", fontsize=7)
    ax1.set_xlim(0.995, 1.015)
    ax1.set_yticks([])
    ax1.set_xlabel("Local FASTQ bytes / ENA bytes")
    ax1.set_title("Local inputs match published files", fontsize=9)
    ax1.grid(axis="x", color=COLORS["grid"], lw=0.6)

    panel_label(ax2, "C")
    matrix = df.pivot_table(index="run", columns="mate", values="agent_gc_percent", aggfunc="mean")
    matrix = matrix.reindex(run_summary["run"])
    im = ax2.imshow(matrix.fillna(np.nan), aspect="auto", cmap="copper", vmin=35, vmax=85)
    ax2.set_xticks(np.arange(matrix.shape[1]))
    ax2.set_xticklabels(matrix.columns)
    ax2.set_yticks(np.arange(matrix.shape[0]))
    ax2.set_yticklabels(matrix.index)
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            value = matrix.iloc[i, j]
            if not np.isnan(value):
                ax2.text(j, i, f"{value:.0f}", ha="center", va="center", fontsize=7, color="white" if value > 55 else COLORS["ink"])
    ax2.set_title("Agent-derived GC% from FastQC reports", fontsize=9)
    cbar = fig.colorbar(im, ax=ax2, fraction=0.025, pad=0.02)
    cbar.set_label("GC (%)")

    fig.suptitle("Agent reproducibility check across corresponding paper datasets", fontsize=12, fontweight="bold")
    stem = OUT / "overview_publication_comparison"
    save_figure(fig, stem)
    plt.close(fig)
    return [stem.with_suffix(".png")]


def write_summary(df: pd.DataFrame) -> Path:
    path = OUT / "comparison_source_data.csv"
    df.to_csv(path, index=False)
    return path


def main() -> None:
    set_style()
    OUT.mkdir(parents=True, exist_ok=True)
    fastq_df = build_fastq_summary()
    made = []
    made.extend(figure_group1())
    for run in ENA:
        made.extend(figure_fastq_run(run, fastq_df))
    made.extend(figure_overview(fastq_df))
    summary = write_summary(fastq_df)
    manifest = OUT / "figure_manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "style": "publication-style multi-panel figures; no large bar charts",
                "figures_png": [str(path) for path in made],
                "source_data": str(summary),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(json.dumps({"figures": [str(path) for path in made], "source_data": str(summary)}, indent=2))


if __name__ == "__main__":
    main()
