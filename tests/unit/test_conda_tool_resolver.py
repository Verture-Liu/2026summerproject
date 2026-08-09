from pathlib import Path
from subprocess import CompletedProcess

from research_agent.skills.conda_tools import (
    ToolCommand,
    resolve_tool,
    run_tool_command,
)


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
