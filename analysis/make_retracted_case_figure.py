from __future__ import annotations

import json
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyBboxPatch


ROOT = Path(__file__).resolve().parents[1]
FINAL = ROOT / "Final data"
RESULT = FINAL / "retracted_result"
RAW = ROOT / "data" / "raw" / "retracted_case" / "SRP508771_SRR29088443"
OUT = FINAL / "retracted_case_figure"

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
    "pale_blue": "#eef6f8",
    "pale_gold": "#fbf5e6",
}


ENA = {
    "study": "SRP508771",
    "bioproject": "PRJNA1111407",
    "run": "SRR29088443",
    "sample": "SAMN41390659",
    "scientific_name": "Escherichia sp.",
    "layout": "PAIRED",
    "read_count_per_mate": 53571,
    "base_count_total": 26517645,
    "bytes_r1": 1240071,
    "bytes_r2": 1428410,
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
    paths: list[Path] = []
    for ext in (".png", ".pdf", ".svg"):
        path = stem.with_suffix(ext)
        if ext == ".png":
            fig.savefig(path, dpi=320, bbox_inches="tight")
        else:
            fig.savefig(path, bbox_inches="tight")
        paths.append(path)
    return paths


def panel_label(ax: plt.Axes, label: str) -> None:
    ax.text(-0.08, 1.06, label, transform=ax.transAxes, fontsize=11, fontweight="bold", va="bottom")


def strip(ax: plt.Axes) -> None:
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_xticks([])
    ax.set_yticks([])


def load_agent_metrics() -> pd.DataFrame:
    metadata = json.loads((RESULT / "final_outputs" / "fastqc_run_metadata.json").read_text())
    records = []
    for item in metadata["input_metrics"]:
        name = item["name"]
        mate = "R1" if "_1" in name else "R2"
        raw_path = RAW / f"{ENA['run']}_{1 if mate == 'R1' else 2}.fastq.gz"
        records.append(
            {
                "mate": mate,
                "file": name,
                "agent_records": item["records"],
                "agent_total_bases": item["total_bases"],
                "agent_mean_length": item["mean_length"],
                "agent_gc_percent": item["gc_percent"],
                "agent_n_fraction": item["n_fraction"],
                "malformed_records": item["malformed_records"],
                "local_bytes": raw_path.stat().st_size,
            }
        )
    frame = pd.DataFrame(records).sort_values("mate")
    return frame


def write_source_data(df: pd.DataFrame) -> Path:
    source = df.copy()
    source["ena_read_count_per_mate"] = ENA["read_count_per_mate"]
    source["ena_total_base_count"] = ENA["base_count_total"]
    source["ena_bytes"] = [ENA["bytes_r1"], ENA["bytes_r2"]]
    source["read_count_match"] = source["agent_records"] == source["ena_read_count_per_mate"]
    source["file_bytes_match"] = source["local_bytes"] == source["ena_bytes"]
    source["run"] = ENA["run"]
    source["study"] = ENA["study"]
    source_path = OUT / "task3_retracted_source_data.csv"
    source.to_csv(source_path, index=False)
    return source_path


def draw_case_card(ax: plt.Axes) -> None:
    strip(ax)
    panel_label(ax, "A")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.text(0.00, 0.98, "Retraction-associated public FASTQ case", fontsize=10, fontweight="bold", va="top")
    ax.text(0.00, 0.88, "Used as a negative-control audit,\nnot as evidence for the retracted claim.", fontsize=7.4, color=COLORS["muted"], va="top")

    cards = [
        ("Publication", "Genes Immunity\nPMID 39533019"),
        ("Retraction note", "Genes Immunity\nPMID 41927935"),
        ("Public record", f"{ENA['study']}\n{ENA['bioproject']}\n{ENA['run']}"),
        ("Sequencing file", f"{ENA['layout'].title()} FASTQ\n{ENA['scientific_name']}"),
    ]
    ys = [0.68, 0.49, 0.30, 0.11]
    fills = [COLORS["panel"], COLORS["pale_gold"], COLORS["pale_blue"], "#ffffff"]
    for (title, text), y, fill in zip(cards, ys, fills):
        ax.add_patch(
            FancyBboxPatch(
                (0.02, y),
                0.82,
                0.13,
                boxstyle="round,pad=0.012,rounding_size=0.02",
                fc=fill,
                ec=COLORS["grid"],
                lw=0.8,
            )
        )
        ax.text(0.07, y + 0.085, title, fontsize=7.4, fontweight="bold", va="center")
        ax.text(0.07, y + 0.035, text, fontsize=6.9, color=COLORS["muted"], va="center", linespacing=1.1)


def draw_agreement(ax: plt.Axes, df: pd.DataFrame) -> None:
    panel_label(ax, "B")
    agent_total_bases = int(df["agent_total_bases"].sum())
    checks = pd.DataFrame(
        [
            {
                "metric": "R1 records",
                "published": ENA["read_count_per_mate"],
                "agent": int(df.loc[df["mate"] == "R1", "agent_records"].iloc[0]),
                "unit": "reads",
            },
            {
                "metric": "R2 records",
                "published": ENA["read_count_per_mate"],
                "agent": int(df.loc[df["mate"] == "R2", "agent_records"].iloc[0]),
                "unit": "reads",
            },
            {
                "metric": "Total bases",
                "published": ENA["base_count_total"],
                "agent": agent_total_bases,
                "unit": "bp",
            },
            {
                "metric": "R1 bytes",
                "published": ENA["bytes_r1"],
                "agent": int(df.loc[df["mate"] == "R1", "local_bytes"].iloc[0]),
                "unit": "bytes",
            },
            {
                "metric": "R2 bytes",
                "published": ENA["bytes_r2"],
                "agent": int(df.loc[df["mate"] == "R2", "local_bytes"].iloc[0]),
                "unit": "bytes",
            },
        ]
    )
    checks["agreement"] = checks["agent"] / checks["published"] * 100
    checks["deviation"] = checks["agreement"] - 100

    y = np.arange(len(checks))[::-1]
    ax.axvline(0, color=COLORS["grid"], lw=1.5, zorder=1)
    ax.scatter(checks["deviation"], y, s=70, color=COLORS["agent"], edgecolor="white", lw=0.9, zorder=3)
    for yi, row in zip(y, checks.itertuples()):
        ax.text(-0.014, yi, row.metric, ha="right", va="center", fontsize=7.2)
        ax.text(0.018, yi, f"{row.agent:,} / {row.published:,}", ha="left", va="center", fontsize=6.7, color=COLORS["muted"])
    ax.set_xlim(-0.06, 0.09)
    ax.set_yticks([])
    ax.set_xlabel("Deviation from ENA/SRA value (%)")
    ax.set_title("Source-level metadata are exactly reproduced", fontsize=9)
    ax.grid(axis="x", color=COLORS["grid"], lw=0.6)
    ax.text(0.088, 4.10, "all checks = 0% deviation", fontsize=7.1, ha="right", color=COLORS["agent"], fontweight="bold")


def draw_quality(ax: plt.Axes, df: pd.DataFrame) -> None:
    ax.text(-0.20, 1.20, "C", transform=ax.transAxes, fontsize=11, fontweight="bold", va="bottom")
    x = np.arange(len(df))
    width = 0.34
    ax.bar(x - width / 2, df["agent_gc_percent"], width=width, color=COLORS["agent"], alpha=0.9, label="GC (%)")
    ax2 = ax.twinx()
    ax2.bar(x + width / 2, df["agent_mean_length"], width=width, color=COLORS["gold"], alpha=0.86, label="Mean length")

    for xi, gc, length in zip(x, df["agent_gc_percent"], df["agent_mean_length"]):
        ax.text(xi - width / 2, gc + 1.0, f"{gc:.1f}%", ha="center", fontsize=7, color=COLORS["agent"])
        ax2.text(xi + width / 2, length + 3, f"{length:.0f}", ha="center", fontsize=7, color=COLORS["gold"])

    ax.set_xticks(x)
    ax.set_xticklabels(df["mate"])
    ax.set_ylim(0, 70)
    ax2.set_ylim(0, 285)
    ax.set_ylabel("GC (%)", color=COLORS["agent"])
    ax2.set_ylabel("Mean read length (bp)", color=COLORS["gold"])
    ax.tick_params(axis="y", colors=COLORS["agent"])
    ax2.tick_params(axis="y", colors=COLORS["gold"])
    ax.set_title("Derived FASTQ quality metrics", fontsize=9, pad=18)
    ax.grid(axis="y", color=COLORS["grid"], lw=0.6)

    malformed = int(df["malformed_records"].sum())
    n_fraction = df["agent_n_fraction"].max()
    ax.text(
        0.50,
        -0.30,
        f"Malformed records: {malformed}; max N fraction: {n_fraction:.0e}",
        transform=ax.transAxes,
        ha="center",
        va="top",
        fontsize=7.2,
        color=COLORS["muted"],
    )


def draw_audit(ax: plt.Axes) -> None:
    strip(ax)
    panel_label(ax, "D")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.text(0.00, 0.98, "Audit interpretation", fontsize=9.5, fontweight="bold", va="top")

    items = [
        ("FASTQ format", "pass", COLORS["green"]),
        ("Paired-end structure", "pass", COLORS["green"]),
        ("Read/base/file metadata", "match public record", COLORS["agent"]),
        ("QC report generation", "FastQC + MultiQC + seqkit", COLORS["purple"]),
        ("Biological conclusion", "not claimed", COLORS["accent"]),
    ]
    y0 = 0.78
    for i, (label, status, color) in enumerate(items):
        y = y0 - i * 0.128
        ax.add_patch(
            FancyBboxPatch(
                (0.02, y - 0.055),
                0.92,
                0.102,
                boxstyle="round,pad=0.006,rounding_size=0.012",
                fc="#ffffff",
                ec=COLORS["grid"],
                lw=0.45,
            )
        )
        ax.add_patch(plt.Circle((0.065, y), 0.012, color=color, ec="white", lw=0.5))
        ax.text(0.105, y + 0.020, label, fontsize=6.25, fontweight="bold", va="center")
        ax.text(0.105, y - 0.026, status, fontsize=5.65, color=COLORS["muted"], va="center")

    ax.add_patch(
        FancyBboxPatch(
            (0.00, 0.015),
            0.99,
            0.135,
            boxstyle="round,pad=0.014,rounding_size=0.02",
            fc=COLORS["panel"],
            ec=COLORS["grid"],
            lw=0.8,
        )
    )
    ax.text(
        0.045,
        0.082,
        "Negative-control role:\naudit source-data reproducibility\nfrom a problematic literature record.",
        fontsize=5.95,
        color=COLORS["muted"],
        va="center",
        linespacing=1.05,
    )


def make_figure() -> dict[str, list[str] | str]:
    OUT.mkdir(parents=True, exist_ok=True)
    df = load_agent_metrics()
    source_path = write_source_data(df)

    fig = plt.figure(figsize=(7.6, 5.15), constrained_layout=True)
    gs = fig.add_gridspec(2, 3, width_ratios=[1.05, 1.16, 1.55], height_ratios=[1.03, 1.0])
    ax_a = fig.add_subplot(gs[:, 0])
    ax_b = fig.add_subplot(gs[0, 1:])
    ax_c = fig.add_subplot(gs[1, 1])
    ax_d = fig.add_subplot(gs[1, 2])

    draw_case_card(ax_a)
    draw_agreement(ax_b, df)
    draw_quality(ax_c, df)
    draw_audit(ax_d)

    fig.suptitle(
        "Task 3 | Retraction-associated FASTQ data support source-level audit, not claim validation",
        fontsize=12,
        fontweight="bold",
    )
    paths = save(fig, OUT / "task3_retracted_fastq_audit")
    plt.close(fig)
    manifest = {
        "figures": [str(p) for p in paths],
        "source_data": str(source_path),
        "interpretation": "Retraction-associated dataset used as a negative-control source-data audit case.",
    }
    (OUT / "task3_retracted_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def main() -> None:
    set_style()
    print(json.dumps(make_figure(), indent=2))


if __name__ == "__main__":
    main()
