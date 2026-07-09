from research_agent.skills.amplit.skill import AmplitPredictionSkill
from research_agent.skills.amplit.external_predictors import (
    external_amp_predictor_skills,
)


def create_skills():
    return [AmplitPredictionSkill(), *external_amp_predictor_skills()]
