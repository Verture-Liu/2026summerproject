from pathlib import Path
import json
import subprocess

import pandas as pd

from research_agent.skills.base import SkillContext
from research_agent.skills.conda_tools import ToolCommand
from research_agent.skills.ancient_dna.authentication import (
    AncientDnaAuthenticationSkill,
)
from research_agent.skills.ancient_dna.fastq_qc import FastqQcSkill
from research_agent.skills.ancient_dna.host_removal import HostDnaRemovalSkill
from research_agent.skills.ancient_dna.sample_sheet import SampleSheetPrepareSkill


def test_prepares_samplesheet_from_sra_runinfo(tmp_path):
    source = tmp_path / "runinfo.csv"
    source.write_text(
        "run_accession,sample_accession,library_layout,scientific_name\n"
        "SRR1,SAMN1,PAIRED,soil metagenome\n"
        "SRR2,SAMN2,SINGLE,dental calculus\n",
        encoding="utf-8",
    )
    result = SampleSheetPrepareSkill().run(
        SkillContext(tmp_path / "work", [source]),
        {"fastq_directory": "/data/reads"},
    )
    frame = pd.read_csv(result.outputs[0], keep_default_na=False)
    assert frame.to_dict("records") == [
        {
            "sample_id": "SAMN1",
            "run_accession": "SRR1",
            "layout": "paired",
            "fastq_1": "/data/reads/SRR1_1.fastq.gz",
            "fastq_2": "/data/reads/SRR1_2.fastq.gz",
            "organism": "soil metagenome",
        },
        {
            "sample_id": "SAMN2",
            "run_accession": "SRR2",
            "layout": "single",
            "fastq_1": "/data/reads/SRR2.fastq.gz",
            "fastq_2": "",
            "organism": "dental calculus",
        },
    ]


def test_fastq_qc_reports_missing_fastqc(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "research_agent.skills.ancient_dna.fastq_qc.resolve_tool",
        lambda names: None,
    )
    result = FastqQcSkill().run(
        SkillContext(tmp_path / "work", [tmp_path / "reads.fastq.gz"]),
        {},
    )
    assert result.status == "dependency_missing"
    assert "FastQC" in result.error
    assert result.metrics["dependency_report"]["official_url"].startswith("https://")


def test_fastq_qc_returns_outputs_in_declared_workflow_order(tmp_path, monkeypatch):
    source = tmp_path / "minimal_reads.fastq"
    source.write_text("@r1\nACGT\n+\n!!!!\n@r2\nGGCCAA\n+\n!!!!!!\n", encoding="utf-8")

    monkeypatch.setattr(
        "research_agent.skills.ancient_dna.fastq_qc.resolve_tool",
        lambda names: ToolCommand("fastqc", ["/usr/local/bin/fastqc"], "path"),
    )

    def fake_run_command(command, cwd, stdout_path, stderr_path, timeout):
        output_dir = Path(command[command.index("--outdir") + 1])
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "minimal_reads_fastqc.html").write_text(
            "<html>FastQC</html>",
            encoding="utf-8",
        )
        (output_dir / "minimal_reads_fastqc.zip").write_bytes(b"fake zip")
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(
        "research_agent.skills.ancient_dna.fastq_qc.run_command",
        fake_run_command,
    )

    result = FastqQcSkill().run(SkillContext(tmp_path / "work", [source]), {})

    assert result.status == "succeeded"
    assert [Path(output).suffix for output in result.outputs] == [
        ".html",
        ".json",
        ".zip",
    ]
    assert Path(result.outputs[0]).name == "minimal_reads_fastqc.html"
    assert Path(result.outputs[1]).name == "fastqc_run_metadata.json"
    assert Path(result.outputs[2]).name == "minimal_reads_fastqc.zip"
    metadata = json.loads(Path(result.outputs[1]).read_text(encoding="utf-8"))
    assert metadata["input_metrics"] == [
        {
            "path": str(source),
            "name": "minimal_reads.fastq",
            "records": 2,
            "total_bases": 10,
            "min_length": 4,
            "max_length": 6,
            "mean_length": 5.0,
            "gc_percent": 60.0,
            "n_fraction": 0.0,
            "malformed_records": 0,
        }
    ]


def test_fastq_qc_rejects_late_malformed_record_before_running_tool(tmp_path, monkeypatch):
    source = tmp_path / "late_broken.fastq"
    valid = "".join(f"@r{i}\nACGT\n+\n!!!!\n" for i in range(100))
    source.write_text(valid + "broken\nACGT\n+\n!!!\n", encoding="utf-8")
    monkeypatch.setattr(
        "research_agent.skills.ancient_dna.fastq_qc.resolve_tool",
        lambda names: ToolCommand("fastqc", ["/usr/local/bin/fastqc"], "path"),
    )

    def must_not_run(*args, **kwargs):
        raise AssertionError("FastQC must not run for a structurally invalid FASTQ")

    monkeypatch.setattr(
        "research_agent.skills.ancient_dna.fastq_qc.run_command",
        must_not_run,
    )

    result = FastqQcSkill().run(SkillContext(tmp_path / "work", [source]), {})

    assert result.status == "failed"
    assert "malformed FASTQ" in result.error


