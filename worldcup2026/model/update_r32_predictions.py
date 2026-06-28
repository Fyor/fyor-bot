#!/usr/bin/env python3
"""
Update model ratings using actual group stage results, then predict R32.
Blend: 70% Elo-updated-from-actuals + 30% original blended model ratings.
"""
import csv, json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from run_predictions import score_grid, best_pick, outcome_probs, CFG, KO_SCORING, _CONF_MAP, HOSTS

HERE  = os.path.dirname(os.path.abspath(__file__))
DATA  = os.path.join(HERE, "..", "data")
OUT   = os.path.join(HERE, "..", "output")

# ── Load original blended ratings ─────────────────────────────────────────────
orig = {}
with open(os.path.join(OUT, "champion_probs.csv"), newline="") as f:
    for r in csv.DictReader(f):
        orig[r["team"]] = float(r["rating"])

# ── Actual group stage results (all 72 matches) ────────────────────────────────
# Format: (team1, score1, score2, team2)
ACTUAL = [
    # Group A
    ("Mexico", 2, 0, "South Africa"),
    ("South Korea", 2, 1, "Czechia"),
    ("Czechia", 1, 1, "South Africa"),
    ("Mexico", 1, 0, "South Korea"),
    ("Mexico", 3, 0, "Czechia"),
    ("South Africa", 1, 0, "South Korea"),
    # Group B
    ("Canada", 1, 0, "Bosnia and Herzegovina"),
    ("Qatar", 0, 2, "Switzerland"),
    ("Switzerland", 2, 1, "Bosnia and Herzegovina"),
    ("Canada", 2, 1, "Qatar"),
    ("Switzerland", 2, 1, "Canada"),
    ("Bosnia and Herzegovina", 3, 1, "Qatar"),
    # Group C
    ("Brazil", 1, 1, "Morocco"),
    ("Haiti", 0, 1, "Scotland"),
    ("Scotland", 0, 1, "Morocco"),
    ("Brazil", 3, 0, "Haiti"),
    ("Morocco", 4, 2, "Haiti"),
    ("Scotland", 0, 3, "Brazil"),
    # Group D
    ("United States", 4, 1, "Paraguay"),
    ("Turkey", 0, 2, "Australia"),
    ("United States", 2, 0, "Australia"),
    ("Turkey", 0, 1, "Paraguay"),
    ("Turkey", 3, 2, "United States"),
    ("Paraguay", 0, 0, "Australia"),
    # Group E
    ("Germany", 7, 1, "Curaçao"),
    ("Ivory Coast", 1, 0, "Ecuador"),
    ("Germany", 2, 1, "Ivory Coast"),
    ("Ecuador", 0, 0, "Curaçao"),
    ("Curaçao", 0, 2, "Ivory Coast"),
    ("Ecuador", 2, 1, "Germany"),
    # Group F
    ("Netherlands", 2, 2, "Japan"),
    ("Sweden", 5, 1, "Tunisia"),
    ("Netherlands", 5, 1, "Sweden"),
    ("Japan", 4, 0, "Tunisia"),
    ("Japan", 1, 1, "Sweden"),
    ("Netherlands", 3, 1, "Tunisia"),
    # Group G
    ("Belgium", 1, 1, "Egypt"),
    ("Iran", 2, 2, "New Zealand"),
    ("Belgium", 0, 0, "Iran"),
    ("Egypt", 3, 1, "New Zealand"),
    ("Egypt", 1, 1, "Iran"),
    ("Belgium", 5, 1, "New Zealand"),
    # Group H
    ("Spain", 0, 0, "Cape Verde"),
    ("Saudi Arabia", 1, 1, "Uruguay"),
    ("Spain", 4, 0, "Saudi Arabia"),
    ("Uruguay", 2, 2, "Cape Verde"),
    ("Cape Verde", 0, 0, "Saudi Arabia"),
    ("Spain", 1, 0, "Uruguay"),
    # Group I
    ("France", 3, 1, "Senegal"),
    ("Iraq", 1, 4, "Norway"),
    ("France", 2, 0, "Iraq"),
    ("Norway", 1, 0, "Senegal"),
    ("Norway", 1, 4, "France"),
    ("Senegal", 5, 0, "Iraq"),
    # Group J
    ("Argentina", 3, 0, "Algeria"),
    ("Austria", 3, 1, "Jordan"),
    ("Argentina", 2, 1, "Austria"),
    ("Algeria", 2, 1, "Jordan"),
    ("Argentina", 3, 1, "Jordan"),
    ("Algeria", 3, 3, "Austria"),
    # Group K
    ("Portugal", 1, 1, "DR Congo"),
    ("Uzbekistan", 1, 3, "Colombia"),
    ("Portugal", 2, 0, "Uzbekistan"),
    ("Colombia", 2, 1, "DR Congo"),
    ("Colombia", 0, 0, "Portugal"),
    ("DR Congo", 3, 1, "Uzbekistan"),
    # Group L
    ("England", 4, 2, "Croatia"),
    ("Ghana", 1, 0, "Panama"),
    ("England", 2, 0, "Ghana"),
    ("Panama", 0, 2, "Croatia"),
    ("England", 2, 0, "Panama"),
    ("Croatia", 2, 1, "Ghana"),
]

