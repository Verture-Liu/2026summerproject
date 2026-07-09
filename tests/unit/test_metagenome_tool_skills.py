from pathlib import Path
from subprocess import CompletedProcess

from research_agent.skills.base import SkillContext
from research_agent.skills.metagenome_tools import metagenome_tool_skills
from research_agent.skills.metagenome_tools.assembly import MegahitAssemblySkill, MetaspadesAssemblySkill
from research_agent.skills.metagenome_tools.ancient import (
    Bowtie2AlignSkill,
    BwaAlignSkill,
    SamtoolsSortIndexSkill,
)
from research_agent.skills.metagenome_tools.functional import (
    BrackenAbundanceSkill,
    DiamondBlastxSkill,
)
from research_agent.skills.metagenome_tools.preprocessing import FastpPreprocessSkill
from research_agent.skills.metagenome_tools.taxonomy import Kraken2ProfileSkill


EXPECTED_NAMES = {
    "fastp_preprocess",
    "adapterremoval_preprocess",
    "cutadapt_preprocess",
    "metaphlan_profile",
    "kraken2_profile",
    "malt_profile",
    "megahit_assembly",
    "metaspades_assembly",
    "metabat2_binning",
    "maxbin2_binning",
    "concoct_binning",
    "dastool_refine",
    "checkm2_quality",
    "drep_dereplicate",
    "gtdbtk_classify",
    "bwa_align",
    "bowtie2_align",
    "samtools_sort_index",
    "samtools_stats",
    "picard_markduplicates",
    "dedup_pcr_duplicates",
    "damageprofiler_profile",
    "qualimap_bamqc",
    "mosdepth_coverage",
    "bracken_abundance",
    "humann_profile",
    "diamond_blastx",
    "blastn_search",
}


def test_exposes_first_batch_of_paper_tool_skills():
    skills = metagenome_tool_skills()
    assert {skill.name for skill in skills} == EXPECTED_NAMES
    assert all(
        skill.parameter_schema["additionalProperties"] is False
        for skill in skills
    )


def test_fastp_reports_missing_dependency_without_running(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "research_agent.skills.metagenome_tools.base.resolve_tool",
        lambda names: None,
    )
    result = FastpPreprocessSkill().run(
        SkillContext(
            tmp_path / "work",
            [tmp_path / "sample_R1.fastq.gz", tmp_path / "sample_R2.fastq.gz"],
        ),
        {},
    )
    assert result.status == "dependency_missing"
    assert result.metrics["dependency_report"]["tool"] == "fastp"
    assert "automatically" in result.error


def test_fastp_builds_paired_command_inside_work_directory(tmp_path):
    context = SkillContext(
        tmp_path / "work",
        [tmp_path / "sample_R1.fastq.gz", tmp_path / "sample_R2.fastq.gz"],
    )
    command = FastpPreprocessSkill().build_command(
        context, {"threads": 6, "min_length": 30}, "/usr/bin/fastp"
    )
    assert command == [
        "/usr/bin/fastp",
        "--in1", str(context.inputs[0]),
        "--in2", str(context.inputs[1]),
        "--out1", str(context.work_dir / "trimmed_R1.fastq.gz"),
        "--out2", str(context.work_dir / "trimmed_R2.fastq.gz"),
        "--thread", "6",
        "--length_required", "30",
        "--html", str(context.work_dir / "fastp.html"),
        "--json", str(context.work_dir / "fastp.json"),
    ]


def test_metaspades_uses_meta_flag_when_falling_back_to_spades_py(tmp_path):
    context = SkillContext(tmp_path / "work", [tmp_path / "reads.fastq.gz"])
    command = MetaspadesAssemblySkill().build_command(
        context,
        {"threads": 3},
        "spades.py",
    )
    assert command[:2] == ["spades.py", "--meta"]
    assert "-s" in command


def test_kraken_requires_database_and_builds_report_command(tmp_path):
    context = SkillContext(tmp_path / "work", [tmp_path / "reads.fastq.gz"])
    command = Kraken2ProfileSkill().build_command(
        context,
        {"database": "/db/kraken", "threads": 4, "confidence": 0.15},
        "/usr/bin/kraken2",
    )
    assert command[:7] == [
        "/usr/bin/kraken2",
        "--db", "/db/kraken",
        "--threads", "4",
        "--confidence", "0.15",
    ]
    assert "--report" in command
    assert command[-1] == str(context.inputs[0])


