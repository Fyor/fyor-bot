#!/usr/bin/env python3
"""
Full 2026 World Cup prediction runner.
Reads data from ../data/, writes results to ../output/.
Produces match picks for all 72 group games + tournament simulation stats.
"""
from __future__ import annotations

import csv
import json
import math
import os
import sys
from collections import defaultdict

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")
OUT = os.path.join(HERE, "..", "output")

# ── Config ────────────────────────────────────────────────────────────────────

CFG = dict(
    # Model blend: bookmaker-implied strength vs raw Elo
    w_odds=0.65, w_elo=0.35,
    # Goals model: calibrated on WC 2010-2022 (avg 2.27–2.69 gpg)
    gd_slope=0.0036,          # expected goal-diff per Elo point
    gd_cap=3.4,
    total_base_group=2.55,    # evenly-matched group game expected total
    total_base_ko=2.35,
    mismatch_bump=1.05,       # extra goals at extreme mismatches
    lambda_floor=0.18,
    rho=-0.10,                # Dixon-Coles low-score adjustment (draw inflation)
    max_g=10,                 # scoreline grid
    host_adv_group=90.0,      # host Elo bonus at home group venue
    host_adv_ko={"United States": 80.0, "Mexico": 50.0, "Canada": 45.0},
    et_skill_carry=0.55,      # skill-carry through extra time / penalties
    # Simulation
    n_fit=8000, fit_iter=16, fit_lr=0.4, fit_step=60.0, fit_band=280.0,
    n_sim=40000, seed=26,
    # Prediction-game points (Kicktipp classic)
    pts_exact=4, pts_gd=3, pts_tend=2,
    pick_max=6,
)

HOST_CITY_COUNTRY = {
    "Mexico City": "Mexico", "Guadalajara": "Mexico", "Monterrey": "Mexico",
    "Toronto": "Canada", "Vancouver": "Canada",
}
HOSTS = {"Mexico", "Canada", "United States"}

ALIASES = {
    "usa": "United States", "u.s.a.": "United States",
    "korea republic": "South Korea", "ir iran": "Iran",
    "cote d'ivoire": "Ivory Coast", "côte d'ivoire": "Ivory Coast",
    "dr congo": "DR Congo", "democratic republic of the congo": "DR Congo",
    "curacao": "Curaçao", "turkiye": "Turkey", "türkiye": "Turkey",
    "cabo verde": "Cape Verde", "czech republic": "Czechia",
    "bosnia": "Bosnia and Herzegovina", "bosnia-herzegovina": "Bosnia and Herzegovina",
}


def canon(name: str, known: set | None = None) -> str:
    n = name.strip().strip('"')
    k = n.lower()
    if k in ALIASES:
        return ALIASES[k]
    if known:
        for t in known:
            if t.lower() == k:
                return t
    return n


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return [{k.strip().lower(): (v or "").strip()
                 for k, v in row.items()} for row in csv.DictReader(f)]


# ── Data loaders ──────────────────────────────────────────────────────────────

def load_groups():
    rows = read_csv(os.path.join(DATA, "groups.csv"))
    g: dict[str, list[str]] = defaultdict(list)
    for r in rows:
        grp = r["group"].strip().upper().replace("GROUP ", "")
        g[grp].append(canon(r["team"]))
    g = dict(sorted(g.items()))
    assert len(g) == 12
    for grp, ts in g.items():
        assert len(ts) == 4, f"group {grp}: {ts}"
    return g


def load_fixtures(teams):
    rows = read_csv(os.path.join(DATA, "fixtures_group_stage.csv"))
    fx = []
    for r in rows:
        t1 = canon(r["team1"], teams)
        t2 = canon(r["team2"], teams)
        if t1 not in teams:
            raise ValueError(f"Unknown team: {t1}")
        if t2 not in teams:
            raise ValueError(f"Unknown team: {t2}")
        fx.append(dict(
            match=int(r["match_number"]), date=r["date"],
            group=r["group"].strip().upper().replace("GROUP ", ""),
            t1=t1, t2=t2, city=r.get("city", ""),
        ))
    fx.sort(key=lambda x: x["match"])
    assert len(fx) == 72, f"expected 72 fixtures, got {len(fx)}"
    return fx


