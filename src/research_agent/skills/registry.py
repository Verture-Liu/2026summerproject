from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

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
            )
            for skill in self._skills.values()
        ]


def builtin_skill_root() -> Path:
    return Path(__file__).resolve().parents[1] / "skill_packages" / "builtin"


def installed_skill_root() -> Path:
    return Path.cwd() / "workspace" / "skill-packages" / "installed"


def build_default_registry() -> SkillRegistry:
    return SkillRouter([builtin_skill_root(), installed_skill_root()])
