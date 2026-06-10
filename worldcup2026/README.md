# World Cup 2026 Prediction System

Quantitative prediction system for all 72 group-stage matches + full tournament simulation.  
Built for a friends' prediction tournament (binary scoring: exact=45 / outcome=30 in groups,
escalating to exact=270 / outcome=180 in the Final; standings 25 pts/position; top scorers
earn per-goal points with position multipliers MF=2×, DEF/GK=4×).

## Quick Start

```bash
pip install numpy pandas
cd worldcup2026/model
python3 run_predictions.py        # run model, write output/ CSVs
python3 make_predictions_md.py    # regenerate PREDICTIONS.md from outputs
```

Outputs appear in `worldcup2026/output/`.

## Files

```
worldcup2026/
├── PREDICTIONS.md          ← Complete predictions (read this!)
├── data/
│   ├── groups.csv           Groups A–L, all 48 teams
│   ├── fixtures_group_stage.csv   All 72 group matches with dates + venues
│   ├── team_ratings.csv     Elo + FIFA ranking for all 48 teams (June 8, 2026)
│   ├── winner_odds.csv      Outright winner odds, 9 sources, 22 teams
│   ├── topscorer_odds.csv   Golden Boot odds + player positions
│   └── group_winner_odds.csv  Group-winner odds for all 12 groups
├── model/
│   ├── run_predictions.py   Main model runner
│   ├── bracket.py           Knockout bracket + third-place allocation
│   ├── make_predictions_md.py  PREDICTIONS.md generator
│   └── predict.py           Extended model with odds-fitting (reference)
├── output/
│   ├── match_predictions.csv     All 72 picks + win/draw/loss probs + xG
│   ├── champion_probs.csv        All 48 teams: p(champion), p(semifinal), etc.
│   ├── group_standings.csv       P(position) per team per group (25 pts/position)
│   ├── ko_predictions.csv        Predicted KO bracket picks, stage-weighted scoring
│   ├── group_predictions.txt     Group-by-group detailed standings + picks
│   ├── topscorer_predictions.csv  Top scorer E[pts] with position multipliers
│   └── simulation_summary.json   Summary + top-15 champion probabilities
└── research/
    ├── squad_news.md        Verified injury/squad facts (June 2026)
    └── methodology.md       Literature review on prediction methodology
```

## Methodology Summary

1. **Strength** = 65% bookmaker-consensus (de-vigged via power method) + 35% World Football Elo, with confederation quality adjustment
2. **Scores** = Dixon-Coles bivariate Poisson (rho=-0.10) + WC historical scoreline calibration
3. **Picks** = score maximising `E[pts] = outcome_pts × P(direction) + (exact_pts − outcome_pts) × P(exact)` per stage
4. **Tournament** = 40,000 Monte Carlo runs, full bracket including R32 thirds allocation

**Key finding:** Spain (18.6%) is the narrow favourite, followed by France (13.6%), Argentina (10.7%), England (10.1%), Brazil (8.6%), Portugal (7.4%).

**Important platform note:** the prediction platform derives group standings from your match
score picks (you don't enter standings separately). The model's picks were verified to imply
exactly the most-likely standings in all 12 groups.

See `research/methodology.md` for academic citations (Leitner/Zeileis 2010, Dixon-Coles 1997, Hvattum 2010, etc.)