def load_ratings(teams):
    rows = read_csv(os.path.join(DATA, "team_ratings.csv"))
    elo, fifa = {}, {}
    for r in rows:
        t = canon(r["team"], teams)
        if t not in teams:
            continue
        if r.get("elo"):
            elo[t] = float(r["elo"])
        if r.get("fifa_rank"):
            fifa[t] = int(float(r["fifa_rank"]))
    missing = teams - set(elo)
    if missing:
        raise ValueError(f"Missing Elo for: {sorted(missing)}")
    return elo, fifa


def load_winner_odds(teams):
    rows = read_csv(os.path.join(DATA, "winner_odds.csv"))
    acc = defaultdict(list)
    for r in rows:
        t = canon(r["team"], teams)
        if t in teams and r.get("decimal_odds"):
            try:
                acc[t].append(float(r["decimal_odds"]))
            except ValueError:
                pass
    return {t: float(np.mean(v)) for t, v in acc.items()}


# ── Probability model ─────────────────────────────────────────────────────────

def devig(odds: dict, elo: dict) -> dict:
    """Power-method de-vig; spread residual mass to unquoted teams by Elo."""
    quoted = sorted(odds)
    raw = np.array([1.0 / odds[t] for t in quoted])

    def total(k): return float(np.sum(raw ** k))

    lo, hi = 0.5, 3.0
    for _ in range(100):
        mid = 0.5 * (lo + hi)
        if total(mid) > 0.995:
            lo = mid
        else:
            hi = mid
    k = 0.5 * (lo + hi)
    probs = {t: float(p) for t, p in zip(quoted, raw ** k)}
    rest = [t for t in elo if t not in probs]
    if rest:
        w = np.array([10 ** (elo[t] / 400) for t in rest])
        w = w / w.sum() * max(1.0 - sum(probs.values()), 1e-4)
        for t, p in zip(rest, w):
            probs[t] = float(p)
    s = sum(probs.values())
    return {t: p / s for t, p in probs.items()}


def we(d): return 1.0 / (1.0 + 10 ** (-d / 400.0))


def match_lambdas(r1, r2, h1=0.0, h2=0.0, ko=False):
    d = (r1 + h1) - (r2 + h2)
    gd = float(np.clip(CFG["gd_slope"] * d, -CFG["gd_cap"], CFG["gd_cap"]))
    base = CFG["total_base_ko"] if ko else CFG["total_base_group"]
    total = base + CFG["mismatch_bump"] * (2 * abs(we(d) - 0.5)) ** 2
    total = max(total, abs(gd) + 2 * CFG["lambda_floor"])
    lam1 = max((total + gd) / 2.0, CFG["lambda_floor"])
    lam2 = max((total - gd) / 2.0, CFG["lambda_floor"])
    return float(lam1), float(lam2)


def score_grid(lam1, lam2):
    n = CFG["max_g"] + 1
    i = np.arange(n)
    fac = np.array([math.factorial(x) for x in i], dtype=float)
    p1 = np.exp(-lam1) * (lam1 ** i) / fac
    p2 = np.exp(-lam2) * (lam2 ** i) / fac
    g = np.outer(p1, p2)
    rho = CFG["rho"]
    g[0, 0] *= 1 - lam1 * lam2 * rho
    g[0, 1] *= 1 + lam1 * rho
    g[1, 0] *= 1 + lam2 * rho
    g[1, 1] *= 1 - rho
    g = np.maximum(g, 0)
    return g / g.sum()


