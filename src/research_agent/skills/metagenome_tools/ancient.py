from __future__ import annotations

import subprocess

from research_agent.skills.ancient_dna.common import run_command, write_metadata
from research_agent.skills.base import SkillResult
from research_agent.skills.metagenome_tools.base import LocalCliSkill, object_schema


THREADS = {"type": "integer", "minimum": 1, "maximum": 64}
REFERENCE = {"type": "string", "minLength": 1}
INDEX = {"type": "string", "minLength": 1}


class BwaAlignSkill(LocalCliSkill):
    max_inputs = 2
    name = "bwa_align"
    description = "Align FASTQ reads to a reference genome with BWA MEM."
    executable_candidates = ("bwa",)
    official_url = "https://github.com/lh3/bwa"
    installation_hint = "Install BWA and prepare an indexed reference genome."
    input_formats = {"fastq"}
    output_formats = {"sam"}
    parameter_schema = object_schema({"reference": REFERENCE, "threads": THREADS}, ["reference"])

    def build_command(self, context, parameters, executable):
        return [
            executable,
            "mem",
            "-t", str(parameters.get("threads", 4)),
            "-o", str(context.work_dir / "bwa_aligned.sam"),
            parameters["reference"],
            *[str(path) for path in context.inputs],
        ]

    def output_roots(self, context, parameters):
        return [context.work_dir / "bwa_aligned.sam"]


class Bowtie2AlignSkill(LocalCliSkill):
    max_inputs = 2
    name = "bowtie2_align"
    description = "Align single-end or paired-end FASTQ reads to a Bowtie2 index."
    executable_candidates = ("bowtie2",)
    official_url = "https://bowtie-bio.sourceforge.net/bowtie2/index.shtml"
    installation_hint = "Install Bowtie2 and prepare a Bowtie2 index."
    input_formats = {"fastq"}
    output_formats = {"sam"}
    parameter_schema = object_schema(
        {"index": INDEX, "threads": THREADS, "very_sensitive": {"type": "boolean"}},
        ["index"],
    )

    def build_command(self, context, parameters, executable):
        if len(context.inputs) not in {1, 2}:
            raise ValueError("Bowtie2 accepts one single-end or two paired-end FASTQ inputs")
        command = [
            executable,
            "-x", parameters["index"],
            "-p", str(parameters.get("threads", 4)),
        ]
        if parameters.get("very_sensitive", False):
            command.append("--very-sensitive")
        if len(context.inputs) == 2:
            command += ["-1", str(context.inputs[0]), "-2", str(context.inputs[1])]
        else:
            command += ["-U", str(context.inputs[0])]
        command += ["-S", str(context.work_dir / "bowtie2_aligned.sam")]
        return command

    def output_roots(self, context, parameters):
        return [context.work_dir / "bowtie2_aligned.sam"]


