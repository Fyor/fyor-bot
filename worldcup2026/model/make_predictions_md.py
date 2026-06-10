#!/usr/bin/env python3
"""Generate PREDICTIONS.md from the model output CSVs so the document
always matches the latest run exactly."""
import csv
import os
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "output")
DOC = os.path.join(HERE, "..", "PREDICTIONS.md")


def read(name):
    with open(os.path.join(OUT, name), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def pct(x):
    return f"{float(x) * 100:.0f}"


def main():
    picks = read("match_predictions.csv")
    champs = read("champion_probs.csv")
    standings = read("group_standings.csv")
    ko = read("ko_predictions.csv")
    scorers = read("topscorer_predictions.csv")

    by_group = defaultdict(list)
    for r in picks:
        by_group[r["group"]].append(r)

    st_by_group = defaultdict(list)
    for r in standings:
        st_by_group[r["group"]].append(r)
    for g in st_by_group:
        st_by_group[g].sort(key=lambda r: int(r["predicted_rank"]))

    L = []
    L.append("# World Cup 2026 — Complete Tournament Predictions\n")
    L.append("**Model:** 65% bookmaker-consensus (de-vigged power method) + 35% World Football Elo  ")
    L.append("**Simulation:** 40,000 Monte Carlo runs, Dixon-Coles bivariate Poisson (ρ=−0.10), WC historical calibration  ")
    L.append("**Scoring system:** Exact=45 / Outcome=30 (group); escalates to Exact=270 / Outcome=180 (Final)  ")
    L.append("**Generated from latest model run** — regenerate with `python3 model/make_predictions_md.py`\n")
    L.append("---\n")

    # Champion
    top = champs[0]["team"]
    L.append("## CHAMPION PICK\n")
    L.append(f"**→ {top}** ({float(champs[0]['p_Champion'])*100:.1f}% win probability, "
             f"E[pts] = {float(champs[0]['p_Champion'])*250:.0f} from 250-pt bonus)\n")
    L.append("| Team | P(Champion) | P(Final) | P(Semi-final) |")
    L.append("|------|-------------|----------|---------------|")
    for r in champs[:10]:
        L.append(f"| {r['team']} | {float(r['p_Champion'])*100:.1f}% | "
                 f"{float(r['p_Final'])*100:.1f}% | {float(r['p_SF'])*100:.1f}% |")
    L.append("")
    L.append("---\n")

    # Top scorers
    L.append("## TOP SCORER PICKS\n")
    L.append("**Position multiplier: Forward=1×, Midfielder=2×, Defender/GK=4× per goal scored.**  ")
    L.append("A midfielder scoring 3 goals earns the same points as a forward scoring 6.\n")
    L.append("| Rank | Player | Team | Position | Mult | E[pts] | Odds |")
    L.append("|------|--------|------|----------|------|--------|------|")
    for i, p in enumerate(scorers[:8], 1):
        L.append(f"| {i} | **{p['player']}** | {p['team']} | {p['position'].capitalize()} | "
                 f"{p['position_multiplier']}× | {p['player_exp_pts']} | {p['golden_boot_odds']} |")
    L.append("")
    L.append("**Recommended 6:** " + ", ".join(p["player"] for p in scorers[:6]))
    L.append("")
    L.append("**Why midfielders rank top:** at 2× points per goal, Bellingham scoring 3 goals "
             "earns the same as Kane scoring 6. The model balances scoring volume against the multiplier.\n")
    L.append("---\n")

    # Group stage
    L.append("## GROUP STAGE — ALL 72 MATCH PICKS\n")
    L.append("Enter the **Pick** column. E[pts] uses the binary rule: 30 × P(outcome) + 15 × P(exact).  ")
    L.append("The platform derives your group standings from these picks — the implied standings below "
             "match the model's most-likely final order in every group.\n")

    for grp in sorted(by_group):
        teams = [r["team"] for r in st_by_group[grp]]
        L.append(f"### Group {grp} — {', '.join(teams)}\n")
        order = " → ".join(f"{i}. {r['team']}" for i, r in enumerate(st_by_group[grp], 1))
        L.append(f"**Predicted standings: {order}**\n")
        L.append("| Date | Team 1 | **Pick** | Team 2 | E[pts] | W/D/L | Alternatives |")
        L.append("|------|--------|----------|--------|--------|-------|--------------|")
        for r in sorted(by_group[grp], key=lambda x: int(x["match"])):
            alts = ", ".join(a.split("(")[0] for a in r["top_alternatives"].split(" | ")[1:4])
            date = r["date"][5:].replace("-", " ")
            mon, day = date.split()
            datestr = f"Jun {int(day)}"
            L.append(f"| {datestr} | {r['team1']} | **{r['optimal_pick']}** | {r['team2']} | "
                     f"{float(r['exp_pts']):.1f} | {pct(r['p_win1'])}/{pct(r['p_draw'])}/{pct(r['p_win2'])}% | {alts} |")
        L.append("")

    L.append("---\n")

    # Standings summary
    L.append("## GROUP STANDINGS SUMMARY (derived from your picks — 25 pts per correct position)\n")
    L.append("| Group | 1st | 2nd | 3rd | 4th |")
    L.append("|-------|-----|-----|-----|-----|")
    for grp in sorted(st_by_group):
        rows = st_by_group[grp]
        cells = []
        for i, r in enumerate(rows):
            p = float(r[f"p_pos{i+1}"]) * 100
            cells.append(f"{r['team']} ({p:.0f}%)")
        L.append(f"| {grp} | " + " | ".join(cells) + " |")
    L.append("")
    L.append("---\n")

    # KO predictions
    L.append("## KNOCKOUT ROUND PREDICTIONS (reference — fill in when bracket is known)\n")
    L.append("Points escalate: R32=90/60 → R16=135/90 → QF=180/120 → SF=225/150 → **Final=270/180**.  ")
    L.append("Bracket below assumes the most-likely group outcomes; actual R32 ties depend on real results.\n")
    stage_titles = {"R32": "Round of 32", "R16": "Round of 16", "QF": "Quarter-finals",
                    "SF": "Semi-finals", "Final": "Final"}
    cur_stage = None
    for r in ko:
        if r["round"] != cur_stage:
            cur_stage = r["round"]
            L.append(f"### {stage_titles[cur_stage]}\n")
            L.append("| Match | Team 1 | **Pick** | Team 2 | E[pts] | W/D/L |")
            L.append("|-------|--------|----------|--------|--------|-------|")
        L.append(f"| {r['round']}-{r['match']} | {r['team1']} | **{r['optimal_pick']}** | {r['team2']} | "
                 f"{float(r['exp_pts']):.1f} | {pct(r['p_win1'])}/{pct(r['p_draw'])}/{pct(r['p_win2'])}% |")
        if r["round"] == "Final":
            L.append("")
            alts = r["top_alternatives"]
            L.append(f"Final alternatives: {alts}. The final is close to a coin-flip — "
                     f"the optimal pick is only marginally ahead.")
        if r["round"] != "Final" and ko[min(ko.index(r) + 1, len(ko) - 1)]["round"] != r["round"]:
            L.append("")

    L.append("")
    L.append("---\n")
    L.append("## METHODOLOGY\n")
    L.append("- **Strength blend:** 65% de-vigged bookmaker consensus (power method) + 35% World Football Elo")
    L.append("- **Goals model:** Dixon-Coles bivariate Poisson ρ=−0.10 with WC historical calibration (1-0/0-1 ×1.18, 2-1/1-2 ×1.08)")
    L.append("- **Confederation adjustment:** OFC −50, CONCACAF −25, CAF −20, AFC −15 Elo vs UEFA/CONMEBOL")
    L.append("- **Pick formula:** `E[pts] = outcome_pts × P(direction) + (exact_pts − outcome_pts) × P(exact a-b)`")
    L.append("- **KO bracket:** Official FIFA 2026 R32 pairings; 8 best thirds resolved by backtracking constraint solver")
    L.append("- **Host advantage:** USA +80 / Mexico +50 / Canada +45 Elo in KO; +90 Elo in home group venue\n")
    L.append("See `research/methodology.md` for academic citations.")

    with open(DOC, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    print(f"Wrote {DOC}")


if __name__ == "__main__":
    main()
