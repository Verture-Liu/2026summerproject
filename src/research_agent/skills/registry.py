from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from research_agent.runtime.paths import (
    AppPaths,
    is_packaged_runtime,
    resource_root,
)
from research_agent.skills.peptide_filter.skill import PeptideFilterSkill
from research_agent.skills.peptide_table import peptide_table_skills
from research_agent.skills.amplit.skill import AmplitPredictionSkill
from research_agent.skills.table_filter.skill import TableFilterSkill
from research_agent.skills.external_tool.skill import amp_external_skills
from research_agent.skills.router import SkillRouter


@dataclass(frozen=True)
class SkillDescriptor:
    name: str
    description: str
    input_formats: list[str]
    output_formats: list[str]
    resource_class: str
    parameter_schema: dict[str, Any]
    min_inputs: int
    max_inputs: int | None


class SkillRegistry:
    def __init__(self, skills: Iterable):
        self._skills = {skill.name: skill for skill in skills}

    def get(self, name: str):
        if name not in self._skills:
            raise KeyError(f"Unknown skill: {name}")
        return self._skills[name]

    def catalog(self) -> list[SkillDescriptor]:
        return [
            SkillDescriptor(
                name=skill.name,
                description=skill.description,
                input_formats=sorted(skill.input_formats),
                output_formats=sorted(skill.output_formats),
                resource_class=skill.resource_class,
                parameter_schema=skill.parameter_schema,
                min_inputs=getattr(
                    skill,
                    "min_inputs",
                    0 if "none" in skill.input_formats else 1,
                ),
                max_inputs=getattr(
                    skill,
                    "max_inputs",
                    0 if skill.input_formats == {"none"} else 1,
                ),
            )
            for skill in self._skills.values()
        ]


def builtin_skill_root() -> Path:
    return resource_root() / "skill_packages" / "builtin"


def installed_skill_root() -> Path:
    return AppPaths.for_runtime().installed_skill_root


def build_default_registry() -> SkillRegistry:
    roots = [builtin_skill_root()]
    if not is_packaged_runtime():
        roots.append(installed_skill_root())
    return SkillRouter(roots)
