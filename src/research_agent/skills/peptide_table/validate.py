from collections import Counter
from typing import Any

import pandas as pd

from research_agent.skills.base import SkillContext, SkillResult
from research_agent.skills.peptide_table.common import (
    CANONICAL_AMINO_ACIDS,
    read_canonical_table,
    write_table,
)


class PeptideValidateSkill:
    name = "peptide_validate"
    description = "Pre-analysis validation stage: validate binary labels and amino-acid sequences before peptide filtering, statistics, charts, export, or prediction."
    input_formats = {"csv"}
    output_formats = {"csv"}
    resource_class = "light"
    parameter_schema = {
        "type": "object",
        "properties": {
            "allowed_alphabet": {"type": "string"},
            "min_length": {"type": "integer", "minimum": 1},
            "max_length": {"type": "integer", "minimum": 1},
            "invalid_row_policy": {"enum": ["reject", "fail"]},
        },
        "additionalProperties": False,
    }

    def run(self, context: SkillContext, parameters: dict[str, Any]) -> SkillResult:
        frame = read_canonical_table(context.inputs[0])
        alphabet = set(parameters.get("allowed_alphabet", CANONICAL_AMINO_ACIDS).upper())
        minimum = parameters.get("min_length", 1)
        maximum = parameters.get("max_length", 10000)
        if maximum < minimum:
            raise ValueError("max_length must be greater than or equal to min_length")
        valid_rows = []
        rejected_rows = []
        for row in frame.to_dict("records"):
            label = row["label"]
            sequence = str(row["sequence"]).strip().upper()
            if str(label).strip() not in {"0", "1", "0.0", "1.0"}:
                reason = "invalid_label"
            elif sequence == "":
                reason = "empty_sequence"
            elif len(sequence) < minimum:
                reason = "below_min_length"
            elif len(sequence) > maximum:
                reason = "above_max_length"
            elif any(character not in alphabet for character in sequence):
                reason = "invalid_amino_acid"
            else:
                reason = None
            normalized = {"label": int(float(label)), "sequence": sequence}
            if reason:
                normalized["rejection_reason"] = reason
                rejected_rows.append(normalized)
            else:
                valid_rows.append(normalized)
        if rejected_rows and parameters.get("invalid_row_policy", "reject") == "fail":
            raise ValueError(f"{len(rejected_rows)} invalid peptide row(s) found")
        valid = pd.DataFrame(valid_rows, columns=["label", "sequence"])
        rejected = pd.DataFrame(
            rejected_rows, columns=["label", "sequence", "rejection_reason"]
        )
        valid_path = context.work_dir / "valid_peptides.csv"
        rejected_path = context.work_dir / "rejected_peptides.csv"
        write_table(valid, valid_path)
        write_table(rejected, rejected_path)
        reasons = Counter(row["rejection_reason"] for row in rejected_rows)
        return SkillResult(
            "succeeded",
            [str(valid_path), str(rejected_path)],
            {
                "input_rows": len(frame),
                "valid_rows": len(valid),
                "rejected_rows": len(rejected),
                "rejection_reasons": dict(sorted(reasons.items())),
            },
            [f"Rejected {len(rejected)} invalid row(s)."] if len(rejected) else [],
        )
