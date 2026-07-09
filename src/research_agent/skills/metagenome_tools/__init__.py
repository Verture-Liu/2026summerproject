from research_agent.skills.metagenome_tools.assembly import (
    MegahitAssemblySkill,
    MetaspadesAssemblySkill,
)
from research_agent.skills.metagenome_tools.ancient import (
    ancient_metagenome_alignment_skills,
)
from research_agent.skills.metagenome_tools.functional import (
    functional_profile_skills,
)
from research_agent.skills.metagenome_tools.mag import (
    Checkm2QualitySkill,
    ConcoctBinningSkill,
    DasToolRefineSkill,
    DrepDereplicateSkill,
    GtdbtkClassifySkill,
    Maxbin2BinningSkill,
    Metabat2BinningSkill,
)
from research_agent.skills.metagenome_tools.preprocessing import (
    AdapterRemovalPreprocessSkill,
    CutadaptPreprocessSkill,
    FastpPreprocessSkill,
)
from research_agent.skills.metagenome_tools.taxonomy import (
    Kraken2ProfileSkill,
    MaltProfileSkill,
    MetaphlanProfileSkill,
)


def metagenome_tool_skills():
    return [
        FastpPreprocessSkill(),
        AdapterRemovalPreprocessSkill(),
        CutadaptPreprocessSkill(),
        MetaphlanProfileSkill(),
        Kraken2ProfileSkill(),
        MaltProfileSkill(),
        MegahitAssemblySkill(),
        MetaspadesAssemblySkill(),
        Metabat2BinningSkill(),
        Maxbin2BinningSkill(),
        ConcoctBinningSkill(),
        DasToolRefineSkill(),
        Checkm2QualitySkill(),
        DrepDereplicateSkill(),
        GtdbtkClassifySkill(),
        *ancient_metagenome_alignment_skills(),
        *functional_profile_skills(),
    ]
