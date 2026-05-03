"""Pure-function eligibility decision: does this synced match count toward weekly accountability?

This module imports nothing from app.models, app.crud, app.database, or httpx.
The interface IS the test surface -- callers compose inputs from match_history rows
and excluded_friends rows; this module returns the verdict.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import FrozenSet, Iterable


# Riot queue IDs that count toward weekly accountability.
# 420 = Ranked Solo/Duo. Add flex/clash here later if they should count -- callers don't change.
COUNTING_QUEUE_IDS: FrozenSet[int] = frozenset({420})


@dataclass(frozen=True)
class EligibilityVerdict:
    counts: bool
    reason: str  # human-readable, surfaced in API responses and the UI


def evaluate_match(
    *,
    queue_id: int,
    team_puuids: Iterable[str],
    excluded_puuids: FrozenSet[str],
    user_excluded: bool,
) -> EligibilityVerdict:
    """Decide whether a synced match should produce a weekly_champions row for this player."""
    if user_excluded:
        return EligibilityVerdict(False, "user manually excluded this match")

    if queue_id not in COUNTING_QUEUE_IDS:
        return EligibilityVerdict(False, f"queue {queue_id} does not count toward accountability")

    team_set = set(team_puuids or [])
    excluded_on_my_team = excluded_puuids.intersection(team_set)
    if excluded_on_my_team:
        return EligibilityVerdict(False, "queued with an excluded friend")

    return EligibilityVerdict(True, "counts")
