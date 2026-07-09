from research_agent.skills.metagenome_tools.base import LocalCliSkill, object_schema


THREADS = {"type": "integer", "minimum": 1, "maximum": 64}
DATABASE = {"type": "string", "minLength": 1}


class BrackenAbundanceSkill(LocalCliSkill):
    name = "bracken_abundance"
    description = "Estimate species or genus abundance from a Kraken2 report with Bracken."
    executable_candidates = ("bracken",)
    official_url = "https://github.com/jenniferlu717/Bracken"
    installation_hint = "Install Bracken and prepare a Bracken-compatible Kraken database."
    input_formats = {"tsv", "txt"}
    output_formats = {"tsv"}
    parameter_schema = object_schema(
        {
            "database": DATABASE,
            "read_length": {"type": "integer", "minimum": 1},
            "level": {"enum": ["D", "P", "C", "O", "F", "G", "S"]},
        },
        ["database"],
    )

    def build_command(self, context, parameters, executable):
        return [
            executable,
            "-d", parameters["database"],
            "-i", str(context.inputs[0]),
            "-o", str(context.work_dir / "bracken_abundance.tsv"),
            "-r", str(parameters.get("read_length", 100)),
            "-l", parameters.get("level", "S"),
        ]

    def output_roots(self, context, parameters):
        return [context.work_dir / "bracken_abundance.tsv"]


class HumannProfileSkill(LocalCliSkill):
    name = "humann_profile"
    description = "Profile microbial gene families and pathways from metagenomic reads with HUMAnN."
    executable_candidates = ("humann",)
    official_url = "https://github.com/biobakery/humann"
    installation_hint = "Install HUMAnN and download its required nucleotide/protein databases."
    input_formats = {"fastq", "fasta"}
    output_formats = {"tsv", "log"}
    parameter_schema = object_schema({"threads": THREADS})

    def build_command(self, context, parameters, executable):
        return [
            executable,
            "--input", str(context.inputs[0]),
            "--output", str(context.work_dir / "humann"),
            "--threads", str(parameters.get("threads", 4)),
        ]

    def output_roots(self, context, parameters):
        return [context.work_dir / "humann"]


class DiamondBlastxSkill(LocalCliSkill):
    name = "diamond_blastx"
    description = "Search translated nucleotide sequences against a protein database with DIAMOND blastx."
    executable_candidates = ("diamond",)
    official_url = "https://github.com/bbuchfink/diamond"
    installation_hint = "Install DIAMOND and provide a local .dmnd database."
    input_formats = {"fasta", "fastq"}
    output_formats = {"tsv"}
    parameter_schema = object_schema({"database": DATABASE, "threads": THREADS}, ["database"])

    def build_command(self, context, parameters, executable):
        return [
            executable,
            "blastx",
            "--db", parameters["database"],
            "--query", str(context.inputs[0]),
            "--out", str(context.work_dir / "diamond_blastx.tsv"),
            "--threads", str(parameters.get("threads", 4)),
            "--outfmt", "6",
        ]

    def output_roots(self, context, parameters):
        return [context.work_dir / "diamond_blastx.tsv"]


class BlastnSearchSkill(LocalCliSkill):
    name = "blastn_search"
    description = "Search nucleotide FASTA sequences against a local BLAST database with blastn."
    executable_candidates = ("blastn",)
    official_url = "https://blast.ncbi.nlm.nih.gov/"
    installation_hint = "Install NCBI BLAST+ and provide a local nucleotide database."
    input_formats = {"fasta"}
    output_formats = {"tsv"}
    parameter_schema = object_schema({"database": DATABASE, "threads": THREADS}, ["database"])

    def build_command(self, context, parameters, executable):
        return [
            executable,
            "-db", parameters["database"],
            "-query", str(context.inputs[0]),
            "-out", str(context.work_dir / "blastn.tsv"),
            "-outfmt", "6",
            "-num_threads", str(parameters.get("threads", 4)),
        ]

    def output_roots(self, context, parameters):
        return [context.work_dir / "blastn.tsv"]


def functional_profile_skills():
    return [
        BrackenAbundanceSkill(),
        HumannProfileSkill(),
        DiamondBlastxSkill(),
        BlastnSearchSkill(),
    ]
