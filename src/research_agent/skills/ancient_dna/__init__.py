from research_agent.skills.ancient_dna.authentication import (
    AncientDnaAuthenticationSkill,
)
from research_agent.skills.ancient_dna.fastq_qc import FastqQcSkill
from research_agent.skills.ancient_dna.host_removal import HostDnaRemovalSkill
from research_agent.skills.ancient_dna.sample_sheet import SampleSheetPrepareSkill


def ancient_dna_core_skills():
    return [
        SampleSheetPrepareSkill(),
        FastqQcSkill(),
        HostDnaRemovalSkill(),
        AncientDnaAuthenticationSkill(),
    ]

