from pathlib import Path
from typing import Any

from research_agent.skills.base import SkillContext, SkillResult
from research_agent.skills.peptide_table.common import read_canonical_table, write_table


class PeptideCsvExportSkill:
    name = "peptide_csv_export"
    description = "Export selected peptide-table columns to a safely named CSV."
    input_formats = {"csv"}
    output_formats = {"csv"}
    resource_class = "light"
    parameter_schema = {
        "type": "object",
        "properties": {
            "columns": {"type": "array", "minItems": 1},
            "sort_by": {"type": "string"},
            "sort_order": {"enum": ["ascending", "descending"]},
            "filename": {"type": "string"},
        },
        "additionalProperties": False,
    }

    def run(self, context: SkillContext, parameters: dict[str, Any]) -> SkillResult:
        frame = read_canonical_table(context.inputs[0])
        filename = parameters.get("filename", "processed_peptides.csv")
        if Path(filename).name != filename or not filename.lower().endswith(".csv"):
            raise ValueError("filename must be a safe CSV basename")
        columns = parameters.get("columns", list(frame.columns))
        if columns == ["*"]:
            columns = list(frame.columns)
        missing = [column for column in columns if column not in frame.columns]
        if missing:
            raise ValueError(f"Unknown export column(s): {', '.join(missing)}")
        sort_by = parameters.get("sort_by")
        if sort_by is not None:
            if sort_by not in frame.columns:
                raise ValueError(f"Unknown sort column: {sort_by}")
            frame = frame.sort_values(
                sort_by,
                ascending=parameters.get("sort_order", "ascending") == "ascending",
                kind="mergesort",
            )
        output = context.work_dir / filename
        write_table(frame.loc[:, columns], output)
        return SkillResult(
            "succeeded",
            [str(output)],
            {"exported_rows": len(frame), "columns": columns},
            [],
            None,
        )
