# World Cup 2026 — Complete Tournament Predictions

**Model:** 65% bookmaker-consensus (de-vigged power method) + 35% World Football Elo  
**Simulation:** 40,000 Monte Carlo runs, Dixon-Coles bivariate Poisson (ρ=−0.10), WC historical calibration  
**Scoring system:** Exact=45 / Outcome=30 (group); escalates to Exact=270 / Outcome=180 (Final)  
**Generated:** 2026-06-10

---

## CHAMPION PICK

**→ Spain** (18.5% win probability, E[pts] = 46 from 250-pt bonus)

| Team | P(Champion) | P(Final) | P(Semi-final) |
|------|-------------|----------|---------------|
| Spain | 18.5% | 31.0% | 42.8% |
| France | 13.6% | 21.5% | 32.6% |
| Argentina | 10.7% | 17.8% | 28.5% |
| England | 10.1% | 16.7% | 27.6% |
| Brazil | 8.6% | 18.3% | 36.3% |
| Portugal | 7.3% | 13.0% | 23.0% |
| Germany | 5.5% | 11.7% | 21.8% |
| Netherlands | 3.8% | 8.2% | 16.0% |
| Colombia | 2.7% | 5.8% | 13.7% |
| Belgium | 2.6% | 7.0% | 13.7% |

---

## TOP SCORER PICKS

**Position multiplier: Forward=1×, Midfielder=2×, Defender/GK=4× per goal scored.**  
A midfielder scoring 3 goals earns the same points as a forward scoring 6.

| Rank | Player | Team | Position | Mult | E[pts] | Odds | Strategy |
|------|--------|------|----------|------|--------|------|---------|
| 1 | **Jude Bellingham** | England | Midfielder | 2× | 91.6 | 51 | Value — 2× pts/goal; England likely deep run |
| 2 | **Jamal Musiala** | Germany | Midfielder | 2× | 83.3 | 66 | Same logic; Germany top-half bracket |
| 3 | **Lamine Yamal** | Spain | Forward | 1× | 52.7 | 21 | Spain deepest expected run (42.8% to SF) |
| 4 | **Mikel Oyarzabal** | Spain | Forward | 1× | 52.7 | 19 | Same Spain upside; clinical finisher |
| 5 | **Harry Kane** | England | Forward | 1× | 45.8 | 8 | Safest forward pick; penalty taker |
| 6 | **Kylian Mbappé** | France | Forward | 1× | 45.3 | 7 | Best bookmaker odds; France reach Final 21.5% |

**Why Bellingham over Mbappé:** At 51 odds Bellingham is the value play — his midfielder multiplier means he earns ~274 pts for 3 tournament goals vs Kane's ~137 pts for the same. If you're picking 6 scorers, mix midfielders (Bellingham, Musiala) with safe forwards (Mbappé, Kane).

---

## GROUP STAGE — ALL 72 MATCH PICKS

Enter the `Optimal Pick` column. `E[pts]` = expected points from this pick given the binary scoring rule (Exact=45, Outcome=30).

### Group A — Mexico, South Korea, Czechia, South Africa

**Predicted standings: 1. Mexico → 2. South Korea → 3. Czechia → 4. South Africa**

| Date | Team 1 | **Optimal Pick** | Team 2 | E[pts] | W/D/L | Alternatives |
|------|--------|-----------------|--------|--------|-------|--------------|
| Jun 11 | Mexico | **2-1** | South Africa | 20.5 | 63/21/16% | 2-0, 1-0, 3-0 |
| Jun 11 | South Korea | **1-0** | Czechia | 12.6 | 37/28/35% | 2-1, 2-0, 0-1 |
| Jun 18 | Czechia | **1-0** | South Africa | 15.2 | 46/27/27% | 2-1, 2-0, 3-1 |
| Jun 18 | Mexico | **1-0** | South Korea | 17.4 | 53/25/22% | 2-1, 2-0, 3-1 |
| Jun 24 | Czechia | **0-1** | Mexico | 19.7 | 22/24/54% | 1-2, 0-2, 1-3 |
| Jun 24 | South Africa | **0-1** | South Korea | 17.8 | 26/26/47% | 1-2, 0-2, 1-3 |