def test_bwa_align_builds_sam_output_command(tmp_path):
    context = SkillContext(tmp_path / "work", [tmp_path / "reads.fastq.gz"])
    command = BwaAlignSkill().build_command(
        context,
        {"reference": "/refs/human.fa", "threads": 8},
        "/usr/bin/bwa",
    )
    assert command == [
        "/usr/bin/bwa",
        "mem",
        "-t", "8",
        "-o", str(context.work_dir / "bwa_aligned.sam"),
        "/refs/human.fa",
        str(context.inputs[0]),
    ]


def test_bowtie2_align_builds_paired_command(tmp_path):
    context = SkillContext(
        tmp_path / "work",
        [tmp_path / "R1.fastq.gz", tmp_path / "R2.fastq.gz"],
    )
    command = Bowtie2AlignSkill().build_command(
        context,
        {"index": "/indexes/human", "threads": 4, "very_sensitive": True},
        "/usr/bin/bowtie2",
    )
    assert command == [
        "/usr/bin/bowtie2",
        "-x", "/indexes/human",
        "-p", "4",
        "--very-sensitive",
        "-1", str(context.inputs[0]),
        "-2", str(context.inputs[1]),
        "-S", str(context.work_dir / "bowtie2_aligned.sam"),
    ]


def test_samtools_sort_index_reports_missing_samtools(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "research_agent.skills.metagenome_tools.base.resolve_tool",
        lambda names: None,
    )
    result = SamtoolsSortIndexSkill().run(
        SkillContext(tmp_path / "work", [tmp_path / "aligned.sam"]),
        {},
    )
    assert result.status == "dependency_missing"
    assert "samtools" in result.error


def test_bracken_builds_abundance_command(tmp_path):
    context = SkillContext(tmp_path / "work", [tmp_path / "kraken2_report.tsv"])
    command = BrackenAbundanceSkill().build_command(
        context,
        {"database": "/db/kraken", "read_length": 75, "level": "S"},
        "/usr/bin/bracken",
    )
    assert command == [
        "/usr/bin/bracken",
        "-d", "/db/kraken",
        "-i", str(context.inputs[0]),
        "-o", str(context.work_dir / "bracken_abundance.tsv"),
        "-r", "75",
        "-l", "S",
    ]


def test_diamond_builds_blastx_command(tmp_path):
    context = SkillContext(tmp_path / "work", [tmp_path / "reads.fasta"])
    command = DiamondBlastxSkill().build_command(
        context,
        {"database": "/db/nr.dmnd", "threads": 12},
        "/usr/bin/diamond",
    )
    assert command[:6] == [
        "/usr/bin/diamond",
        "blastx",
        "--db", "/db/nr.dmnd",
        "--query", str(context.inputs[0]),
    ]
    assert "--outfmt" in command


def test_megahit_builds_paired_assembly_command(tmp_path):
    context = SkillContext(
        tmp_path / "work",
        [tmp_path / "R1.fastq.gz", tmp_path / "R2.fastq.gz"],
    )
    command = MegahitAssemblySkill().build_command(
        context, {"threads": 8, "min_contig_length": 1000}, "/usr/bin/megahit"
    )
    assert command == [
        "/usr/bin/megahit",
        "-1", str(context.inputs[0]),
        "-2", str(context.inputs[1]),
        "-o", str(context.work_dir / "megahit"),
        "-t", "8",
        "--min-contig-len", "1000",
    ]


def test_successful_command_without_tool_outputs_is_failed(tmp_path, monkeypatch):
    source = tmp_path / "reads.fastq.gz"
    source.write_bytes(b"reads")
    skill = FastpPreprocessSkill()
    monkeypatch.setattr(skill, "find_executable", lambda: "/usr/bin/fastp")
    monkeypatch.setattr(
        "research_agent.skills.metagenome_tools.base.run_command",
        lambda *args, **kwargs: CompletedProcess(args[0], 0, "", ""),
    )
    result = skill.run(SkillContext(tmp_path / "work", [source]), {})
    assert result.status == "failed"
    assert "without expected outputs" in result.error
