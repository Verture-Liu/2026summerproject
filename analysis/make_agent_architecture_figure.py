from __future__ import annotations

import json
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Final data" / "manuscript_figures"

COLORS = {
    "ink": "#1f2933",
    "muted": "#6b7280",
    "grid": "#e5e7eb",
    "blue": "#2f6f8f",
    "teal": "#5b8f8a",
    "gold": "#d8a24a",
    "purple": "#7b6ca8",
    "red": "#c46a4a",
    "panel": "#f7f8fa",
    "pale_blue": "#eef6f8",
    "pale_gold": "#fbf5e6",
    "pale_purple": "#f2eff8",
    "pale_green": "#eff7f3",
}


def set_style() -> None:
    mpl.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
            "svg.fonttype": "none",
            "pdf.fonttype": 42,
            "font.size": 8,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "savefig.facecolor": "white",
            "text.color": COLORS["ink"],
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


def add_box(
    ax: plt.Axes,
    x: float,
    y: float,
    w: float,
    h: float,
    title: str,
    body: str,
    fc: str,
    ec: str = "#d9dee5",
    title_color: str | None = None,
) -> None:
    shadow = FancyBboxPatch(
        (x + 0.004, y - 0.005),
        w,
        h,
        boxstyle="round,pad=0.014,rounding_size=0.035",
        fc="#000000",
        ec="none",
        alpha=0.045,
        zorder=0,
    )
    ax.add_patch(shadow)
    box = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.014,rounding_size=0.035",
        fc=fc,
        ec=ec,
        lw=1.05,
        zorder=1,
    )
    ax.add_patch(box)
    ax.text(x + 0.020, y + h - 0.032, title, fontsize=8.0, fontweight="bold", va="top", color=title_color or COLORS["ink"], zorder=2)
    ax.text(x + 0.020, y + h - 0.078, body, fontsize=6.25, va="top", color=COLORS["muted"], linespacing=1.16, zorder=2)


def arrow(ax: plt.Axes, start: tuple[float, float], end: tuple[float, float], color: str = "#9aa5b1") -> None:
    ax.add_patch(
        FancyArrowPatch(
            start,
            end,
            arrowstyle="-|>",
            mutation_scale=10,
            lw=1.2,
            color=color,
            alpha=0.9,
            shrinkA=2,
            shrinkB=2,
            connectionstyle="arc3,rad=0.0",
        )
    )


def add_lane_background(ax: plt.Axes, x: float, y: float, w: float, h: float, fc: str) -> None:
    ax.add_patch(
        FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle="round,pad=0.018,rounding_size=0.04",
            fc=fc,
            ec="none",
            alpha=0.55,
            zorder=-2,
        )
    )