### Group B — Switzerland, Canada, Bosnia and Herzegovina, Qatar

**Predicted standings: 1. Switzerland → 2. Canada → 3. Bosnia and Herzegovina → 4. Qatar**

| Date | Team 1 | **Optimal Pick** | Team 2 | E[pts] | W/D/L | Alternatives |
|------|--------|-----------------|--------|--------|-------|--------------|
| Jun 12 | Canada | **2-1** | Bosnia and Herzegovina | 18.9 | 58/23/19% | 1-0, 2-0, 3-1 |
| Jun 13 | Qatar | **0-2** | Switzerland | 23.8 | 14/20/66% | 1-2, 0-1, 0-3 |
| Jun 18 | Switzerland | **2-1** | Bosnia and Herzegovina | 19.4 | 60/22/18% | 1-0, 2-0, 3-1 |
| Jun 18 | Canada | **2-1** | Qatar | 20.5 | 64/21/16% | 2-0, 1-0, 3-0 |
| Jun 24 | Switzerland | **1-0** | Canada | 13.4 | 39/28/34% | 2-1, 2-0, 3-1 |
| Jun 24 | Bosnia and Herzegovina | **1-0** | Qatar | 14.9 | 42/27/30% | 2-1, 2-0, 3-1 |

### Group C — Brazil, Morocco, Scotland, Haiti

**Predicted standings: 1. Brazil → 2. Morocco → 3. Scotland → 4. Haiti**

| Date | Team 1 | **Optimal Pick** | Team 2 | E[pts] | W/D/L | Alternatives |
|------|--------|-----------------|--------|--------|-------|--------------|
| Jun 13 | Brazil | **1-0** | Morocco | 19.5 | 50/26/24% | 2-1, 2-0, 3-1 |
| Jun 13 | Haiti | **0-1** | Scotland | 20.7 | 20/23/57% | 1-2, 0-2, 1-3 |
| Jun 19 | Scotland | **0-1** | Morocco | 20.5 | 20/24/56% | 1-2, 0-2, 1-3 |
| Jun 19 | Brazil | **2-0** | Haiti | 25.5 | 83/12/5% | 3-0, 1-0, 4-0 |
| Jun 24 | Morocco | **2-0** | Haiti | 24.5 | 74/17/10% | 2-1, 1-0, 3-0 |
| Jun 24 | Scotland | **0-2** | Brazil | 23.5 | 13/19/68% | 1-2, 0-1, 0-3 |

### Group D — United States, Turkey, Australia, Paraguay

**Predicted standings: 1. United States → 2. Turkey → 3. Australia → 4. Paraguay**

| Date | Team 1 | **Optimal Pick** | Team 2 | E[pts] | W/D/L | Alternatives |
|------|--------|-----------------|--------|--------|-------|--------------|
| Jun 12 | United States | **2-1** | Paraguay | 18.9 | 58/23/19% | 1-0, 2-0, 3-1 |
| Jun 13 | Turkey | **1-0** | Australia | 13.3 | 38/28/34% | 2-1, 2-0, 3-1 |
| Jun 19 | United States | **1-0** | Australia | 17.7 | 55/24/21% | 2-1, 2-0, 3-1 |
| Jun 20 | Turkey | **1-0** | Paraguay | 14.5 | 41/28/32% | 2-1, 2-0, 3-1 |
| Jun 25 | Turkey | **0-1** | United States | 19.7 | 22/24/54% | 1-2, 0-2, 1-3 |
| Jun 25 | Paraguay | **0-1** | Australia | 13.5 | 34/28/39% | 1-2, 0-2, 1-3 |

