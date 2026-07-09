import json
from collections import Counter
from typing import Any

import pandas as pd

from research_agent.skills.base import SkillContext, SkillResult
from research_agent.skills.peptide_table.common import (
    CANONICAL_AMINO_ACIDS,
    describe_lengths,
    read_canonical_table,
    write_table,
)


class PeptideStatisticsSkill:
    name = "peptide_statistics"
    description = "Calculate descriptive peptide counts, lengths, labels, and amino-acid composition."
    input_formats = {"csv"}
    output_formats = {"json", "csv"}
    resource_class = "light"
    parameter_schema = {
        "type": "object",
        "properties": {
            "group_by_label": {"type": "boolean"},
            "include_amino_acid_composition": {"type": "boolean"},
        },
        "additionalProperties": False,
    }

    def run(self, context: SkillContext, parameters: dict[str, Any]) -> SkillResult:
        frame = read_canonical_table(context.inputs[0])
        lengths = frame["sequence"].astype(str).str.len()
        counts = frame["label"].astype(int).value_counts().sort_index()
        stats = {
            "total_rows": len(frame),
            "unique_sequences": int(frame["sequence"].nunique()),
            "length": describe_lengths(lengths),
        }
        if parameters.get("group_by_label", True):
            stats["label_counts"] = {
                str(key): int(value) for key, value in counts.items()
            }
            stats["label_proportions"] = {
                str(key): float(value / len(frame)) if len(frame) else 0.0
                for key, value in counts.items()
            }
        context.work_dir.mkdir(parents=True, exist_ok=True)
        stats_path = context.work_dir / "peptide_statistics.json"
        stats_path.write_text(
            json.dumps(stats, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        distribution = (
            lengths.value_counts()
            .sort_index()
            .rename_axis("length")
            .reset_index(name="count")
        )
        distribution_path = context.work_dir / "length_distribution.csv"
        write_table(distribution, distribution_path)
        outputs = [str(stats_path), str(distribution_path)]
        if parameters.get("include_amino_acid_composition", True):
            residues = Counter("".join(frame["sequence"].astype(str)))
            total = sum(residues.values())
            composition = pd.DataFrame(
                [
                    {
                        "amino_acid": amino_acid,
                        "count": residues.get(amino_acid, 0),
                        "frequency": residues.get(amino_acid, 0) / total
                        if total
                        else 0.0,
                    }
                    for amino_acid in CANONICAL_AMINO_ACIDS
                ]
            )
            composition_path = context.work_dir / "amino_acid_composition.csv"
            write_table(composition, composition_path)
            outputs.append(str(composition_path))
        return SkillResult("succeeded", outputs, stats, [], None)
