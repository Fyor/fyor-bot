# World Cup 2026 — Complete Tournament Predictions

**Model:** 65% bookmaker-consensus (de-vigged power method) + 35% World Football Elo  
**Simulation:** 40,000 Monte Carlo runs, Dixon-Coles bivariate Poisson (ρ=−0.10), WC historical calibration  
**Scoring system:** Exact=45 / Outcome=30 (group); escalates to Exact=270 / Outcome=180 (Final)  
**Generated from latest model run** — regenerate with `python3 model/make_predictions_md.py`

---

## CHAMPION PICK

**→ Spain** (18.6% win probability, E[pts] = 46 from 250-pt bonus)

| Team | P(Champion) | P(Final) | P(Semi-final) |
|------|-------------|----------|---------------|
| Spain | 18.6% | 31.1% | 43.0% |
| France | 13.6% | 21.4% | 32.6% |
| Argentina | 10.7% | 17.8% | 28.3% |
| England | 10.1% | 16.7% | 27.6% |
| Brazil | 8.6% | 18.3% | 36.5% |
| Portugal | 7.4% | 13.0% | 23.1% |
| Germany | 5.6% | 11.8% | 22.0% |
| Netherlands | 3.9% | 8.4% | 16.3% |
| Belgium | 2.7% | 7.2% | 14.0% |
| Colombia | 2.6% | 5.9% | 13.6% |

---

## TOP SCORER PICKS

**Position multiplier: Forward=1×, Midfielder=2×, Defender/GK=4× per goal scored.**  
A midfielder scoring 3 goals earns the same points as a forward scoring 6.

| Rank | Player | Team | Position | Mult | E[pts] | Odds |
|------|--------|------|----------|------|--------|------|
| 1 | **Jude Bellingham** | England | Midfielder | 2.0× | 91.5 | 51.0 |
| 2 | **Jamal Musiala** | Germany | Midfielder | 2.0× | 83.7 | 66.0 |
| 3 | **Christian Pulisic** | United States | Midfielder | 2.0× | 69.7 | 126.0 |
| 4 | **Mikel Oyarzabal** | Spain | Forward | 1.0× | 53.2 | 19.0 |
| 5 | **Lamine Yamal** | Spain | Forward | 1.0× | 53.2 | 21.0 |
| 6 | **Vinicius Junior** | Brazil | Forward | 1.0× | 46.5 | 26.0 |
| 7 | **Raphinha** | Brazil | Forward | 1.0× | 46.5 | 29.0 |
| 8 | **Lionel Messi** | Argentina | Forward | 1.0× | 45.9 | 17.0 |

**Recommended 6:** Jude Bellingham, Jamal Musiala, Christian Pulisic, Mikel Oyarzabal, Lamine Yamal, Vinicius Junior

**Why midfielders rank top:** at 2× points per goal, Bellingham scoring 3 goals earns the same as Kane scoring 6. The model balances scoring volume against the multiplier.

---

## GROUP STAGE — ALL 72 MATCH PICKS

Enter the **Pick** column. E[pts] uses the binary rule: 30 × P(outcome) + 15 × P(exact).  
The platform derives your group standings from these picks — the implied standings below match the model's most-likely final order in every group.

### Group A — Mexico, Czechia, South Korea, South Africa

**Predicted standings: 1. Mexico → 2. Czechia → 3. South Korea → 4. South Africa**

| Date | Team 1 | **Pick** | Team 2 | E[pts] | W/D/L | Alternatives |
|------|--------|----------|--------|--------|-------|--------------|
| Jun 11 | Mexico | **2-0** | South Africa | 21.3 | 66/20/14% | 2-1, 1-0, 3-0 |
| Jun 11 | South Korea | **0-1** | Czechia | 12.5 | 36/28/37% | 1-2, 1-0, 0-2 |
| Jun 18 | Czechia | **1-0** | South Africa | 16.1 | 48/26/26% | 2-1, 2-0, 3-1 |
| Jun 18 | Mexico | **1-0** | South Korea | 18.2 | 56/24/21% | 2-1, 2-0, 3-1 |
| Jun 24 | Czechia | **0-1** | Mexico | 18.1 | 21/24/55% | 1-2, 0-2, 1-3 |
| Jun 24 | South Africa | **0-1** | South Korea | 15.9 | 26/26/48% | 1-2, 0-2, 1-3 |

