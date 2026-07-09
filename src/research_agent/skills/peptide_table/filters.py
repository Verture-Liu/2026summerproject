from typing import Any

from research_agent.skills.base import SkillContext, SkillResult
from research_agent.skills.peptide_table.common import (
    describe_lengths,
    empty_filter_warning,
    read_canonical_table,
    write_table,
)


class PeptideLabelFilterSkill:
    name = "peptide_label_filter"
    description = "Keep peptide rows matching requested binary labels."
    input_formats = {"csv"}
    output_formats = {"csv"}
    resource_class = "light"
    parameter_schema = {
        "type": "object",
        "required": ["labels"],
        "properties": {
            "labels": {"type": "array", "items": {"enum": [0, 1]}, "minItems": 1}
        },
        "additionalProperties": False,
    }

    def run(self, context: SkillContext, parameters: dict[str, Any]) -> SkillResult:
        labels = parameters["labels"]
        if not labels or any(label not in {0, 1} for label in labels):
            raise ValueError("labels must be a non-empty list containing 0 or 1")
        frame = read_canonical_table(context.inputs[0])
        numeric_labels = frame["label"].astype(int)
        filtered = frame.loc[numeric_labels.isin(labels)].copy()
        output = context.work_dir / "label_filtered_peptides.csv"
        write_table(filtered, output)
        counts = filtered["label"].astype(int).value_counts().sort_index()
        return SkillResult(
            "succeeded",
            [str(output)],
            {
                "input_rows": len(frame),
                "kept_rows": len(filtered),
                "removed_rows": len(frame) - len(filtered),
                "label_counts": {str(key): int(value) for key, value in counts.items()},
            },
            empty_filter_warning(filtered),
        )


class PeptideLengthFilterSkill:
    name = "peptide_length_filter"
    description = "Keep peptide rows within an inclusive amino-acid length range."
    input_formats = {"csv"}
    output_formats = {"csv"}
    resource_class = "light"
    parameter_schema = {
        "type": "object",
        "required": ["min_length", "max_length"],
        "properties": {
            "min_length": {"type": "integer", "minimum": 1},
            "max_length": {"type": "integer", "minimum": 1},
            "include_length_column": {"type": "boolean"},
        },
        "additionalProperties": False,
    }

    def run(self, context: SkillContext, parameters: dict[str, Any]) -> SkillResult:
        minimum = parameters["min_length"]
        maximum = parameters["max_length"]
        if maximum < minimum:
            raise ValueError("max_length must be greater than or equal to min_length")
        frame = read_canonical_table(context.inputs[0])
        lengths = frame["sequence"].astype(str).str.len()
        filtered = frame.loc[lengths.between(minimum, maximum)].copy()
        filtered_lengths = filtered["sequence"].astype(str).str.len()
        if parameters.get("include_length_column", True):
            filtered["length"] = filtered_lengths
        output = context.work_dir / "length_filtered_peptides.csv"
        write_table(filtered, output)
        return SkillResult(
            "succeeded",
            [str(output)],
            {
                "input_rows": len(frame),
                "kept_rows": len(filtered),
                "removed_rows": len(frame) - len(filtered),
                "before": describe_lengths(lengths),
                "after": describe_lengths(filtered_lengths),
            },
            empty_filter_warning(filtered),
        )