# ── Prediction accuracy analysis ───────────────────────────────────────────────
def load_picks():
    picks = {}
    with open(os.path.join(OUT, "match_predictions.csv"), newline="") as f:
        for r in csv.DictReader(f):
            picks[(r["team1"], r["team2"])] = r["optimal_pick"]
    return picks

def analyse_accuracy(actual, picks):
    exact, direction_right, total = 0, 0, 0
    misses = []
    for t1, s1, s2, t2 in actual:
        key = (t1, t2)
        pick = picks.get(key)
        if pick is None:
            continue
        pa, pb = map(int, pick.split("-"))
        total += 1
        # Direction
        pred_dir = "1" if pa > pb else ("d" if pa == pb else "2")
        act_dir  = "1" if s1 > s2 else ("d" if s1 == s2 else "2")
        if pred_dir == act_dir:
            direction_right += 1
            if pa == s1 and pb == s2:
                exact += 1
        else:
            misses.append(f"  {t1} {s1}-{s2} {t2}  (picked {pick})")
    return total, direction_right, exact, misses

# ── Elo update from actual results ─────────────────────────────────────────────
K = 35  # WC K-factor

def elo_update(ratings, results):
    r = dict(ratings)
    for t1, s1, s2, t2 in results:
        if t1 not in r or t2 not in r:
            continue
        e1 = 1 / (1 + 10 ** ((r[t2] - r[t1]) / 400))
        w1 = 1.0 if s1 > s2 else (0.5 if s1 == s2 else 0.0)
        margin = abs(s1 - s2)
        # Margin-of-victory multiplier (Logistic, capped)
        mov = math.log(max(margin, 1) + 1) * 0.8 + 0.2
        delta = K * mov * (w1 - e1)
        r[t1] += delta
        r[t2] -= delta
    return r

print("=" * 70)
print("GROUP STAGE PREDICTION ACCURACY")
print("=" * 70)
picks = load_picks()
total, direction_right, exact, misses = analyse_accuracy(ACTUAL, picks)
print(f"Outcome direction correct: {direction_right}/{total}  ({direction_right/total*100:.0f}%)")
print(f"Exact score correct:       {exact}/{total}  ({exact/total*100:.0f}%)")
print(f"\nIncorrect directions ({total - direction_right} matches):")
for m in misses:
    print(m)

