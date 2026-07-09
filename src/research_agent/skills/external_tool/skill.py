import shutil

from research_agent.skills.base import SkillContext, SkillResult


class ExternalToolSkill:
    def __init__(
        self,
        *,
        name: str,
        description: str,
        executable: str,
        input_formats: set[str],
        output_formats: set[str],
        parameter_schema: dict,
    ):
        self.name = name
        self.description = description
        self.executable = executable
        self.input_formats = input_formats
        self.output_formats = output_formats
        self.parameter_schema = parameter_schema
        self.resource_class = "heavy"

    def run(self, context: SkillContext, parameters: dict) -> SkillResult:
        executable = shutil.which(self.executable)
        if executable is None:
            return SkillResult(
                status="dependency_missing",
                outputs=[],
                metrics={},
                warnings=[],
                error=f"Required tool is not installed: {self.executable}",
            )
        return SkillResult(
            status="not_configured",
            outputs=[],
            metrics={"executable": executable},
            warnings=[],
            error=(
                f"{self.name} is registered for planning, but its version-specific "
                "command adapter is not configured in this MVP."
            ),
        )


def amp_external_skills() -> list[ExternalToolSkill]:
    no_extra = {"type": "object", "properties": {}, "additionalProperties": False}
    return [
        ExternalToolSkill(
            name="environmental_decontamination",
            description="Remove reads shared with environmental control samples.",
            executable="kneaddata",
            input_formats={"fastq"},
            output_formats={"fastq"},
            parameter_schema=no_extra,
        ),
        ExternalToolSkill(
            name="host_dna_removal",
            description="Remove reads aligning to a configured host reference.",
            executable="kneaddata",
            input_formats={"fastq"},
            output_formats={"fastq"},
            parameter_schema={
                "type": "object",
                "required": ["reference"],
                "properties": {"reference": {"type": "string"}},
                "additionalProperties": False,
            },
        ),
        ExternalToolSkill(
            name="fastq_quality_filter",
            description="Filter FASTQ reads by validated length and quality settings.",
            executable="cutadapt",
            input_formats={"fastq"},
            output_formats={"fastq"},
            parameter_schema={
                "type": "object",
                "required": ["min_length"],
                "properties": {"min_length": {"type": "integer", "minimum": 1}},
                "additionalProperties": False,
            },
        ),
        ExternalToolSkill(
            name="metagenome_assembly",
            description="Assemble metagenomic reads into contigs.",
            executable="spades.py",
            input_formats={"fastq"},
            output_formats={"fasta"},
            parameter_schema={
                "type": "object",
                "required": ["mode"],
                "properties": {"mode": {"enum": ["meta"]}},
                "additionalProperties": False,
            },
        ),
        ExternalToolSkill(
            name="orf_extraction",
            description="Extract ORFs and translate them into peptide sequences.",
            executable="prodigal",
            input_formats={"fasta"},
            output_formats={"fasta"},
            parameter_schema={
                "type": "object",
                "required": ["min_nt", "max_nt"],
                "properties": {
                    "min_nt": {"type": "integer", "minimum": 3},
                    "max_nt": {"type": "integer", "minimum": 3},
                },
                "additionalProperties": False,
            },
        ),
        ExternalToolSkill(
            name="cross_sample_presence_filter",
            description="Retain sequences observed across a minimum number of samples.",
            executable="seqkit",
            input_formats={"csv", "fasta"},
            output_formats={"csv", "fasta"},
            parameter_schema={
                "type": "object",
                "required": ["min_samples"],
                "properties": {"min_samples": {"type": "integer", "minimum": 1}},
                "additionalProperties": False,
            },
        ),
        ExternalToolSkill(
            name="sequence_deduplicate",
            description="Create a non-redundant sequence set.",
            executable="seqkit",
            input_formats={"csv", "fasta"},
            output_formats={"csv", "fasta"},
            parameter_schema=no_extra,
        ),
        ExternalToolSkill(
            name="cytotoxicity_prediction",
            description="Run a configured peptide cytotoxicity predictor.",
            executable="toxinpred",
            input_formats={"csv", "fasta"},
            output_formats={"csv"},
            parameter_schema=no_extra,
        ),
    ]
