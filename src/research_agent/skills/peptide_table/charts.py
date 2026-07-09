from collections import Counter
import os
from pathlib import Path
import tempfile
from typing import Any

_cache_root = Path(tempfile.gettempdir()) / "research-agent-cache"
(_cache_root / "matplotlib").mkdir(parents=True, exist_ok=True)
(_cache_root / "xdg").mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(_cache_root / "matplotlib"))
os.environ.setdefault("XDG_CACHE_HOME", str(_cache_root / "xdg"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from research_agent.skills.base import SkillContext, SkillResult
from research_agent.skills.peptide_table.common import (
    CANONICAL_AMINO_ACIDS,
    read_canonical_table,
)


CHARTS = {"length_histogram", "label_counts", "amino_acid_composition"}
CHART_ALIASES = {
    "length_distribution": "length_histogram",
    "label_distribution": "label_counts",
}


class PeptideChartSkill:
    name = "peptide_chart"
    description = "Create PNG charts for peptide lengths, labels, and amino-acid composition."
    input_formats = {"csv"}
    output_formats = {"png"}
    resource_class = "light"
    parameter_schema = {
        "type": "object",
        "required": ["charts"],
        "properties": {
            "charts": {"type": "array", "minItems": 1},
            "width": {"type": "integer", "minimum": 600, "maximum": 2400},
            "height": {"type": "integer", "minimum": 400, "maximum": 1800},
            "dpi": {"type": "integer", "minimum": 72, "maximum": 600},
        },
        "additionalProperties": False,
    }

    def run(self, context: SkillContext, parameters: dict[str, Any]) -> SkillResult:
        requested = [
            CHART_ALIASES.get(chart, chart)
            for chart in parameters["charts"]
        ]
        if not requested or any(chart not in CHARTS for chart in requested):
            raise ValueError("charts must contain supported chart names")
        frame = read_canonical_table(context.inputs[0])
        if frame.empty:
            raise ValueError("Cannot create charts from an empty peptide table")
        width = parameters.get("width", 1200)
        height = parameters.get("height", 800)
        dpi = parameters.get("dpi", 150)
        if not 600 <= width <= 2400 or not 400 <= height <= 1800 or not 72 <= dpi <= 600:
            raise ValueError("Chart dimensions or DPI are outside supported bounds")
        context.work_dir.mkdir(parents=True, exist_ok=True)
        outputs = []
        for chart in requested:
            fig, ax = plt.subplots(figsize=(width / dpi, height / dpi), dpi=dpi)
            if chart == "length_histogram":
                ax.hist(frame["sequence"].astype(str).str.len(), bins="auto", color="#0072B2")
                ax.set(xlabel="Peptide length", ylabel="Count", title="Peptide length distribution")
            elif chart == "label_counts":
                counts = frame["label"].astype(int).value_counts().reindex([0, 1], fill_value=0)
                ax.bar(["0", "1"], counts.values, color=["#56B4E9", "#D55E00"])
                ax.set(xlabel="Label", ylabel="Count", title="Peptide label counts")
            else:
                counts = Counter("".join(frame["sequence"].astype(str)))
                ax.bar(
                    list(CANONICAL_AMINO_ACIDS),
                    [counts.get(item, 0) for item in CANONICAL_AMINO_ACIDS],
                    color="#009E73",
                )
                ax.set(xlabel="Amino acid", ylabel="Count", title="Amino-acid composition")
            ax.spines[["top", "right"]].set_visible(False)
            fig.tight_layout()
            output = context.work_dir / f"{chart}.png"
            fig.savefig(output)
            plt.close(fig)
            outputs.append(str(output))
        return SkillResult(
            "succeeded", outputs, {"charts_created": len(outputs)}, [], None
        )