### Group E — Germany, Ecuador, Ivory Coast, Curaçao

**Predicted standings: 1. Germany → 2. Ecuador → 3. Ivory Coast → 4. Curaçao**

| Date | Team 1 | **Optimal Pick** | Team 2 | E[pts] | W/D/L | Alternatives |
|------|--------|-----------------|--------|--------|-------|--------------|
| Jun 14 | Germany | **2-0** | Curaçao | 25.2 | 82/13/6% | 3-0, 1-0, 2-1 |
| Jun 14 | Ivory Coast | **0-1** | Ecuador | 20.5 | 20/24/56% | 1-2, 0-2, 1-3 |
| Jun 20 | Germany | **2-0** | Ivory Coast | 22.6 | 67/19/14% | 2-1, 1-0, 3-0 |
| Jun 20 | Ecuador | **2-0** | Curaçao | 24.2 | 73/17/10% | 2-1, 1-0, 3-0 |
| Jun 25 | Ecuador | **0-1** | Germany | 19.4 | 25/26/49% | 1-2, 0-2, 1-3 |
| Jun 25 | Curaçao | **0-1** | Ivory Coast | 20.7 | 20/23/57% | 1-2, 0-2, 1-3 |

### Group F — Netherlands, Japan, Sweden, Tunisia

**Predicted standings: 1. Netherlands → 2. Japan → 3. Sweden → 4. Tunisia**

| Date | Team 1 | **Optimal Pick** | Team 2 | E[pts] | W/D/L | Alternatives |
|------|--------|-----------------|--------|--------|-------|--------------|
| Jun 14 | Netherlands | **1-0** | Japan | 15.7 | 47/26/27% | 2-1, 2-0, 3-1 |
| Jun 14 | Sweden | **1-0** | Tunisia | 15.3 | 45/27/28% | 2-1, 2-0, 3-1 |
| Jun 20 | Netherlands | **2-1** | Sweden | 20.1 | 61/22/17% | 2-0, 1-0, 3-0 |
| Jun 21 | Japan | **2-1** | Tunisia | 19.8 | 60/22/18% | 1-0, 2-0, 3-1 |
| Jun 25 | Japan | **1-0** | Sweden | 16.7 | 51/25/23% | 2-1, 2-0, 3-1 |
| Jun 25 | Tunisia | **0-2** | Netherlands | 24.0 | 13/19/69% | 1-2, 0-1, 0-3 |

### Group G — Belgium, Iran, New Zealand, Egypt

**Predicted standings: 1. Belgium → 2. Iran → 3. New Zealand → 4. Egypt**

| Date | Team 1 | **Optimal Pick** | Team 2 | E[pts] | W/D/L | Alternatives |
|------|--------|-----------------|--------|--------|-------|--------------|
| Jun 15 | Belgium | **2-0** | Egypt | 23.2 | 70/18/12% | 2-1, 1-0, 3-0 |
| Jun 15 | Iran | **1-0** | New Zealand | 17.7 | 54/24/22% | 2-1, 2-0, 3-1 |
| Jun 21 | Belgium | **2-1** | Iran | 20.5 | 63/21/16% | 2-0, 1-0, 3-0 |
| Jun 21 | New Zealand | **0-1** | Egypt | 14.1 | 28/27/45% | 1-2, 0-2, 1-3 |
| Jun 26 | Egypt | **0-2** | Belgium | 23.2 | 12/18/70% | 1-2, 0-1, 0-3 |
| Jun 26 | New Zealand | **0-1** | Iran | 19.7 | 22/24/54% | 1-2, 0-2, 1-3 |

### Group H — Spain, Uruguay, Saudi Arabia, Cape Verde

**Predicted standings: 1. Spain → 2. Uruguay → 3. Saudi Arabia → 4. Cape Verde**

