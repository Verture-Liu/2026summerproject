from __future__ import annotations

import json
import shutil
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


ROOT = Path(__file__).resolve().parents[1]
FINAL = ROOT / "Final data"
RAW = ROOT / "data" / "raw" / "reproducibility_cases"
SOURCE_FIGS = FINAL / "comparison_figures"
OUT = FINAL / "manuscript_figures_schemeB"

COLORS = {
    "ink": "#1f2933",
    "muted": "#6b7280",
    "grid": "#e5e7eb",
    "panel": "#f7f8fa",
    "paper": "#9aa6b2",
    "agent": "#2f6f8f",
    "accent": "#c46a4a",
    "gold": "#d8a24a",
    "green": "#5b8f73",
    "purple": "#7b6ca8",
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
    for ext in [".png", ".pdf", ".svg"]:
        path = stem.with_suffix(ext)
        if ext == ".png":
            fig.savefig(path, dpi=320, bbox_inches="tight")
        else:
            fig.savefig(path, bbox_inches="tight")
        paths.append(path)
    return paths


def panel_label(ax, label: str, x: float = -0.06, y: float = 1.06) -> None:
    ax.text(x, y, label, transform=ax.transAxes, fontsize=11, fontweight="bold", va="bottom", ha="left")


def strip(ax) -> None:
    for side in ax.spines:
        ax.spines[side].set_visible(False)
    ax.set_xticks([])
    ax.set_yticks([])


def box(ax, xy, wh, title, subtitle="", fc="white", ec=None, title_color=None) -> None:
    x, y = xy
    w, h = wh
    patch = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.018,rounding_size=0.025",
        fc=fc,
        ec=ec or COLORS["grid"],
        lw=1.0,
    )
    ax.add_patch(patch)
    ax.text(x + w / 2, y + h * 0.62, title, ha="center", va="center", fontsize=8.5, fontweight="bold", color=title_color or COLORS["ink"])
    if subtitle:
        ax.text(x + w / 2, y + h * 0.30, subtitle, ha="center", va="center", fontsize=6.8, color=COLORS["muted"], linespacing=1.25)


def arrow(ax, start, end, color=COLORS["paper"], rad=0.0) -> None:
    ax.add_patch(
        FancyArrowPatch(
            start,
            end,
            arrowstyle="-|>",
            mutation_scale=11,
            lw=1.1,
            color=color,
            connectionstyle=f"arc3,rad={rad}",
        )
    )


def fastq_df() -> pd.DataFrame:
    path = SOURCE_FIGS / "comparison_source_data.csv"
    if not path.exists():
        raise FileNotFoundError(f"Missing source table: {path}")
    return pd.read_csv(path)


def peptide_summary() -> dict[str, int]:
    raw = pd.read_csv(RAW / "case1_amplit_validation" / "Validation.csv", header=None, names=["label", "sequence"])
    cleaned = pd.read_csv(FINAL / "1" / "final_outputs" / "cleaned_Validation.csv")
    return {
        "raw_rows": len(raw),
        "cleaned_rows": len(cleaned),
        "duplicates_removed": len(raw) - len(cleaned),
        "raw_unique_sequences": raw["sequence"].nunique(),
        "cleaned_unique_sequences": cleaned["sequence"].nunique(),
        "label_classes": cleaned["label"].nunique(),
    }


def run_summary(df: pd.DataFrame) -> pd.DataFrame:
    summary = (
        df.groupby(["group", "run", "paper", "source", "layout", "scientific_name"], as_index=False)
        .agg(
            ena_read_count=("ena_run_read_count", "first"),
            agent_total_sequences=("agent_total_sequences", "sum"),
            ena_fastq_bytes=("ena_fastq_bytes", "sum"),
            local_fastq_bytes=("local_fastq_bytes", "sum"),
            mean_gc_percent=("agent_gc_percent", "mean"),
            min_read_length=("agent_sequence_length_mean", "min"),
            max_read_length=("agent_sequence_length_mean", "max"),
        )
        .sort_values("group")
    )
    summary["read_count_delta"] = summary["agent_total_sequences"] - summary["ena_read_count"]
    summary["bytes_ratio"] = summary["local_fastq_bytes"] / summary["ena_fastq_bytes"]
    summary["match_status"] = np.where((summary["read_count_delta"] == 0) & np.isclose(summary["bytes_ratio"], 1.0), "matched", "check")
    return summary


