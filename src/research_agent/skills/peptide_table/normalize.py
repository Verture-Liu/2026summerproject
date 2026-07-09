import csv
from pathlib import Path
from typing import Any

import pandas as pd

from research_agent.skills.base import SkillContext, SkillResult
from research_agent.skills.peptide_table.common import write_table


LABEL_ALIASES = {"label", "class", "target", "activity", "is_amp"}
SEQUENCE_ALIASES = {"sequence", "peptide", "peptide_sequence", "seq"}


def _delimiter(source: Path, requested: str) -> str:
    if requested == "comma":
        return ","
    if requested == "tab":
        return "\t"
    sample = source.read_text(encoding="utf-8-sig", errors="replace")[:4096]
    try:
        return csv.Sniffer().sniff(sample, delimiters=",\t").delimiter
    except csv.Error:
        return "\t" if source.suffix.lower() in {".tsv", ".txt"} else ","


def _looks_like_header(values: list[str]) -> bool:
    lowered = {str(value).strip().lower() for value in values}
    return bool(lowered & LABEL_ALIASES) and bool(lowered & SEQUENCE_ALIASES)


def _resolve_column(frame: pd.DataFrame, requested, aliases: set[str], kind: str):
    if requested is not None:
        if isinstance(requested, int):
            if requested < 0 or requested >= len(frame.columns):
                raise ValueError(f"{kind} column index is out of range")
            return frame.columns[requested]
        if requested not in frame.columns:
            raise ValueError(f"Unknown {kind} column: {requested}")
        return requested
    matches = [column for column in frame.columns if str(column).strip().lower() in aliases]
    if len(matches) == 1:
        return matches[0]
    raise ValueError(f"Could not identify one unambiguous {kind} column")


def _headerless_columns(frame: pd.DataFrame, parameters: dict[str, Any]) -> tuple[Any, Any, list[str]]:
    warnings = []
    label_hint = parameters.get("label_column")
    sequence_hint = parameters.get("sequence_column")
    hints = [hint for hint in (label_hint, sequence_hint) if hint is not None]
    if any(not isinstance(hint, int) for hint in hints):
        warnings.append(
            "Headerless peptide table received non-index column hints; using columns 0 and 1."
        )
        return frame.columns[0], frame.columns[1], warnings
    return (
        _resolve_column(frame, parameters.get("label_column", 0), LABEL_ALIASES, "label"),
        _resolve_column(
            frame, parameters.get("sequence_column", 1), SEQUENCE_ALIASES, "sequence"
        ),
        warnings,
    )


def _normalize_label(value) -> int:
    text = str(value).strip().lower()
    if text in {"1", "1.0", "true", "yes", "positive"}:
        return 1
    if text in {"0", "0.0", "false", "no", "negative"}:
        return 0
    raise ValueError(f"Labels must be binary 0/1 values; found {value!r}")


class PeptideCsvNormalizeSkill:
    name = "peptide_csv_normalize"
    description = "Input preparation stage: normalize raw peptide CSV or TSV files, including headerless tables, to canonical label and sequence columns."
    input_formats = {"csv", "tsv"}
    output_formats = {"csv"}
    resource_class = "light"
    parameter_schema = {
        "type": "object",
        "properties": {
            "delimiter": {"enum": ["auto", "comma", "tab"]},
            "label_column": {},
            "sequence_column": {},
            "drop_empty_rows": {"type": "boolean"},
        },
        "additionalProperties": False,
    }

    def run(self, context: SkillContext, parameters: dict[str, Any]) -> SkillResult:
        source = context.inputs[0]
        delimiter = _delimiter(source, parameters.get("delimiter", "auto"))
        raw = pd.read_csv(
            source,
            sep=delimiter,
            header=None,
            dtype=str,
            keep_default_na=False,
            encoding="utf-8-sig",
        )
        if raw.shape[1] < 2:
            raise ValueError("Peptide table must contain at least two columns")
        header_detected = _looks_like_header(raw.iloc[0].tolist())
        warnings = []
        if header_detected:
            frame = pd.read_csv(
                source,
                sep=delimiter,
                dtype=str,
                keep_default_na=False,
                encoding="utf-8-sig",
            )
            label_column = _resolve_column(
                frame, parameters.get("label_column"), LABEL_ALIASES, "label"
            )
            sequence_column = _resolve_column(
                frame, parameters.get("sequence_column"), SEQUENCE_ALIASES, "sequence"
            )
        else:
            frame = raw
            label_column, sequence_column, warnings = _headerless_columns(frame, parameters)
        selected = pd.DataFrame(
            {
                "label": frame[label_column],
                "sequence": frame[sequence_column].astype(str).str.strip().str.upper(),
            }
        )
        input_rows = len(selected)
        empty_mask = selected["sequence"].eq("") & selected["label"].astype(str).str.strip().eq("")
        if parameters.get("drop_empty_rows", True):
            selected = selected.loc[~empty_mask].copy()
        selected["label"] = selected["label"].map(_normalize_label)
        output = context.work_dir / "normalized_peptides.csv"
        write_table(selected, output)
        return SkillResult(
            "succeeded",
            [str(output)],
            {
                "input_rows": input_rows,
                "normalized_rows": len(selected),
                "empty_rows_removed": int(empty_mask.sum()),
                "header_detected": header_detected,
                "label_column": str(label_column),
                "sequence_column": str(sequence_column),
            },
            warnings,
        )