# ── Points scored (estimate) ───────────────────────────────────────────────────
pts_match = 0
for t1, s1, s2, t2 in ACTUAL:
    key = (t1, t2)
    pick = picks.get(key)
    if pick is None: continue
    pa, pb = map(int, pick.split("-"))
    pred_dir = "1" if pa > pb else ("d" if pa == pb else "2")
    act_dir  = "1" if s1 > s2 else ("d" if s1 == s2 else "2")
    if pred_dir == act_dir:
        pts_match += 30
        if pa == s1 and pb == s2:
            pts_match += 15
print(f"\nEstimated match points earned (72 group games): {pts_match}")
print(f"  ({direction_right} × 30 + {exact} × 15 = {direction_right*30 + exact*15})")

# Standings points
ACTUAL_STANDINGS = {
    "A": ["Mexico", "South Africa", "South Korea", "Czechia"],
    "B": ["Switzerland", "Canada", "Bosnia and Herzegovina", "Qatar"],
    "C": ["Brazil", "Morocco", "Scotland", "Haiti"],
    "D": ["United States", "Australia", "Paraguay", "Turkey"],
    "E": ["Germany", "Ivory Coast", "Ecuador", "Curaçao"],
    "F": ["Netherlands", "Japan", "Sweden", "Tunisia"],
    "G": ["Belgium", "Egypt", "Iran", "New Zealand"],
    "H": ["Spain", "Cape Verde", "Uruguay", "Saudi Arabia"],
    "I": ["France", "Norway", "Senegal", "Iraq"],
    "J": ["Argentina", "Austria", "Algeria", "Jordan"],
    "K": ["Colombia", "Portugal", "DR Congo", "Uzbekistan"],
    "L": ["England", "Croatia", "Ghana", "Panama"],
}
PRED_STANDINGS = {
    "A": ["Mexico", "Czechia", "South Korea", "South Africa"],
    "B": ["Switzerland", "Canada", "Bosnia and Herzegovina", "Qatar"],
    "C": ["Brazil", "Morocco", "Scotland", "Haiti"],
    "D": ["United States", "Turkey", "Australia", "Paraguay"],
    "E": ["Germany", "Ecuador", "Ivory Coast", "Curaçao"],
    "F": ["Netherlands", "Japan", "Sweden", "Tunisia"],
    "G": ["Belgium", "Iran", "Egypt", "New Zealand"],
    "H": ["Spain", "Uruguay", "Saudi Arabia", "Cape Verde"],
    "I": ["France", "Norway", "Senegal", "Iraq"],
    "J": ["Argentina", "Austria", "Algeria", "Jordan"],
    "K": ["Portugal", "Colombia", "DR Congo", "Uzbekistan"],
    "L": ["England", "Croatia", "Ghana", "Panama"],
}
pts_standings = 0
print("\nGroup standings accuracy:")
for g in sorted(ACTUAL_STANDINGS):
    act = ACTUAL_STANDINGS[g]
    pred = PRED_STANDINGS[g]
    gpts = sum(25 for i in range(4) if act[i] == pred[i])
    pts_standings += gpts
    match = "✓" if gpts == 100 else f"{gpts}pts"
    print(f"  Group {g}: predicted {pred} | actual {act}  [{match}]")
print(f"\nStandings points: {pts_standings}/1200")
print(f"Total estimated group-stage points: {pts_match + pts_standings}")

# ── Build updated ratings ──────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("UPDATED RATINGS (Elo-adjusted from actuals, 70/30 blend)")
print("=" * 70)
updated_elo = elo_update(orig, ACTUAL)
# Blend: 70% updated + 30% original
W_ACT, W_ORIG = 0.70, 0.30
blended_new = {t: W_ACT * updated_elo[t] + W_ORIG * orig[t] for t in orig}

# Show biggest movers
diffs = {t: blended_new[t] - orig[t] for t in orig}
sorted_diff = sorted(diffs.items(), key=lambda x: -abs(x[1]))
print("Biggest rating changes:")
for t, d in sorted_diff[:16]:
    arrow = "▲" if d > 0 else "▼"
    print(f"  {t:<24} {orig[t]:>7.1f} → {blended_new[t]:>7.1f}  {arrow}{abs(d):.1f}")

