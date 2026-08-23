import json
import os
import stat
import sys
from pathlib import Path

from research_agent.skills.ancient_dna.authentication import AncientDnaAuthenticationSkill
from research_agent.skills.ancient_dna.fastq_qc import FastqQcSkill
from research_agent.skills.ancient_dna.host_removal import HostDnaRemovalSkill
from research_agent.skills.base import SkillContext
from research_agent.skills.external_tool.skill import ExternalToolSkill
from research_agent.skills.registry import build_default_registry
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
        lambda packaged=None: None,
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


def _make_canary_executable(path: Path, marker: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"#!/bin/sh\nprintf invoked > '{marker}'\n",
        encoding="utf-8",
    )
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


def test_all_registered_executable_skills_reject_external_discovery_when_frozen(
    tmp_path, monkeypatch
):
    registry = build_default_registry()
    executable_skills = [
        registry.get(descriptor.name)
        for descriptor in registry.catalog()
        if descriptor.name == "tool_environment_check"
        or any(
            hasattr(registry.get(descriptor.name), attribute)
            for attribute in (
                "check_readiness",
                "check_dependencies",
                "find_tool_command",
                "find_executable",
            )
        )
    ]
    assert len(executable_skills) == 48

    signed_resources = tmp_path / "signed" / "research_agent"
    (signed_resources / "tools").mkdir(parents=True)
    (signed_resources / "resources").mkdir(parents=True)
    source_manifest = Path(
        "src/research_agent/resources/tool_manifest.json"
    ).read_text(encoding="utf-8")
    (signed_resources / "resources" / "tool_manifest.json").write_text(
        source_manifest,
        encoding="utf-8",
    )

    malicious_root = tmp_path / "malicious-tools"
    malicious_bin = malicious_root / "bin"
    marker = tmp_path / "external-executable-invoked"
    candidate_names = {
        "conda",
        "amplit-python",
        "gzip",
        "mapDamage",
        "pigz",
    }
    for skill in executable_skills:
        candidate_names.update(getattr(skill, "executable_candidates", ()))
        executable = getattr(skill, "executable", None)
        if executable:
            candidate_names.add(executable)
    candidate_names.update(tool["id"] for tool in json.loads(source_manifest)["tools"])
    for name in candidate_names:
        _make_canary_executable(malicious_bin / name, marker)

    amplit_home = malicious_root / "AMPLiT"
    for relative in (
        "utils1.py",
        "word2vec11.bin",
        "Model/G1.h5",
        "Model/G2.h5",
        "Model/G3.h5",
    ):
        path = amplit_home / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("malicious canary", encoding="utf-8")

    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(
        sys,
        "_MEIPASS",
        str(signed_resources.parent),
        raising=False,
    )
    monkeypatch.setenv("PATH", str(malicious_bin))
    monkeypatch.setenv("PALEORIGOR_TOOL_ROOT", str(malicious_root))
    monkeypatch.setenv("AMPLIT_HOME", str(amplit_home))
    monkeypatch.setenv("AMPLIT_PYTHON", str(malicious_bin / "amplit-python"))
    monkeypatch.setattr(
        "research_agent.skills.conda_tools.load_tool_envs",
        lambda: {name: "malicious" for name in candidate_names},
    )

    input_path = tmp_path / "input.fastq"
    input_path.write_text("@r1\nACGT\n+\n!!!!\n", encoding="utf-8")
    observations = []
    for skill in executable_skills:
        if hasattr(skill, "check_readiness"):
            observations.append(skill.check_readiness())
        if hasattr(skill, "check_dependencies"):
            observations.append(skill.check_dependencies(tmp_path / "dependency-check"))
        if hasattr(skill, "find_tool_command"):
            observations.append(skill.find_tool_command())
        if hasattr(skill, "find_executable"):
            observations.append(skill.find_executable())
        try:
            observations.append(
                skill.run(
                    SkillContext(tmp_path / "work" / skill.name, [input_path]),
                    {},
                )
            )
        except (KeyError, TypeError, ValueError) as exc:
            observations.append(str(exc))

    assert str(malicious_root) not in repr(observations)
    assert not marker.exists()
