from pathlib import Path

from analysis.benchmark_v2.scenarios import build_call_schedule, load_scenarios
from research_agent.files.inspector import inspect_file
from research_agent.skills.registry import build_default_registry


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "analysis" / "benchmark_v4" / "heldout_manifest.json"
OLDER_MANIFESTS = [
    ROOT / "analysis" / "benchmark_v2" / "scenario_manifest.json",
    ROOT / "analysis" / "benchmark_v3" / "heldout_manifest.json",
]


def test_v4_manifest_is_balanced_new_and_frozen():
    heldout = load_scenarios(ROOT, manifest_path=MANIFEST)
    older_paths = {
        path
        for manifest in OLDER_MANIFESTS
        for item in load_scenarios(ROOT, manifest_path=manifest)
        for path in item.input_paths
    }
    assert len(heldout) == 8
    assert sum(item.kind == "supported" for item in heldout) == 4
    assert sum(item.kind == "boundary" for item in heldout) == 4
    assert all(path.is_file() for item in heldout for path in item.input_paths)
    assert all(not item.execute for item in heldout if item.kind == "boundary")
    assert not ({path for item in heldout for path in item.input_paths} & older_paths)

    schedule = build_call_schedule(heldout, repeats=3)
    assert len(schedule) == 24
    assert sum(item.arm_order[0] == "raw_llm" for item in schedule) == 12
    assert sum(item.arm_order[0] == "paleorigor" for item in schedule) == 12


def test_v4_files_match_formats_and_skills_exist():
    heldout = load_scenarios(ROOT, manifest_path=MANIFEST)
    available = {item.name for item in build_default_registry().catalog()}
    for scenario in heldout:
        for path in scenario.input_paths:
            assert inspect_file(path).format == scenario.uploaded_formats[path.name]
        assert set(scenario.required_skills) <= available
        assert set(scenario.forbidden_skills) <= available