def write_tables(df: pd.DataFrame) -> dict[str, Path]:
    OUT.mkdir(parents=True, exist_ok=True)
    rs = run_summary(df)
    pep = peptide_summary()

    matched = rs[
        [
            "group",
            "run",
            "paper",
            "source",
            "layout",
            "scientific_name",
            "ena_read_count",
            "agent_total_sequences",
            "read_count_delta",
            "ena_fastq_bytes",
            "local_fastq_bytes",
            "bytes_ratio",
            "match_status",
        ]
    ].copy()
    matched.insert(0, "validation_type", "FASTQ source-data reproducibility")

    audit = pd.DataFrame(
        [
            {
                "group": "1",
                "item": "Peptide Validation.csv row count",
                "observed_difference": f"{pep['raw_rows']:,} raw rows -> {pep['cleaned_rows']:,} cleaned rows",
                "interpretation": "Expected change caused by duplicate peptide removal, not a source-data mismatch.",
                "severity": "audited_expected_change",
            },
            {
                "group": "1",
                "item": "Duplicate peptide sequences",
                "observed_difference": f"{pep['duplicates_removed']:,} duplicate rows removed",
                "interpretation": "The agent records the curation step and exports a non-redundant peptide table.",
                "severity": "audited_expected_change",
            },
            {
                "group": "2-9",
                "item": "GC% and read-length values",
                "observed_difference": "Reported by Agent FastQC rather than used as direct paper-reported targets",
                "interpretation": "These are derived QC metrics for auditability; they should not be treated as paper mismatches unless the paper reports the same metric.",
                "severity": "derived_metric",
            },
            {
                "group": "paired FASTQ",
                "item": "R1/R2 file-size and GC differences",
                "observed_difference": "Mate-specific values differ in several paired-end runs",
                "interpretation": "Expected paired-end behavior; reproducibility is judged by source file identity and total read count.",
                "severity": "expected_paired_end_difference",
            },
        ]
    )

    matched_path = OUT / "table_matched_datasets_summary.csv"
    audit_path = OUT / "table_audit_differences_summary.csv"
    matched.to_csv(matched_path, index=False)
    audit.to_csv(audit_path, index=False)
    return {"matched": matched_path, "audit": audit_path}


def figure1_architecture() -> list[Path]:
    fig, ax = plt.subplots(figsize=(7.4, 4.35))
    strip(ax)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    ax.text(0.02, 0.975, "Figure 1 | Natural-language Research Agent architecture", fontsize=12, fontweight="bold", va="top")
    ax.text(0.02, 0.905, "The system converts user intent into validated local workflows with separated final outputs and audit records.", fontsize=8.3, color=COLORS["muted"])

    y = 0.61
    xs = [0.04, 0.22, 0.40, 0.58, 0.76]
    titles = ["User request", "Workflow\nplanner", "Validator", "Skill manager", "Local execution"]
    subs = [
        "natural language\n+ uploaded files",
        "JSON workflow\nwith steps",
        "schema, refs,\nfile formats",
        "peptide, FASTQ,\nQC tools",
        "conda/env-aware\nbioinformatics",
    ]
    colors = [COLORS["panel"], "#eef5f7", "#f4f0fa", "#f7f2e8", "#eef6f1"]
    for x, title, sub, fc in zip(xs, titles, subs, colors):
        box(ax, (x, y), (0.145, 0.18), title, sub, fc=fc)
    for x1, x2 in zip(xs[:-1], xs[1:]):
        arrow(ax, (x1 + 0.145, y + 0.09), (x2, y + 0.09))

    box(ax, (0.18, 0.24), (0.22, 0.18), "Final outputs", "files requested by the user\nclean CSV, QC report, figures", fc="#eef5f7", title_color=COLORS["agent"])
    box(ax, (0.60, 0.24), (0.25, 0.18), "Step outputs + records", "intermediate files, parameters,\nwarnings, hashes, errors", fc="#fff7ed", title_color=COLORS["accent"])
    arrow(ax, (0.83, y), (0.72, 0.42), color=COLORS["accent"], rad=-0.10)
    arrow(ax, (0.78, y), (0.32, 0.42), color=COLORS["agent"], rad=0.12)

    ax.text(0.06, 0.115, "Design principle", fontsize=8.5, fontweight="bold")
    ax.text(0.06, 0.055, "Strict workflow validation reduces model hallucination, while local execution keeps data and environment decisions auditable.", fontsize=8.2, color=COLORS["muted"])
    return save(fig, OUT / "figure1_agent_architecture")


