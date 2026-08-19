from pathlib import Path

from analysis.benchmark_v2.scenarios import build_call_schedule, load_scenarios


ROOT = Path(__file__).resolve().parents[2]


def test_manifest_freezes_six_scenarios_and_existing_inputs():
    scenarios = load_scenarios(ROOT)
    assert [item.id for item in scenarios] == [
        "V2-S1", "V2-S2", "V2-B1", "V2-B2", "V2-B3", "V2-B4"
    ]
    assert sum(item.kind == "supported" for item in scenarios) == 2
    assert sum(item.kind == "boundary" for item in scenarios) == 4
    assert all(path.is_file() for item in scenarios for path in item.input_paths)
    assert all(not item.execute for item in scenarios if item.kind == "boundary")


def test_schedule_has_18_pairs_and_balanced_first_arm():
    schedule = build_call_schedule(load_scenarios(ROOT), repeats=3)
    assert len(schedule) == 18
    assert sum(pair.arm_order[0] == "raw_llm" for pair in schedule) == 9
    assert sum(pair.arm_order[0] == "paleorigor" for pair in schedule) == 9
    assert {(pair.scenario_id, pair.repeat) for pair in schedule} == {
        (scenario, repeat)
        for scenario in ["V2-S1", "V2-S2", "V2-B1", "V2-B2", "V2-B3", "V2-B4"]
        for repeat in [1, 2, 3]
    }


def test_loader_accepts_an_explicit_frozen_manifest(tmp_path):
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        '{"schema_version":"1.0","repeats":1,"scenarios":[]}',
        encoding="utf-8",
    )
    assert load_scenarios(ROOT, manifest_path=manifest) == []