def test_fastq_qc_multi_input_returns_per_mate_json_and_named_outputs(tmp_path, monkeypatch):
    sources = []
    for mate in [1, 2]:
        source = tmp_path / f"sample_{mate}.fastq"
        source.write_text(f"@r{mate}\nACGT\n+\n!!!!\n", encoding="utf-8")
        sources.append(source)

    monkeypatch.setattr(
        "research_agent.skills.ancient_dna.fastq_qc.resolve_tool",
        lambda names: ToolCommand("fastqc", ["/usr/local/bin/fastqc"], "path"),
    )

    def fake_run_command(command, cwd, stdout_path, stderr_path, timeout):
        output_dir = Path(command[command.index("--outdir") + 1])
        output_dir.mkdir(parents=True, exist_ok=True)
        for mate in [1, 2]:
            (output_dir / f"sample_{mate}_fastqc.html").write_text("<html></html>", encoding="utf-8")
            (output_dir / f"sample_{mate}_fastqc.zip").write_bytes(b"zip")
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr("research_agent.skills.ancient_dna.fastq_qc.run_command", fake_run_command)
    result = FastqQcSkill().run(SkillContext(tmp_path / "work", sources), {})

    assert result.status == "succeeded"
    assert [Path(path).suffix for path in result.outputs] == [".html", ".html", ".json", ".json", ".zip", ".zip"]
    assert Path(result.named_outputs["fastqc_r1_html"]).name == "sample_1_fastqc.html"
    assert Path(result.named_outputs["fastqc_r2_json"]).name == "sample_2_fastqc_metrics.json"
    assert Path(result.named_outputs["fastqc_r2_zip"]).name == "sample_2_fastqc.zip"


def test_host_removal_reports_missing_alignment_stack(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "research_agent.skills.ancient_dna.host_removal.resolve_tool",
        lambda names: None,
    )
    result = HostDnaRemovalSkill().run(
        SkillContext(tmp_path / "work", [tmp_path / "reads.fastq.gz"]),
        {"reference": str(tmp_path / "human.fa")},
    )
    assert result.status == "dependency_missing"
    assert "bowtie2" in result.error
    assert "samtools" in result.error


def test_host_removal_uses_conda_aware_tool_resolution(tmp_path, monkeypatch):
    source = tmp_path / "reads.fastq.gz"
    source.write_bytes(b"fake")

    def fake_resolve_tool(names):
        tool = names[0]
        return ToolCommand(tool, ["conda", "run", "-n", f"{tool}_env", tool], f"conda:{tool}_env")

    captured = {}

    def fake_run_command(command, cwd, stdout_path, stderr_path, timeout):
        captured["command"] = command
        output = Path(command[command.index("--un-gz") + 1])
        output.write_bytes(b"host removed")
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(
        "research_agent.skills.ancient_dna.host_removal.resolve_tool",
        fake_resolve_tool,
    )
    monkeypatch.setattr(
        "research_agent.skills.ancient_dna.host_removal.run_command",
        fake_run_command,
    )

    result = HostDnaRemovalSkill().run(
        SkillContext(tmp_path / "work", [source]),
        {"reference": "human_index", "threads": 1},
    )

    assert result.status == "succeeded"
    assert captured["command"][:5] == ["conda", "run", "-n", "bowtie2_env", "bowtie2"]
    assert Path(result.outputs[0]).name == "host_removed.fastq.gz"


def test_authentication_reports_missing_mapdamage(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "research_agent.skills.ancient_dna.authentication.resolve_tool",
        lambda names: None,
    )
    result = AncientDnaAuthenticationSkill().run(
        SkillContext(tmp_path / "work", [tmp_path / "sample.bam"]),
        {"reference": str(tmp_path / "reference.fa")},
    )
    assert result.status == "dependency_missing"
    assert "mapDamage" in result.error


def test_authentication_uses_conda_aware_tool_resolution(tmp_path, monkeypatch):
    bam = tmp_path / "sample.bam"
    bam.write_bytes(b"bam")
    reference = tmp_path / "reference.fa"
    reference.write_text(">ref\nACGT\n", encoding="utf-8")

    def fake_resolve_tool(names):
        tool = names[0]
        return ToolCommand(tool, ["conda", "run", "-n", f"{tool}_env", tool], f"conda:{tool}_env")

    captured = {}

    def fake_run_command(command, cwd, stdout_path, stderr_path, timeout):
        captured["command"] = command
        output_dir = Path(command[command.index("-d") + 1])
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "Fragmisincorporation_plot.pdf").write_bytes(b"pdf")
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(
        "research_agent.skills.ancient_dna.authentication.resolve_tool",
        fake_resolve_tool,
    )
    monkeypatch.setattr(
        "research_agent.skills.ancient_dna.authentication.run_command",
        fake_run_command,
    )

    result = AncientDnaAuthenticationSkill().run(
        SkillContext(tmp_path / "work", [bam]),
        {"reference": str(reference)},
    )

    assert result.status == "succeeded"
    assert captured["command"][:5] == ["conda", "run", "-n", "mapDamage_env", "mapDamage"]
