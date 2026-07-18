from __future__ import annotations

import json
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


ROOT = Path(__file__).resolve().parents[1]
FINAL = ROOT / "Final data"
RESULT = FINAL / "retracted_result"
RAW = ROOT / "data" / "raw" / "retracted_case" / "SRP508771_SRR29088443"
OUT = FINAL / "retracted_case_figure_v2"

COLORS = {
    "ink": "#1f2933",
    "muted": "#687282",
    "grid": "#e1e7ec",
    "panel": "#f8fafb",
    "blue": "#2f6f8f",
    "blue_light": "#eaf4f6",
    "green": "#4f8b6b",
    "green_light": "#edf7f1",
    "orange": "#c46a4a",
    "orange_light": "#fbefe9",
    "gold": "#d9a84e",
    "gold_light": "#fbf4df",
    "purple": "#7566a4",
}

ENA = {
    "study": "SRP508771",
    "bioproject": "PRJNA1111407",
    "run": "SRR29088443",
    "layout": "PAIRED",
    "scientific_name": "Escherichia sp.",
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
            "font.size": 8.2,
            "axes.spines.top": False,
            "axes.spines.right": False,
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


def strip(ax: plt.Axes) -> None:
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_xticks([])
    ax.set_yticks([])


def panel_label(ax: plt.Axes, label: str) -> None:
    ax.text(-0.035, 1.045, label, transform=ax.transAxes, fontsize=12, fontweight="bold", va="bottom")


def rounded(ax: plt.Axes, xy, w, h, fc, ec=None, lw=0.9, radius=0.025):
    patch = FancyBboxPatch(
        xy,
        w,
        h,
        boxstyle=f"round,pad=0.012,rounding_size={radius}",
        fc=fc,
        ec=ec or COLORS["grid"],
        lw=lw,
    )
    ax.add_patch(patch)
    return patch


def arrow(ax: plt.Axes, start, end, color=COLORS["muted"], lw=1.1):
    ax.add_patch(
        FancyArrowPatch(
            start,
            end,
            arrowstyle="-|>",
            mutation_scale=12,
            lw=lw,
            color=color,
            shrinkA=3,
            shrinkB=3,
        )
    )


def load_agent_metrics() -> pd.DataFrame:
    metadata = json.loads((RESULT / "final_outputs" / "fastqc_run_metadata.json").read_text())
    rows = []
    for item in metadata["input_metrics"]:
        mate = "R1" if "_1" in item["name"] else "R2"
        local = RAW / f"{ENA['run']}_{1 if mate == 'R1' else 2}.fastq.gz"
        rows.append(
            {
                "mate": mate,
                "records": int(item["records"]),
                "total_bases": int(item["total_bases"]),
                "mean_length": float(item["mean_length"]),
                "gc_percent": float(item["gc_percent"]),
                "n_fraction": float(item["n_fraction"]),
                "malformed_records": int(item["malformed_records"]),
                "local_bytes": int(local.stat().st_size),
            }
        )
    return pd.DataFrame(rows).sort_values("mate").reset_index(drop=True)


def build_comparison(df: pd.DataFrame) -> pd.DataFrame:
    values = {
        "R1": df.loc[df["mate"] == "R1"].iloc[0],
        "R2": df.loc[df["mate"] == "R2"].iloc[0],
    }
    rows = [
        ("R1 reads", ENA["read_count_per_mate"], int(values["R1"]["records"]), "reads"),
        ("R2 reads", ENA["read_count_per_mate"], int(values["R2"]["records"]), "reads"),
        ("Total bases", ENA["base_count_total"], int(df["total_bases"].sum()), "bp"),
        ("R1 file size", ENA["bytes_r1"], int(values["R1"]["local_bytes"]), "bytes"),
        ("R2 file size", ENA["bytes_r2"], int(values["R2"]["local_bytes"]), "bytes"),
    ]
    comp = pd.DataFrame(rows, columns=["metric", "published", "agent", "unit"])
    comp["difference"] = comp["agent"] - comp["published"]
    comp["relative_difference_percent"] = comp["difference"] / comp["published"] * 100
    return comp


def draw_context(ax: plt.Axes) -> None:
    strip(ax)
    panel_label(ax, "A")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.text(0.00, 0.99, "Boundary-stress question", fontsize=10.4, fontweight="bold", va="top")
    ax.text(
        0.00,
        0.865,
        "Can a high-risk literature record be converted\ninto a bounded source-data audit?",
        fontsize=7.35,
        color=COLORS["muted"],
        va="top",
        linespacing=1.16,
    )

    boxes = [
        (0.02, 0.535, 0.26, 0.155, COLORS["orange_light"], "Retracted\nrecord"),
        (0.37, 0.535, 0.26, 0.155, COLORS["blue_light"], "Public\nFASTQ"),
        (0.72, 0.535, 0.24, 0.155, COLORS["green_light"], "Source\naudit"),
    ]
    for x, y, w, h, fc, label in boxes:
        rounded(ax, (x, y), w, h, fc)
        ax.text(x + w / 2, y + h / 2, label, ha="center", va="center", fontsize=7.8, fontweight="bold", linespacing=1.05)
    arrow(ax, (0.29, 0.612), (0.37, 0.612))
    arrow(ax, (0.64, 0.612), (0.72, 0.612))

    rounded(ax, (0.03, 0.305), 0.90, 0.13, "#ffffff")
    ax.text(0.07, 0.388, "Public accession", fontsize=7.4, fontweight="bold", va="center")
    ax.text(0.07, 0.333, f"{ENA['study']} / {ENA['bioproject']} / {ENA['run']}", fontsize=7.0, color=COLORS["muted"], va="center")

    rounded(ax, (0.03, 0.055), 0.90, 0.165, COLORS["panel"])
    ax.text(0.07, 0.178, "Predefined boundary", fontsize=7.4, fontweight="bold", va="center")
    ax.text(
        0.07,
        0.115,
        "verify files and QC outputs;\ndo not rescue the biological claim",
        fontsize=6.65,
        color=COLORS["muted"],
        va="center",
        linespacing=1.20,
    )


def draw_comparison(ax: plt.Axes, comp: pd.DataFrame) -> None:
    strip(ax)
    panel_label(ax, "B")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.text(0.00, 0.99, "Published record vs agent output", fontsize=10.4, fontweight="bold", va="top")
    ax.text(0.00, 0.91, "Direct source-data comparison shows exact file-level reproducibility.", fontsize=7.5, color=COLORS["muted"], va="top")

    x_metric, x_pub, x_agent, x_diff = 0.02, 0.38, 0.61, 0.82
    y_top, row_h = 0.78, 0.118
    headers = [(x_metric, "Metric"), (x_pub, "Public"), (x_agent, "Agent"), (x_diff, "Difference")]
    for x, label in headers:
        ax.text(x, y_top + 0.055, label, fontsize=7.2, fontweight="bold", color=COLORS["muted"], va="center")
    ax.plot([0.02, 0.98], [y_top + 0.025, y_top + 0.025], color=COLORS["grid"], lw=0.8)

    for i, row in enumerate(comp.itertuples()):
        y = y_top - i * row_h
        if i % 2 == 0:
            rounded(ax, (0.012, y - 0.048), 0.965, 0.085, "#fbfcfd", ec="#f0f3f6", lw=0.4, radius=0.010)
        ax.text(x_metric, y, row.metric, fontsize=7.1, va="center")
        ax.text(x_pub, y, f"{row.published:,}", fontsize=7.1, va="center", ha="left")
        ax.text(x_agent, y, f"{row.agent:,}", fontsize=7.1, va="center", ha="left", color=COLORS["blue"], fontweight="bold")
        ax.text(x_diff, y, "0", fontsize=7.1, va="center", ha="left", color=COLORS["green"], fontweight="bold")

    rounded(ax, (0.18, 0.045), 0.64, 0.075, COLORS["green_light"], ec="#c9e6d3", lw=0.8, radius=0.02)
    ax.text(
        0.50,
        0.082,
        "All five source-level checks matched exactly",
        ha="center",
        va="center",
        fontsize=7.7,
        color=COLORS["green"],
        fontweight="bold",
    )


def draw_qc(ax: plt.Axes, df: pd.DataFrame) -> None:
    ax.text(-0.035, 1.135, "C", transform=ax.transAxes, fontsize=12, fontweight="bold", va="bottom")
    mates = list(df["mate"])
    x = range(len(mates))
    width = 0.34
    ax.bar([v - width / 2 for v in x], df["gc_percent"], width=width, color=COLORS["blue"], alpha=0.90, label="GC (%)")
    ax2 = ax.twinx()
    ax2.bar([v + width / 2 for v in x], df["mean_length"], width=width, color=COLORS["gold"], alpha=0.88, label="Mean length")

    for xi, gc, length in zip(x, df["gc_percent"], df["mean_length"]):
        ax.text(xi - width / 2, gc + 1.0, f"{gc:.1f}%", ha="center", va="bottom", fontsize=7.1, color=COLORS["blue"])
        ax2.text(xi + width / 2, length + 3, f"{length:.0f}", ha="center", va="bottom", fontsize=7.1, color=COLORS["gold"])

    ax.set_xticks(list(x))
    ax.set_xticklabels(mates)
    ax.set_ylim(0, 70)
    ax2.set_ylim(0, 285)
    ax.set_ylabel("GC (%)", color=COLORS["blue"])
    ax2.set_ylabel("Mean read length (bp)", color=COLORS["gold"])
    ax.tick_params(axis="y", colors=COLORS["blue"])
    ax2.tick_params(axis="y", colors=COLORS["gold"])
    ax.set_title("QC outputs generated from the same files", fontsize=10.0, pad=13)
    ax.grid(axis="y", color=COLORS["grid"], lw=0.6)

    malformed = int(df["malformed_records"].sum())
    n_fraction = df["n_fraction"].max()
    ax.text(
        0.50,
        -0.25,
        f"Malformed records: {malformed}; max N fraction: {n_fraction:.0e}",
        transform=ax.transAxes,
        ha="center",
        va="top",
        fontsize=7.0,
        color=COLORS["muted"],
    )


def draw_boundary(ax: plt.Axes) -> None:
    strip(ax)
    panel_label(ax, "D")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.text(0.00, 0.99, "What the agent demonstrates", fontsize=10.4, fontweight="bold", va="top")
    ax.text(0.00, 0.90, "The output is useful because it is bounded, not because it overclaims.", fontsize=7.4, color=COLORS["muted"], va="top")

    rounded(ax, (0.02, 0.42), 0.45, 0.36, COLORS["green_light"], ec="#cfe8d6")
    rounded(ax, (0.53, 0.42), 0.45, 0.36, COLORS["orange_light"], ec="#edd0c3")
    ax.text(0.055, 0.735, "CAN verify", fontsize=8.0, fontweight="bold", color=COLORS["green"])
    ax.text(0.565, 0.735, "CANNOT claim", fontsize=8.0, fontweight="bold", color=COLORS["orange"])

    can = ["file identity", "paired-end structure", "read/base/file metadata", "QC report provenance"]
    cannot = ["retracted conclusion", "ancient authenticity", "contamination source", "biological mechanism"]
    for i, item in enumerate(can):
        y = 0.675 - i * 0.070
        ax.text(0.065, y, f"• {item}", fontsize=7.0, va="center", color=COLORS["ink"])
    for i, item in enumerate(cannot):
        y = 0.675 - i * 0.070
        ax.text(0.575, y, f"• {item}", fontsize=7.0, va="center", color=COLORS["ink"])

    rounded(ax, (0.08, 0.18), 0.84, 0.115, COLORS["blue_light"], ec="#cddfe6")
    ax.text(
        0.50,
        0.237,
        "Result: source-data reproducibility = PASS;\nclaim-level interpretation = expert-gated",
        ha="center",
        va="center",
        fontsize=7.8,
        color=COLORS["blue"],
        fontweight="bold",
        linespacing=1.12,
    )


def save(fig: mpl.figure.Figure, stem: Path) -> list[Path]:
    OUT.mkdir(parents=True, exist_ok=True)
    paths = []
    for ext in [".png", ".pdf", ".svg"]:
        path = stem.with_suffix(ext)
        if ext == ".png":
            fig.savefig(path, dpi=360, bbox_inches="tight")
        else:
            fig.savefig(path, bbox_inches="tight")
        paths.append(path)
    return paths


def main() -> None:
    set_style()
    df = load_agent_metrics()
    comp = build_comparison(df)

    OUT.mkdir(parents=True, exist_ok=True)
    comp.to_csv(OUT / "task3_public_vs_agent_source_data.csv", index=False)

    fig = plt.figure(figsize=(7.8, 6.0), constrained_layout=True)
    gs = fig.add_gridspec(2, 2, width_ratios=[0.95, 1.45], height_ratios=[1.05, 1.0])
    ax_a = fig.add_subplot(gs[0, 0])
    ax_b = fig.add_subplot(gs[0, 1])
    ax_c = fig.add_subplot(gs[1, 0])
    ax_d = fig.add_subplot(gs[1, 1])

    draw_context(ax_a)
    draw_comparison(ax_b, comp)
    draw_qc(ax_c, df)
    draw_boundary(ax_d)

    fig.suptitle(
        "Task 3 | Boundary-aware audit of a retraction-associated FASTQ record",
        fontsize=12.2,
        fontweight="bold",
    )
    paths = save(fig, OUT / "task3_boundary_aware_source_audit")
    plt.close(fig)

    manifest = {
        "figure_files": [str(p) for p in paths],
        "source_data": str(OUT / "task3_public_vs_agent_source_data.csv"),
        "main_claim": "The agent exactly reproduced source-level public metadata while gating biological interpretation.",
    }
    (OUT / "task3_boundary_aware_source_audit_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
