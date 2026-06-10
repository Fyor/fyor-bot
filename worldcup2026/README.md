# World Cup 2026 Prediction System

Quantitative prediction system for all 72 group-stage matches + full tournament simulation.  
Built for a friends' prediction tournament (Kicktipp-style scoring: exact=4 / goal-diff=3 / tendency=2).

## Quick Start

```bash
pip install numpy pandas
cd worldcup2026/model
python3 run_predictions.py
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
│   ├── topscorer_odds.csv   Golden Boot odds, top 18 players
│   └── group_winner_odds.csv  Group-winner odds for all 12 groups
├── model/
│   ├── run_predictions.py   Main model runner
│   ├── bracket.py           Knockout bracket + third-place allocation
│   └── predict.py           Extended model with odds-fitting (reference)
├── output/
│   ├── match_predictions.csv     All 72 picks + win/draw/loss probs + xG
│   ├── champion_probs.csv        All 48 teams: p(champion), p(semifinal), etc.
│   ├── group_predictions.txt     Group-by-group detailed standings + picks
│   ├── topscorer_predictions.csv  Top scorer model output
│   └── simulation_summary.json   Summary + top-15 champion probabilities
└── research/
    ├── squad_news.md        Verified injury/squad facts (June 2026)
    └── methodology.md       Literature review on prediction methodology
```

## Methodology Summary

1. **Strength** = 65% bookmaker-consensus (de-vigged via power method) + 35% World Football Elo
2. **Scores** = Dixon-Coles bivariate Poisson (rho=-0.10; base 2.55 goals/game group stage, 2.35 KO)
3. **Picks** = score maximising expected Kicktipp points across a 0–6 × 0–6 grid
4. **Tournament** = 40,000 Monte Carlo runs, full bracket including R32 thirds allocation

**Key finding:** Spain (18.7%) is the narrow favourite, followed by France (13.1%), England (10.4%), Argentina (10.6%), Brazil (8.7%), Portugal (7.9%).

See `research/methodology.md` for academic citations (Leitner/Zeileis 2010, Dixon-Coles 1997, Hvattum 2010, etc.)