| Date | Team 1 | **Optimal Pick** | Team 2 | E[pts] | W/D/L | Alternatives |
|------|--------|-----------------|--------|--------|-------|--------------|
| Jun 15 | Spain | **2-0** | Cape Verde | 26.2 | 86/10/4% | 3-0, 4-0, 1-0 |
| Jun 15 | Saudi Arabia | **1-2** | Uruguay | 21.0 | 19/23/58% | 0-1, 0-2, 1-3 |
| Jun 21 | Spain | **2-0** | Saudi Arabia | 24.5 | 75/16/9% | 3-0, 2-1, 1-0 |
| Jun 21 | Uruguay | **2-0** | Cape Verde | 23.8 | 72/17/11% | 2-1, 1-0, 3-0 |
| Jun 26 | Cape Verde | **0-1** | Saudi Arabia | 19.5 | 22/25/53% | 1-2, 0-2, 1-3 |
| Jun 26 | Spain | **1-0** | Uruguay | 18.5 | 57/23/20% | 2-1, 2-0, 3-1 |

### Group I — France, Norway, Senegal, Iraq

**Predicted standings: 1. France → 2. Norway → 3. Senegal → 4. Iraq**

| Date | Team 1 | **Optimal Pick** | Team 2 | E[pts] | W/D/L | Alternatives |
|------|--------|-----------------|--------|--------|-------|--------------|
| Jun 16 | France | **2-1** | Senegal | 20.0 | 60/22/18% | 1-0, 2-0, 3-1 |
| Jun 16 | Iraq | **0-2** | Norway | 24.2 | 11/18/71% | 1-2, 0-1, 0-3 |
| Jun 22 | France | **2-0** | Iraq | 25.2 | 82/13/5% | 3-0, 1-0, 2-1 |
| Jun 22 | Norway | **1-0** | Senegal | 15.1 | 44/27/29% | 2-1, 2-0, 3-1 |
| Jun 26 | Norway | **0-1** | France | 19.3 | 23/25/52% | 1-2, 0-2, 1-3 |
| Jun 26 | Senegal | **2-0** | Iraq | 22.3 | 65/20/15% | 2-1, 1-0, 3-0 |

### Group J — Argentina, Austria, Algeria, Jordan

**Predicted standings: 1. Argentina → 2. Austria → 3. Algeria → 4. Jordan**

| Date | Team 1 | **Optimal Pick** | Team 2 | E[pts] | W/D/L | Alternatives |
|------|--------|-----------------|--------|--------|-------|--------------|
| Jun 16 | Argentina | **2-0** | Algeria | 23.8 | 72/17/11% | 2-1, 1-0, 3-0 |
| Jun 16 | Austria | **2-0** | Jordan | 23.2 | 70/18/12% | 2-1, 1-0, 3-0 |
| Jun 21 | Argentina | **2-1** | Austria | 20.0 | 60/22/18% | 1-0, 2-0, 3-1 |
| Jun 22 | Algeria | **2-1** | Jordan | 18.9 | 58/23/19% | 1-0, 2-0, 3-1 |
| Jun 25 | Argentina | **2-0** | Jordan | 26.2 | 86/10/4% | 3-0, 4-0, 1-0 |
| Jun 25 | Algeria | **0-1** | Austria | 19.4 | 24/25/51% | 1-2, 0-2, 1-3 |

### Group K — Portugal, Colombia, DR Congo, Uzbekistan

**Predicted standings: 1. Portugal → 2. Colombia → 3. DR Congo → 4. Uzbekistan**

| Date | Team 1 | **Optimal Pick** | Team 2 | E[pts] | W/D/L | Alternatives |
|------|--------|-----------------|--------|--------|-------|--------------|
| Jun 17 | Portugal | **2-0** | DR Congo | 23.8 | 72/17/11% | 2-1, 1-0, 3-0 |
| Jun 17 | Uzbekistan | **0-2** | Colombia | 23.2 | 12/18/70% | 1-2, 0-1, 0-3 |
| Jun 23 | Portugal | **2-0** | Uzbekistan | 24.5 | 77/15/8% | 3-0, 2-1, 1-0 |
| Jun 23 | Colombia | **2-0** | DR Congo | 22.3 | 65/20/15% | 2-1, 1-0, 3-0 |
| Jun 27 | Colombia | **0-1** | Portugal | 19.4 | 28/27/45% | 1-2, 0-2, 1-3 |
| Jun 27 | DR Congo | **1-0** | Uzbekistan | 14.9 | 42/27/30% | 2-1, 2-0, 3-1 |

