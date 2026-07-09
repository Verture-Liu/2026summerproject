from pathlib import Path

import pytest

from research_agent.skills.router import SkillRouter


MANIFEST = """
protocol_version: "1.0"
package_id: demo-package
package_version: "1.0.0"
factory: adapter.py:create_skills
enabled: true
"""

ADAPTER = """
class DemoSkill:
    name = "demo_skill"
    description = "Demo dynamically installed skill."
    input_formats = {"csv"}
    output_formats = {"csv"}
    resource_class = "light"
    parameter_schema = {
        "type": "object",
        "properties": {},
        "additionalProperties": False,
    }

    def run(self, context, parameters):
        raise NotImplementedError

def create_skills():
    return [DemoSkill()]
"""


def write_package(root: Path, name="demo", manifest=MANIFEST, adapter=ADAPTER):
    package = root / name
    package.mkdir(parents=True)
    (package / "skill.yaml").write_text(manifest, encoding="utf-8")
    (package / "adapter.py").write_text(adapter, encoding="utf-8")
    return package


def test_discovers_reviewed_package_without_core_code_changes(tmp_path):
    installed = tmp_path / "installed"
    write_package(installed)
    router = SkillRouter([installed])
    assert router.get("demo_skill").name == "demo_skill"
    assert router.packages()[0]["package_id"] == "demo-package"
    assert router.diagnostics() == []


def test_never_scans_quarantine_directory(tmp_path):
    write_package(tmp_path / "quarantine")
    router = SkillRouter([tmp_path / "installed"])
    with pytest.raises(KeyError):
        router.get("demo_skill")


def test_broken_package_does_not_block_valid_package(tmp_path):
    installed = tmp_path / "installed"
    write_package(installed, "valid")
    write_package(installed, "broken", manifest="not: [valid")
    router = SkillRouter([installed])
    assert router.get("demo_skill").name == "demo_skill"
    assert any("broken" in item["package"] for item in router.diagnostics())


def test_duplicate_skill_names_are_not_silently_selected(tmp_path):
    installed = tmp_path / "installed"
    write_package(installed, "first")
    second_manifest = MANIFEST.replace("demo-package", "second-package")
    write_package(installed, "second", manifest=second_manifest)
    router = SkillRouter([installed])
    with pytest.raises(KeyError):
        router.get("demo_skill")
    assert any("Duplicate skill name" in item["error"] for item in router.diagnostics())