### Group B — Switzerland, Canada, Bosnia and Herzegovina, Qatar

**Predicted standings: 1. Switzerland → 2. Canada → 3. Bosnia and Herzegovina → 4. Qatar**

| Date | Team 1 | **Pick** | Team 2 | E[pts] | W/D/L | Alternatives |
|------|--------|----------|--------|--------|-------|--------------|
| Jun 12 | Canada | **1-0** | Bosnia and Herzegovina | 18.0 | 55/24/21% | 2-1, 2-0, 3-1 |
| Jun 13 | Qatar | **0-2** | Switzerland | 21.2 | 14/20/66% | 1-2, 0-1, 0-3 |
| Jun 18 | Switzerland | **2-1** | Bosnia and Herzegovina | 18.8 | 58/23/19% | 1-0, 2-0, 3-1 |
| Jun 18 | Canada | **2-1** | Qatar | 20.4 | 63/21/16% | 2-0, 1-0, 3-0 |
| Jun 24 | Switzerland | **1-0** | Canada | 13.3 | 39/28/33% | 2-1, 2-0, 3-1 |
| Jun 24 | Bosnia and Herzegovina | **1-0** | Qatar | 15.2 | 45/27/28% | 2-1, 2-0, 3-1 |

### Group C — Brazil, Morocco, Scotland, Haiti

**Predicted standings: 1. Brazil → 2. Morocco → 3. Scotland → 4. Haiti**

| Date | Team 1 | **Pick** | Team 2 | E[pts] | W/D/L | Alternatives |
|------|--------|----------|--------|--------|-------|--------------|
| Jun 13 | Brazil | **1-0** | Morocco | 16.5 | 50/26/25% | 2-1, 2-0, 3-1 |
| Jun 13 | Haiti | **0-1** | Scotland | 17.3 | 23/25/52% | 1-2, 0-2, 1-3 |
| Jun 19 | Scotland | **1-2** | Morocco | 19.8 | 17/22/61% | 0-2, 0-1, 0-3 |
| Jun 19 | Brazil | **2-0** | Haiti | 26.8 | 83/12/5% | 3-0, 1-0, 4-0 |
| Jun 24 | Morocco | **2-0** | Haiti | 23.8 | 74/16/10% | 2-1, 1-0, 3-0 |
| Jun 24 | Scotland | **0-2** | Brazil | 23.2 | 11/17/72% | 1-2, 0-1, 0-3 |

### Group D — United States, Turkey, Australia, Paraguay

**Predicted standings: 1. United States → 2. Turkey → 3. Australia → 4. Paraguay**

| Date | Team 1 | **Pick** | Team 2 | E[pts] | W/D/L | Alternatives |
|------|--------|----------|--------|--------|-------|--------------|
| Jun 12 | United States | **2-1** | Paraguay | 19.1 | 58/23/19% | 1-0, 2-0, 3-1 |
| Jun 13 | Turkey | **1-0** | Australia | 13.7 | 40/28/32% | 2-1, 2-0, 3-1 |
| Jun 19 | United States | **2-1** | Australia | 18.9 | 58/23/19% | 1-0, 2-0, 3-1 |
| Jun 20 | Turkey | **1-0** | Paraguay | 14.0 | 41/28/31% | 2-1, 2-0, 3-1 |
| Jun 25 | Turkey | **0-1** | United States | 17.7 | 22/24/54% | 1-2, 0-2, 1-3 |
| Jun 25 | Paraguay | **0-1** | Australia | 12.5 | 35/28/37% | 1-2, 1-0, 0-2 |

