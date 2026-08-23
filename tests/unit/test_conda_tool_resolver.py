import json
import os
import stat
import sys
from pathlib import Path
from subprocess import CompletedProcess

from research_agent.skills.conda_tools import (
    ToolCommand,
    bundled_tool_root,
    resolve_tool,
    run_tool_command,
)
from research_agent.runtime.paths import resource_root


EXPECTED_BUNDLED_TOOLS = [
    ("fastqc", "0.12.1", "bin/fastqc"),
    ("multiqc", "1.35", "bin/multiqc"),
    ("seqkit", "2.13.0", "bin/seqkit"),
    ("seqtk", "1.5-r133", "bin/seqtk"),
    ("samtools", "1.23.1", "bin/samtools"),
    ("bwa", "0.7.19-r1273", "bin/bwa"),
    ("bowtie2", "2.5.5", "bin/bowtie2"),
]


def _make_executable(path: Path) -> Path:
    path.parent.mkdir(parents=True)
    path.write_text("#!/bin/sh\n", encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)
    return path


def test_tool_manifest_declares_exact_bundled_tools_and_versions():
    manifest_path = resource_root() / "resources" / "tool_manifest.json"

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert [
        (tool["id"], tool["version"], tool["command"])
        for tool in manifest["tools"]
    ] == EXPECTED_BUNDLED_TOOLS
    assert all(
        set(tool) == {"id", "version", "command", "upstream", "license_file"}
        for tool in manifest["tools"]
    )
    assert all(tool["upstream"].startswith("https://") for tool in manifest["tools"])
    assert all(tool["license_file"] for tool in manifest["tools"])


def test_bundled_tool_root_uses_environment_override_in_developer_mode(tmp_path):
    tools = tmp_path / "tools"
    tools.mkdir()

    assert bundled_tool_root(
        {"PALEORIGOR_TOOL_ROOT": str(tools)}, packaged=False
    ) == tools


def test_packaged_tool_root_ignores_environment_and_uses_signed_resources(
    tmp_path, monkeypatch
):
    signed_resources = tmp_path / "signed" / "research_agent"
    signed_tools = signed_resources / "tools"
    signed_tools.mkdir(parents=True)
    malicious_tools = tmp_path / "malicious" / "tools"
    malicious_tools.mkdir(parents=True)
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(
        "research_agent.skills.conda_tools.resource_root",
        lambda: signed_resources,
    )

    assert bundled_tool_root(
        {"PALEORIGOR_TOOL_ROOT": str(malicious_tools)}
    ) == signed_tools


def test_resolve_tool_prefers_explicit_bundle_over_environment_and_path(
    tmp_path, monkeypatch
):
    explicit_executable = _make_executable(tmp_path / "explicit" / "bin" / "fastqc")
    environment_executable = _make_executable(tmp_path / "environment" / "bin" / "fastqc")
    monkeypatch.setenv("PALEORIGOR_TOOL_ROOT", str(environment_executable.parents[1]))
    monkeypatch.setattr(
        "research_agent.skills.conda_tools.shutil.which",
        lambda name: "/usr/local/bin/fastqc" if name == "fastqc" else None,
    )

    command = resolve_tool(("fastqc",), bundle_root=explicit_executable.parents[1])

    assert command == ToolCommand(
        tool="fastqc", command=[str(explicit_executable)], source="bundle"
    )


def test_resolve_tool_uses_environment_bundle_before_path(tmp_path, monkeypatch):
    executable = _make_executable(tmp_path / "tools" / "bin" / "fastqc")
    monkeypatch.setenv("PALEORIGOR_TOOL_ROOT", str(executable.parents[1]))
    monkeypatch.setattr(
        "research_agent.skills.conda_tools.shutil.which",
        lambda name: "/usr/local/bin/fastqc" if name == "fastqc" else None,
    )

    command = resolve_tool(("fastqc",))

    assert command == ToolCommand(
        tool="fastqc", command=[str(executable)], source="bundle"
    )


def test_packaged_resolver_never_falls_back_to_path_or_conda(tmp_path, monkeypatch):
    bundle_root = tmp_path / "missing-tools"
    monkeypatch.setattr(
        "research_agent.skills.conda_tools.shutil.which",
        lambda name: "/usr/local/bin/fastqc" if name == "fastqc" else "/usr/local/bin/conda",
    )

    command = resolve_tool(
        ("fastqc",),
        {"fastqc": "fastqc_env"},
        bundle_root=bundle_root,
        packaged=True,
    )

    assert command is None


