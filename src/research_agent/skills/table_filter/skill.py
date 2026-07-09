from typing import Any

import pandas as pd

from research_agent.skills.base import SkillContext, SkillResult


OPERATORS = {
    ">=": lambda series, value: series >= value,
    ">": lambda series, value: series > value,
    "<=": lambda series, value: series <= value,
    "<": lambda series, value: series < value,
    "==": lambda series, value: series == value,
    "!=": lambda series, value: series != value,
}


class TableFilterSkill:
    name = "table_filter"
    description = "Filter CSV, TSV, or Excel rows using one explicit condition."
    input_formats = {"csv", "tsv", "xlsx"}
    output_formats = {"csv", "tsv", "xlsx"}
    resource_class = "light"
    parameter_schema = {
        "type": "object",
        "required": ["column", "operator", "value"],
        "properties": {
            "column": {"type": "string"},
            "operator": {"enum": list(OPERATORS)},
            "value": {},
            "output_format": {"enum": ["csv", "tsv", "xlsx"]},
        },
        "additionalProperties": False,
    }

    def run(self, context: SkillContext, parameters: dict[str, Any]) -> SkillResult:
        source = context.inputs[0]
        suffixes = "".join(source.suffixes).lower()
        if suffixes.endswith(".csv"):
            frame = pd.read_csv(source)
        elif suffixes.endswith((".tsv", ".txt")):
            frame = pd.read_csv(source, sep="\t")
        else:
            frame = pd.read_excel(source)
        column = parameters["column"]
        operator = parameters["operator"]
        if column not in frame:
            raise ValueError(f"Unknown column: {column}")
        if operator not in OPERATORS:
            raise ValueError(f"Unsupported operator: {operator}")
        filtered = frame.loc[OPERATORS[operator](frame[column], parameters["value"])]
        output_format = parameters.get("output_format", "csv")
        context.work_dir.mkdir(parents=True, exist_ok=True)
        output = context.work_dir / f"filtered_table.{output_format}"
        if output_format == "csv":
            filtered.to_csv(output, index=False)
        elif output_format == "tsv":
            filtered.to_csv(output, sep="\t", index=False)
        else:
            filtered.to_excel(output, index=False)
        return SkillResult(
            "succeeded",
            [str(output)],
            {"input_rows": len(frame), "kept_rows": len(filtered)},
            [],
        )