### Group E — Germany, Ecuador, Ivory Coast, Curaçao

**Predicted standings: 1. Germany → 2. Ecuador → 3. Ivory Coast → 4. Curaçao**

| Date | Team 1 | **Pick** | Team 2 | E[pts] | W/D/L | Alternatives |
|------|--------|----------|--------|--------|-------|--------------|
| Jun 14 | Germany | **2-0** | Curaçao | 26.5 | 82/12/5% | 3-0, 1-0, 2-1 |
| Jun 14 | Ivory Coast | **0-1** | Ecuador | 18.3 | 21/24/56% | 1-2, 0-2, 1-3 |
| Jun 20 | Germany | **2-0** | Ivory Coast | 21.8 | 67/19/13% | 2-1, 1-0, 3-0 |
| Jun 20 | Ecuador | **2-0** | Curaçao | 23.6 | 73/17/10% | 2-1, 1-0, 3-0 |
| Jun 25 | Ecuador | **0-1** | Germany | 16.5 | 25/26/50% | 1-2, 0-2, 1-3 |
| Jun 25 | Curaçao | **0-1** | Ivory Coast | 18.5 | 20/23/57% | 1-2, 0-2, 1-3 |

### Group F — Netherlands, Japan, Sweden, Tunisia

**Predicted standings: 1. Netherlands → 2. Japan → 3. Sweden → 4. Tunisia**

| Date | Team 1 | **Pick** | Team 2 | E[pts] | W/D/L | Alternatives |
|------|--------|----------|--------|--------|-------|--------------|
| Jun 14 | Netherlands | **1-0** | Japan | 15.7 | 47/26/27% | 2-1, 2-0, 3-1 |
| Jun 14 | Sweden | **1-0** | Tunisia | 15.8 | 47/26/26% | 2-1, 2-0, 3-1 |
| Jun 20 | Netherlands | **2-1** | Sweden | 18.9 | 58/23/19% | 1-0, 2-0, 3-1 |
| Jun 21 | Japan | **2-1** | Tunisia | 19.0 | 58/23/19% | 1-0, 2-0, 3-1 |
| Jun 25 | Japan | **1-0** | Sweden | 15.9 | 48/26/26% | 2-1, 2-0, 3-1 |
| Jun 25 | Tunisia | **0-2** | Netherlands | 21.8 | 13/19/68% | 1-2, 0-1, 0-3 |

### Group G — Belgium, Iran, Egypt, New Zealand

**Predicted standings: 1. Belgium → 2. Iran → 3. Egypt → 4. New Zealand**

| Date | Team 1 | **Pick** | Team 2 | E[pts] | W/D/L | Alternatives |
|------|--------|----------|--------|--------|-------|--------------|
| Jun 15 | Belgium | **2-0** | Egypt | 22.0 | 68/19/13% | 2-1, 1-0, 3-0 |
| Jun 15 | Iran | **1-0** | New Zealand | 17.6 | 53/25/22% | 2-1, 2-0, 3-1 |
| Jun 21 | Belgium | **2-1** | Iran | 20.6 | 63/21/16% | 2-0, 1-0, 3-0 |
| Jun 21 | New Zealand | **0-1** | Egypt | 15.9 | 26/26/48% | 1-2, 0-2, 1-3 |
| Jun 26 | Egypt | **0-1** | Iran | 14.1 | 31/27/42% | 1-2, 0-2, 1-3 |
| Jun 26 | New Zealand | **0-2** | Belgium | 24.7 | 8/15/77% | 0-3, 1-2, 0-1 |

### Group H — Spain, Uruguay, Saudi Arabia, Cape Verde

**Predicted standings: 1. Spain → 2. Uruguay → 3. Saudi Arabia → 4. Cape Verde**