def outcome_probs(g):
    p1 = float(np.tril(g, -1).sum())
    px = float(np.trace(g))
    p2 = float(np.triu(g, 1).sum())
    return p1, px, p2


def best_pick(g):
    n = CFG["pick_max"] + 1
    sz = g.shape[0]
    best, best_ep = (0, 0), -1.0
    alts = []
    for a in range(n):
        for b in range(n):
            p_exact = g[a, b]
            diff_ab = a - b
            same_gd = 0.0
            for x in range(sz):
                for y in range(sz):
                    if x - y == diff_ab and not (x == a and y == b):
                        same_gd += g[x, y]
            if diff_ab > 0:
                same_tend = float(np.tril(g, -1).sum()) - p_exact - same_gd
            elif diff_ab < 0:
                same_tend = float(np.triu(g, 1).sum()) - p_exact - same_gd
            else:
                same_tend = float(np.trace(g)) - p_exact - same_gd
            ep = (CFG["pts_exact"] * p_exact +
                  CFG["pts_gd"] * same_gd +
                  CFG["pts_tend"] * same_tend)
            alts.append(((a, b), float(ep)))
            if ep > best_ep:
                best, best_ep = (a, b), float(ep)
    alts.sort(key=lambda x: -x[1])
    return best, best_ep, alts[:5]


# ── Tournament simulator ──────────────────────────────────────────────────────

def host_bonus_for(team, city, ko=False):
    if team not in HOSTS:
        return 0.0
    if ko:
        return CFG["host_adv_ko"].get(team, 0.0)
    country = HOST_CITY_COUNTRY.get(city, "United States")
    return CFG["host_adv_group"] if country == team else 0.0


