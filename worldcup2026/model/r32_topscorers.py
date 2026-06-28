#!/usr/bin/env python3
"""R32-specific top scorer analysis using actual group stage results and updated probabilities."""
import csv, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from update_r32_predictions import blended_new, ACTUAL_STANDINGS
from run_predictions import CFG, KO_SCORING

HERE = os.path.dirname(os.path.abspath(__file__))
OUT  = os.path.join(HERE, "..", "output")
DATA = os.path.join(HERE, "..", "data")

# Use champion_probs for stage reach probabilities (we'll update these manually
# from actual group stage outcomes using the updated match-by-match sim approach)
# For R32 top scorer estimate, we only care about P(score in this round),
# which = P(team in R32) × goals_in_one_KO_game × player_share × pts_per_goal

# Actual R32 participants (confirmed)
R32_PARTICIPANTS = {
    "South Africa", "Canada", "Brazil", "Japan", "Germany", "Paraguay",
    "Netherlands", "Morocco", "Ivory Coast", "Norway", "France", "Sweden",
    "Mexico", "Ecuador", "United States", "Bosnia and Herzegovina",
    "England", "DR Congo", "Belgium", "Senegal", "Argentina", "Cape Verde",
    "Spain", "Austria", "Switzerland", "Algeria", "Portugal", "Croatia",
    "Colombia", "Ghana", "Australia", "Egypt"
}

# R32 point values per goal
PTS_FWD_R32 = 16
POS_MULT = {"forward": 1.0, "midfielder": 2.0, "defender": 4.0, "gk": 4.0}
PLAYER_SHARE = 0.33
KO_GPG = CFG["total_base_ko"] * 0.5  # ~1.175 goals per team per game

# Load original champion_probs for deeper round probabilities
orig_stages = {}
with open(os.path.join(OUT, "champion_probs.csv"), newline="") as f:
    for r in csv.DictReader(f):
        orig_stages[r["team"]] = {
            "p_R16": float(r["p_R16"]),
            "p_QF":  float(r["p_QF"]),
            "p_SF":  float(r["p_SF"]),
            "p_F":   float(r["p_Final"]),
        }

# Per-stage pts for forward (group through final), only stages AFTER R32
FUTURE_STAGES = [
    ("R16", 24, 1),
    ("QF",  32, 1),
    ("SF",  40, 1),
    ("F",   48, 1),
]

def r32_topscorer_pts(team, player_share, pos):
    if team not in R32_PARTICIPANTS:
        return 0.0
    mult = POS_MULT.get(pos, 1.0)
    # R32 contribution (certain since they're in R32)
    ep = 1.0 * KO_GPG * player_share * PTS_FWD_R32 * mult
    # Future rounds — use original probabilities as baseline (conservative)
    # Scale by updated rating vs original to adjust
    sp = orig_stages.get(team, {})
    KO_PTS = {"R16": 24, "QF": 32, "SF": 40, "F": 48}
    for stage_name, base_fwd, n_games in FUTURE_STAGES:
        p = sp.get(f"p_{stage_name}", sp.get(f"p_F", 0.0))
        ep += p * KO_GPG * player_share * base_fwd * mult
    return ep

ALIASES = {"USA": "United States"}
seen, players = set(), []
with open(os.path.join(DATA, "topscorer_odds.csv"), newline="") as f:
    for r in csv.DictReader(f):
        name = r["player"].strip()
        team = ALIASES.get(r["team"].strip(), r["team"].strip())
        if name in seen: continue
        seen.add(name)
        pos = r.get("position", "forward").strip().lower()
        try: odds = float(r["decimal_odds"])
        except: odds = 99.0
        ep = r32_topscorer_pts(team, PLAYER_SHARE, pos)
        players.append({
            "name": name, "team": team, "pos": pos,
            "odds": odds, "ep": ep,
            "in_r32": team in R32_PARTICIPANTS
        })

players.sort(key=lambda x: -x["ep"])
print("TOP SCORER PICKS FOR R32 (platform asks for 4 players)")
print(f"Scoring: Forward={PTS_FWD_R32}pts/goal, Midfielder=32pts/goal, Defender/GK=64pts/goal")
print()
print(f"{'Rank':<5}{'Player':<26}{'Team':<22}{'Pos':<12}{'Odds':<8}{'R32 E[pts]':>11}{'In R32?'}")
print("-" * 90)
for i, p in enumerate(players[:12], 1):
    flag = "✓" if p["in_r32"] else "✗ ELIMINATED"
    print(f"#{i:<4}{p['name']:<26}{p['team']:<22}{p['pos']:<12}{p['odds']:<8.0f}{p['ep']:>11.1f}  {flag}")
