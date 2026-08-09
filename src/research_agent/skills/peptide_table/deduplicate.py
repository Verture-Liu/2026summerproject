from typing import Any

import pandas as pd

from research_agent.skills.base import SkillContext, SkillResult
from research_agent.skills.peptide_table.common import read_canonical_table, write_table


class PeptideDeduplicateSkill:
    name = "peptide_deduplicate"
    description = "Remove duplicate peptide sequences and audit conflicting labels."
    input_formats = {"csv"}
    output_formats = {"csv"}
    resource_class = "light"
    parameter_schema = {
        "type": "object",
        "properties": {
            "conflict_policy": {"enum": ["fail", "prefer_positive", "keep_first"]},
            "keep": {"enum": ["first", "last"]},
        },
        "additionalProperties": False,
    }

    def run(self, context: SkillContext, parameters: dict[str, Any]) -> SkillResult:
        frame = read_canonical_table(context.inputs[0]).reset_index(drop=True)
        policy = parameters.get("conflict_policy", "fail")
        keep = parameters.get("keep", "first")
        conflicts = []
        reports = []
        chosen_rows = []
        for sequence, group in frame.groupby("sequence", sort=False):
            labels = sorted({int(value) for value in group["label"]})
            if len(labels) > 1:
                conflicts.append(sequence)
                if policy == "fail":
                    continue
                if policy == "prefer_positive":
                    selected = group.loc[group["label"].astype(int).eq(1)].iloc[
                        0 if keep == "first" else -1
                    ]
                    resolution = "preferred_positive"
                else:
                    selected = group.iloc[0]
                    resolution = "kept_first_conflict"
            else:
                selected = group.iloc[0 if keep == "first" else -1]
                resolution = "duplicate_removed" if len(group) > 1 else "unique"
            chosen_rows.append(selected)
            if len(group) > 1:
                reports.append(
                    {
                        "sequence": sequence,
                        "labels": "|".join(map(str, labels)),
                        "row_count": len(group),
                        "resolution": resolution,
                    }
                )
        if conflicts and policy == "fail":
            raise ValueError(
                f"{len(conflicts)} sequence(s) have conflicting labels"
            )
        deduplicated = (
            pd.DataFrame(chosen_rows).reset_index(drop=True)
            if chosen_rows
            else frame.iloc[0:0].copy()
        )
        report = pd.DataFrame(
            reports, columns=["sequence", "labels", "row_count", "resolution"]
        )
        output = context.work_dir / "deduplicated_peptides.csv"
        report_path = context.work_dir / "duplicate_report.csv"
        write_table(deduplicated, output)
        write_table(report, report_path)
        return SkillResult(
            "succeeded",
            [str(output), str(report_path)],
            {
                "input_rows": len(frame),
                "unique_sequences": len(deduplicated),
                "duplicate_rows_removed": len(frame) - len(deduplicated),
                "conflicting_sequences": len(conflicts),
            },
            [],
            named_outputs={
                "deduplicated": str(output),
                "deduplicated_csv": str(output),
                "dedup_csv": str(output),
                "duplicates": str(report_path),
                "duplicate_report": str(report_path),
                "duplicate_report_csv": str(report_path),
            },
        )
