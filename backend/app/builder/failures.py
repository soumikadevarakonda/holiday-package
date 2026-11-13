"""Count why candidate plans fail, so "no package" can say the most specific reason (M2)."""

from __future__ import annotations

from collections import Counter


class Failures:
    """Reasons by stage. The stage that eliminated plans furthest down the pipeline is the most specific."""

    STAGES = ["request", "flights", "hotels", "arrival_transfer", "return_transfer", "intercity",
              "attractions", "validation"]

    def __init__(self) -> None:
        self.reasons: dict[str, Counter] = {s: Counter() for s in self.STAGES}

    def add(self, stage: str, reason: str) -> None:
        self.reasons[stage][reason] += 1

    def best_reason(self) -> str:
        for stage in reversed(self.STAGES):
            if self.reasons[stage]:
                reason, n = self.reasons[stage].most_common(1)[0]
                return reason if n == 1 else f"{reason} ({n} city plans failed this way)"
        return "No valid package exists for this request."
