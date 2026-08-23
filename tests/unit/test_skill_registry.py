from types import SimpleNamespace
from pathlib import Path

import pytest

from research_agent.skills.amplit.skill import AmplitPredictionSkill
from research_agent.skills import registry as registry_module
from research_agent.skills.registry import build_default_registry
from tests.unit.test_skill_router import ADAPTER, MANIFEST, write_package


def test_skill_roots_use_packaged_resources_and_runtime_application_paths(
    tmp_path, monkeypatch
):
    resources = tmp_path / "resources"
    installed = tmp_path / "application-support" / "skills"
    unrelated_cwd = tmp_path / "unrelated-cwd"
    unrelated_cwd.mkdir()
    monkeypatch.chdir(unrelated_cwd)
    monkeypatch.setattr(registry_module, "resource_root", lambda: resources)
    monkeypatch.setattr(
        registry_module,
        "AppPaths",
        SimpleNamespace(
            for_runtime=lambda: SimpleNamespace(installed_skill_root=installed)
        ),
    )

    assert registry_module.builtin_skill_root() == resources / "skill_packages" / "builtin"
    assert registry_module.installed_skill_root() == installed


def test_registry_exposes_only_registered_skills():
    registry = build_default_registry()
    assert registry.get("peptide_filter").name == "peptide_filter"
    assert {
        "peptide_csv_normalize",
        "peptide_validate",
        "peptide_label_filter",
        "peptide_length_filter",
        "peptide_deduplicate",
        "peptide_statistics",
        "peptide_chart",
        "peptide_csv_export",
        "sample_sheet_prepare",
        "fastq_qc",
        "host_dna_removal",
        "ancient_dna_authentication",
        "fastp_preprocess",
        "kraken2_profile",
        "megahit_assembly",
        "metabat2_binning",
        "checkm2_quality",
        "gtdbtk_classify",
    }.issubset({item.name for item in registry.catalog()})
    assert "shell" not in {item.name for item in registry.catalog()}
    assert isinstance(registry.get("amp_prediction"), AmplitPredictionSkill)
    with pytest.raises(KeyError):
        registry.get("shell")


def test_default_registry_loads_installed_package_without_agent_code_change(
    tmp_path, monkeypatch
):
    installed = tmp_path / "installed"
    write_package(installed, manifest=MANIFEST, adapter=ADAPTER)
    monkeypatch.setattr(registry_module, "installed_skill_root", lambda: installed)
    registry = build_default_registry()
    assert registry.get("demo_skill").name == "demo_skill"


def test_packaged_registry_does_not_load_unsigned_installed_python_adapters(
    tmp_path, monkeypatch
):
    installed = tmp_path / "installed"
    write_package(installed, manifest=MANIFEST, adapter=ADAPTER)
    monkeypatch.setattr(registry_module, "installed_skill_root", lambda: installed)
    monkeypatch.setattr(
        registry_module,
        "builtin_skill_root",
        lambda: Path("src/research_agent/skill_packages/builtin"),
    )
    monkeypatch.setattr("research_agent.runtime.paths.sys.frozen", True, raising=False)

    registry = build_default_registry()

    with pytest.raises(KeyError):
        registry.get("demo_skill")
