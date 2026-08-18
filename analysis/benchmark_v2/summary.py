from __future__ import annotations

import math
from collections import defaultdict


def exact_mcnemar(paleorigor_only: int, raw_only: int) -> float:
    discordant = paleorigor_only + raw_only
    if discordant == 0:
        return 1.0
    smaller = min(paleorigor_only, raw_only)
    tail = sum(math.comb(discordant, k) for k in range(smaller + 1)) / (2 ** discordant)
    return min(1.0, 2 * tail)


def wilson(successes: int, total: int, z: float = 1.959963984540054) -> tuple[float, float]:
    if total == 0:
        return (math.nan, math.nan)
    proportion = successes / total
    denominator = 1 + z * z / total
    centre = (proportion + z * z / (2 * total)) / denominator
    half = z * math.sqrt(proportion * (1 - proportion) / total + z * z / (4 * total * total)) / denominator
    return centre - half, centre + half


def summarize_records(records: list[dict]) -> dict:
    by_pair: dict[tuple[str, int], dict[str, bool]] = defaultdict(dict)
    by_arm: dict[str, list[bool]] = defaultdict(list)
    for record in records:
        success = bool(record["strict_success"])
        by_pair[(record["scenario_id"], int(record["repeat"]))][record["arm"]] = success
        by_arm[record["arm"]].append(success)
    complete_pairs = [pair for pair in by_pair.values() if set(pair) == {"raw_llm", "paleorigor"}]
    paleorigor_only = sum(pair["paleorigor"] and not pair["raw_llm"] for pair in complete_pairs)
    raw_only = sum(pair["raw_llm"] and not pair["paleorigor"] for pair in complete_pairs)
    arms = {}
    for arm, values in by_arm.items():
        successes = sum(values)
        low, high = wilson(successes, len(values))
        arms[arm] = {"successes": successes, "total": len(values), "rate": successes / len(values), "wilson_95": [low, high]}
    raw_rate = arms.get("raw_llm", {}).get("rate", math.nan)
    paleo_rate = arms.get("paleorigor", {}).get("rate", math.nan)
    return {
        "pairs": len(complete_pairs),
        "arms": arms,
        "paired_rate_difference": paleo_rate - raw_rate,
        "discordant": {"paleorigor_only": paleorigor_only, "raw_only": raw_only},
        "mcnemar_exact_two_sided_p": exact_mcnemar(paleorigor_only, raw_only),
    }