def simulate(groups, fixtures, ratings, n_sims, rng, collect=False):
    from bracket import BRACKET_2026, resolve_round_of_32
    teams = sorted({t for ts in groups.values() for t in ts})
    idx = {t: i for i, t in enumerate(teams)}
    nT = len(teams)
    glabels = sorted(groups)

    # Precompute group-stage scoreline CDFs
    cdfs = []
    for fx in fixtures:
        i1, i2 = idx[fx["t1"]], idx[fx["t2"]]
        l1, l2 = match_lambdas(
            ratings[fx["t1"]], ratings[fx["t2"]],
            host_bonus_for(fx["t1"], fx["city"]),
            host_bonus_for(fx["t2"], fx["city"]),
        )
        g = score_grid(l1, l2)
        cdfs.append((i1, i2, np.cumsum(g.ravel()), g.shape[0]))

    pts_all = np.zeros((n_sims, nT), dtype=np.int32)
    gf_all = np.zeros((n_sims, nT), dtype=np.int32)
    ga_all = np.zeros((n_sims, nT), dtype=np.int32)

    for i1, i2, cdf, sz in cdfs:
        u = rng.random(n_sims)
        k = np.searchsorted(cdf, u)
        g1, g2 = k // sz, k % sz
        pts_all[:, i1] += np.where(g1 > g2, 3, np.where(g1 == g2, 1, 0)).astype(np.int32)
        pts_all[:, i2] += np.where(g2 > g1, 3, np.where(g1 == g2, 1, 0)).astype(np.int32)
        gf_all[:, i1] += g1; ga_all[:, i1] += g2
        gf_all[:, i2] += g2; ga_all[:, i2] += g1

    noise = rng.random((n_sims, nT)) * 1e-3
    key = pts_all * 1e6 + (gf_all - ga_all) * 1e3 + gf_all + noise

    group_rank = {}
    for g, ts in groups.items():
        cols = np.array([idx[t] for t in ts])
        order = np.argsort(-key[:, cols], axis=1)
        group_rank[g] = cols[order]   # (n_sims, 4)

    thirds = np.stack([group_rank[g][:, 2] for g in glabels], axis=1)
    third_key = np.take_along_axis(key, thirds, axis=1)
    third_order = np.argsort(-third_key, axis=1)
    best8 = third_order[:, :8]

    winners = {g: group_rank[g][:, 0] for g in glabels}
    runners = {g: group_rank[g][:, 1] for g in glabels}

    champ_counts = np.zeros(nT, dtype=np.int64)
    stages = {s: np.zeros(nT, dtype=np.int64)
              for s in ("R32", "R16", "QF", "SF", "F", "W")}
    matches_ko = np.zeros(nT, dtype=np.int64)
    exp_gf = gf_all.mean(axis=0)

    ko_cache: dict = {}

    def ko_wp(a, b):
        if (a, b) not in ko_cache:
            ta, tb = teams[a], teams[b]
            l1, l2 = match_lambdas(ratings[ta], ratings[tb],
                                   CFG["host_adv_ko"].get(ta, 0.0) if ta in HOSTS else 0.0,
                                   CFG["host_adv_ko"].get(tb, 0.0) if tb in HOSTS else 0.0,
                                   ko=True)
            g = score_grid(l1, l2)
            p1, px, _ = outcome_probs(g)
            pet = 0.5 + (we(ratings[ta] - ratings[tb]) - 0.5) * CFG["et_skill_carry"]
            ko_cache[(a, b)] = p1 + px * pet
            ko_cache[(b, a)] = 1.0 - ko_cache[(a, b)]
        return ko_cache[(a, b)]

    adv_counts = np.zeros(nT, dtype=np.int64)
    wg_counts = np.zeros(nT, dtype=np.int64)

    for s in range(n_sims):
        w = {g: int(winners[g][s]) for g in glabels}
        r = {g: int(runners[g][s]) for g in glabels}
        adv_groups = [glabels[j] for j in best8[s]]
        third_t = {glabels[j]: int(thirds[s, j]) for j in range(12)}
        pairs = resolve_round_of_32(BRACKET_2026, w, r, adv_groups, third_t)

        for g in glabels:
            wg_counts[w[g]] += 1
            adv_counts[w[g]] += 1
            adv_counts[r[g]] += 1
        for j in best8[s]:
            adv_counts[thirds[s, j]] += 1

        for stage_name in ("R32", "R16", "QF", "SF"):
            nxt = []
            for a, b in pairs:
                stages[stage_name][a] += 1
                stages[stage_name][b] += 1
                matches_ko[a] += 1
                matches_ko[b] += 1
                winner = a if rng.random() < ko_wp(a, b) else b
                nxt.append(winner)
            pairs = [(nxt[i], nxt[i + 1]) for i in range(0, len(nxt), 2)]

        (fa, fb), = pairs
        stages["F"][fa] += 1; stages["F"][fb] += 1
        matches_ko[fa] += 1; matches_ko[fb] += 1
        champ = fa if rng.random() < ko_wp(fa, fb) else fb
        champ_counts[champ] += 1
        stages["W"][champ] += 1

    if not collect:
        return champ_counts

    return {
        "champ": champ_counts, "stages": stages,
        "advance": adv_counts, "win_group": wg_counts,
        "matches_ko": matches_ko, "exp_gf": exp_gf,
        "group_rank": group_rank, "teams": teams, "idx": idx, "n": n_sims,
    }


# ── Odds-rating fitter ────────────────────────────────────────────────────────

def fit_ratings(groups, fixtures, elo, target, rng):
    ratings = dict(elo)
    teams = sorted({t for ts in groups.values() for t in ts})
    p = np.array([target[t] for t in teams])
    elo_v = np.array([elo[t] for t in teams])
    for it in range(CFG["fit_iter"]):
        counts = simulate(groups, fixtures, ratings, CFG["n_fit"], rng)
        q = (counts + 1.0) / (counts.sum() + len(teams))
        step = CFG["fit_lr"] * (400 / math.log(10)) * np.log(p / q)
        step = np.clip(step, -CFG["fit_step"], CFG["fit_step"])
        new = np.array([ratings[t] for t in teams]) + step
        new = np.clip(new, elo_v - CFG["fit_band"], elo_v + CFG["fit_band"])
        ratings = {t: float(v) for t, v in zip(teams, new)}
        err = float(np.abs(np.log(p / q)).mean())
        print(f"  fit {it+1:2d}: mean|log p/q|={err:.3f}", flush=True)
    return ratings


