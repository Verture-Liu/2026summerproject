from pathlib import Path

from research_agent.skills.base import SkillContext


def test_skill_context_normalizes_work_and_input_paths_to_absolute():
    context = SkillContext(
        Path("workspace/tasks/example/steps/step_01"),
        [Path("examples/minimal_reads.fastq")],
    )
    assert context.work_dir.is_absolute()
    assert all(path.is_absolute() for path in context.inputs)