| Date | Team 1 | **Pick** | Team 2 | E[pts] | W/D/L | Alternatives |
|------|--------|----------|--------|--------|-------|--------------|
| Jun 15 | Spain | **2-0** | Cape Verde | 27.9 | 86/10/4% | 3-0, 4-0, 1-0 |
| Jun 15 | Saudi Arabia | **1-2** | Uruguay | 20.2 | 16/21/62% | 0-2, 0-1, 0-3 |
| Jun 21 | Spain | **2-0** | Saudi Arabia | 25.3 | 78/14/7% | 3-0, 1-0, 2-1 |
| Jun 21 | Uruguay | **2-0** | Cape Verde | 23.3 | 72/17/11% | 2-1, 1-0, 3-0 |
| Jun 26 | Cape Verde | **0-1** | Saudi Arabia | 16.2 | 25/26/49% | 1-2, 0-2, 1-3 |
| Jun 26 | Spain | **1-0** | Uruguay | 18.7 | 57/23/20% | 2-1, 2-0, 3-1 |

### Group I — France, Norway, Senegal, Iraq

**Predicted standings: 1. France → 2. Norway → 3. Senegal → 4. Iraq**

| Date | Team 1 | **Pick** | Team 2 | E[pts] | W/D/L | Alternatives |
|------|--------|----------|--------|--------|-------|--------------|
| Jun 16 | France | **2-1** | Senegal | 19.4 | 60/22/18% | 1-0, 2-0, 3-1 |
| Jun 16 | Iraq | **0-2** | Norway | 22.8 | 12/18/70% | 1-2, 0-1, 0-3 |
| Jun 22 | France | **2-0** | Iraq | 26.5 | 82/13/6% | 3-0, 1-0, 2-1 |
| Jun 22 | Norway | **1-0** | Senegal | 14.7 | 44/27/29% | 2-1, 2-0, 3-1 |
| Jun 26 | Norway | **0-1** | France | 17.4 | 23/25/53% | 1-2, 0-2, 1-3 |
| Jun 26 | Senegal | **2-0** | Iraq | 20.9 | 65/20/15% | 2-1, 1-0, 3-0 |

### Group J — Argentina, Austria, Algeria, Jordan

**Predicted standings: 1. Argentina → 2. Austria → 3. Algeria → 4. Jordan**

| Date | Team 1 | **Pick** | Team 2 | E[pts] | W/D/L | Alternatives |
|------|--------|----------|--------|--------|-------|--------------|
| Jun 16 | Argentina | **2-0** | Algeria | 23.3 | 72/17/11% | 2-1, 1-0, 3-0 |
| Jun 16 | Austria | **2-0** | Jordan | 22.8 | 71/18/12% | 2-1, 1-0, 3-0 |
| Jun 21 | Argentina | **2-1** | Austria | 19.3 | 59/22/18% | 1-0, 2-0, 3-1 |
| Jun 22 | Algeria | **2-1** | Jordan | 18.7 | 57/23/20% | 1-0, 2-0, 3-1 |
| Jun 25 | Argentina | **2-0** | Jordan | 27.9 | 86/10/4% | 3-0, 4-0, 1-0 |
| Jun 25 | Algeria | **0-1** | Austria | 17.2 | 23/25/52% | 1-2, 0-2, 1-3 |

### Group K — Portugal, Colombia, DR Congo, Uzbekistan

**Predicted standings: 1. Portugal → 2. Colombia → 3. DR Congo → 4. Uzbekistan**

| Date | Team 1 | **Pick** | Team 2 | E[pts] | W/D/L | Alternatives |
|------|--------|----------|--------|--------|-------|--------------|
| Jun 17 | Portugal | **2-0** | DR Congo | 22.9 | 71/18/11% | 2-1, 1-0, 3-0 |
| Jun 17 | Uzbekistan | **0-2** | Colombia | 23.2 | 11/17/72% | 1-2, 0-1, 0-3 |
| Jun 23 | Portugal | **2-0** | Uzbekistan | 25.4 | 79/14/7% | 3-0, 1-0, 2-1 |
| Jun 23 | Colombia | **2-1** | DR Congo | 20.6 | 63/21/16% | 2-0, 1-0, 3-0 |
| Jun 27 | Colombia | **0-1** | Portugal | 15.3 | 28/27/46% | 1-2, 0-2, 1-3 |
| Jun 27 | DR Congo | **1-0** | Uzbekistan | 15.7 | 47/26/27% | 2-1, 2-0, 3-1 |

