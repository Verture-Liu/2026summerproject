from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from research_agent.skills.base import SkillContext, SkillResult
from research_agent.skills.peptide_table.common import (
    CANONICAL_AMINO_ACIDS,
    write_table,
)


RESIDUE_MASS = {
    "A": 89.09,
    "C": 121.16,
    "D": 133.10,
    "E": 147.13,
    "F": 165.19,
    "G": 75.07,
    "H": 155.16,
    "I": 131.17,
    "K": 146.19,
    "L": 131.17,
    "M": 149.21,
    "N": 132.12,
    "P": 115.13,
    "Q": 146.15,
    "R": 174.20,
    "S": 105.09,
    "T": 119.12,
    "V": 117.15,
    "W": 204.23,
    "Y": 181.19,
}
HYDROPHOBIC = set("AILMFWYV")


def _read_sequences(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".csv":
        frame = pd.read_csv(path, keep_default_na=False)
        if "sequence" not in frame.columns:
            raise ValueError("CSV input must contain a sequence column")
        return frame.copy()
    if path.suffix.lower() in {".fasta", ".fa", ".faa"}:
        records, chunks, name = [], [], None
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith(">"):
                if name is not None:
                    records.append({"name": name, "sequence": "".join(chunks)})
                name, chunks = line[1:].strip(), []
            elif line:
                chunks.append(line)
        if name is not None:
            records.append({"name": name, "sequence": "".join(chunks)})
        return pd.DataFrame(records)
    raise ValueError("Peptide input must be CSV or FASTA")


def _validate_sequence(sequence: str) -> str:
    sequence = str(sequence).strip().upper()
    if not sequence:
        raise ValueError("Empty peptide sequence")
    invalid = sorted(set(sequence) - set(CANONICAL_AMINO_ACIDS))
    if invalid:
        raise ValueError("Invalid amino acid letters: " + ", ".join(invalid))
    return sequence


class PeptidePropertiesSkill:
    name = "peptide_properties"
    description = "Calculate basic peptide physicochemical properties from peptide CSV or FASTA inputs."
    input_formats = {"csv", "fasta"}
    output_formats = {"csv", "json"}
    resource_class = "light"
    parameter_schema = {"type": "object", "properties": {}, "additionalProperties": False}

    def run(self, context: SkillContext, parameters: dict) -> SkillResult:
        try:
            context.work_dir.mkdir(parents=True, exist_ok=True)
            frame = _read_sequences(context.inputs[0])
            frame["sequence"] = frame["sequence"].map(_validate_sequence)
            properties = []
            for sequence in frame["sequence"]:
                length = len(sequence)
                positive = sequence.count("K") + sequence.count("R") + sequence.count("H")
                negative = sequence.count("D") + sequence.count("E")
                mass = sum(RESIDUE_MASS[aa] for aa in sequence) - (length - 1) * 18.015
                properties.append(
                    {
                        "length": length,
                        "net_charge": positive - negative,
                        "molecular_weight": round(mass, 3),
                        "hydrophobic_fraction": round(
                            sum(aa in HYDROPHOBIC for aa in sequence) / length,
                            4,
                        ),
                        "basic_residue_count": positive,
                        "acidic_residue_count": negative,
                    }
                )
            output = pd.concat([frame.reset_index(drop=True), pd.DataFrame(properties)], axis=1)
            csv_path = context.work_dir / "peptide_properties.csv"
            write_table(output, csv_path)
            metadata = context.work_dir / "peptide_properties_metadata.json"
            metadata.write_text(
                json.dumps({"rows": len(output), "columns": list(output.columns)}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            return SkillResult("succeeded", [str(csv_path), str(metadata)], {"rows": len(output)}, [])
        except Exception as exc:
            return SkillResult("failed", [], {}, [], str(exc))


class PeptideCandidateRankSkill:
    name = "peptide_candidate_rank"
    description = "Rank peptide candidates by combining positive prediction scores and negative risk scores."
    input_formats = {"csv"}
    output_formats = {"csv", "json"}
    resource_class = "light"
    parameter_schema = {
        "type": "object",
        "properties": {
            "positive_score_columns": {"type": "array", "items": {"type": "string"}},
            "negative_score_columns": {"type": "array", "items": {"type": "string"}},
        },
        "additionalProperties": False,
    }

    def run(self, context: SkillContext, parameters: dict) -> SkillResult:
        try:
            context.work_dir.mkdir(parents=True, exist_ok=True)
            frame = pd.read_csv(context.inputs[0], keep_default_na=False)
            positive = parameters.get("positive_score_columns") or [
                column for column in frame.columns if column.endswith("_score") and "tox" not in column.lower()
            ]
            negative = parameters.get("negative_score_columns") or [
                column for column in frame.columns if "tox" in column.lower() and column.endswith("_score")
            ]
            if not positive:
                raise ValueError("Provide positive_score_columns or include at least one *_score column")
            missing = [column for column in positive + negative if column not in frame.columns]
            if missing:
                raise ValueError("Missing score columns: " + ", ".join(missing))
            for column in positive + negative:
                frame[column] = pd.to_numeric(frame[column], errors="raise")
            frame["positive_score_mean"] = frame[positive].mean(axis=1)
            frame["negative_score_mean"] = frame[negative].mean(axis=1) if negative else 0.0
            frame["candidate_score"] = frame["positive_score_mean"] - frame["negative_score_mean"]
            frame = frame.sort_values("candidate_score", ascending=False).reset_index(drop=True)
            frame["candidate_rank"] = range(1, len(frame) + 1)
            output = context.work_dir / "peptide_candidate_rank.csv"
            write_table(frame, output)
            metadata = context.work_dir / "peptide_candidate_rank_metadata.json"
            metadata.write_text(
                json.dumps(
                    {
                        "rows": len(frame),
                        "positive_score_columns": positive,
                        "negative_score_columns": negative,
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            return SkillResult("succeeded", [str(output), str(metadata)], {"rows": len(frame)}, [])
        except Exception as exc:
            return SkillResult("failed", [], {}, [], str(exc))