def make_figure() -> dict[str, list[str]]:
    OUT.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(10.4, 6.0))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    ax.text(
        0.03,
        0.965,
        "Human-in-the-loop architecture of the natural-language research agent",
        fontsize=13,
        fontweight="bold",
        va="top",
    )

    add_lane_background(ax, 0.025, 0.610, 0.95, 0.265, "#f8fafc")
    add_lane_background(ax, 0.025, 0.275, 0.95, 0.275, "#fbfcfd")
    add_lane_background(ax, 0.055, 0.090, 0.890, 0.185, "#fbfbfb")
    ax.text(
        0.03,
        0.915,
        "The language model plans constrained workflows; experts review key decisions; predefined local skills and command-line tools perform execution.",
        fontsize=7.6,
        color=COLORS["muted"],
        va="top",
    )

    # Top workflow lane
    y_top = 0.665
    w = 0.158
    h = 0.165
    xs = [0.035, 0.225, 0.415, 0.605, 0.795]
    boxes = [
        (
            "User request",
            "Natural language\n+ uploaded data\nCSV / FASTQ / metadata",
            COLORS["panel"],
            COLORS["ink"],
        ),
        (
            "Workflow planner",
            "Structured workflow\nsteps, skills,\ninputs and outputs",
            COLORS["pale_blue"],
            COLORS["blue"],
        ),
        (
            "Workflow validator",
            "Check file type,\nstep references,\nskill compatibility",
            COLORS["pale_gold"],
            COLORS["gold"],
        ),
        (
            "Skill execution",
            "Dispatch steps\nto deterministic\nskills and tools",
            COLORS["pale_green"],
            COLORS["teal"],
        ),
        (
            "Organized outputs",
            "final_outputs\nstep_outputs\naudit records",
            COLORS["pale_purple"],
            COLORS["purple"],
        ),
    ]
    for x, (title, body, fc, tc) in zip(xs, boxes):
        add_box(ax, x, y_top, w, h, title, body, fc, title_color=tc)
    for i in range(len(xs) - 1):
        arrow(ax, (xs[i] + w + 0.008, y_top + h / 2), (xs[i + 1] - 0.008, y_top + h / 2))

    # Human-in-the-loop checkpoints
    checkpoint_y = 0.585
    checkpoints = [
        (0.265, "Expert workflow\nreview"),
        (0.620, "Local execution\napproval"),
        (0.840, "Result audit\nand interpretation"),
    ]
    for x, label in checkpoints:
        add_box(
            ax,
            x,
            checkpoint_y,
            0.130,
            0.072,
            "Human check",
            label,
            "#fff7ed",
            ec="#f0d2a8",
            title_color=COLORS["gold"],
        )
    arrow(ax, (0.290, checkpoint_y + 0.072), (0.300, y_top), color=COLORS["gold"])
    arrow(ax, (0.655, checkpoint_y + 0.072), (0.675, y_top), color=COLORS["gold"])
    arrow(ax, (0.875, checkpoint_y + 0.072), (0.875, y_top), color=COLORS["gold"])

    # Skill/tool layer
    ax.text(0.035, 0.545, "Skill and tool layer", fontsize=9.2, fontweight="bold", va="top")
    ax.text(0.035, 0.500, "Current skills focus on entry-level but failure-prone ancient-data analysis steps.", fontsize=6.9, color=COLORS["muted"])

    skill_y = 0.315
    skill_w = 0.165
    skill_h = 0.140
    skill_xs = [0.035, 0.225, 0.415, 0.605, 0.795]
    skill_boxes = [
        ("Peptide / CSV", "header detection\nsequence validation\ndeduplication", COLORS["panel"]),
        ("FASTQ QC", "FastQC\nMultiQC\nseqkit stats", COLORS["pale_blue"]),
        ("Source audit", "ENA/SRA metadata\nread counts\nfile sizes", COLORS["pale_gold"]),
        ("Ancient-DNA ready", "paired-end checks\nread length\nGC / N metrics", COLORS["pale_green"]),
        ("Future skills", "BWA / Bowtie2\nsamtools\nmapDamage", COLORS["pale_purple"]),
    ]
    for x, (title, body, fc) in zip(skill_xs, skill_boxes):
        add_box(ax, x, skill_y, skill_w, skill_h, title, body, fc)

    arrow(ax, (0.685, y_top), (0.50, skill_y + skill_h + 0.008), color=COLORS["teal"])
    arrow(ax, (0.685, y_top), (0.88, skill_y + skill_h + 0.008), color=COLORS["teal"])

    # Local execution and audit note
    add_box(
        ax,
        0.055,
        0.125,
        0.405,
        0.135,
        "Local execution environment",
        "Runs on the user's machine with configured environments.\nMissing external tools are reported explicitly.",
        "#ffffff",
        ec=COLORS["grid"],
        title_color=COLORS["ink"],
    )
    add_box(
        ax,
        0.535,
        0.125,
        0.405,
        0.135,
        "Reproducibility and audit trail",
        "Each run keeps final outputs, intermediate files,\nworkflow JSON, manifests, checksums, and reports.",
        "#ffffff",
        ec=COLORS["grid"],
        title_color=COLORS["ink"],
    )
    arrow(ax, (0.46, 0.19), (0.535, 0.19), color=COLORS["muted"])

    ax.text(
        0.035,
        0.045,
        "Design principle: the LLM proposes; experts approve and interpret; constrained skills and local tools execute.",
        fontsize=7.2,
        color=COLORS["blue"],
        fontweight="bold",
    )

    paths = save(fig, OUT / "figure1_agent_architecture_workflow")
    plt.close(fig)
    manifest = {"figures": [str(p) for p in paths]}
    (OUT / "figure1_agent_architecture_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def main() -> None:
    set_style()
    print(json.dumps(make_figure(), indent=2))


if __name__ == "__main__":
    main()
