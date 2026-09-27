import json
from dataclasses import asdict

from research_agent.agent.models import Workflow


WORKFLOW_EXAMPLE = {
    "schema_version": "1.0",
    "task_summary": "Filter peptide sequences by amino-acid length.",
    "steps": [
        {
            "id": "step_01",
            "skill": "peptide_filter",
            "inputs": [{"source": "uploaded", "ref": "peptides"}],
            "parameters": {"min_length": 13, "max_length": 26},
            "outputs": [{"name": "filtered", "format": "fasta"}],
            "reason": "Retain peptides between 13 and 26 amino acids.",
        }
    ],
}


# The control layer the desktop planner runs with. These rules and the blocked
# schema are the ones the PaleoRigor arm of the frozen evaluation received
# (supplementary/file_4_system_prompts); a test keeps the two identical.
CONTROL_LAYER_RULES = (
    "PALEORIGOR_CONTROL_LAYER=enabled",
    "When the request conflicts with the observed file format, return blocked with reason_code file_type_mismatch; do not substitute another analysis.",
    "When a named paired-end mate is absent, return blocked with reason_code missing_mate; do not invent or reuse a file.",
    "FastQC or general QC cannot prove ancient authenticity or absence of contamination. Return blocked with reason_code unsupported_scientific_claim for such proof requests.",
    "mapDamage and DamageProfiler require aligned BAM data and an explicit valid reference workflow. If prerequisites are absent, return blocked with reason_code missing_prerequisite; never choose an arbitrary reference.",
    "Read alignment and host-DNA removal require an explicit reference genome or named existing index. If it is absent, return blocked with reason_code missing_prerequisite; never invent or guess one.",
    "A blocked decision is valid JSON and takes precedence over the workflow-only wording above when a scientific or input boundary is reached.",
)

BLOCKED_JSON_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["status", "reason_code", "message"],
    "properties": {
        "status": {"const": "blocked"},
        "reason_code": {
            "enum": [
                "file_type_mismatch",
                "missing_mate",
                "unsupported_scientific_claim",
                "missing_prerequisite",
            ]
        },
        "message": {"type": "string", "minLength": 1},
    },
}


def build_planner_prompt(file_summaries, skill_descriptors) -> str:
    """The system prompt the desktop app sends: the workflow contract plus the control layer."""
    return "\n".join(
        [
            build_system_prompt(file_summaries, skill_descriptors),
            *CONTROL_LAYER_RULES,
            f"BLOCKED_JSON_SCHEMA={json.dumps(BLOCKED_JSON_SCHEMA, ensure_ascii=False)}",
        ]
    )


def build_system_prompt(file_summaries, skill_descriptors) -> str:
    return "\n".join(
        [
            "You are the workflow planner for a local research data application.",
            "Return exactly one JSON object matching workflow schema version 1.0.",
            "Use only skill names listed in AVAILABLE_SKILLS.",
            "Do not return shell commands, source code, markdown, or prose outside JSON.",
            "Do not invent files or outputs. Every step must explain its reason.",
            "The model plans only. Registered local Skills execute the work.",
            "Use these exact field names. Never rename parameters to params or schema_version to version.",
            "Treat workflows as staged scientific pipelines, not isolated tool calls.",
            "Use the actual uploaded file formats in FILES as hard constraints when choosing Skills.",
            "Do not plan FASTQ-only Skills for CSV or TSV uploads; do not plan CSV-only Skills for FASTQ uploads.",
            "For raw FASTQ/FASTA/CSV/TSV inputs, include file type detection or sample/pair validation when useful.",
            "For sequencing workflows, run raw QC before cleaning or downstream analysis.",
            "FastQC accepts .fastq.gz and .fq.gz directly. Do not insert gzip_decompress before fastq_qc for files whose FILES format is fastq, even when the filename ends with .gz.",
            "After cleaning, filtering, host-removal, deduplication, or normalization, run a cleaned-data quality gate before downstream application analysis.",
            "Do not jump directly from raw data to application analysis such as taxonomy, alignment, AMP prediction, clustering, assembly, or functional profiling.",
            "Use reporting or export Skills at the end when the user asks for a report, summary, chart, or reusable output.",
            "Peptide CSV staged template: peptide_csv_normalize -> peptide_validate -> peptide_deduplicate -> data_quality_gate -> requested peptide filtering/statistics/charts/export/prediction.",
            "For peptide CSV workflows, duplicate sequences are normally handled by peptide_deduplicate; Do not set fail_on_error true before deduplication.",
            "For headerless peptide CSV files, let peptide_csv_normalize auto-detect columns or use numeric zero-based indices only. Do not set label_column or sequence_column to observed row values such as 1, 0, or an actual peptide sequence.",
            "FASTQ staged template: file_type_detect -> fastq_pair_match -> fastq_qc -> multiqc_summary -> requested cleaning/filtering/host-removal -> data_quality_gate -> requested downstream application.",
            "For paired-end reads, use one separate fastq_qc step per mate, then pass both FastQC ZIP outputs to multiqc_summary. Do not combine both mates into one fastq_qc step.",
            "Read alignment and host-DNA removal require an explicit reference genome or a named existing index. Never invent, guess, or silently substitute a reference genome or index.",
            "sample_sheet_prepare converts archive metadata into a sample sheet. Do not add sample_sheet_validate when the referenced FASTQ files were not uploaded or otherwise shown to exist, unless the user explicitly asks for that validation.",
            "For uploaded raw peptide CSV or TSV files, normalize before peptide operations.",
            "Validate canonical peptide tables before filtering, statistics, charts, or export.",
            "peptide_validate has two canonical CSV outputs: validated_csv (valid rows) and rejected_csv (rejected rows). Use validated_csv for downstream steps and declare rejected_csv when an audit table is needed.",
            "peptide_statistics canonical summary outputs are statistics_json and statistics_csv; length_distribution_csv and amino_acid_composition_csv are optional detail tables.",
            "For peptide_chart, use only the canonical chart names length_histogram, label_counts, or amino_acid_composition.",
            "Use only optional peptide operations requested by the user.",
            "Do not invent peptide prediction or machine-learning steps.",
            f"WORKFLOW_JSON_SCHEMA={json.dumps(Workflow.model_json_schema(), ensure_ascii=False)}",
            f"VALID_EXAMPLE={json.dumps(WORKFLOW_EXAMPLE, ensure_ascii=False)}",
            f"FILES={json.dumps(file_summaries, ensure_ascii=False)}",
            f"AVAILABLE_SKILLS={json.dumps([asdict(item) for item in skill_descriptors], ensure_ascii=False)}",
        ]
    )
