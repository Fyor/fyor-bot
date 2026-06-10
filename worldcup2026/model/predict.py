#!/usr/bin/env python3
"""
World Cup 2026 prediction pipeline.

Methodology (see ../research/methodology.md for evidence & citations):
  1. Team strength = blend of (a) ratings implied by de-vigged bookmaker
     outright-winner odds, recovered by inverting a Monte-Carlo tournament
     simulation (bookmaker-consensus approach, Leitner/Zeileis/Hornik style),
     and (b) World Football Elo ratings.
  2. Strength difference -> expected goals via a calibrated mapping;
     scorelines via independent Poisson with a Dixon-Coles low-score
     adjustment (slight draw inflation).
  3. Full tournament Monte Carlo (group tables incl. tiebreakers, best-third
     ranking and allocation, knockout bracket with extra-time/penalty model).
  4. Score picks per match maximize EXPECTED PREDICTION-GAME POINTS under a
     configurable kicktipp-style scoring system (exact / goal-diff / tendency).

Inputs (../data/):  groups.csv, fixtures_group_stage.csv, team_ratings.csv,
                    winner_odds.csv, topscorer_odds.csv
Outputs (../output/): match_predictions.csv, group_tables.md,
                    knockout_path.md, champion_probs.csv, simulation_summary.json
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

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------

CONFIG = {
    # Strength blend weights (must sum to 1). Evidence: bookmaker consensus
    # is the strongest single forecaster; Elo adds robustness/regularization.
    "w_odds": 0.65,
    "w_elo": 0.35,

    # Elo-difference -> goals mapping
    "gd_slope": 0.0036,        # expected goal difference per Elo point
    "gd_cap": 3.4,             # cap on expected goal difference
    "total_base_group": 2.55,  # expected total goals, evenly matched, group stage
    "total_base_ko": 2.35,     # expected total goals, evenly matched, knockouts
    "total_mismatch_bump": 1.1,  # extra total goals at maximal mismatch
    "lambda_floor": 0.18,      # minimum expected goals for a side

    "dixon_coles_rho": -0.10,  # low-score dependence (inflates draws slightly)
    "max_goals_grid": 10,      # scoreline grid size for probabilities

    # Host advantage in Elo points when a host nation plays in its own country
    "host_adv_group": 100.0,
    "host_adv_ko": {"United States": 80.0, "Mexico": 50.0, "Canada": 50.0},

    # P(win in extra time / penalties | draw after 90') for the stronger side:
    # 0.5 + (We-0.5)*et_skill_carry
    "et_skill_carry": 0.55,

    # Monte Carlo
    "n_sims": 40000,
    "n_sims_fit": 8000,
    "fit_iterations": 16,
    "fit_lr": 0.4,
    "fit_max_step": 60.0,
    "fit_rating_band": 280.0,  # max |odds-rating - elo| allowed by the fit
    "seed": 26,

    # Prediction-game scoring (kicktipp classic): exact / correct gd / tendency
    "pts_exact": 4,
    "pts_gd": 3,
    "pts_tendency": 2,
    "pick_grid_max": 6,        # search picks among 0..6 x 0..6
}

HOST_COUNTRY_BY_CITY = {
    # Mexico
    "Mexico City": "Mexico", "Guadalajara": "Mexico", "Monterrey": "Mexico",
    # Canada
    "Toronto": "Canada", "Vancouver": "Canada",
    # USA (everything else in the 2026 schedule)
}
HOSTS = {"Mexico", "Canada", "United States"}

# Team-name aliases -> canonical (canonical = name used in groups.csv)
ALIASES = {
    "usa": "United States", "u.s.a.": "United States", "united states of america": "United States",
    "us": "United States", "u.s.": "United States",
    "korea republic": "South Korea", "republic of korea": "South Korea", "korea": "South Korea",
    "ir iran": "Iran", "iran ir": "Iran",
    "cote d'ivoire": "Ivory Coast", "côte d'ivoire": "Ivory Coast", "cote divoire": "Ivory Coast",
    "dr congo": "DR Congo", "congo dr": "DR Congo", "democratic republic of the congo": "DR Congo",
    "curacao": "Curaçao", "curaçao": "Curaçao",
    "cabo verde": "Cape Verde", "cape verde islands": "Cape Verde",
    "saudiarabia": "Saudi Arabia", "ksa": "Saudi Arabia",
    "new zealand": "New Zealand", "uae": "United Arab Emirates",
    "czech republic": "Czechia", "turkiye": "Turkey", "türkiye": "Turkey",
    "bosnia": "Bosnia and Herzegovina", "bosnia-herzegovina": "Bosnia and Herzegovina",
    "northern ireland": "Northern Ireland", "republic of ireland": "Ireland",
}


def canon(name: str, known: set[str] | None = None) -> str:
    n = name.strip().strip('"')
    key = n.lower()
    if key in ALIASES:
        return ALIASES[key]
    if known:
        for k in known:
            if k.lower() == key:
                return k
    return n


# --------------------------------------------------------------------------
# Data loading
# --------------------------------------------------------------------------

def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return [{k.strip().lower(): (v or "").strip() for k, v in row.items()}
                for row in csv.DictReader(f)]


def load_groups():
    rows = read_csv(os.path.join(DATA, "groups.csv"))
    groups: dict[str, list[str]] = defaultdict(list)
    for r in rows:
        g = r["group"].strip().upper().replace("GROUP ", "")
        groups[g].append(canon(r["team"]))
    groups = dict(sorted(groups.items()))
    assert len(groups) == 12, f"expected 12 groups, got {len(groups)}"
    for g, ts in groups.items():
        assert len(ts) == 4, f"group {g} has {len(ts)} teams"
    return groups


def load_fixtures(teams: set[str]):
    rows = read_csv(os.path.join(DATA, "fixtures_group_stage.csv"))
    fixtures = []
    for r in rows:
        t1, t2 = canon(r["team1"], teams), canon(r["team2"], teams)
        assert t1 in teams, f"unknown team in fixtures: {t1!r}"
        assert t2 in teams, f"unknown team in fixtures: {t2!r}"
        fixtures.append({
            "match": int(r["match_number"]),
            "date": r["date"],
            "group": r["group"].strip().upper().replace("GROUP ", ""),
            "t1": t1, "t2": t2,
            "city": r.get("city", ""),
        })
    fixtures.sort(key=lambda x: x["match"])
    assert len(fixtures) == 72, f"expected 72 fixtures, got {len(fixtures)}"
    return fixtures


def load_ratings(teams: set[str]):
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
    assert not missing, f"missing Elo for: {sorted(missing)}"
    return elo, fifa


def load_winner_odds(teams: set[str]):
    """Average decimal odds per team across bookmakers."""
    rows = read_csv(os.path.join(DATA, "winner_odds.csv"))
    acc = defaultdict(list)
    for r in rows:
        t = canon(r["team"], teams)
        if t in teams and r.get("decimal_odds"):
            acc[t].append(float(r["decimal_odds"]))
    return {t: float(np.mean(v)) for t, v in acc.items()}


# --------------------------------------------------------------------------
# Odds -> probabilities (de-vig with power method, handles longshot bias)
# --------------------------------------------------------------------------

def devig_power(odds: dict[str, float], elo: dict[str, float]) -> dict[str, float]:
    """Convert outright odds to champion probabilities.

    Power method: p_i = (1/odds_i)^k, k chosen so probabilities sum to <=1
    over quoted teams; remaining mass spread over unquoted teams by Elo.
    """
    quoted = sorted(odds)
    raw = np.array([1.0 / odds[t] for t in quoted])

    def total(k):
        return float(np.sum(raw ** k))

    lo, hi = 0.5, 3.0
    target = 0.995  # leave a sliver for unquoted longshots
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if total(mid) > target:
            lo = mid  # need larger k to shrink the probabilities
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


# --------------------------------------------------------------------------
# Match model
# --------------------------------------------------------------------------

def win_expectancy(d):
    return 1.0 / (1.0 + 10 ** (-d / 400.0))


def lambdas(r1, r2, host_bonus1=0.0, host_bonus2=0.0, knockout=False):
    """Expected goals (lam1, lam2) for a match given Elo-scale ratings."""
    c = CONFIG
    d = (r1 + host_bonus1) - (r2 + host_bonus2)
    we = win_expectancy(d)
    gd = np.clip(c["gd_slope"] * d, -c["gd_cap"], c["gd_cap"])
    base = c["total_base_ko"] if knockout else c["total_base_group"]
    total = base + c["total_mismatch_bump"] * (2 * abs(we - 0.5)) ** 2
    total = max(total, abs(gd) + 2 * c["lambda_floor"])
    lam1 = max((total + gd) / 2.0, c["lambda_floor"])
    lam2 = max((total - gd) / 2.0, c["lambda_floor"])
    return float(lam1), float(lam2)


def score_grid(lam1, lam2):
    """P(i goals, j goals) grid with Dixon-Coles low-score adjustment."""
    n = CONFIG["max_goals_grid"] + 1
    i = np.arange(n)
    p1 = np.exp(-lam1) * lam1 ** i / np.array([math.factorial(x) for x in i])
    p2 = np.exp(-lam2) * lam2 ** i / np.array([math.factorial(x) for x in i])
    grid = np.outer(p1, p2)
    rho = CONFIG["dixon_coles_rho"]
    # Dixon & Coles (1997) tau adjustment on the four low-score cells
    grid[0, 0] *= 1 - lam1 * lam2 * rho
    grid[0, 1] *= 1 + lam1 * rho
    grid[1, 0] *= 1 + lam2 * rho
    grid[1, 1] *= 1 - rho
    grid = np.maximum(grid, 0)
    return grid / grid.sum()


def outcome_probs(grid):
    p1 = float(np.tril(grid, -1).sum())   # rows = team1 goals; i>j
    px = float(np.trace(grid))
    p2 = float(np.triu(grid, 1).sum())
    return p1, px, p2


def best_pick(grid):
    """Scoreline maximizing expected prediction-game points."""
    c = CONFIG
    n = c["pick_grid_max"] + 1
    g = grid
    size = g.shape[0]
    ii, jj = np.meshgrid(np.arange(size), np.arange(size), indexing="ij")
    diff = ii - jj
    sign = np.sign(diff)
    best, best_ep, ranking = None, -1.0, []
    for a in range(n):
        for b in range(n):
            exact = g[a, b]
            same_gd = g[diff == (a - b)].sum() - exact
            same_tend = g[sign == np.sign(a - b)].sum() - same_gd - exact
            ep = c["pts_exact"] * exact + c["pts_gd"] * same_gd + c["pts_tendency"] * same_tend
            ranking.append(((a, b), float(ep)))
            if ep > best_ep:
                best, best_ep = (a, b), float(ep)
    ranking.sort(key=lambda x: -x[1])
    return best, best_ep, ranking[:4]


# --------------------------------------------------------------------------
# Tournament simulation (vectorized across sims)
# --------------------------------------------------------------------------

class Tournament:
    def __init__(self, groups, fixtures, bracket_spec):
        self.groups = groups                    # {"A": [4 teams], ...}
        self.fixtures = fixtures                # 72 dicts
        self.bracket = bracket_spec             # see model/bracket.py
        self.teams = sorted({t for ts in groups.values() for t in ts})
        self.idx = {t: i for i, t in enumerate(self.teams)}
        self.group_of = {t: g for g, ts in groups.items() for t in ts}

    def host_bonus(self, team, city, knockout=False):
        if team not in HOSTS:
            return 0.0
        country = HOST_COUNTRY_BY_CITY.get(city, "United States")
        if knockout:
            return CONFIG["host_adv_ko"].get(team, 0.0)
        return CONFIG["host_adv_group"] if country == team else 0.0

    # -- group stage ------------------------------------------------------
    def simulate(self, ratings: dict[str, float], n_sims: int, rng,
                 collect=False):
        """Returns champion counts (and optional rich stats)."""
        nT = len(self.teams)
        pts = np.zeros((n_sims, nT), dtype=np.int32)
        gf = np.zeros((n_sims, nT), dtype=np.int32)
        ga = np.zeros((n_sims, nT), dtype=np.int32)

        cum_grids = {}
        for fx in self.fixtures:
            i1, i2 = self.idx[fx["t1"]], self.idx[fx["t2"]]
            l1, l2 = lambdas(
                ratings[fx["t1"]], ratings[fx["t2"]],
                self.host_bonus(fx["t1"], fx["city"]),
                self.host_bonus(fx["t2"], fx["city"]),
            )
            grid = score_grid(l1, l2)
            flat = grid.ravel()
            cum = np.cumsum(flat)
            cum_grids[fx["match"]] = (i1, i2, cum, grid.shape[0])

        for m, (i1, i2, cum, size) in cum_grids.items():
            u = rng.random(n_sims)
            k = np.searchsorted(cum, u)
            g1, g2 = k // size, k % size
            pts[:, i1] += np.where(g1 > g2, 3, np.where(g1 == g2, 1, 0)).astype(np.int32)
            pts[:, i2] += np.where(g2 > g1, 3, np.where(g1 == g2, 1, 0)).astype(np.int32)
            gf[:, i1] += g1; ga[:, i1] += g2
            gf[:, i2] += g2; ga[:, i2] += g1

        # rank within groups: points, GD, GF, random
        noise = rng.random((n_sims, nT)) * 1e-3
        key = pts * 1e6 + (gf - ga) * 1e3 + gf + noise
        group_rank = {}   # group -> (n_sims, 4) team indices best..worst
        for g, ts in self.groups.items():
            cols = np.array([self.idx[t] for t in ts])
            order = np.argsort(-key[:, cols], axis=1)
            group_rank[g] = cols[order]

        # thirds across groups
        glabels = sorted(self.groups)
        thirds = np.stack([group_rank[g][:, 2] for g in glabels], axis=1)  # (n,12)
        tkey = np.take_along_axis(key, thirds, axis=1)
        third_order = np.argsort(-tkey, axis=1)          # positions into glabels
        best8 = third_order[:, :8]                        # group indices of advancing thirds

        winners = {g: group_rank[g][:, 0] for g in glabels}
        runners = {g: group_rank[g][:, 1] for g in glabels}

        champ_counts = np.zeros(nT, dtype=np.int64)
        stage_counts = {s: np.zeros(nT, dtype=np.int64)
                        for s in ("R32", "R16", "QF", "SF", "F", "W")}
        matches_played = np.zeros(nT, dtype=np.int64)

        # knockout pairwise win prob cache
        ko_cache = {}

        def ko_winprob(a, b):
            kk = (a, b)
            if kk not in ko_cache:
                ta, tb = self.teams[a], self.teams[b]
                l1, l2 = lambdas(ratings[ta], ratings[tb],
                                 CONFIG["host_adv_ko"].get(ta, 0.0) if ta in HOSTS else 0.0,
                                 CONFIG["host_adv_ko"].get(tb, 0.0) if tb in HOSTS else 0.0,
                                 knockout=True)
                grid = score_grid(l1, l2)
                p1, px, p2 = outcome_probs(grid)
                we = win_expectancy(ratings[ta] - ratings[tb])
                pet = 0.5 + (we - 0.5) * CONFIG["et_skill_carry"]
                ko_cache[kk] = p1 + px * pet
            return ko_cache[kk]

        # resolve bracket per sim (python loop; n_sims kept moderate)
        from bracket import resolve_round_of_32  # local import; see bracket.py
        for s in range(n_sims):
            w = {g: winners[g][s] for g in glabels}
            r = {g: runners[g][s] for g in glabels}
            adv_third_groups = [glabels[j] for j in best8[s]]
            third_team = {glabels[j]: thirds[s, j] for j in range(12)}
            pairs = resolve_round_of_32(self.bracket, w, r,
                                        adv_third_groups, third_team)
            alive = pairs  # list of (a, b) team indices in bracket order
            for stage in ("R32", "R16", "QF", "SF"):
                for a, b in alive:
                    stage_counts[stage][a] += 1
                    stage_counts[stage][b] += 1
                    matches_played[a] += 1
                    matches_played[b] += 1
                nxt = []
                for a, b in alive:
                    p = ko_winprob(a, b)
                    winner = a if rng.random() < p else b
                    nxt.append(winner)
                alive = [(nxt[i], nxt[i + 1]) for i in range(0, len(nxt), 2)]
            (fa, fb), = alive
            stage_counts["F"][fa] += 1
            stage_counts["F"][fb] += 1
            matches_played[fa] += 1
            matches_played[fb] += 1
            champ = fa if rng.random() < ko_winprob(fa, fb) else fb
            champ_counts[champ] += 1
            stage_counts["W"][champ] += 1

        if not collect:
            return champ_counts

        adv_counts = np.zeros(nT, dtype=np.int64)   # reached knockout
        win_group_counts = np.zeros(nT, dtype=np.int64)
        for g in glabels:
            np.add.at(win_group_counts, winners[g], 1)
            np.add.at(adv_counts, winners[g], 1)
            np.add.at(adv_counts, runners[g], 1)
        for s in range(n_sims):
            for j in best8[s]:
                adv_counts[thirds[s, j]] += 1

        # group stage expected goals per team (group matches only)
        exp_group_goals = gf.mean(axis=0)
        exp_rank = {g: group_rank[g] for g in glabels}

        return {
            "champ": champ_counts, "stages": stage_counts,
            "advance": adv_counts, "win_group": win_group_counts,
            "matches": matches_played, "exp_group_goals": exp_group_goals,
            "group_rank": exp_rank, "n": n_sims,
        }


# --------------------------------------------------------------------------
# Odds-implied ratings: invert the simulation
# --------------------------------------------------------------------------

def fit_odds_ratings(tour: Tournament, elo: dict[str, float],
                     target_probs: dict[str, float]) -> dict[str, float]:
    c = CONFIG
    rng = np.random.default_rng(c["seed"])
    r = dict(elo)
    teams = tour.teams
    p = np.array([target_probs[t] for t in teams])
    elo_v = np.array([elo[t] for t in teams])
    for it in range(c["fit_iterations"]):
        counts = tour.simulate(r, c["n_sims_fit"], rng)
        q = (counts + 1.0) / (counts.sum() + len(teams))
        step = c["fit_lr"] * (400 / math.log(10)) * np.log(p / q)
        step = np.clip(step, -c["fit_max_step"], c["fit_max_step"])
        new = np.array([r[t] for t in teams]) + step
        new = np.clip(new, elo_v - c["fit_rating_band"], elo_v + c["fit_rating_band"])
        r = {t: float(v) for t, v in zip(teams, new)}
        err = float(np.abs(np.log(p / q)).mean())
        print(f"  fit iter {it+1:2d}: mean |log p/q| = {err:.3f}", file=sys.stderr)
    return r


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main():
    os.makedirs(OUT, exist_ok=True)
    sys.path.insert(0, HERE)
    from bracket import BRACKET_2026  # noqa

    groups = load_groups()
    teams = {t for ts in groups.values() for t in ts}
    fixtures = load_fixtures(teams)
    elo, fifa = load_ratings(teams)
    odds = load_winner_odds(teams)
    print(f"Loaded {len(teams)} teams, {len(fixtures)} fixtures, "
          f"odds for {len(odds)} teams", file=sys.stderr)

    target = devig_power(odds, elo)
    tour = Tournament(groups, fixtures, BRACKET_2026)

    print("Fitting odds-implied ratings…", file=sys.stderr)
    r_odds = fit_odds_ratings(tour, elo, target)

    blended = {t: CONFIG["w_odds"] * r_odds[t] + CONFIG["w_elo"] * elo[t]
               for t in teams}

    rng = np.random.default_rng(CONFIG["seed"] + 1)
    print(f"Final simulation ({CONFIG['n_sims']} runs)…", file=sys.stderr)
    stats = tour.simulate(blended, CONFIG["n_sims"], rng, collect=True)

    write_outputs(tour, blended, elo, fifa, odds, target, stats, fixtures, groups)
    print("Done. Outputs in worldcup2026/output/", file=sys.stderr)


def write_outputs(tour, ratings, elo, fifa, odds, target, stats, fixtures, groups):
    n = stats["n"]
    teams = tour.teams

    # --- per-match picks ---
    rows = []
    for fx in fixtures:
        l1, l2 = lambdas(ratings[fx["t1"]], ratings[fx["t2"]],
                         tour.host_bonus(fx["t1"], fx["city"]),
                         tour.host_bonus(fx["t2"], fx["city"]))
        grid = score_grid(l1, l2)
        p1, px, p2 = outcome_probs(grid)
        pick, ep, alts = best_pick(grid)
        rows.append({
            "match": fx["match"], "date": fx["date"], "group": fx["group"],
            "team1": fx["t1"], "team2": fx["t2"], "city": fx["city"],
            "lambda1": round(l1, 2), "lambda2": round(l2, 2),
            "p1": round(p1, 3), "px": round(px, 3), "p2": round(p2, 3),
            "pick": f"{pick[0]}-{pick[1]}", "exp_points": round(ep, 3),
            "alternatives": " | ".join(f"{a}-{b} ({e:.2f})" for (a, b), e in alts),
        })
    with open(os.path.join(OUT, "match_predictions.csv"), "w", newline="",
              encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    # --- champion / stage probabilities ---
    champ_rows = []
    for t in sorted(teams, key=lambda t: -stats["champ"][tour.idx[t]]):
        i = tour.idx[t]
        champ_rows.append({
            "team": t, "group": tour.group_of[t],
            "elo": round(elo[t]), "rating_blended": round(ratings[t], 1),
            "odds_avg": odds.get(t, ""),
            "p_champion": round(stats["champ"][i] / n, 4),
            "p_final": round(stats["stages"]["F"][i] / n, 4),
            "p_semifinal": round((stats["stages"]["SF"][i]) / n, 4),
            "p_quarterfinal": round(stats["stages"]["QF"][i] / n, 4),
            "p_advance_group": round(stats["advance"][i] / n, 4),
            "p_win_group": round(stats["win_group"][i] / n, 4),
            "exp_matches": round(stats["matches"][i] / n + 3, 2),
            "exp_goals_groupstage": round(stats["exp_group_goals"][i], 2),
        })
    with open(os.path.join(OUT, "champion_probs.csv"), "w", newline="",
              encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(champ_rows[0]))
        w.writeheader()
        w.writerows(champ_rows)

    with open(os.path.join(OUT, "simulation_summary.json"), "w") as f:
        json.dump({"config": {k: v for k, v in CONFIG.items()},
                   "target_champion_probs_top15": dict(sorted(
                       target.items(), key=lambda kv: -kv[1])[:15])}, f, indent=2)


if __name__ == "__main__":
    main()
