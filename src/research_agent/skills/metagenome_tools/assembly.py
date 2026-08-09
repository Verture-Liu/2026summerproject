from research_agent.skills.metagenome_tools.base import LocalCliSkill, object_schema


THREADS = {"type": "integer", "minimum": 1, "maximum": 128}
MIN_CONTIG = {"type": "integer", "minimum": 200}


class MegahitAssemblySkill(LocalCliSkill):
    max_inputs = 2
    name = "megahit_assembly"
    description = "Assemble metagenomic FASTQ reads into contigs with MEGAHIT."
    executable_candidates = ("megahit",)
    official_url = "https://github.com/voutcn/megahit"
    installation_hint = "Install MEGAHIT from Bioconda or its official release."
    input_formats = {"fastq"}
    output_formats = {"fasta", "txt"}
    parameter_schema = object_schema(
        {"threads": THREADS, "min_contig_length": MIN_CONTIG}
    )

    def build_command(self, context, parameters, executable):
        if len(context.inputs) not in {1, 2}:
            raise ValueError("MEGAHIT accepts one or two FASTQ inputs")
        command = [executable]
        if len(context.inputs) == 2:
            command += ["-1", str(context.inputs[0]), "-2", str(context.inputs[1])]
        else:
            command += ["-r", str(context.inputs[0])]
        return command + [
            "-o", str(context.work_dir / "megahit"),
            "-t", str(parameters.get("threads", 4)),
            "--min-contig-len", str(parameters.get("min_contig_length", 1000)),
        ]

    def output_roots(self, context, parameters):
        return [context.work_dir / "megahit"]


class MetaspadesAssemblySkill(LocalCliSkill):
    max_inputs = 2
    name = "metaspades_assembly"
    description = "Assemble metagenomic FASTQ reads into contigs with metaSPAdes."
    executable_candidates = ("spades.py", "metaspades.py")
    official_url = "https://github.com/ablab/spades"
    installation_hint = "Install SPAdes from Bioconda or its official release."
    input_formats = {"fastq"}
    output_formats = {"fasta", "txt"}
    parameter_schema = object_schema({"threads": THREADS})

    def build_command(self, context, parameters, executable):
        if len(context.inputs) not in {1, 2}:
            raise ValueError("metaSPAdes accepts one or two FASTQ inputs")
        command = [executable]
        if executable.endswith("spades.py"):
            command.append("--meta")
        if len(context.inputs) == 2:
            command += ["-1", str(context.inputs[0]), "-2", str(context.inputs[1])]
        else:
            command += ["-s", str(context.inputs[0])]
        return command + [
            "-t", str(parameters.get("threads", 4)),
            "-o", str(context.work_dir / "metaspades"),
        ]

    def output_roots(self, context, parameters):
        return [context.work_dir / "metaspades"]
