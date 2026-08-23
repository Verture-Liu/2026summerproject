import sys

from research_agent.skills.ancient_dna.authentication import AncientDnaAuthenticationSkill
from research_agent.skills.ancient_dna.fastq_qc import FastqQcSkill
from research_agent.skills.ancient_dna.host_removal import HostDnaRemovalSkill
from research_agent.skills.base import SkillContext
from research_agent.skills.external_tool.skill import ExternalToolSkill
from research_agent.skills.sequence_utilities import SeqkitStatsSkill, SeqtkSampleSkill


def test_host_removal_reports_all_missing_dependencies(monkeypatch):
    monkeypatch.setattr(
        "research_agent.skills.ancient_dna.host_removal.resolve_tool",
        lambda candidates: None,
    )

    report = HostDnaRemovalSkill().check_readiness()

    assert report["ready"] is False
    assert report["missing"] == ["bowtie2", "samtools"]
    assert "will not install" in " ".join(report["installation_instructions"])


def test_ancient_dna_authentication_reports_missing_dependencies(monkeypatch):
    monkeypatch.setattr(
        "research_agent.skills.ancient_dna.authentication.resolve_tool",
        lambda candidates: None,
    )

    report = AncientDnaAuthenticationSkill().check_readiness()

    assert report["ready"] is False
    assert report["missing"] == ["mapDamage", "samtools"]


def test_seqkit_and_seqtk_publish_readiness_contracts(monkeypatch):
    monkeypatch.setattr(
        "research_agent.skills.sequence_utilities.resolve_tool",
        lambda candidates: None,
    )

    seqkit = SeqkitStatsSkill().check_readiness()
    seqtk = SeqtkSampleSkill().check_readiness()

    assert seqkit["ready"] is False
    assert seqkit["tool"] == "seqkit"
    assert seqtk["ready"] is False
    assert seqtk["tool"] == "seqtk"


def test_legacy_external_tool_skill_publishes_readiness(monkeypatch):
    monkeypatch.setattr(
        "research_agent.skills.external_tool.skill.resolve_tool",
        lambda candidates: None,
    )
    skill = ExternalToolSkill(
        name="legacy_tool",
        description="legacy test tool",
        executable="legacy-bin",
        input_formats={"fastq"},
        output_formats={"fastq"},
        parameter_schema={"type": "object", "properties": {}},
    )

    report = skill.check_readiness()

    assert report["ready"] is False
    assert report["tool"] == "legacy-bin"


def test_legacy_external_tool_remains_blocked_when_adapter_is_not_configured(monkeypatch):
    from research_agent.skills.conda_tools import ToolCommand

    monkeypatch.setattr(
        "research_agent.skills.external_tool.skill.resolve_tool",
        lambda candidates: ToolCommand(
            tool="legacy-bin",
            command=["/opt/example/legacy-bin"],
            source="path",
        ),
    )
    skill = ExternalToolSkill(
        name="legacy_tool",
        description="legacy test tool",
        executable="legacy-bin",
        input_formats={"fastq"},
        output_formats={"fastq"},
        parameter_schema={"type": "object", "properties": {}},
    )

    report = skill.check_readiness()

    assert report["ready"] is False
    assert report["issue_code"] == "skill_not_configured"
    assert "adapter" in report["error"].lower()


def test_real_fastqc_skill_cannot_use_developer_path_in_inferred_packaged_mode(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(
        "research_agent.skills.conda_tools.bundled_tool_root",
        lambda: None,
    )
    monkeypatch.setattr(
        "research_agent.skills.conda_tools.shutil.which",
        lambda _name: "/developer/bin/fastqc",
    )
    source = tmp_path / "reads.fastq"
    source.write_text("@r1\nACGT\n+\n!!!!\n", encoding="utf-8")
    skill = FastqQcSkill()

    readiness = skill.check_readiness()
    result = skill.run(SkillContext(tmp_path / "work", [source]), {})

    assert readiness["ready"] is False
    assert readiness["executable"] == ""
    assert result.status == "dependency_missing"
    assert not (tmp_path / "work").exists()
