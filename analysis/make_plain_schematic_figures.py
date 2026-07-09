from __future__ import annotations

import json
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Final data" / "manuscript_figures" / "plain_schematics"

INK = "#26313d"
MUTED = "#65717f"
LINE = "#9aa7b3"
PALE = "#f7f9fb"
BLUE = "#2f6f8f"
ORANGE = "#c9854a"


def set_style() -> None:
    mpl.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
            "svg.fonttype": "none",
            "pdf.fonttype": 42,
            "font.size": 8,
            "figure.facecolor": "white",
            "savefig.facecolor": "white",
            "axes.facecolor": "white",
            "text.color": INK,
        }
    )


def save(fig: mpl.figure.Figure, stem: Path) -> list[str]:
    OUT.mkdir(parents=True, exist_ok=True)
    paths: list[str] = []
    for ext in (".svg", ".pdf", ".png"):
        path = stem.with_suffix(ext)
        if ext == ".png":
            fig.savefig(path, dpi=300, bbox_inches="tight", pad_inches=0.08)
        else:
            fig.savefig(path, bbox_inches="tight", pad_inches=0.08)
        paths.append(str(path))
    return paths


def box(
    ax: plt.Axes,
    x: float,
    y: float,
    w: float,
    h: float,
    title: str,
    subtitle: str = "",
    edge: str = LINE,
    fill: str = "white",
    title_color: str = INK,
) -> None:
    patch = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.010,rounding_size=0.020",
        fc=fill,
        ec=edge,
        lw=1.2,
    )
    ax.add_patch(patch)
    ax.text(x + 0.025, y + h - 0.032, title, fontsize=8.2, fontweight="bold", color=title_color, va="top")
    if subtitle:
        ax.text(x + 0.025, y + h - 0.075, subtitle, fontsize=6.7, color=MUTED, va="top", linespacing=1.18)


def arrow(ax: plt.Axes, start: tuple[float, float], end: tuple[float, float], color: str = LINE) -> None:
    ax.add_patch(
        FancyArrowPatch(
            start,
            end,
            arrowstyle="-|>",
            mutation_scale=10,
            lw=1.1,
            color=color,
            shrinkA=4,
            shrinkB=4,
        )
    )


def make_workflow_plain() -> list[str]:
    fig, ax = plt.subplots(figsize=(8.2, 3.9))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    ax.text(0.03, 0.94, "Plain workflow schematic", fontsize=11.5, fontweight="bold", va="top")
    ax.text(
        0.03,
        0.885,
        "Use this as an Illustrator redraw guide: boxes, arrows, and one expert checkpoint layer.",
        fontsize=7.4,
        color=MUTED,
        va="top",
    )

    y = 0.58
    w = 0.135
    h = 0.135
    xs = [0.035, 0.220, 0.405, 0.590, 0.775]
    items = [
        ("User request", "Natural language\n+ input files", BLUE),
        ("Workflow draft", "Steps, skills,\ninputs, outputs", INK),
        ("Expert review", "Check task and\nparameters", ORANGE),
        ("Local execution", "Run approved\nskills/tools", INK),
        ("Outputs", "Final files\n+ audit records", BLUE),
    ]
    for x, (title, sub, color) in zip(xs, items):
        box(ax, x, y, w, h, title, sub, title_color=color)
    for i in range(4):
        arrow(ax, (xs[i] + w, y + h / 2), (xs[i + 1], y + h / 2))

    # Small skill/tool strip, deliberately simple for manual redraw.
    strip_y = 0.255
    ax.plot([0.08, 0.92], [strip_y + 0.12, strip_y + 0.12], color="#d9dee5", lw=1.0)
    ax.text(0.035, strip_y + 0.14, "Skill/tool layer", fontsize=8.2, fontweight="bold", va="bottom")
    skill_labels = ["CSV curation", "FASTQ QC", "Source audit", "Future aDNA tools"]
    skill_xs = [0.12, 0.335, 0.55, 0.765]
    for x, label in zip(skill_xs, skill_labels):
        ax.add_patch(Rectangle((x - 0.073, strip_y), 0.146, 0.080, fc=PALE, ec="#cfd6dd", lw=1.0))
        ax.text(x, strip_y + 0.040, label, ha="center", va="center", fontsize=6.9)

    arrow(ax, (0.660, y), (0.550, strip_y + 0.085), color=BLUE)
    arrow(ax, (0.660, y), (0.765, strip_y + 0.085), color=BLUE)

    ax.text(
        0.035,
        0.080,
        "Main message: LLM proposes; expert reviews; constrained local skills execute; outputs remain auditable.",
        fontsize=7.3,
        color=MUTED,
    )
    return save(fig, OUT / "figure1_agent_workflow_plain_redraw_guide")