# ── Output writers ────────────────────────────────────────────────────────────

def write_match_predictions(fixtures, ratings, groups_map, group_of):
    rows = []
    for fx in fixtures:
        l1, l2 = match_lambdas(
            ratings[fx["t1"]], ratings[fx["t2"]],
            host_bonus_for(fx["t1"], fx["city"]),
            host_bonus_for(fx["t2"], fx["city"]),
        )
        g = score_grid(l1, l2)
        p1, px, p2 = outcome_probs(g)
        pick, ep, alts = best_pick(g)
        # Compute modal score (highest single probability for reference)
        modal_idx = np.unravel_index(np.argmax(g), g.shape)
        rows.append({
            "match": fx["match"], "date": fx["date"],
            "group": fx["group"], "team1": fx["t1"], "team2": fx["t2"],
            "city": fx["city"],
            "xG1": round(l1, 2), "xG2": round(l2, 2),
            "modal_score": f"{modal_idx[0]}-{modal_idx[1]}",
            "optimal_pick": f"{pick[0]}-{pick[1]}",
            "exp_pts": round(ep, 3),
            "p_win1": round(p1, 3), "p_draw": round(px, 3), "p_win2": round(p2, 3),
            "top_alternatives": " | ".join(
                f"{a}-{b}({e:.2f}pts)" for (a, b), e in alts[:4]
            ),
        })
    path = os.path.join(OUT, "match_predictions.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)
    print(f"  Wrote {len(rows)} match predictions → {path}")
    return rows


def write_champion_probs(stats, elo, ratings_blended, odds, group_of):
    teams = stats["teams"]
    n = stats["n"]
    rows = []
    for t in sorted(teams, key=lambda t: -stats["champ"][stats["idx"][t]]):
        i = stats["idx"][t]
        rows.append({
            "team": t, "group": group_of[t],
            "elo": round(elo[t]),
            "rating": round(ratings_blended[t], 1),
            "avg_odds": round(odds.get(t, 99.0), 2),
            "p_win_group": round(stats["win_group"][i] / n, 4),
            "p_advance": round(stats["advance"][i] / n, 4),
            "p_R32": round(stats["stages"]["R32"][i] / n, 4),
            "p_R16": round(stats["stages"]["R16"][i] / n, 4),
            "p_QF": round(stats["stages"]["QF"][i] / n, 4),
            "p_SF": round(stats["stages"]["SF"][i] / n, 4),
            "p_Final": round(stats["stages"]["F"][i] / n, 4),
            "p_Champion": round(stats["champ"][i] / n, 4),
            "exp_group_goals": round(stats["exp_gf"][i], 2),
            "avg_ko_matches": round(stats["matches_ko"][i] / n, 2),
        })
    path = os.path.join(OUT, "champion_probs.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)
    print(f"  Wrote champion probabilities → {path}")
    return rows


def write_group_predictions(fixtures, ratings, groups, group_of):
    """Write per-group expected standings using mean-field table."""
    lines = []
    for grp in sorted(groups):
        ts = groups[grp]
        # Points table from expected outcomes (not simulation, for speed)
        pts = {t: 0.0 for t in ts}
        gfd = {t: 0.0 for t in ts}
        gff = {t: 0.0 for t in ts}
        grp_fixtures = [fx for fx in fixtures if fx["group"] == grp]
        for fx in grp_fixtures:
            l1, l2 = match_lambdas(
                ratings[fx["t1"]], ratings[fx["t2"]],
                host_bonus_for(fx["t1"], fx["city"]),
                host_bonus_for(fx["t2"], fx["city"]),
            )
            g = score_grid(l1, l2)
            p1, px, p2 = outcome_probs(g)
            pts[fx["t1"]] += 3 * p1 + px
            pts[fx["t2"]] += 3 * p2 + px
            # Expected goals
            E_g1 = float(np.sum(np.arange(g.shape[0]) * g.sum(axis=1)))
            E_g2 = float(np.sum(np.arange(g.shape[1]) * g.sum(axis=0)))
            gff[fx["t1"]] += E_g1; gfd[fx["t1"]] += E_g1 - E_g2
            gff[fx["t2"]] += E_g2; gfd[fx["t2"]] += E_g2 - E_g1
        ranked = sorted(ts, key=lambda t: -(pts[t] * 1000 + gfd[t] * 10 + gff[t]))
        lines.append(f"\n## Group {grp}\n")
        lines.append(f"{'Pos':<4} {'Team':<26} {'xPts':>6} {'xGD':>6} {'xGF':>5}\n")
        lines.append("-" * 48 + "\n")
        for pos, t in enumerate(ranked, 1):
            qual = "✓ Q" if pos <= 2 else ("   (borderline 3rd)" if pos == 3 else "   ✗")
            lines.append(
                f"{pos:<4} {t:<26} {pts[t]:>6.2f} {gfd[t]:>+6.2f} {gff[t]:>5.2f} {qual}\n"
            )
        lines.append("\nGroup fixtures (optimal picks):\n")
        for fx in sorted(grp_fixtures, key=lambda x: x["match"]):
            l1, l2 = match_lambdas(
                ratings[fx["t1"]], ratings[fx["t2"]],
                host_bonus_for(fx["t1"], fx["city"]),
                host_bonus_for(fx["t2"], fx["city"]),
            )
            g = score_grid(l1, l2)
            p1, px, p2 = outcome_probs(g)
            pick, ep, alts = best_pick(g)
            result_line = (
                f"  {fx['date']}  {fx['t1']:<22} {pick[0]}-{pick[1]}"
                f"  {fx['t2']:<22}  "
                f"[W{p1:.0%} D{px:.0%} L{p2:.0%}]  "
                f"alts: {', '.join(f'{a}-{b}' for (a,b),_ in alts[1:4])}\n"
            )
            lines.append(result_line)
    path = os.path.join(OUT, "group_predictions.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write("# Group Stage Predictions — 2026 World Cup\n")
        f.writelines(lines)
    print(f"  Wrote group predictions → {path}")


def write_topscorer_predictions(stats, fixtures, ratings, groups):
    """Estimate expected tournament goals for each player/team."""
    teams = stats["teams"]
    n = stats["n"]
    # Expected goals per team = group-stage goals + knockout stage goals
    exp_group_g = stats["exp_gf"]
    # Expected KO goals: avg goals per KO match * expected KO matches played
    ko_gpg = CFG["total_base_ko"] * 0.55  # team goals in a KO game at average strength
    exp_ko_g = stats["matches_ko"] / n * ko_gpg

    # Load golden boot odds
    tb_rows = read_csv(os.path.join(DATA, "topscorer_odds.csv"))
    players = []
    seen = set()
    for r in tb_rows:
        player = r.get("player", "").strip()
        team = canon(r.get("team", "").strip(), set(teams))
        if not player or player in seen:
            continue
        seen.add(player)
        try:
            odds = float(r["decimal_odds"])
        except (ValueError, KeyError):
            odds = 99.0
        i = stats["idx"].get(team)
        if i is None:
            continue
        team_exp_g = float(exp_group_g[i]) + float(exp_ko_g[i])
        # Crude individual share: assume top striker scores ~35% of team goals
        # weighted by tournament penetration
        p_advance = stats["advance"][i] / n
        p_deep = stats["stages"]["QF"][i] / n + stats["stages"]["SF"][i] / n * 0.5
        personal_exp_g = team_exp_g * 0.33 * (1 + p_deep * 0.4)
        players.append({
            "player": player, "team": team,
            "golden_boot_odds": odds,
            "p_champion_odds_implied": round(1.0 / odds, 4),
            "team_p_advance_group": round(p_advance, 3),
            "team_p_quarterfinal": round(stats["stages"]["QF"][i] / n, 3),
            "team_exp_goals_total": round(team_exp_g, 2),
            "player_exp_goals": round(personal_exp_g, 2),
        })
    players.sort(key=lambda x: -x["player_exp_goals"])
    path = os.path.join(OUT, "topscorer_predictions.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(players[0]))
        w.writeheader(); w.writerows(players)
    print(f"  Wrote top scorer predictions → {path}")
    return players


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    os.makedirs(OUT, exist_ok=True)
    sys.path.insert(0, HERE)

    print("Loading data…")
    groups = load_groups()
    teams = {t for ts in groups.values() for t in ts}
    group_of = {t: g for g, ts in groups.items() for t in ts}
    fixtures = load_fixtures(teams)
    elo, fifa = load_ratings(teams)
    odds = load_winner_odds(teams)
    print(f"  {len(teams)} teams, {len(fixtures)} fixtures, odds for {len(odds)}")

    print("De-vigging bookmaker odds → champion probabilities…")
    target = devig(odds, elo)

    rng = np.random.default_rng(CFG["seed"])
    print("Fitting odds-implied ratings (Leitner/Zeileis bookmaker-consensus style)…")
    r_fit = fit_ratings(groups, fixtures, elo, target, rng)

    blended = {t: CFG["w_odds"] * r_fit[t] + CFG["w_elo"] * elo[t]
               for t in teams}

    rng2 = np.random.default_rng(CFG["seed"] + 1)
    print(f"Running {CFG['n_sim']:,} tournament simulations…")
    stats = simulate(groups, fixtures, blended, CFG["n_sim"], rng2, collect=True)

    print("Writing outputs…")
    match_rows = write_match_predictions(fixtures, blended, groups, group_of)
    champ_rows = write_champion_probs(stats, elo, blended, odds, group_of)
    write_group_predictions(fixtures, blended, groups, group_of)
    scorer_rows = write_topscorer_predictions(stats, fixtures, blended, groups)

    # ── Final summary ──────────────────────────────────────────────────────
    n = stats["n"]
    teams_list = stats["teams"]
    idx = stats["idx"]

    top5 = sorted(teams_list,
                  key=lambda t: -stats["champ"][idx[t]])[:5]
    print("\n" + "=" * 60)
    print("TOURNAMENT CHAMPION PROBABILITIES (top 10)")
    print("=" * 60)
    for t in sorted(teams_list, key=lambda t: -stats["champ"][idx[t]])[:10]:
        i = idx[t]
        print(f"  {t:<24} {stats['champ'][i]/n*100:5.1f}%  "
              f"(Final: {stats['stages']['F'][i]/n*100:.1f}%)")

    print("\nPREDICTED CHAMPION: " + top5[0])
    print("\nTOP SCORER PREDICTIONS (top 6):")
    for p in scorer_rows[:6]:
        print(f"  {p['player']:<22} ({p['team']:<14}) "
              f"xGoals={p['player_exp_goals']:.2f}  "
              f"odds={p['golden_boot_odds']}")

    with open(os.path.join(OUT, "simulation_summary.json"), "w") as f:
        json.dump({
            "top_champion": {
                t: round(stats["champ"][idx[t]] / n, 4)
                for t in sorted(teams_list,
                                key=lambda t: -stats["champ"][idx[t]])[:15]
            },
            "top_scorer_prediction": [p["player"] for p in scorer_rows[:6]],
        }, f, indent=2)
    print("\nDone. All outputs in worldcup2026/output/")


if __name__ == "__main__":
    main()