def test_packaged_resolver_ignores_environment_and_explicit_external_roots(
    tmp_path, monkeypatch
):
    signed_resources = tmp_path / "signed" / "research_agent"
    signed_executable = _make_executable(
        signed_resources / "tools" / "bin" / "fastqc"
    )
    (signed_resources / "resources").mkdir(parents=True)
    (signed_resources / "resources" / "tool_manifest.json").write_text(
        json.dumps(
            {
                "tools": [
                    {
                        "id": "fastqc",
                        "version": "0.12.1",
                        "command": "bin/fastqc",
                        "license_file": "licenses/fastqc.txt",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    malicious_environment = tmp_path / "malicious-environment"
    malicious_explicit = tmp_path / "malicious-explicit"
    _make_executable(malicious_environment / "bin" / "fastqc")
    _make_executable(malicious_explicit / "bin" / "fastqc")
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setenv("PALEORIGOR_TOOL_ROOT", str(malicious_environment))
    monkeypatch.setattr(
        "research_agent.skills.conda_tools.resource_root",
        lambda: signed_resources,
    )

    command = resolve_tool(
        ("fastqc",),
        bundle_root=malicious_explicit,
        packaged=False,
    )

    assert command == ToolCommand(
        tool="fastqc", command=[str(signed_executable)], source="bundle"
    )


def test_resolver_infers_packaged_mode_and_rejects_explicit_developer_override(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(
        "research_agent.skills.conda_tools.shutil.which",
        lambda name: "/developer/bin/fastqc" if name == "fastqc" else None,
    )

    inferred = resolve_tool(("fastqc",), bundle_root=tmp_path / "missing")
    explicit_developer = resolve_tool(
        ("fastqc",),
        bundle_root=tmp_path / "missing",
        packaged=False,
    )

    assert inferred is None
    assert explicit_developer is None


def test_resolve_tool_rejects_bundle_command_that_escapes_tool_root(
    tmp_path, monkeypatch
):
    resources = tmp_path / "resources"
    resources.mkdir()
    (resources / "tool_manifest.json").write_text(
        json.dumps(
            {
                "tools": [
                    {
                        "id": "fastqc",
                        "version": "0",
                        "command": "../outside/fastqc",
                        "license_file": "licenses/fastqc.txt",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    _make_executable(tmp_path / "outside" / "fastqc")
    monkeypatch.setattr(
        "research_agent.skills.conda_tools.resource_root", lambda: tmp_path
    )

    command = resolve_tool(
        ("fastqc",), bundle_root=tmp_path / "tools", packaged=True
    )

    assert command is None


def test_resolve_tool_uses_path_before_conda(monkeypatch):
    monkeypatch.setattr(
        "research_agent.skills.conda_tools.shutil.which",
        lambda name: "/usr/bin/fastqc" if name == "fastqc" else None,
    )

    command = resolve_tool(("fastqc",), {"fastqc": "fastqc_env"})

    assert command == ToolCommand(tool="fastqc", command=["/usr/bin/fastqc"], source="path")


def test_resolve_tool_falls_back_to_conda_mapping(tmp_path, monkeypatch):
    conda = tmp_path / "miniconda" / "bin" / "conda"
    executable = tmp_path / "miniconda" / "envs" / "multiqc_env" / "bin" / "multiqc"
    conda.parent.mkdir(parents=True)
    executable.parent.mkdir(parents=True)
    conda.write_text("", encoding="utf-8")
    executable.write_text("", encoding="utf-8")
    monkeypatch.setattr(
        "research_agent.skills.conda_tools.shutil.which",
        lambda name: str(conda) if name == "conda" else None,
    )

    command = resolve_tool(("multiqc",), {"multiqc": "multiqc_env"})

    assert command == ToolCommand(
        tool="multiqc",
        command=[str(conda), "run", "-n", "multiqc_env", "multiqc"],
        source="conda:multiqc_env",
    )


def test_resolve_tool_rejects_stale_conda_environment_mapping(tmp_path, monkeypatch):
    conda = tmp_path / "miniconda" / "bin" / "conda"
    conda.parent.mkdir(parents=True)
    conda.write_text("", encoding="utf-8")
    monkeypatch.setattr(
        "research_agent.skills.conda_tools.shutil.which",
        lambda name: str(conda) if name == "conda" else None,
    )

    command = resolve_tool(("multiqc",), {"multiqc": "missing_env"})

    assert command is None


def test_run_tool_command_prepends_resolved_command(tmp_path, monkeypatch):
    seen = {}

    def fake_run(command, cwd, capture_output, text, timeout, check):
        seen["command"] = command
        return CompletedProcess(command, 0, "ok", "")

    monkeypatch.setattr(
        "research_agent.skills.conda_tools.subprocess.run",
        fake_run,
    )

    completed = run_tool_command(
        ToolCommand(
            tool="multiqc",
            command=["conda", "run", "-n", "multiqc_env", "multiqc"],
            source="conda:multiqc_env",
        ),
        ["--version"],
        cwd=Path(tmp_path),
        timeout=10,
    )

    assert completed.returncode == 0
    assert seen["command"] == ["conda", "run", "-n", "multiqc_env", "multiqc", "--version"]
