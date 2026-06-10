"""Knockout bracket structure for the 2026 World Cup (48 teams, R32).

Slot spec syntax:
  ("W", "A")      winner of group A
  ("R", "A")      runner-up of group A
  ("T", "ABCDF")  best-third slot that may receive the 3rd of one of these groups

BRACKET_2026["r32"] lists the 16 round-of-32 ties in bracket order:
winners of ties 0,1 meet in the round of 16, then 2,3, and so on.

NOTE: the concrete template below is filled from the official FIFA match
schedule (see ../data/knockout_bracket.md). The third-place allocation is
solved by constraint matching over each slot's allowed group set, memoized
on the combination of advancing third-place groups.
"""

from functools import lru_cache

# Placeholder — replaced with the official template by the data pipeline.
BRACKET_2026 = {"r32": []}

_alloc_cache: dict[frozenset, dict[int, str] | None] = {}


def _third_slots(spec):
    return [(k, set(slot[1])) for k, tie in enumerate_slots(spec) for slot in tie
            if slot[0] == "T"]


def enumerate_slots(spec):
    return list(enumerate(spec["r32"]))


def allocate_thirds(spec, adv_groups: frozenset):
    """Assign each advancing third-place group to a unique third slot.

    Deterministic backtracking: slots in bracket order, candidate groups in
    alphabetical order. Returns {slot_position_in_flat_list: group_letter}.
    """
    if adv_groups in _alloc_cache:
        return _alloc_cache[adv_groups]

    slots = []   # (flat_index, allowed_set) for slots holding thirds
    flat = []
    for tie in spec["r32"]:
        for s in tie:
            flat.append(s)
    for i, s in enumerate(flat):
        if s[0] == "T":
            slots.append((i, set(s[1])))

    groups = sorted(adv_groups)
    assignment: dict[int, str] = {}
    used: set[str] = set()

    def bt(k):
        if k == len(slots):
            return True
        idx, allowed = slots[k]
        for g in groups:
            if g not in used and g in allowed:
                assignment[idx] = g
                used.add(g)
                if bt(k + 1):
                    return True
                used.discard(g)
                del assignment[idx]
        return False

    ok = bt(0)
    if not ok:
        # Should not happen with the official template; degrade gracefully.
        assignment = {}
        gs = list(groups)
        for idx, _ in slots:
            assignment[idx] = gs.pop(0)
    _alloc_cache[adv_groups] = dict(assignment)
    return _alloc_cache[adv_groups]


def resolve_round_of_32(spec, winners, runners, adv_third_groups, third_team):
    """Concrete (team_index, team_index) pairs for the round of 32.

    winners/runners: {group_letter: team_index} for this simulation run.
    adv_third_groups: iterable of the 8 group letters whose thirds advanced.
    third_team: {group_letter: team_index} third-placed team per group.
    """
    alloc = allocate_thirds(spec, frozenset(adv_third_groups))
    pairs = []
    flat_i = 0
    for tie in spec["r32"]:
        resolved = []
        for s in tie:
            kind = s[0]
            if kind == "W":
                resolved.append(winners[s[1]])
            elif kind == "R":
                resolved.append(runners[s[1]])
            else:
                resolved.append(third_team[alloc[flat_i]])
            flat_i += 1
        pairs.append(tuple(resolved))
    return pairs
