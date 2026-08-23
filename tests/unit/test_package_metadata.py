import tomllib
from pathlib import Path


def test_python_artifacts_are_excluded_from_wheel_and_sdist_metadata():
    metadata = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    excluded = metadata["tool"]["setuptools"]["exclude-package-data"]["research_agent"]

    assert "**/__pycache__/*" in excluded
    assert "**/*.pyc" in excluded
    assert "**/*.pyo" in excluded

    manifest = Path("MANIFEST.in").read_text(encoding="utf-8")
    assert "global-exclude *.pyc *.pyo" in manifest
