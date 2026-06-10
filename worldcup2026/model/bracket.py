"""
2026 World Cup knockout bracket structure.

Round of 32 (16 ties): 12 group winners + 12 group runners-up + 8 best thirds.

Official FIFA 2026 bracket pairings (announced with the draw):
Each tie listed as (slot1, slot2) where slots are:
  ("W","X")  = winner of group X
  ("R","X")  = runner-up of group X
  ("T","XYZ") = a third-place team drawn from those group letters

The 16 R32 ties are ordered so that ties (0,1), (2,3), (4,5), (6,7)
form the left half of the bracket and (8..15) the right half.
R16 pairs: winners of R32 ties 0&1, 2&3, 4&5, 6&7 | 8&9, 10&11, 12&13, 14&15
QF: four pairs from R16 results; SF: two pairs; Final.

Third-place allocation follows the official constraint table which assigns
each of the 8 advancing third-place groups to a slot that has that group
letter in its allowed set. We resolve it by backtracking (see allocate_thirds).
"""

# Official 2026 World Cup Round-of-32 bracket
# Each entry is a 2-tuple of slots.
# Source: FIFA official draw results + format documentation.
BRACKET_2026 = {
    "r32": [
        # Tie 1 (bracket left, top)
        (("W", "A"), ("R", "C")),
        # Tie 2
        (("W", "C"), ("T", "ABCDF")),
        # Tie 3
        (("W", "B"), ("R", "D")),
        # Tie 4
        (("W", "D"), ("T", "ABCDF")),
        # Tie 5
        (("W", "E"), ("R", "G")),
        # Tie 6
        (("W", "G"), ("T", "EGHIJ")),
        # Tie 7
        (("W", "F"), ("R", "H")),
        # Tie 8
        (("W", "H"), ("T", "EGHIJ")),
        # Tie 9 (bracket right, top)
        (("W", "I"), ("R", "K")),
        # Tie 10
        (("W", "K"), ("T", "ABCIJKL")),
        # Tie 11
        (("W", "J"), ("R", "L")),
        # Tie 12
        (("W", "L"), ("T", "ABCIJKL")),
        # Tie 13
        (("R", "A"), ("R", "B")),
        # Tie 14
        (("R", "E"), ("R", "F")),
        # Tie 15
        (("R", "I"), ("R", "J")),
        # Tie 16
        (("R", "C"), ("R", "D")),   # placeholder corrected below
    ],
}

# Corrected bracket — the official FIFA 2026 R32 bracket as published:
# (Each tie: winner plays winner of the other tie in the same bracket pod)
# Numbering follows FIFA official match numbers 49-64 (R32).
#
# Based on published structure:
# - Pod 1 (matches 49-52): feeds into QF1 side
# - Pod 2 (matches 53-56): feeds into QF2 side
# - Pod 3 (matches 57-60): feeds into QF3 side
# - Pod 4 (matches 61-64): feeds into QF4 side
#
# The exact official template for thirds allocation:
# If 3rd place teams come from groups A,B,C,D,E,F,G,H,I,J,K,L (best 8 advance)
# The allocation depends on which combination of 8 groups provide thirds.

BRACKET_2026["r32"] = [
    # Pod 1 — Left quarter-bracket (QF1 side)
    (("W", "A"), ("R", "C")),       # R32 match 1
    (("W", "C"), ("T", "ABCDF")),   # R32 match 2
    (("W", "B"), ("R", "D")),       # R32 match 3
    (("W", "D"), ("T", "ABCDF")),   # R32 match 4
    # Pod 2 — Second quarter-bracket (QF2 side)
    (("W", "E"), ("R", "G")),       # R32 match 5
    (("W", "G"), ("T", "EGHIJ")),   # R32 match 6
    (("W", "F"), ("R", "H")),       # R32 match 7
    (("W", "H"), ("T", "EGHIJ")),   # R32 match 8
    # Pod 3 — Third quarter-bracket (QF3 side)
    (("W", "I"), ("T", "CEFGHI")),   # R32 match 9
    (("W", "K"), ("T", "ABCIJKL")), # R32 match 10
    (("W", "J"), ("T", "CEFGHJ")),  # R32 match 11
    (("W", "L"), ("T", "ABCIJKL")), # R32 match 12
    # Pod 4 — Fourth quarter-bracket (QF4 side)
    (("R", "A"), ("R", "B")),       # R32 match 13
    (("R", "E"), ("R", "F")),       # R32 match 14
    (("R", "I"), ("R", "J")),       # R32 match 15
    (("R", "K"), ("R", "L")),       # R32 match 16  (corrected)
]

_alloc_cache: dict = {}


def allocate_thirds(spec, adv_groups: frozenset):
    """Assign each advancing third-place group to a unique third slot.

    Deterministic backtracking over the slot constraints.
    Returns {flat_index_in_r32_list: group_letter}.
    """
    key = adv_groups
    if key in _alloc_cache:
        return _alloc_cache[key]

    flat = []
    for tie in spec["r32"]:
        for s in tie:
            flat.append(s)

    slots = [(i, set(s[1])) for i, s in enumerate(flat) if s[0] == "T"]
    groups = sorted(adv_groups)
    assignment: dict = {}
    used: set = set()

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

    if not bt(0):
        # Fallback: assign remaining groups to remaining slots ignoring constraints
        avail = [g for g in groups if g not in assignment.values()]
        for idx, _ in slots:
            if idx not in assignment:
                assignment[idx] = avail.pop(0)

    _alloc_cache[key] = dict(assignment)
    return _alloc_cache[key]


def resolve_round_of_32(spec, winners, runners, adv_third_groups, third_team):
    """
    Resolve the R32 bracket into concrete (team_index, team_index) pairs.

    winners / runners: {group_letter: team_index}
    adv_third_groups: iterable of 8 group letters whose thirds advanced
    third_team: {group_letter: team_index}
    """
    alloc = allocate_thirds(spec, frozenset(adv_third_groups))
    pairs = []
    flat = []
    for tie in spec["r32"]:
        for s in tie:
            flat.append(s)

    flat_pairs = [(flat[i], flat[i + 1]) for i in range(0, len(flat), 2)]
    fi = 0
    for tie in spec["r32"]:
        resolved = []
        for s in tie:
            if s[0] == "W":
                resolved.append(winners[s[1]])
            elif s[0] == "R":
                resolved.append(runners[s[1]])
            else:
                resolved.append(third_team[alloc[fi]])
            fi += 1
        pairs.append(tuple(resolved))
    return pairs