### Group L — England, Croatia, Ghana, Panama

**Predicted standings: 1. England → 2. Croatia → 3. Ghana → 4. Panama**

| Date | Team 1 | **Pick** | Team 2 | E[pts] | W/D/L | Alternatives |
|------|--------|----------|--------|--------|-------|--------------|
| Jun 17 | England | **1-0** | Croatia | 17.9 | 55/24/21% | 2-1, 2-0, 3-1 |
| Jun 17 | Ghana | **1-0** | Panama | 15.8 | 47/26/26% | 2-1, 2-0, 3-1 |
| Jun 23 | England | **2-0** | Ghana | 25.4 | 79/14/7% | 3-0, 1-0, 2-1 |
| Jun 23 | Panama | **0-2** | Croatia | 23.8 | 10/17/74% | 1-2, 0-1, 0-3 |
| Jun 27 | England | **2-0** | Panama | 27.7 | 86/11/4% | 3-0, 1-0, 4-0 |
| Jun 27 | Croatia | **2-0** | Ghana | 21.0 | 65/20/15% | 2-1, 1-0, 3-0 |

---

## GROUP STANDINGS SUMMARY (derived from your picks — 25 pts per correct position)

| Group | 1st | 2nd | 3rd | 4th |
|-------|-----|-----|-----|-----|
| A | Mexico (56%) | Czechia (29%) | South Korea (30%) | South Africa (47%) |
| B | Switzerland (44%) | Canada (34%) | Bosnia and Herzegovina (36%) | Qatar (52%) |
| C | Brazil (62%) | Morocco (46%) | Scotland (47%) | Haiti (65%) |
| D | United States (54%) | Turkey (28%) | Australia (29%) | Paraguay (35%) |
| E | Germany (61%) | Ecuador (43%) | Ivory Coast (46%) | Curaçao (68%) |
| F | Netherlands (53%) | Japan (34%) | Sweden (34%) | Tunisia (52%) |
| G | Belgium (71%) | Iran (36%) | Egypt (34%) | New Zealand (51%) |
| H | Spain (71%) | Uruguay (52%) | Saudi Arabia (47%) | Cape Verde (61%) |
| I | France (60%) | Norway (37%) | Senegal (40%) | Iraq (73%) |
| J | Argentina (71%) | Austria (47%) | Algeria (45%) | Jordan (68%) |
| K | Portugal (58%) | Colombia (44%) | DR Congo (44%) | Uzbekistan (59%) |
| L | England (69%) | Croatia (52%) | Ghana (47%) | Panama (60%) |

---

## KNOCKOUT ROUND PREDICTIONS (reference — fill in when bracket is known)

Points escalate: R32=90/60 → R16=135/90 → QF=180/120 → SF=225/150 → **Final=270/180**.  
Bracket below assumes the most-likely group outcomes; actual R32 ties depend on real results.

### Round of 32