class SamtoolsSortIndexSkill(LocalCliSkill):
    name = "samtools_sort_index"
    description = "Sort an alignment file into BAM format and create a BAM index with samtools."
    executable_candidates = ("samtools",)
    official_url = "https://www.htslib.org/"
    installation_hint = "Install samtools from Bioconda, Homebrew, or the official HTSlib project."
    input_formats = {"sam", "bam"}
    output_formats = {"bam", "bai", "json"}
    parameter_schema = object_schema({"threads": THREADS})

    def build_command(self, context, parameters, executable):
        return [
            executable,
            "sort",
            "-@", str(parameters.get("threads", 4)),
            "-o", str(context.work_dir / "sorted.bam"),
            str(context.inputs[0]),
        ]

    def output_roots(self, context, parameters):
        return [context.work_dir / "sorted.bam", context.work_dir / "sorted.bam.bai"]

    def run(self, context, parameters):
        executable = self.find_executable()
        if executable is None:
            return SkillResult(
                "dependency_missing",
                [],
                {"dependency_report": {"tool": "samtools", "official_url": self.official_url}},
                [],
                "Required tool is missing: samtools. Install samtools, then restart the Agent.",
            )
        try:
            if not context.inputs or not context.inputs[0].exists():
                raise ValueError("Input SAM/BAM file does not exist")
            context.work_dir.mkdir(parents=True, exist_ok=True)
            sorted_bam = context.work_dir / "sorted.bam"
            sort_cmd = self.build_command(context, parameters, executable)
            index_cmd = [executable, "index", str(sorted_bam)]
            for name, command in (("sort", sort_cmd), ("index", index_cmd)):
                completed = run_command(
                    command,
                    cwd=context.work_dir,
                    stdout_path=context.work_dir / f"samtools_{name}_stdout.log",
                    stderr_path=context.work_dir / f"samtools_{name}_stderr.log",
                    timeout=self.timeout_seconds,
                )
                if completed.returncode:
                    raise RuntimeError(
                        f"samtools {name} exited with code {completed.returncode}: {completed.stderr.strip()}"
                    )
            outputs = [path for path in self.output_roots(context, parameters) if path.exists()]
            metadata = write_metadata(
                context.work_dir / "samtools_sort_index_run_metadata.json",
                {"skill": self.name, "tool": "samtools", "commands": [sort_cmd, index_cmd], "outputs": [str(path) for path in outputs]},
            )
            return SkillResult("succeeded", [str(path) for path in outputs] + [str(metadata)], {"output_count": len(outputs)}, [])
        except subprocess.TimeoutExpired:
            return SkillResult("failed", [], {}, [], "samtools timed out")
        except Exception as exc:
            return SkillResult("failed", [], {}, [], str(exc))


class SamtoolsStatsSkill(LocalCliSkill):
    name = "samtools_stats"
    description = "Generate alignment statistics from BAM or SAM files with samtools stats."
    executable_candidates = ("samtools",)
    official_url = "https://www.htslib.org/"
    installation_hint = "Install samtools from Bioconda, Homebrew, or the official HTSlib project."
    input_formats = {"sam", "bam"}
    output_formats = {"txt", "json"}
    parameter_schema = object_schema({})

    def build_command(self, context, parameters, executable):
        return [executable, "stats", str(context.inputs[0])]

    def output_roots(self, context, parameters):
        return [context.work_dir / "samtools_stats.txt"]

    def run(self, context, parameters):
        executable = self.find_executable()
        if executable is None:
            return SkillResult("dependency_missing", [], {}, [], "Required tool is missing: samtools")
        try:
            context.work_dir.mkdir(parents=True, exist_ok=True)
            command = self.build_command(context, parameters, executable)
            completed = run_command(
                command,
                cwd=context.work_dir,
                stdout_path=context.work_dir / "samtools_stats.txt",
                stderr_path=context.work_dir / "samtools_stats_stderr.log",
                timeout=self.timeout_seconds,
            )
            if completed.returncode:
                raise RuntimeError(f"samtools stats exited with code {completed.returncode}: {completed.stderr.strip()}")
            metadata = write_metadata(context.work_dir / "samtools_stats_run_metadata.json", {"command": command})
            return SkillResult("succeeded", [str(context.work_dir / "samtools_stats.txt"), str(metadata)], {}, [])
        except Exception as exc:
            return SkillResult("failed", [], {}, [], str(exc))


class PicardMarkDuplicatesSkill(LocalCliSkill):
    name = "picard_markduplicates"
    description = "Mark or remove PCR duplicates from BAM files with Picard MarkDuplicates."
    executable_candidates = ("picard",)
    official_url = "https://broadinstitute.github.io/picard/"
    installation_hint = "Install Picard and ensure the picard command is available on PATH."
    input_formats = {"bam"}
    output_formats = {"bam", "txt"}
    parameter_schema = object_schema({"remove_duplicates": {"type": "boolean"}})

    def build_command(self, context, parameters, executable):
        return [
            executable,
            "MarkDuplicates",
            f"I={context.inputs[0]}",
            f"O={context.work_dir / 'picard_markduplicates.bam'}",
            f"M={context.work_dir / 'picard_markduplicates_metrics.txt'}",
            f"REMOVE_DUPLICATES={str(parameters.get('remove_duplicates', False)).lower()}",
        ]

    def output_roots(self, context, parameters):
        return [
            context.work_dir / "picard_markduplicates.bam",
            context.work_dir / "picard_markduplicates_metrics.txt",
        ]


