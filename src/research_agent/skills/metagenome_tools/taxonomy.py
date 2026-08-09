from research_agent.skills.metagenome_tools.base import LocalCliSkill, object_schema


THREADS = {"type": "integer", "minimum": 1, "maximum": 64}
DATABASE = {"type": "string", "minLength": 1}


class MetaphlanProfileSkill(LocalCliSkill):
    max_inputs = 2
    name = "metaphlan_profile"
    description = "Generate microbial taxonomic profiles from FASTQ reads with MetaPhlAn."
    executable_candidates = ("metaphlan",)
    official_url = "https://github.com/biobakery/MetaPhlAn"
    installation_hint = "Install MetaPhlAn and download its marker database separately."
    input_formats = {"fastq"}
    output_formats = {"tsv", "bowtie2"}
    parameter_schema = object_schema(
        {"database": DATABASE, "threads": THREADS}, ["database"]
    )

    def build_command(self, context, parameters, executable):
        reads = ",".join(str(path) for path in context.inputs)
        return [
            executable, reads,
            "--input_type", "fastq",
            "--bowtie2db", parameters["database"],
            "--nproc", str(parameters.get("threads", 4)),
            "--bowtie2out", str(context.work_dir / "metaphlan.bowtie2.bz2"),
            "-o", str(context.work_dir / "metaphlan_profile.tsv"),
        ]

    def output_roots(self, context, parameters):
        return [
            context.work_dir / "metaphlan_profile.tsv",
            context.work_dir / "metaphlan.bowtie2.bz2",
        ]


class Kraken2ProfileSkill(LocalCliSkill):
    max_inputs = 2
    name = "kraken2_profile"
    description = "Classify metagenomic FASTQ reads against a local Kraken2 database."
    executable_candidates = ("kraken2",)
    official_url = "https://github.com/DerrickWood/kraken2"
    installation_hint = "Install Kraken2 and prepare or download a Kraken2 database."
    input_formats = {"fastq"}
    output_formats = {"tsv", "txt"}
    parameter_schema = object_schema(
        {
            "database": DATABASE,
            "threads": THREADS,
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        },
        ["database"],
    )

    def build_command(self, context, parameters, executable):
        if len(context.inputs) not in {1, 2}:
            raise ValueError("Kraken2 accepts one or two FASTQ inputs")
        command = [
            executable,
            "--db", parameters["database"],
            "--threads", str(parameters.get("threads", 4)),
            "--confidence", str(parameters.get("confidence", 0.15)),
            "--report", str(context.work_dir / "kraken2_report.tsv"),
            "--output", str(context.work_dir / "kraken2_assignments.txt"),
        ]
        if len(context.inputs) == 2:
            command.append("--paired")
        return command + [str(path) for path in context.inputs]

    def output_roots(self, context, parameters):
        return [
            context.work_dir / "kraken2_report.tsv",
            context.work_dir / "kraken2_assignments.txt",
        ]


class MaltProfileSkill(LocalCliSkill):
    max_inputs = None
    name = "malt_profile"
    description = "Align and taxonomically bin ancient metagenomic reads with MALT."
    executable_candidates = ("malt-run",)
    official_url = "https://software-ab.cs.uni-tuebingen.de/download/malt/"
    installation_hint = "Install MALT and build a local MALT reference database."
    input_formats = {"fastq"}
    output_formats = {"rma6", "txt"}
    parameter_schema = object_schema(
        {
            "database": DATABASE,
            "threads": THREADS,
            "min_support": {"type": "integer", "minimum": 1},
            "min_percent_identity": {"type": "number", "minimum": 0, "maximum": 100},
        },
        ["database"],
    )

    def build_command(self, context, parameters, executable):
        return [
            executable,
            "-i", *[str(path) for path in context.inputs],
            "-d", parameters["database"],
            "-o", str(context.work_dir / "malt_output.rma6"),
            "-m", "BlastN",
            "-t", str(parameters.get("threads", 4)),
            "--minSupport", str(parameters.get("min_support", 10)),
            "--minPercentIdentity", str(parameters.get("min_percent_identity", 95)),
        ]

    def output_roots(self, context, parameters):
        return [context.work_dir / "malt_output.rma6"]