### Group L — England, Croatia, Ghana, Panama

**Predicted standings: 1. England → 2. Croatia → 3. Ghana → 4. Panama**

| Date | Team 1 | **Optimal Pick** | Team 2 | E[pts] | W/D/L | Alternatives |
|------|--------|-----------------|--------|--------|-------|--------------|
| Jun 17 | England | **1-0** | Croatia | 17.7 | 54/24/21% | 2-1, 2-0, 3-1 |
| Jun 17 | Ghana | **1-0** | Panama | 15.2 | 46/27/27% | 2-1, 2-0, 3-1 |
| Jun 23 | England | **2-0** | Ghana | 24.5 | 79/14/7% | 3-0, 1-0, 2-1 |
| Jun 23 | Panama | **0-2** | Croatia | 24.7 | 10/17/74% | 1-2, 0-1, 0-3 |
| Jun 27 | England | **2-0** | Panama | 26.2 | 86/11/4% | 3-0, 1-0, 4-0 |
| Jun 27 | Croatia | **2-0** | Ghana | 22.5 | 66/20/14% | 2-1, 1-0, 3-0 |

---

## GROUP STANDINGS (25 pts per correct position — up to 1,200 pts total)

| Group | 1st | 2nd | 3rd | 4th |
|-------|-----|-----|-----|-----|
| A | Mexico (54%) | South Korea (37%) | Czechia | South Africa |
| B | Switzerland (45%) | Canada (45%) | Bosnia and Herzegovina | Qatar |
| C | Brazil (61%) | Morocco | Scotland | Haiti |
| D | United States (53%) | Turkey | Australia | Paraguay |
| E | Germany (60%) | Ecuador | Ivory Coast | Curaçao |
| F | Netherlands (54%) | Japan | Sweden | Tunisia |
| G | Belgium (69%) | Iran | New Zealand | Egypt |
| H | Spain (70%) | Uruguay | Saudi Arabia | Cape Verde |
| I | France (60%) | Norway | Senegal | Iraq |
| J | Argentina (72%) | Austria | Algeria | Jordan |
| K | Portugal (58%) | Colombia | DR Congo | Uzbekistan |
| L | England (69%) | Croatia | Ghana | Panama |

---

## KNOCKOUT ROUND PREDICTIONS

Points per correct result escalate: R32=90/60 → R16=135/90 → QF=180/120 → SF=225/150 → **Final=270/180**

### Round of 32

| Match | Team 1 | **Pick** | Team 2 | E[pts] | W/D/L |
|-------|--------|----------|--------|--------|-------|
| R32-1 | Mexico | **0-1** | Morocco | 25.6 | 34/29/37% |
| R32-2 | Brazil | **2-0** | Czechia | 42.6 | 65/21/14% |
| R32-3 | Switzerland | **1-0** | Turkey | 34.6 | 52/26/22% |
| R32-4 | United States | **1-0** | Australia | 36.5 | 55/25/20% |
| R32-5 | Germany | **2-0** | Iran | 44.5 | 68/20/12% |
| R32-6 | Belgium | **1-0** | Ivory Coast | 40.9 | 63/22/16% |
| R32-7 | Netherlands | **1-0** | Uruguay | 29.6 | 43/28/29% |
| R32-8 | Spain | **2-0** | Saudi Arabia | 49.6 | 76/16/8% |
| R32-9 | France | **2-0** | Scotland | 49.7 | 76/16/8% |
| R32-10 | Portugal | **1-0** | Senegal | 36.3 | 54/25/21% |
| R32-11 | Argentina | **2-0** | Sweden | 46.0 | 71/19/11% |
| R32-12 | England | **2-0** | Algeria | 46.6 | 72/18/10% |
| R32-13 | South Korea | **0-1** | Canada | 29.3 | 29/28/43% |
| R32-14 | Ecuador | **0-1** | Japan | 26.5 | 33/29/38% |
| R32-15 | Norway | **1-0** | Austria | 31.7 | 47/28/26% |
| R32-16 | Colombia | **1-0** | Croatia | 29.4 | 43/28/29% |