| Match | Team 1 | **Pick** | Team 2 | E[pts] | W/D/L |
|-------|--------|----------|--------|--------|-------|
| R32-1 | Mexico | **0-1** | Morocco | 25.8 | 34/29/37% |
| R32-2 | Brazil | **2-0** | South Korea | 43.4 | 66/20/13% |
| R32-3 | Switzerland | **1-0** | Turkey | 34.4 | 51/26/23% |
| R32-4 | United States | **1-0** | Australia | 38.0 | 57/24/19% |
| R32-5 | Germany | **2-0** | Iran | 45.0 | 69/19/12% |
| R32-6 | Belgium | **1-0** | Ivory Coast | 41.0 | 63/22/16% |
| R32-7 | Netherlands | **1-0** | Uruguay | 30.0 | 44/28/28% |
| R32-8 | Spain | **2-0** | Egypt | 54.1 | 83/12/5% |
| R32-9 | France | **2-0** | Sweden | 45.0 | 69/19/12% |
| R32-10 | Portugal | **2-0** | Bosnia and Herzegovina | 48.6 | 75/17/9% |
| R32-11 | Argentina | **2-0** | Algeria | 47.5 | 73/17/10% |
| R32-12 | England | **1-0** | Senegal | 37.4 | 56/24/19% |
| R32-13 | Czechia | **0-1** | Canada | 30.0 | 28/28/44% |
| R32-14 | Ecuador | **0-1** | Japan | 26.6 | 32/29/38% |
| R32-15 | Norway | **1-0** | Austria | 30.9 | 45/28/27% |
| R32-16 | Colombia | **1-0** | Croatia | 29.3 | 43/28/29% |

### Round of 16

| Match | Team 1 | **Pick** | Team 2 | E[pts] | W/D/L |
|-------|--------|----------|--------|--------|-------|
| R16-17 | Morocco | **0-1** | Brazil | 50.3 | 24/27/50% |
| R16-18 | Switzerland | **0-1** | United States | 38.6 | 34/29/37% |
| R16-19 | Germany | **1-0** | Belgium | 43.1 | 42/28/30% |
| R16-20 | Netherlands | **0-1** | Spain | 50.1 | 24/27/49% |
| R16-21 | France | **1-0** | Portugal | 42.8 | 42/29/30% |
| R16-22 | Argentina | **1-0** | England | 38.3 | 37/29/34% |
| R16-23 | Canada | **0-1** | Japan | 46.6 | 27/28/46% |
| R16-24 | Norway | **0-1** | Colombia | 38.2 | 34/29/37% |

### Quarter-finals

| Match | Team 1 | **Pick** | Team 2 | E[pts] | W/D/L |
|-------|--------|----------|--------|--------|-------|
| QF-25 | Brazil | **1-0** | United States | 67.8 | 50/26/23% |
| QF-26 | Germany | **0-1** | Spain | 67.1 | 24/27/50% |
| QF-27 | France | **1-0** | Argentina | 52.2 | 38/29/33% |
| QF-28 | Japan | **0-1** | Colombia | 60.1 | 28/28/44% |

### Semi-finals

| Match | Team 1 | **Pick** | Team 2 | E[pts] | W/D/L |
|-------|--------|----------|--------|--------|-------|
| SF-29 | Brazil | **0-1** | Spain | 79.4 | 26/28/47% |
| SF-30 | France | **1-0** | Colombia | 86.3 | 51/26/22% |

### Final

| Match | Team 1 | **Pick** | Team 2 | E[pts] | W/D/L |
|-------|--------|----------|--------|--------|-------|
| Final-31 | Spain | **1-0** | France | 75.4 | 36/29/35% |

Final alternatives: 2-1(73pts) | 0-1(72pts) | 2-0(71pts). The final is close to a coin-flip — the optimal pick is only marginally ahead.

---

## METHODOLOGY

- **Strength blend:** 65% de-vigged bookmaker consensus (power method) + 35% World Football Elo
- **Goals model:** Dixon-Coles bivariate Poisson ρ=−0.10 with WC historical calibration (1-0/0-1 ×1.18, 2-1/1-2 ×1.08)
- **Confederation adjustment:** OFC −50, CONCACAF −25, CAF −20, AFC −15 Elo vs UEFA/CONMEBOL
- **Pick formula:** `E[pts] = outcome_pts × P(direction) + (exact_pts − outcome_pts) × P(exact a-b)`
- **KO bracket:** Official FIFA 2026 R32 pairings; 8 best thirds resolved by backtracking constraint solver
- **Host advantage:** USA +80 / Mexico +50 / Canada +45 Elo in KO; +90 Elo in home group venue

See `research/methodology.md` for academic citations.