def figure2_dataset_map(df: pd.DataFrame) -> list[Path]:
    rs = run_summary(df)
    pep = peptide_summary()
    fig = plt.figure(figsize=(7.4, 4.4), constrained_layout=True)
    gs = fig.add_gridspec(1, 2, width_ratios=[1.0, 1.45])
    ax0 = fig.add_subplot(gs[0, 0])
    ax1 = fig.add_subplot(gs[0, 1])
    strip(ax0)
    strip(ax1)

    ax0.text(0, 1.00, "Figure 2 | Validation datasets and task coverage", fontsize=12, fontweight="bold", va="top")
    ax0.text(0, 0.86, "Seven validation groups cover two task families:", fontsize=8.5, color=COLORS["muted"])
    box(ax0, (0.02, 0.57), (0.84, 0.18), "Peptide-table curation", f"Group 1\n{pep['raw_rows']:,} raw rows; {pep['duplicates_removed']:,} duplicates audited", fc="#eef5f7", title_color=COLORS["agent"])
    box(ax0, (0.02, 0.30), (0.84, 0.20), "FASTQ source-data QC", f"Groups 2–9\n{len(rs)} public run accessions; {len(df)} FASTQ files", fc="#f7f2e8", title_color=COLORS["gold"])
    ax0.text(0.02, 0.12, "Each dataset was processed by the same local Agent interface but through task-specific skills.", fontsize=8, color=COLORS["muted"], linespacing=1.35)
    ax0.set_xlim(0, 1)
    ax0.set_ylim(0, 1)

    rows = [
        ("1", "Validation.csv", "peptide\nCSV", "curation\n+ stats"),
        *[(r.group, r.run, f"FASTQ\n{r.layout.lower()}", "FastQC\n+ MultiQC") for r in rs.itertuples()],
    ]
    col_x = [0.02, 0.19, 0.51, 0.75]
    headers = ["Group", "Dataset", "Data type", "Agent task"]
    y0 = 0.92
    row_h = 0.095
    ax1.add_patch(plt.Rectangle((0, y0 - 0.04), 1.0, 0.08, color=COLORS["panel"], ec="none"))
    for x, h in zip(col_x, headers):
        ax1.text(x, y0, h, fontsize=7.4, fontweight="bold", va="center")
    for i, row in enumerate(rows):
        y = y0 - (i + 1) * row_h
        if i % 2 == 0:
            ax1.add_patch(plt.Rectangle((0, y - 0.04), 1.0, 0.08, color="#fafafa", ec="none"))
        for x, text in zip(col_x, row):
            ax1.text(x, y, str(text), fontsize=6.8, va="center", color=COLORS["ink"] if i != 0 else COLORS["agent"], linespacing=1.05)
    ax1.set_xlim(0, 1)
    ax1.set_ylim(0.06, 1.02)
    return save(fig, OUT / "figure2_validation_dataset_map")


def figure3_reproducibility_overview() -> list[Path]:
    src_stem = SOURCE_FIGS / "overview_publication_comparison"
    made = []
    for ext in [".png", ".pdf", ".svg"]:
        src = src_stem.with_suffix(ext)
        dst = OUT / f"figure3_reproducibility_overview{ext}"
        shutil.copy2(src, dst)
        made.append(dst)
    return made


