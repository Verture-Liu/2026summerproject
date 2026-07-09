from research_agent.skills.peptide_table.charts import PeptideChartSkill
from research_agent.skills.peptide_table.deduplicate import PeptideDeduplicateSkill
from research_agent.skills.peptide_table.export import PeptideCsvExportSkill
from research_agent.skills.peptide_table.filters import (
    PeptideLabelFilterSkill,
    PeptideLengthFilterSkill,
)
from research_agent.skills.peptide_table.normalize import PeptideCsvNormalizeSkill
from research_agent.skills.peptide_table.prediction_utilities import (
    PeptideCandidateRankSkill,
    PeptidePropertiesSkill,
)
from research_agent.skills.peptide_table.statistics import PeptideStatisticsSkill
from research_agent.skills.peptide_table.validate import PeptideValidateSkill


def peptide_table_skills():
    return [
        PeptideCsvNormalizeSkill(),
        PeptideValidateSkill(),
        PeptideLabelFilterSkill(),
        PeptideLengthFilterSkill(),
        PeptideDeduplicateSkill(),
        PeptideStatisticsSkill(),
        PeptideChartSkill(),
        PeptideCsvExportSkill(),
        PeptidePropertiesSkill(),
        PeptideCandidateRankSkill(),
    ]