# ── R32 predictions with updated ratings ──────────────────────────────────────
print("\n" + "=" * 70)
print("R32 PREDICTIONS (updated ratings — actual results weighted 70%)")
print("=" * 70)

# Re-populate confederation map from ratings file
import run_predictions as rp
teams_all = set(orig.keys())
rp.load_ratings(teams_all)  # repopulates _CONF_MAP

R32_MATCHES = [
    # (date, team1, team2, venue_note)
    ("Jun 28", "South Africa",          "Canada",              "Los Angeles"),
    ("Jun 29", "Brazil",                "Japan",               "Houston"),
    ("Jun 29", "Germany",               "Paraguay",            "Foxborough"),
    ("Jun 29", "Netherlands",           "Morocco",             "Monterrey"),
    ("Jun 30", "Ivory Coast",           "Norway",              "Dallas"),
    ("Jun 30", "France",                "Sweden",              "East Rutherford"),
    ("Jun 30", "Mexico",                "Ecuador",             "Mexico City"),
    ("Jul 1",  "United States",         "Bosnia and Herzegovina", "Santa Clara"),
    ("Jul 1",  "England",               "DR Congo",            "Atlanta"),
    ("Jul 1",  "Belgium",               "Senegal",             "Seattle"),
    ("Jul 2",  "Argentina",             "Cape Verde",          "Miami"),
    ("Jul 2",  "Spain",                 "Austria",             "Los Angeles"),
    ("Jul 2",  "Switzerland",           "Algeria",             "Vancouver"),
    ("Jul 2",  "Portugal",              "Croatia",             "Toronto"),
    ("Jul 3",  "Colombia",              "Ghana",               "Kansas City"),
    ("Jul 3",  "Australia",             "Egypt",               "Dallas"),
]

pts_e, pts_o = KO_SCORING["R32"]

rows = []
for date, t1, t2, venue in R32_MATCHES:
    r1 = blended_new.get(t1, 1700)
    r2 = blended_new.get(t2, 1700)
    # Host bonus for KO stage
    h1 = CFG["host_adv_ko"].get(t1, 0.0) if t1 in HOSTS else 0.0
    h2 = CFG["host_adv_ko"].get(t2, 0.0) if t2 in HOSTS else 0.0
    l1, l2 = rp.match_lambdas(r1, r2, h1, h2, ko=True, t1=t1, t2=t2)
    g = score_grid(l1, l2)
    p1, px, p2 = outcome_probs(g)
    pick, ep, alts = best_pick(g, pts_exact=pts_e, pts_outcome=pts_o)
    alts_str = " | ".join(f"{a}-{b}({e:.0f})" for (a,b),e in alts[1:4])
    rows.append({
        "date": date, "team1": t1, "team2": t2, "venue": venue,
        "pick": f"{pick[0]}-{pick[1]}", "exp_pts": round(ep,1),
        "p_win1": round(p1,3), "p_draw": round(px,3), "p_win2": round(p2,3),
        "xG1": round(l1,2), "xG2": round(l2,2),
        "r1": round(r1,0), "r2": round(r2,0),
        "alts": alts_str,
    })

print(f"{'Date':<8} {'Match':<48} {'Pick':<7} {'E[pts]':<8} {'W/D/L':<16} {'Alternatives'}")
print("-" * 110)
for r in rows:
    wdl = f"{r['p_win1']*100:.0f}/{r['p_draw']*100:.0f}/{r['p_win2']*100:.0f}%"
    print(f"{r['date']:<8} {r['team1']+' vs '+r['team2']:<48} {r['pick']:<7} {r['exp_pts']:<8} {wdl:<16} {r['alts']}")

# Write to CSV
path = os.path.join(OUT, "r32_updated_predictions.csv")
with open(path, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader(); w.writerows(rows)
print(f"\nWrote → {path}")
