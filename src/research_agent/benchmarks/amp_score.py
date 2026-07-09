from dataclasses import dataclass


@dataclass(frozen=True)
class BenchmarkScore:
    step_precision: float
    step_recall: float
    order_accuracy: float
    parameter_accuracy: float
    missing_skills: list[str]
    extra_skills: list[str]


def score_workflow(candidate, reference) -> BenchmarkScore:
    candidate_names = [step.skill for step in candidate.steps]
    reference_names = [step.skill for step in reference.steps]
    candidate_set = set(candidate_names)
    reference_set = set(reference_names)
    matches = len(candidate_set & reference_set)
    precision = matches / len(candidate_set) if candidate_set else 0.0
    recall = matches / len(reference_set) if reference_set else 1.0
    common = [name for name in reference_names if name in candidate_set]
    candidate_common = [name for name in candidate_names if name in reference_set]
    order_accuracy = 1.0 if candidate_common == common else 0.0
    reference_by_skill = {step.skill: step for step in reference.steps}
    parameter_scores = []
    for step in candidate.steps:
        if step.skill in reference_by_skill:
            parameter_scores.append(step.parameters == reference_by_skill[step.skill].parameters)
    parameter_accuracy = (
        sum(parameter_scores) / len(parameter_scores) if parameter_scores else 0.0
    )
    return BenchmarkScore(
        step_precision=precision,
        step_recall=recall,
        order_accuracy=order_accuracy,
        parameter_accuracy=parameter_accuracy,
        missing_skills=[name for name in reference_names if name not in candidate_set],
        extra_skills=[name for name in candidate_names if name not in reference_set],
    )
