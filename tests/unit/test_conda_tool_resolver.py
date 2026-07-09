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


def test_resolve_tool_falls_back_to_conda_mapping(monkeypatch):
    monkeypatch.setattr(
        "research_agent.skills.conda_tools.shutil.which",
        lambda name: "/opt/miniconda3/bin/conda" if name == "conda" else None,
    )

    command = resolve_tool(("multiqc",), {"multiqc": "multiqc_env"})

    assert command == ToolCommand(
        tool="multiqc",
        command=["/opt/miniconda3/bin/conda", "run", "-n", "multiqc_env", "multiqc"],
        source="conda:multiqc_env",
    )


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