def make_scenario_plain() -> list[str]:
    fig, ax = plt.subplots(figsize=(8.2, 4.2))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    ax.text(0.03, 0.94, "Plain usage scenario", fontsize=11.5, fontweight="bold", va="top")
    ax.text(
        0.03,
        0.885,
        "Minimal scene for Illustrator: researcher, local web interface, local tools, and result folder.",
        fontsize=7.4,
        color=MUTED,
        va="top",
    )

    # Researcher card
    box(ax, 0.055, 0.500, 0.170, 0.210, "Researcher", "asks an analysis\nquestion and uploads\nancient-data files", title_color=BLUE)
    ax.add_patch(plt.Circle((0.095, 0.775), 0.022, ec=INK, fc="white", lw=1.1))
    ax.plot([0.095, 0.095], [0.752, 0.710], color=INK, lw=1.1)
    ax.plot([0.075, 0.115], [0.735, 0.735], color=INK, lw=1.1)

    # Interface card
    x0, y0, ww, hh = 0.345, 0.455, 0.260, 0.285
    ax.add_patch(
        FancyBboxPatch(
            (x0, y0),
            ww,
            hh,
            boxstyle="round,pad=0.010,rounding_size=0.020",
            fc="white",
            ec=LINE,
            lw=1.2,
        )
    )
    ax.text(x0 + 0.025, y0 + hh - 0.040, "Local web interface", fontsize=8.2, fontweight="bold", va="top")
    interface_lines = ["review workflow", "approve local run", "inspect report"]
    for i, label in enumerate(interface_lines):
        yy = y0 + hh - 0.100 - i * 0.055
        ax.add_patch(Rectangle((x0 + 0.025, yy - 0.020), ww - 0.050, 0.032, ec="#d9dee5", fc="white", lw=0.8))
        ax.text(x0 + 0.040, yy - 0.004, f"{i + 1}. {label}", fontsize=6.8, color=MUTED, va="center")

    # Tools and result folder
    box(ax, 0.740, 0.590, 0.185, 0.140, "Local tools", "FastQC / MultiQC\nseqkit / CSV skills", title_color=INK)
    box(ax, 0.740, 0.330, 0.185, 0.165, "Result folder", "final outputs\nstep outputs\nrecords", title_color=BLUE)

    arrow(ax, (0.225, 0.610), (0.345, 0.610))
    arrow(ax, (0.605, 0.620), (0.740, 0.660))
    arrow(ax, (0.830, 0.590), (0.830, 0.480))
    arrow(ax, (0.740, 0.405), (0.605, 0.520))

    # Optional blank area marker
    ax.add_patch(Rectangle((0.055, 0.170), 0.870, 0.070, fc="white", ec="#d9dee5", lw=0.9, linestyle="--"))
    ax.text(
        0.490,
        0.205,
        "Optional space: add simple SVG icons or manuscript-specific labels in Illustrator",
        ha="center",
        va="center",
        fontsize=7.0,
        color=MUTED,
    )

    return save(fig, OUT / "figure_graphical_abstract_plain_redraw_guide")


def main() -> None:
    set_style()
    manifest = {
        "workflow_plain": make_workflow_plain(),
        "scenario_plain": make_scenario_plain(),
        "note": "Plain redraw guides for Adobe Illustrator; no AI-generated raster illustration elements.",
    }
    (OUT / "plain_schematic_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