### Round of 16

| Match | Team 1 | **Pick** | Team 2 | E[pts] | W/D/L |
|-------|--------|----------|--------|--------|-------|
| R16-17 | Morocco | **0-1** | Brazil | 50.6 | 23/27/50% |
| R16-18 | Switzerland | **0-1** | United States | 38.3 | 34/29/37% |
| R16-19 | Germany | **1-0** | Belgium | 43.0 | 42/29/30% |
| R16-20 | Netherlands | **0-1** | Spain | 50.4 | 24/27/50% |
| R16-21 | France | **1-0** | Portugal | 42.8 | 42/29/30% |
| R16-22 | Argentina | **1-0** | England | 38.4 | 37/29/34% |
| R16-23 | Canada | **0-1** | Japan | 45.8 | 27/28/45% |
| R16-24 | Norway | **0-1** | Colombia | 37.9 | 35/29/37% |

### Quarter-finals

| Match | Team 1 | **Pick** | Team 2 | E[pts] | W/D/L |
|-------|--------|----------|--------|--------|-------|
| QF-25 | Brazil | **1-0** | United States | 68.0 | 50/26/23% |
| QF-26 | Germany | **0-1** | Spain | 67.5 | 24/27/50% |
| QF-27 | France | **1-0** | Argentina | 52.3 | 38/29/33% |
| QF-28 | Japan | **0-1** | Colombia | 60.4 | 28/28/44% |

### Semi-finals

| Match | Team 1 | **Pick** | Team 2 | E[pts] | W/D/L |
|-------|--------|----------|--------|--------|-------|
| SF-29 | Brazil | **0-1** | Spain | 79.3 | 26/28/47% |
| SF-30 | France | **1-0** | Colombia | 86.1 | 51/26/23% |

### Final — **Spain 1-0 France** (E[pts] = 75.0)

| Pick option | E[pts] | Note |
|-------------|--------|------|
| **1-0 Spain** | 75.0 | Optimal — Spain 36.1% win probability |
| 0-1 France | 73.1 | France 34.9% — essentially coin-flip |
| 2-1 Spain | 72.0 | |
| 2-0 Spain | 71.0 | |

This final is effectively a coin-flip (36.1% Spain, 29.1% draw, 34.9% France). Picking 1-0 Spain is marginally optimal; 0-1 France is only 2 expected points behind. Go with your gut on this one.

---

## METHODOLOGY

- **Strength blend:** 65% de-vigged bookmaker consensus (power method) + 35% World Football Elo
- **Goals model:** Dixon-Coles bivariate Poisson ρ=−0.10 with WC historical calibration (1-0/0-1 ×1.18, 2-1/1-2 ×1.08)
- **Confederation adjustment:** OFC −50, CONCACAF −25, CAF −20, AFC −15 Elo vs UEFA/CONMEBOL
- **Pick formula:** `E[pts] = outcome_pts × P(direction) + (exact_pts − outcome_pts) × P(exact a-b)`
- **KO bracket:** Official FIFA 2026 R32 pairings; 8 best thirds resolved by backtracking constraint solver
- **Host advantage:** USA +80 / Mexico +50 / Canada +45 Elo in KO; +90 Elo in home group venue

See `research/methodology.md` for academic citations.
