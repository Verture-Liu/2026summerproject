from pathlib import Path

from research_agent.skills.base import SkillContext
from research_agent.skills.sequence_utilities import (
    GzipCompressSkill,
    GzipDecompressSkill,
    SeqkitDeduplicateSkill,
    SeqkitLengthFilterSkill,
    SeqkitStatsSkill,
    SeqtkSampleSkill,
    _sequence_suffix,
)


def test_sequence_suffix_does_not_misclassify_fastq_as_fasta():
    assert _sequence_suffix(Path("reads.fastq")) == ".fastq"
    assert _sequence_suffix(Path("reads.fastq.gz")) == ".fastq"
    assert _sequence_suffix(Path("reads.fasta")) == ".fasta"


def test_seqkit_stats_reports_missing_seqkit(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "research_agent.skills.sequence_utilities.shutil.which",
        lambda name: None,
    )

    result = SeqkitStatsSkill().run(
        SkillContext(tmp_path / "work", [tmp_path / "reads.fastq.gz"]),
        {},
    )

    assert result.status == "dependency_missing"
    assert "seqkit" in result.error


def test_seqkit_length_filter_requires_min_or_max_length(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "research_agent.skills.sequence_utilities.shutil.which",
        lambda name: "/usr/local/bin/seqkit",
    )

    result = SeqkitLengthFilterSkill().run(
        SkillContext(tmp_path / "work", [tmp_path / "reads.fastq"]),
        {},
    )

    assert result.status == "failed"
    assert "min_length" in result.error


def test_seqkit_deduplicate_reports_missing_seqkit(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "research_agent.skills.sequence_utilities.shutil.which",
        lambda name: None,
    )

    result = SeqkitDeduplicateSkill().run(
        SkillContext(tmp_path / "work", [tmp_path / "reads.fasta"]),
        {},
    )

    assert result.status == "dependency_missing"
    assert "seqkit" in result.error


def test_seqtk_sample_reports_missing_seqtk(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "research_agent.skills.sequence_utilities.shutil.which",
        lambda name: None,
    )

    result = SeqtkSampleSkill().run(
        SkillContext(tmp_path / "work", [tmp_path / "reads.fastq"]),
        {"fraction": 0.5},
    )

    assert result.status == "dependency_missing"
    assert "seqtk" in result.error


def test_gzip_decompress_and_compress_roundtrip(tmp_path):
    source = tmp_path / "reads.fastq"
    source.write_text("@r1\nACGT\n+\n!!!!\n", encoding="utf-8")

    compressed = GzipCompressSkill().run(SkillContext(tmp_path / "compress", [source]), {})
    assert compressed.status == "succeeded"
    assert Path(compressed.outputs[0]).name == "reads.fastq.gz"

    decompressed = GzipDecompressSkill().run(
        SkillContext(tmp_path / "decompress", [Path(compressed.outputs[0])]),
        {},
    )

    assert decompressed.status == "succeeded"
    assert Path(decompressed.outputs[0]).read_text(encoding="utf-8") == source.read_text(
        encoding="utf-8"
    )