def figure4_representative_validation(df: pd.DataFrame) -> list[Path]:
    pep = peptide_summary()
    rs = run_summary(df)
    rep = rs[rs["run"] == "ERR15682270"].iloc[0]
    rep_df = df[df["run"] == "ERR15682270"].copy()

    fig = plt.figure(figsize=(7.4, 4.6), constrained_layout=True)
    gs = fig.add_gridspec(2, 2, height_ratios=[1.0, 1.0])
    ax0 = fig.add_subplot(gs[0, 0])
    ax1 = fig.add_subplot(gs[0, 1])
    ax2 = fig.add_subplot(gs[1, 0])
    ax3 = fig.add_subplot(gs[1, 1])

    panel_label(ax0, "A")
    labels = ["raw rows", "cleaned rows", "unique seq."]
    vals = [pep["raw_rows"], pep["cleaned_rows"], pep["cleaned_unique_sequences"]]
    ax0.plot(range(len(vals)), vals, color=COLORS["grid"], lw=2, zorder=1)
    ax0.scatter(range(len(vals)), vals, s=70, color=[COLORS["paper"], COLORS["agent"], COLORS["green"]], edgecolor="white", linewidth=0.8, zorder=2)
    for i, v in enumerate(vals):
        ax0.text(i, v + max(vals) * 0.04, f"{v:,}", ha="center", fontsize=7.5)
    ax0.set_xticks(range(len(vals)))
    ax0.set_xticklabels(labels)
    ax0.set_ylabel("Peptide records")
    ax0.set_title("Peptide curation keeps non-redundant records", fontsize=9)
    ax0.grid(axis="y", color=COLORS["grid"], lw=0.6)
    ax0.set_ylim(0, max(vals) * 1.22)

    panel_label(ax1, "B")
    ax1.barh(["removed", "retained"], [pep["duplicates_removed"], pep["cleaned_rows"]], color=[COLORS["accent"], COLORS["agent"]], height=0.48)
    ax1.set_xlabel("Rows")
    ax1.set_title("Curation change is explicit and auditable", fontsize=9)
    for y, v in enumerate([pep["duplicates_removed"], pep["cleaned_rows"]]):
        ax1.text(v + pep["raw_rows"] * 0.015, y, f"{v:,}", va="center", fontsize=7.5)
    ax1.grid(axis="x", color=COLORS["grid"], lw=0.6)
    ax1.set_xlim(0, pep["raw_rows"] * 1.12)

    panel_label(ax2, "C")
    ax2.plot([0, 1], [rep.ena_read_count, rep.agent_total_sequences], color=COLORS["grid"], lw=2)
    ax2.scatter([0], [rep.ena_read_count], s=70, color=COLORS["paper"], edgecolor="white", linewidth=0.8)
    ax2.scatter([1], [rep.agent_total_sequences], s=70, color=COLORS["agent"], edgecolor="white", linewidth=0.8)
    ax2.text(0, rep.ena_read_count * 1.05, f"{rep.ena_read_count:,.0f}", ha="center", fontsize=7.5)
    ax2.text(1, rep.agent_total_sequences * 1.05, f"{rep.agent_total_sequences:,.0f}", ha="center", fontsize=7.5)
    ax2.set_xticks([0, 1])
    ax2.set_xticklabels(["Published\nENA", "Agent\nFastQC"])
    ax2.set_ylabel("Reads")
    ax2.set_title("Representative FASTQ run matches read count", fontsize=9)
    ax2.grid(axis="y", color=COLORS["grid"], lw=0.6)
    ax2.set_ylim(rep.ena_read_count * 0.90, rep.ena_read_count * 1.10)

    panel_label(ax3, "D")
    x = np.arange(len(rep_df))
    ax3.scatter(x - 0.08, rep_df["agent_gc_percent"], s=55, color=COLORS["accent"], label="GC%")
    ax3b = ax3.twinx()
    ax3b.scatter(x + 0.08, rep_df["agent_sequence_length_mean"], s=55, color=COLORS["gold"], marker="D", label="mean read length")
    for i, row in enumerate(rep_df.itertuples()):
        ax3.text(i - 0.08, row.agent_gc_percent + 1.5, f"{row.agent_gc_percent:.0f}%", ha="center", fontsize=7, color=COLORS["accent"])
        ax3b.text(i + 0.08, row.agent_sequence_length_mean + 2.5, f"{row.agent_sequence_length_mean:.0f}", ha="center", fontsize=7, color=COLORS["gold"])
    ax3.set_xticks(x)
    ax3.set_xticklabels(rep_df["mate"])
    ax3.set_ylabel("GC (%)", color=COLORS["accent"])
    ax3b.set_ylabel("Mean read length", color=COLORS["gold"])
    ax3b.spines["right"].set_visible(True)
    ax3b.spines["right"].set_color(COLORS["gold"])
    ax3.set_title("Agent also records derived QC metrics", fontsize=9)
    ax3.grid(axis="y", color=COLORS["grid"], lw=0.6)
    ax3.set_ylim(40, 65)
    ax3b.set_ylim(285, 318)

    fig.suptitle("Figure 4 | Representative task-level validation", fontsize=12, fontweight="bold")
    return save(fig, OUT / "figure4_representative_task_validation")


