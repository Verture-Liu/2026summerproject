from pathlib import Path

from research_agent.skills.base import SkillContext
from research_agent.skills.metagenome_tools.base import LocalCliSkill, object_schema


THREADS = {"type": "integer", "minimum": 1, "maximum": 64}
MIN_LENGTH = {"type": "integer", "minimum": 1, "maximum": 10000}


class FastpPreprocessSkill(LocalCliSkill):
    max_inputs = 2
    name = "fastp_preprocess"
    description = "Trim adapters and low-quality bases from FASTQ reads with fastp."
    executable_candidates = ("fastp",)
    official_url = "https://github.com/OpenGene/fastp"
    installation_hint = "Install fastp from Bioconda or the official release."
    input_formats = {"fastq"}
    output_formats = {"fastq", "html", "json"}
    parameter_schema = object_schema(
        {"threads": THREADS, "min_length": MIN_LENGTH}
    )

    def build_command(self, context, parameters, executable):
        if len(context.inputs) not in {1, 2}:
            raise ValueError("fastp accepts one single-end or two paired-end FASTQ files")
        command = [executable, "--in1", str(context.inputs[0])]
        if len(context.inputs) == 2:
            command += [
                "--in2", str(context.inputs[1]),
                "--out1", str(context.work_dir / "trimmed_R1.fastq.gz"),
                "--out2", str(context.work_dir / "trimmed_R2.fastq.gz"),
            ]
        else:
            command += ["--out1", str(context.work_dir / "trimmed.fastq.gz")]
        command += [
            "--thread", str(parameters.get("threads", 4)),
            "--length_required", str(parameters.get("min_length", 30)),
            "--html", str(context.work_dir / "fastp.html"),
            "--json", str(context.work_dir / "fastp.json"),
        ]
        return command

    def output_roots(self, context, parameters):
        return [
            context.work_dir / "trimmed.fastq.gz",
            context.work_dir / "trimmed_R1.fastq.gz",
            context.work_dir / "trimmed_R2.fastq.gz",
            context.work_dir / "fastp.html",
            context.work_dir / "fastp.json",
        ]


class AdapterRemovalPreprocessSkill(LocalCliSkill):
    max_inputs = 2
    name = "adapterremoval_preprocess"
    description = "Trim and optionally merge ancient paired-end FASTQ reads with AdapterRemoval."
    executable_candidates = ("AdapterRemoval",)
    official_url = "https://github.com/MikkelSchubert/adapterremoval"
    installation_hint = "Install AdapterRemoval from Bioconda or its official repository."
    input_formats = {"fastq"}
    output_formats = {"fastq", "txt"}
    parameter_schema = object_schema(
        {"threads": THREADS, "min_length": MIN_LENGTH, "collapse": {"type": "boolean"}}
    )

    def build_command(self, context, parameters, executable):
        if len(context.inputs) not in {1, 2}:
            raise ValueError("AdapterRemoval accepts one or two FASTQ inputs")
        command = [
            executable,
            "--file1", str(context.inputs[0]),
            "--basename", str(context.work_dir / "adapterremoval"),
            "--threads", str(parameters.get("threads", 4)),
            "--minlength", str(parameters.get("min_length", 30)),
            "--gzip",
        ]
        if len(context.inputs) == 2:
            command += ["--file2", str(context.inputs[1])]
            if parameters.get("collapse", True):
                command.append("--collapse")
        return command

    def output_roots(self, context, parameters):
        prefix = context.work_dir / "adapterremoval"
        return [
            Path(str(prefix) + suffix)
            for suffix in (
                ".settings",
                ".collapsed.gz",
                ".pair1.truncated.gz",
                ".pair2.truncated.gz",
                ".singleton.truncated.gz",
                ".discarded.gz",
                ".truncated.gz",
            )
        ]


class CutadaptPreprocessSkill(LocalCliSkill):
    max_inputs = 2
    name = "cutadapt_preprocess"
    description = "Trim adapters and filter short FASTQ reads with Cutadapt."
    executable_candidates = ("cutadapt",)
    official_url = "https://github.com/marcelm/cutadapt"
    installation_hint = "Install Cutadapt from Bioconda or PyPI in a dedicated environment."
    input_formats = {"fastq"}
    output_formats = {"fastq", "json"}
    parameter_schema = object_schema(
        {
            "threads": THREADS,
            "min_length": MIN_LENGTH,
            "adapter_r1": {"type": "string"},
            "adapter_r2": {"type": "string"},
        }
    )

    def build_command(self, context, parameters, executable):
        if len(context.inputs) not in {1, 2}:
            raise ValueError("Cutadapt accepts one or two FASTQ inputs")
        command = [
            executable,
            "--cores", str(parameters.get("threads", 4)),
            "--minimum-length", str(parameters.get("min_length", 30)),
            "--json", str(context.work_dir / "cutadapt.json"),
        ]
        if parameters.get("adapter_r1"):
            command += ["-a", parameters["adapter_r1"]]
        command += ["-o", str(context.work_dir / "trimmed_R1.fastq.gz")]
        if len(context.inputs) == 2:
            if parameters.get("adapter_r2"):
                command += ["-A", parameters["adapter_r2"]]
            command += ["-p", str(context.work_dir / "trimmed_R2.fastq.gz")]
        return command + [str(path) for path in context.inputs]

    def output_roots(self, context, parameters):
        return [
            context.work_dir / "trimmed_R1.fastq.gz",
            context.work_dir / "trimmed_R2.fastq.gz",
            context.work_dir / "cutadapt.json",
        ]
