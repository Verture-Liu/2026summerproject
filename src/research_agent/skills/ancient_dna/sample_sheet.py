from __future__ import annotations

from pathlib import Path

import pandas as pd

from research_agent.skills.base import SkillContext, SkillResult


ALIASES = {
    "run": ("run_accession", "run", "Run", "Run_accession"),
    "sample": ("sample_accession", "sample_id", "Sample", "sample"),
    "layout": ("library_layout", "LibraryLayout", "layout"),
    "organism": ("scientific_name", "ScientificName", "organism"),
}


def _column(frame: pd.DataFrame, kind: str, required: bool = True) -> str | None:
    for name in ALIASES[kind]:
        if name in frame.columns:
            return name
    if required:
        raise ValueError(
            f"Input table is missing a {kind} column; accepted names: "
            + ", ".join(ALIASES[kind])
        )
    return None


class SampleSheetPrepareSkill:
    name = "sample_sheet_prepare"
    description = "Normalize SRA RunInfo or sequencing metadata into a FASTQ sample sheet."
    input_formats = {"csv", "tsv"}
    output_formats = {"csv"}
    resource_class = "light"
    parameter_schema = {
        "type": "object",
        "properties": {
            "fastq_directory": {"type": "string"},
        },
        "additionalProperties": False,
    }

    def run(self, context: SkillContext, parameters: dict) -> SkillResult:
        source = context.inputs[0]
        delimiter = "\t" if source.suffix.lower() == ".tsv" else ","
        frame = pd.read_csv(source, sep=delimiter, keep_default_na=False)
        run_col = _column(frame, "run")
        sample_col = _column(frame, "sample", required=False)
        layout_col = _column(frame, "layout")
        organism_col = _column(frame, "organism", required=False)
        fastq_directory = Path(parameters.get("fastq_directory", ".")).expanduser()

        records = []
        for _, row in frame.iterrows():
            run = str(row[run_col]).strip()
            if not run:
                raise ValueError("Run accession cannot be empty")
            layout = str(row[layout_col]).strip().lower()
            if layout not in {"paired", "single"}:
                raise ValueError(f"Unsupported library layout for {run}: {layout}")
            sample = (
                str(row[sample_col]).strip()
                if sample_col and str(row[sample_col]).strip()
                else run
            )
            if layout == "paired":
                fastq_1 = fastq_directory / f"{run}_1.fastq.gz"
                fastq_2 = fastq_directory / f"{run}_2.fastq.gz"
            else:
                fastq_1 = fastq_directory / f"{run}.fastq.gz"
                fastq_2 = ""
            records.append(
                {
                    "sample_id": sample,
                    "run_accession": run,
                    "layout": layout,
                    "fastq_1": str(fastq_1),
                    "fastq_2": str(fastq_2),
                    "organism": (
                        str(row[organism_col]).strip() if organism_col else ""
                    ),
                }
            )

        output = pd.DataFrame(records)
        if output["run_accession"].duplicated().any():
            raise ValueError("Run accessions must be unique")
        context.work_dir.mkdir(parents=True, exist_ok=True)
        output_path = context.work_dir / "samplesheet.csv"
        output.to_csv(output_path, index=False)
        return SkillResult(
            "succeeded",
            [str(output_path)],
            {
                "samples": int(output["sample_id"].nunique()),
                "runs": len(output),
                "paired_runs": int((output["layout"] == "paired").sum()),
                "single_runs": int((output["layout"] == "single").sum()),
            },
            [],
        )