class DedupPcrDuplicatesSkill(LocalCliSkill):
    name = "dedup_pcr_duplicates"
    description = "Remove PCR duplicates from ancient DNA BAM files with DeDup."
    executable_candidates = ("dedup", "DeDup")
    official_url = "https://github.com/apeltzer/DeDup"
    installation_hint = "Install DeDup and confirm the dedup command is available."
    input_formats = {"bam"}
    output_formats = {"bam", "json", "txt"}
    parameter_schema = object_schema({"merged": {"type": "boolean"}})

    def build_command(self, context, parameters, executable):
        prefix = context.work_dir / "dedup"
        command = [executable, "-i", str(context.inputs[0]), "-o", str(prefix)]
        if parameters.get("merged", True):
            command.append("-m")
        return command

    def output_roots(self, context, parameters):
        return [context.work_dir]


class DamageProfilerSkill(LocalCliSkill):
    name = "damageprofiler_profile"
    description = "Profile ancient DNA damage patterns from BAM alignments with DamageProfiler."
    executable_candidates = ("DamageProfiler",)
    official_url = "https://github.com/Integrative-Transcriptomics/DamageProfiler"
    installation_hint = "Install DamageProfiler and provide a matching reference FASTA."
    input_formats = {"bam"}
    output_formats = {"txt", "pdf", "json"}
    parameter_schema = object_schema({"reference": REFERENCE, "threads": THREADS}, ["reference"])

    def build_command(self, context, parameters, executable):
        return [
            executable,
            "-i", str(context.inputs[0]),
            "-r", parameters["reference"],
            "-o", str(context.work_dir / "damageprofiler"),
            "-t", str(parameters.get("threads", 4)),
        ]

    def output_roots(self, context, parameters):
        return [context.work_dir / "damageprofiler"]


class QualimapBamqcSkill(LocalCliSkill):
    name = "qualimap_bamqc"
    description = "Assess BAM alignment quality with Qualimap bamqc."
    executable_candidates = ("qualimap",)
    official_url = "http://qualimap.conesalab.org/"
    installation_hint = "Install Qualimap and ensure the qualimap command is available."
    input_formats = {"bam"}
    output_formats = {"html", "txt", "pdf"}
    parameter_schema = object_schema({"threads": THREADS})

    def build_command(self, context, parameters, executable):
        return [
            executable,
            "bamqc",
            "-bam", str(context.inputs[0]),
            "-outdir", str(context.work_dir / "qualimap_bamqc"),
            "-nt", str(parameters.get("threads", 4)),
        ]

    def output_roots(self, context, parameters):
        return [context.work_dir / "qualimap_bamqc"]


class MosdepthCoverageSkill(LocalCliSkill):
    name = "mosdepth_coverage"
    description = "Calculate genome coverage summaries from BAM files with mosdepth."
    executable_candidates = ("mosdepth",)
    official_url = "https://github.com/brentp/mosdepth"
    installation_hint = "Install mosdepth from Bioconda or its official release."
    input_formats = {"bam"}
    output_formats = {"txt", "bed", "gz"}
    parameter_schema = object_schema({"threads": THREADS})

    def build_command(self, context, parameters, executable):
        return [
            executable,
            "-t", str(parameters.get("threads", 4)),
            str(context.work_dir / "mosdepth"),
            str(context.inputs[0]),
        ]

    def output_roots(self, context, parameters):
        return [context.work_dir]


def ancient_metagenome_alignment_skills():
    return [
        BwaAlignSkill(),
        Bowtie2AlignSkill(),
        SamtoolsSortIndexSkill(),
        SamtoolsStatsSkill(),
        PicardMarkDuplicatesSkill(),
        DedupPcrDuplicatesSkill(),
        DamageProfilerSkill(),
        QualimapBamqcSkill(),
        MosdepthCoverageSkill(),
    ]
