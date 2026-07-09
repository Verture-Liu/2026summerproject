from research_agent.skills.external_tool.skill import amp_external_skills
from research_agent.skills.peptide_filter.skill import PeptideFilterSkill
from research_agent.skills.table_filter.skill import TableFilterSkill


def create_skills():
    external = [
        skill for skill in amp_external_skills()
        if skill.name != "host_dna_removal"
    ]
    return [TableFilterSkill(), PeptideFilterSkill(), *external]