def figure5_audit_summary(df: pd.DataFrame) -> list[Path]:
    rs = run_summary(df)
    pep = peptide_summary()
    fig = plt.figure(figsize=(7.4, 4.2), constrained_layout=True)
    gs = fig.add_gridspec(1, 2, width_ratios=[1.0, 1.25])
    ax0 = fig.add_subplot(gs[0, 0])
    ax1 = fig.add_subplot(gs[0, 1])

    panel_label(ax0, "A")
    categories = ["matched\nFASTQ runs", "expected\ncuration changes", "derived\nQC metrics", "true\nmismatches"]
    values = [len(rs[rs["match_status"] == "matched"]), 2, 2, len(rs[rs["match_status"] != "matched"])]
    colors = [COLORS["agent"], COLORS["gold"], COLORS["purple"], COLORS["accent"]]
    ax0.barh(np.arange(len(categories))[::-1], values, color=colors, height=0.48)
    ax0.set_yticks(np.arange(len(categories))[::-1])
    ax0.set_yticklabels(categories)
    ax0.set_xlabel("Count")
    ax0.set_title("Audit separates matches from expected changes", fontsize=9)
    for y, v in zip(np.arange(len(categories))[::-1], values):
        ax0.text(v + 0.08, y, str(v), va="center", fontsize=8)
    ax0.set_xlim(0, max(values) + 1.2)
    ax0.grid(axis="x", color=COLORS["grid"], lw=0.6)

    panel_label(ax1, "B")
    strip(ax1)
    rows = [
        ("Matched", "FASTQ read counts and source file bytes match public records.", COLORS["agent"]),
        ("Expected preprocessing change", f"Peptide-table row count changes because {pep['duplicates_removed']} duplicate rows were removed.", COLORS["gold"]),
        ("Derived QC metric", "GC% and read length are Agent-generated QC outputs, not direct paper-reported targets.", COLORS["purple"]),
        ("Actionable mismatch", "A non-zero read-count delta would trigger input, download, and workflow review.", COLORS["accent"]),
    ]
    y = 0.84
    for label, text, color in rows:
        ax1.add_patch(
            FancyBboxPatch(
                (0.02, y - 0.11),
                0.92,
                0.12,
                boxstyle="round,pad=0.012,rounding_size=0.018",
                fc="#fbfbfb",
                ec=COLORS["grid"],
                lw=0.7,
            )
        )
        ax1.add_patch(plt.Rectangle((0.045, y - 0.065), 0.026, 0.026, color=color, ec="none"))
        ax1.text(0.095, y - 0.032, label, fontsize=7.9, fontweight="bold", va="center")
        ax1.text(0.095, y - 0.077, text, fontsize=6.9, color=COLORS["muted"], va="center", wrap=True)
        y -= 0.19
    ax1.text(0.02, 0.055, "Audit framing prevents expected preprocessing changes from being misreported as failed reproducibility.", fontsize=7.8, color=COLORS["muted"], linespacing=1.3)
    ax1.set_xlim(0, 1)
    ax1.set_ylim(0, 1)

    fig.suptitle("Figure 5 | Reproducibility audit and discrepancy interpretation", fontsize=12, fontweight="bold")
    return save(fig, OUT / "figure5_audit_discrepancy_summary")


def main() -> None:
    set_style()
    OUT.mkdir(parents=True, exist_ok=True)
    df = fastq_df()
    tables = write_tables(df)
    figures = []
    figures.extend(figure1_architecture())
    figures.extend(figure2_dataset_map(df))
    figures.extend(figure3_reproducibility_overview())
    figures.extend(figure4_representative_validation(df))
    figures.extend(figure5_audit_summary(df))
    manifest = {
        "paper_framework": "Scheme B: reproducibility-validation paper",
        "figures": [str(p) for p in figures],
        "tables": {k: str(v) for k, v in tables.items()},
    }
    (OUT / "schemeB_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
