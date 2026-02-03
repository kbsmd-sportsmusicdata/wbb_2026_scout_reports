# Data Dictionary

## Overview

This document defines all fields in the processed data tables used for scout reports, including detailed formula documentation with source references.

**Formula Sources:**
- [Basketball-Reference Glossary](https://www.basketball-reference.com/about/glossary.html)
- [NBA Stats Glossary](https://www.nba.com/stats/help/glossary)
- [Basketball-Reference: Individual Offensive/Defensive Ratings](https://www.basketball-reference.com/about/ratings.html)
- Dean Oliver, *Basketball on Paper* (2004)
- John Hollinger, *Pro Basketball Prospectus* (2002-2011)

---

## Table: `game_analysis.parquet`

One row per team per game. Primary analysis table for Tableau.

### Identifiers

| Field | Type | Description |
|-------|------|-------------|
| `game_id` | int | ESPN unique game identifier |
| `game_date` | date | Game date (YYYY-MM-DD) |
| `season` | int | Academic year (e.g., 2025 = 2024-25 season) |
| `team_id` | int | ESPN team identifier |
| `team_name` | str | Full team name |
| `team_abbrev` | str | 3-4 letter abbreviation |
| `team_logo` | str | URL to team logo image |
| `opponent_id` | int | Opponent team identifier |
| `opponent_name` | str | Opponent full name |

### Box Score Stats (Raw)

| Field | Type | Description |
|-------|------|-------------|
| `pts` | int | Points scored |
| `opp_pts` | int | Opponent points |
| `fgm` | int | Field goals made |
| `fga` | int | Field goals attempted |
| `fg3m` | int | 3-point field goals made |
| `fg3a` | int | 3-point field goals attempted |
| `fg2m` | int | 2-point field goals made (derived) |
| `fg2a` | int | 2-point field goals attempted (derived) |
| `ftm` | int | Free throws made |
| `fta` | int | Free throws attempted |
| `orb` | int | Offensive rebounds |
| `drb` | int | Defensive rebounds |
| `ast` | int | Assists |
| `stl` | int | Steals |
| `blk` | int | Blocks |
| `tov` | int | Turnovers |
| `pf` | int | Personal fouls |

### Derived Metrics (Team)

| Field | Type | Formula | Description |
|-------|------|---------|-------------|
| `poss_est` | float | `FGA + 0.44*FTA - ORB + TOV` | Estimated possessions (Dean Oliver) |
| `efg_pct` | float | `(FGM + 0.5*3PM) / FGA` | Effective field goal % |
| `ts_pct` | float | `PTS / (2*(FGA + 0.44*FTA))` | True shooting % |
| `tov_pct` | float | `TOV / Poss` | Turnover rate |
| `oreb_pct` | float | `ORB / (ORB + Opp_DRB)` | Offensive rebound rate |
| `dreb_pct` | float | `DRB / (DRB + Opp_ORB)` | Defensive rebound rate |
| `ftr` | float | `FTA / FGA` | Free throw rate |
| `fg3_rate` | float | `3PA / FGA` | 3-point attempt rate |
| `fg2_pct` | float | `FG2M / FG2A` | 2-point field goal % |
| `fg3_pct` | float | `3PM / 3PA` | 3-point field goal % |
| `ft_pct` | float | `FTM / FTA` | Free throw % |
| `ast_pct` | float | `AST / FGM` | Assist rate on made shots |
| `ast_tov` | float | `AST / TOV` | Assist to turnover ratio |
| `ortg` | float | `100 * PTS / Poss` | Offensive rating (per 100 poss) |
| `drtg` | float | `100 * Opp_PTS / Opp_Poss` | Defensive rating (per 100 poss) |
| `net_rtg` | float | `ORtg - DRtg` | Net rating |
| `pace` | float | `Poss` | Game pace (possessions) |

### Percentile Fields

| Field | Type | Description |
|-------|------|-------------|
| `efg_pctile` | float | eFG% percentile vs D1 (0-100) |
| `ts_pctile` | float | TS% percentile vs D1 |
| `tov_pctile` | float | TOV% percentile vs D1 (inverted - lower is better) |
| `oreb_pctile` | float | OREB% percentile vs D1 |
| `ftr_pctile` | float | FTr percentile vs D1 |
| `ortg_pctile` | float | ORtg percentile vs D1 |
| `net_rtg_pctile` | float | Net Rating percentile vs D1 |

### Categorical Labels

| Field | Type | Values | Description |
|-------|------|--------|-------------|
| `efg_label` | str | Elite/Great/Above Average/Average/Below Average/Low | eFG% tier |
| `tov_label` | str | (same tiers) | TOV% tier |
| `oreb_label` | str | (same tiers) | OREB% tier |
| `net_rtg_label` | str | (same tiers) | Net Rating tier |

### Game Context

| Field | Type | Description |
|-------|------|-------------|
| `margin` | int | Point differential (pts - opp_pts) |
| `abs_margin` | int | Absolute point differential |
| `win` | bool | True if team won |
| `close_game` | bool | True if margin ≤ 5 |
| `blowout` | bool | True if margin ≥ 15 |
| `home_away` | str | "home" or "away" |

---

## Table: `player_game.parquet`

One row per player per game.

### Identifiers

| Field | Type | Description |
|-------|------|-------------|
| `game_id` | int | ESPN game identifier |
| `athlete_id` | int | ESPN player identifier |
| `athlete_name` | str | Player display name |
| `team_id` | int | Team identifier |
| `team_name` | str | Team name |

### Box Score Stats

| Field | Type | Description |
|-------|------|-------------|
| `minutes` | float | Minutes played |
| `pts` | int | Points |
| `reb` | int | Total rebounds |
| `orb` | int | Offensive rebounds |
| `drb` | int | Defensive rebounds |
| `ast` | int | Assists |
| `stl` | int | Steals |
| `blk` | int | Blocks |
| `tov` | int | Turnovers |
| `pf` | int | Personal fouls |
| `fgm` | int | Field goals made |
| `fga` | int | Field goals attempted |
| `fg3m` | int | 3-pointers made |
| `fg3a` | int | 3-pointers attempted |
| `ftm` | int | Free throws made |
| `fta` | int | Free throws attempted |
| `starter` | bool | True if started |

### Player Metrics (Basic)

| Field | Type | Formula | Description |
|-------|------|---------|-------------|
| `ts_pct` | float | `PTS / (2*(FGA + 0.44*FTA))` | True shooting % |
| `efg_pct` | float | `(FGM + 0.5*3PM) / FGA` | Effective field goal % |
| `usg_pct` | float | See detailed formula below | Usage rate (% of team possessions used) |
| `ast_pct` | float | `AST / (Team_FGM - Player_FGM)` | Assist % |
| `tov_pct` | float | `TOV / (FGA + 0.44*FTA + TOV)` | Individual turnover rate |
| `pts_per40` | float | `PTS * 40 / Minutes` | Points per 40 minutes |
| `reb_per40` | float | `REB * 40 / Minutes` | Rebounds per 40 minutes |
| `ast_per40` | float | `AST * 40 / Minutes` | Assists per 40 minutes |

### Advanced Player Metrics (Box Score Derived)

| Field | Type | Formula | Description |
|-------|------|---------|-------------|
| `game_score` | float | See detailed formula below | Single-game performance metric (Hollinger) |
| `pie` | float | See detailed formula below | Player Impact Estimate (NBA) |
| `stl_pct` | float | `100 * STL * (Tm_MP/5) / (MP * Opp_Poss)` | Steal percentage |
| `blk_pct` | float | `100 * BLK * (Tm_MP/5) / (MP * (Opp_FGA - Opp_3PA))` | Block percentage |
| `trb_pct` | float | `100 * TRB * (Tm_MP/5) / (MP * (Tm_TRB + Opp_TRB))` | Total rebound percentage |
| `floor_pct` | float | `Scoring_Poss / Total_Poss` (simplified) | Floor percentage |
| `ppp` | float | `PTS / (FGA + 0.44*FTA + TOV)` | Points per possession |
| `ppsa` | float | `PTS / (FGA + 0.44*FTA)` | Points per shot attempt |
| `player_ortg` | float | `100 * Points_Produced / Poss_Used` (simplified) | Individual offensive rating |
| `player_drtg` | float | `Team_DRtg - Def_Adjustment` (estimated) | Individual defensive rating |

### Player Labels

| Field | Type | Values | Description |
|-------|------|--------|-------------|
| `usg_ts_label` | str | "High Volume + Efficient" / "High Volume, Struggled" / "Efficient Role Player" / "Quiet Game" | Performance category |
| `position_group` | str | Guard / Forward / Center / Other | Normalized position group |

---

## Table: `d1_benchmarks.csv`

Reference table for D1 averages and percentile breakpoints.

| Field | Type | Description |
|-------|------|-------------|
| `metric` | str | Metric name |
| `n_games` | int | Sample size |
| `mean` | float | D1 average |
| `std` | float | Standard deviation |
| `min` | float | Minimum value |
| `max` | float | Maximum value |
| `p10` | float | 10th percentile |
| `p25` | float | 25th percentile |
| `p50` | float | Median |
| `p75` | float | 75th percentile |
| `p90` | float | 90th percentile |

---

## Notes

### Possession Estimation

The Dean Oliver formula is an approximation. True possessions require play-by-play data:
- Estimated: `FGA + 0.44*FTA - ORB + TOV`
- The 0.44 FTA coefficient accounts for and-ones and technical free throws

### Percentile Direction

Most metrics: higher percentile = better performance.

Exception: `tov_pct` is **inverted** for labeling purposes. A low turnover rate is good, so we flip the percentile before assigning labels.

### Usage Rate (Full Formula)

```
USG% = 100 * (FGA + 0.44*FTA + TOV) * (Team_Min / 5) / (Player_Min * Team_Poss)
```

The simplified version used when team totals aren't available:
```
Usage_Proxy = (FGA + 0.44*FTA + TOV) / Minutes
```

### Missing Data Handling

- Counting stats (pts, reb, ast): `0` if missing
- Rate stats (fg_pct, ts_pct): `NULL` if denominator is 0
- Percentiles: Computed against non-null values only

---

## Detailed Formula Documentation

This section provides comprehensive documentation of all metric calculations with sources.

### Shooting Efficiency Metrics

#### Effective Field Goal Percentage (eFG%)

**Formula:** `eFG% = (FGM + 0.5 * 3PM) / FGA`

**Source:** [Basketball-Reference Glossary](https://www.basketball-reference.com/about/glossary.html)

**Interpretation:** Adjusts field goal percentage to account for three-pointers being worth more. A 3-pointer made counts as 1.5 field goals made.
- D1 WBB Average: ~47%
- Elite (≥90th percentile): ~54%+

---

#### True Shooting Percentage (TS%)

**Formula:** `TS% = PTS / (2 * (FGA + 0.44 * FTA))`

**Source:** [Basketball-Reference Glossary](https://www.basketball-reference.com/about/glossary.html)

**Interpretation:** The most comprehensive shooting efficiency metric, accounting for 2-pointers, 3-pointers, and free throws. The 0.44 coefficient estimates possessions used by free throws (accounting for and-ones, technical FTs, etc.).

**Note:** Some sources use 0.475 instead of 0.44 for the FTA coefficient. We use 0.44 per Basketball-Reference convention.

- D1 WBB Average: ~50%
- Elite scorers: 58%+

---

#### Free Throw Rate (FTr)

**Formula:** `FTr = FTA / FGA`

**Source:** [Basketball-Reference Glossary](https://www.basketball-reference.com/about/glossary.html)

**Interpretation:** Measures ability to get to the free throw line relative to field goal attempts. Higher values indicate players who draw fouls effectively.

- D1 Average: ~0.30
- Elite: 0.45+

---

### Possession & Pace Metrics

#### Possessions (Estimated)

**Formula:** `Poss = FGA + 0.44 * FTA - ORB + TOV`

**Source:** Dean Oliver, *Basketball on Paper* (2004); [Basketball-Reference](https://www.basketball-reference.com/about/glossary.html)

**Interpretation:** Estimates the number of possessions used. A possession ends when the team either scores, turns the ball over, or the opponent gets the rebound.

- The 0.44 FTA coefficient accounts for and-one situations, technical free throws, and 3-shot fouls
- Subtracting ORB removes possessions that continued after a missed shot
- More accurate possession counting requires play-by-play data

---

#### Offensive Rating (ORtg)

**Formula:** `ORtg = 100 * PTS / Poss`

**Source:** [Basketball-Reference](https://www.basketball-reference.com/about/glossary.html)

**Interpretation:** Points scored per 100 possessions. A tempo-free efficiency measure.

- D1 Average: ~92.6
- Elite offenses: 115+

---

#### Defensive Rating (DRtg)

**Formula:** `DRtg = 100 * Opp_PTS / Poss`

**Source:** [Basketball-Reference](https://www.basketball-reference.com/about/glossary.html)

**Interpretation:** Points allowed per 100 possessions. Lower is better.

- D1 Average: ~70-75
- Elite defenses: <65

---

### Four Factors (Dean Oliver)

The Four Factors are the key determinants of basketball success:

| Factor | Offense | Defense | Weight |
|--------|---------|---------|--------|
| Shooting | eFG% | Opp eFG% | 40% |
| Turnovers | TOV% (lower better) | Opp TOV% (higher better) | 25% |
| Rebounding | OREB% | DREB% | 20% |
| Free Throws | FTr | Opp FTr (lower better) | 15% |

---

### Advanced Player Metrics

#### Game Score (GmSc) - John Hollinger

**Formula:**
```
GmSc = PTS + 0.4*FGM - 0.7*FGA - 0.4*(FTA - FTM)
       + 0.7*ORB + 0.3*DRB + STL + 0.7*AST
       + 0.7*BLK - 0.4*PF - TOV
```

**Source:** John Hollinger; [NBSStuffer](https://www.nbastuffer.com/analytics101/game-score/); [Omnicalculator](https://www.omnicalculator.com/sports/game-score)

**Interpretation:** Single-number summary of a player's game performance. Provides a rough measure of productivity.

- Average starter performance: ~10
- Excellent game: 20+
- Outstanding game: 30+
- Historic performance: 40+
- NBA Record: 64.6 (Michael Jordan, 1990)

---

#### Player Impact Estimate (PIE) - NBA

**Formula:**
```
PIE = (PTS + FGM + FTM - FGA - FTA + DRB + 0.5*ORB + AST + STL + 0.5*BLK - PF - TOV)
      / (Game_PTS + Game_FGM + Game_FTM - Game_FGA - Game_FTA + Game_DRB
         + 0.5*Game_ORB + Game_AST + Game_STL + 0.5*Game_BLK - Game_PF - Game_TOV)
```

**Source:** [NBA Stats](https://www.nba.com/stats/help/glossary); [NBAStuffer](https://www.nbastuffer.com/analytics101/player-impact-estimate-pie/)

**Interpretation:** Measures a player's overall statistical contribution as a percentage of the game totals. All players' PIE values in a game sum to 100%.

- Average (per player in 10-player game): 10%
- Good: 12-15%
- Excellent: 15-20%
- Dominant: 20%+

---

#### Usage Percentage (USG%)

**Formula:**
```
USG% = 100 * ((FGA + 0.44*FTA + TOV) * (Tm_MP / 5)) / (MP * (Tm_FGA + 0.44*Tm_FTA + Tm_TOV))
```

**Source:** [Basketball-Reference Glossary](https://www.basketball-reference.com/about/glossary.html)

**Interpretation:** Estimates the percentage of team plays used by a player while on the floor. High usage doesn't necessarily mean efficiency.

- Average: ~20%
- High-usage player: 28%+
- Very high usage: 33%+

---

#### Steal Percentage (STL%)

**Formula:**
```
STL% = 100 * (STL * (Tm_MP / 5)) / (MP * Opp_Poss)
```

**Source:** [Basketball-Reference Glossary](https://www.basketball-reference.com/about/glossary.html)

**Interpretation:** Percentage of opponent possessions that end in a steal by this player while on the floor.

- D1 Average: ~1.5%
- Elite: 3.0%+

---

#### Block Percentage (BLK%)

**Formula:**
```
BLK% = 100 * (BLK * (Tm_MP / 5)) / (MP * (Opp_FGA - Opp_3PA))
```

**Source:** [Basketball-Reference Glossary](https://www.basketball-reference.com/about/glossary.html)

**Interpretation:** Percentage of opponent two-point field goal attempts blocked by this player while on the floor. Three-point attempts are excluded because they are rarely blocked.

- D1 Average: ~2.5%
- Elite rim protector: 8%+

---

#### Total Rebound Percentage (TRB%)

**Formula:**
```
TRB% = 100 * (TRB * (Tm_MP / 5)) / (MP * (Tm_TRB + Opp_TRB))
```

**Source:** [Basketball-Reference Glossary](https://www.basketball-reference.com/about/glossary.html)

**Interpretation:** Percentage of available rebounds grabbed by this player while on the floor.

- D1 Average: ~10%
- Good rebounder: 15%+
- Elite rebounder: 20%+

---

#### Floor Percentage (Floor%)

**Formula (Simplified):**
```
Floor% = (FGM + 0.5*AST) / (FGA + 0.44*FTA + TOV)
```

**Full Formula:** See [Basketball-Reference Individual Ratings](https://www.basketball-reference.com/about/ratings.html)

**Source:** Dean Oliver, *Basketball on Paper*

**Interpretation:** Percentage of a player's possessions that end in points scored. Unlike TS%, this considers assists (creating scoring opportunities for teammates).

- D1 Average: ~54%
- Guards typically have higher Floor% due to assists

---

#### Points Per Possession (PPP)

**Formula:**
```
PPP = PTS / (FGA + 0.44*FTA + TOV)
```

**Source:** Standard basketball analytics

**Interpretation:** Points scored per possession used. Similar to TS% but expressed in points rather than percentage.

- D1 Average: ~0.9-1.0
- Elite: 1.2+

---

#### Points Per Shot Attempt (PPsA)

**Formula:**
```
PPsA = PTS / (FGA + 0.44*FTA)
```

**Source:** Standard basketball analytics

**Interpretation:** Similar to PPP but excludes turnovers from the denominator. Measures pure scoring efficiency on shot attempts.

- Equivalent to 2 × TS%
- Average: ~1.0
- Elite: 1.2+

---

#### Individual Offensive Rating (Player ORtg)

**Formula (Simplified):**
```
Points_Produced = PTS + AST * (Team_PTS / Team_FGM) * 0.5
Poss_Used = FGA + 0.44*FTA + TOV
Player_ORtg = 100 * Points_Produced / Poss_Used
```

**Full Formula:** See [Basketball-Reference Individual Ratings](https://www.basketball-reference.com/about/ratings.html)

**Source:** Dean Oliver, *Basketball on Paper*

**Interpretation:** Points produced per 100 possessions used. The simplified version approximates the full Oliver formula which requires detailed possession tracking.

- D1 Average: ~95-100
- Elite offensive players: 115+

**Note:** The full Dean Oliver formula is complex and involves calculating Scoring Possessions with FG_Part, AST_Part, FT_Part, and ORB_Part components.

---

#### Individual Defensive Rating (Player DRtg)

**Formula (Estimated):**
```
Team_DRtg = 100 * Opp_PTS / Team_Poss
Def_Contribution = (STL * 2.0 + BLK * 1.5 + DRB * 0.5 - PF * 0.5)
Adjustment = Def_Contribution / (Min_Pct * 100 + 1)
Player_DRtg = Team_DRtg - Adjustment
```

**Source:** Adapted from Dean Oliver's methodology; [Basketball-Reference](https://www.basketball-reference.com/about/ratings.html)

**Interpretation:** Points allowed per 100 possessions faced. Lower is better. True individual DRtg requires play-by-play data to track which players are on court when points are allowed.

**Caveat:** Box score-based DRtg is highly approximated. A player's DRtg depends heavily on team defense and linemates.

---

## Play-by-Play Derived Metrics

These metrics require play-by-play data for accurate calculation.

### On/Off Ratings

**Formula:**
```
On_ORtg = 100 * Points_Scored_On_Court / Poss_On_Court
On_DRtg = 100 * Points_Allowed_On_Court / Poss_On_Court
On_Net = On_ORtg - On_DRtg

Off_ORtg = 100 * Points_Scored_Off_Court / Poss_Off_Court
Off_DRtg = 100 * Points_Allowed_Off_Court / Poss_Off_Court
Off_Net = Off_ORtg - Off_DRtg

On/Off_Diff = On_Net - Off_Net
```

**Interpretation:** Compares team performance with a player on vs. off the court. Positive On/Off Diff indicates the team performs better with the player on the floor.

---

### Shot Zone Efficiency

| Zone | Description | Expected PPS |
|------|-------------|--------------|
| Paint | Layups, dunks | 1.2-1.4 |
| Mid-Range | 2PT jumpers | 0.8-0.9 |
| Three-Point | 3PT shots | 1.0-1.2 |
| Free Throw | FTs | 0.7-0.8 |

**Formula:** `Zone_PPS = Points_Value * (Made / Attempted)`

---

### Assisted vs. Unassisted FG%

**Formula:**
```
Assisted_Rate = Assisted_FGM / Total_FGM
Unassisted_Rate = Unassisted_FGM / Total_FGM
```

**Interpretation:**
- High assisted rate: Player scores off teammate's creation (catch-and-shoot, cuts)
- High unassisted rate: Player creates own shot (isolation, pick-and-roll ball handler)

---

### Transition vs. Half-Court

**Formula:**
```
Transition_PPP = Transition_Points / Transition_Poss
Halfcourt_PPP = Halfcourt_Points / Halfcourt_Poss
```

**Interpretation:** Teams typically score more efficiently in transition (~1.1+ PPP) vs. half-court (~0.9 PPP).

---

### Points Off Turnovers (POT)

**Formula:**
```
POT = Points scored on possessions immediately following opponent turnover
POT_PPP = POT / Opponent_Turnovers
```

**Interpretation:** Measures ability to capitalize on opponent mistakes. Expected POT PPP ~1.0-1.2.

---

### Second Chance Points (SCP)

**Formula:**
```
SCP = Points scored on possessions following offensive rebound
SCP_PPP = SCP / Offensive_Rebounds
```

**Interpretation:** Measures ability to convert second-chance opportunities. Expected SCP PPP ~1.0-1.2.

---

## Benchmarks and Percentile Tiers

### Percentile Tier Labels

| Tier | Percentile Range |
|------|------------------|
| Elite | 90-100 |
| Great | 75-89 |
| Above Average | 60-74 |
| Average | 40-59 |
| Below Average | 25-39 |
| Low | 0-24 |

### Position-Specific Benchmarking

Player metrics are benchmarked against their position group:
- **Guards:** PG, SG, Combo Guard
- **Forwards:** SF, PF, Wing
- **Centers:** C, Post

This accounts for positional differences (e.g., centers have higher BLK% than guards).

---

## Source References

1. **Basketball-Reference Glossary**
   https://www.basketball-reference.com/about/glossary.html

2. **Basketball-Reference: Individual Ratings**
   https://www.basketball-reference.com/about/ratings.html

3. **NBA Stats Glossary**
   https://www.nba.com/stats/help/glossary

4. **NBAStuffer Analytics 101**
   https://www.nbastuffer.com/analytics101/

5. **Dean Oliver, *Basketball on Paper* (2004)**
   Foundational text for possession-based basketball analytics.

6. **John Hollinger, *Pro Basketball Prospectus***
   Creator of Game Score and PER metrics.

7. **Hack a Stat - Advanced Basketball Statistics**
   https://hackastat.eu/en/

8. **Cleaning the Glass**
   https://cleaningtheglass.com/ (premium source for NBA/WNBA advanced stats)
