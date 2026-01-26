# Condensed Scout Report Template

## Overview

A streamlined 3-view Tableau dashboard for weekly game analysis. Designed to be produced quickly, consumed easily, and demonstrate analytical rigor through calculated metrics and contextual benchmarks.

**Target Audience:** Coaching staff, front office, analytics-curious fans  
**Production Time:** ~30 minutes per game after pipeline setup  
**Reading Time:** <3 minutes for key insights

---

## View 1: Game Summary Dashboard

### Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│  [Team A Logo]  TEAM A  vs  TEAM B  [Team B Logo]                   │
│                 72           vs      68                              │
│                 W                    L                               │
│                 "Close Game • Ranked Matchup"                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  WHY TEAM A WON                                              │    │
│  │  • Dominated the glass (42% OREB vs 28%)                    │    │
│  │  • Protected the ball (12% TOV vs 18%)                      │    │
│  │  • Out-executed in paint (48% FG In Paint vs 38%)           │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                      │
├─────────────────────────────────────────────────────────────────────┤
│  FOUR FACTORS COMPARISON                                            │
│                                                                      │
│  Metric          Team A   Pctl   Label        Team B   Pctl   Label │
│  ────────────────────────────────────────────────────────────────── │
│  eFG%            52.3%    78     Great        48.1%    55     Avg   │
│  TOV%            12.1%    82     Great        18.4%    35     Below │
│  OREB%           42.0%    91     Elite        28.3%    42     Avg   │
│  FT Rate         24.5%    65     Above Avg    31.2%    77     Great │
│  ────────────────────────────────────────────────────────────────── │
│  Net Rating      +8.5     72     Great        -4.2     38     Below │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Components

**Header Section**
- Team logos (from team_logo field)
- Final score
- Win/Loss indicator
- Game context tags:
  - Close Game (margin ≤5)
  - Blowout (margin ≥15)
  - Ranked Matchup (both in AP Top 25)
  - Upset (lower-ranked team wins)
  - Overtime

**"Why They Won" Callout**
- Auto-generated from metric differentials
- Rules for selection:
  1. Find metrics where winner has ≥15 percentile advantage
  2. Rank by impact (OREB% > TOV% > eFG% > FTr)
  3. Select top 3 differentials
  4. Write in plain language

**Four Factors Table**
| Field | Source | Calculation |
|-------|--------|-------------|
| eFG% | Derived | `(FGM + 0.5 * 3PM) / FGA` |
| TOV% | Derived | `TOV / Poss` where `Poss = FGA + 0.44*FTA - ORB + TOV` |
| OREB% | Derived | `ORB / (ORB + Opp_DRB)` |
| FT Rate | Derived | `FTA / FGA` |
| Percentile | Lookup | vs. D1 season averages |
| Label | Derived | See categorical labels below |

---

## View 2: Metrics Breakdown

### Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│  SHOOTING EFFICIENCY                                                 │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  eFG%      ████████████░░░░  52.3% (78th)    Team A           │  │
│  │            ██████████░░░░░░  48.1% (55th)    Team B           │  │
│  │  TS%       █████████████░░░  56.1% (82nd)                     │  │
│  │            ███████████░░░░░  51.8% (61st)                     │  │
│  │  2P%       ███████████░░░░░  48.2% (65th)                     │  │
│  │            █████████░░░░░░░  42.1% (41st)                     │  │
│  │  3P%       ████████████░░░░  36.4% (71st)                     │  │
│  │            ██████████░░░░░░  33.3% (52nd)                     │  │
│  └───────────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────────┤
│  BALL CONTROL                    │  REBOUNDING                      │
│  ┌─────────────────────────────┐ │ ┌─────────────────────────────┐  │
│  │ TOV%    12.1% (82nd) Great  │ │ │ OREB%   42.0% (91st) Elite  │  │
│  │ AST/TOV 1.8x  (75th) Great  │ │ │ DREB%   71.2% (68th) Above  │  │
│  │ STL%    11.2% (70th) Above  │ │ │ REB%    56.1% (78th) Great  │  │
│  └─────────────────────────────┘ │ └─────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────────┤
│  TEMPO CONTEXT                                                       │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  Pace: 68.5 possessions/game                                  │  │
│  │  [====●============] D1 Avg: 72.1                             │  │
│  │  "Slower than average — this was a grind-it-out game"         │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### Metrics Definitions

**Shooting Efficiency**
| Metric | Formula | Notes |
|--------|---------|-------|
| eFG% | `(FGM + 0.5 * 3PM) / FGA` | Weights 3s appropriately |
| TS% | `PTS / (2 * (FGA + 0.44 * FTA))` | Includes free throws |
| 2P% | `(FGM - 3PM) / (FGA - 3PA)` | Inside the arc only |
| 3P% | `3PM / 3PA` | Beyond the arc |
| FT% | `FTM / FTA` | Free throw conversion |

**Ball Control**
| Metric | Formula | Notes |
|--------|---------|-------|
| TOV% | `TOV / Poss` | Lower is better |
| AST/TOV | `AST / TOV` | Playmaking efficiency |
| AST% | `AST / FGM` | Team ball movement |
| STL% | `STL / Opp_Poss` | Defensive disruption |

**Rebounding**
| Metric | Formula | Notes |
|--------|---------|-------|
| OREB% | `ORB / (ORB + Opp_DRB)` | Second chances |
| DREB% | `DRB / (DRB + Opp_ORB)` | Ending possessions |
| REB% | `TRB / (TRB + Opp_TRB)` | Overall board control |

**Tempo**
| Metric | Formula | Notes |
|--------|---------|-------|
| Pace | `Poss` | Possessions per game |
| Relative Pace | `Pace - D1_Avg_Pace` | Context vs league |

---

## View 3: Player Impact

### Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│  TOP PERFORMERS                                                      │
│                                                                      │
│  Player          Team   PTS  USG%   TS%    Label                    │
│  ────────────────────────────────────────────────────────────────── │
│  J. Smith        A      24   32.1%  62.4%  ★ High Volume + Efficient │
│  M. Johnson      B      22   35.8%  48.2%  ⚠ High Volume, Struggled  │
│  K. Williams     A      18   24.2%  58.1%  ✓ Efficient Role Player   │
│  A. Davis        B      15   21.5%  55.3%  ✓ Efficient Role Player   │
│  T. Brown        A      12   18.1%  61.2%  ✓ Efficient Role Player   │
│                                                                      │
├─────────────────────────────────────────────────────────────────────┤
│  EFFICIENCY vs VOLUME SCATTERPLOT                                   │
│                                                                      │
│  TS%                                                                 │
│  70% │            ●A                                                 │
│      │      ●A         ●A                                            │
│  60% │  ●B      ●B                D1 Avg TS% ─────────              │
│      │              ●B                                               │
│  50% │                  ●B                                           │
│      │                       ●B                                      │
│  40% │                                                               │
│      └──────┼──────┼──────┼──────┼───────                           │
│           15%    20%    25%    30%    35%  USG%                      │
│                                                                      │
│  Legend: ●A = Team A players  ●B = Team B players                   │
│  Quadrants: Upper-right = Stars, Upper-left = Efficient roles       │
│             Lower-right = Volume scorers struggling                  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Player Metrics

**Per-Game Stats** (from box score)
- Points, Rebounds, Assists, Steals, Blocks, Turnovers
- Minutes played
- FGM/FGA, 3PM/3PA, FTM/FTA

**Derived Metrics**
| Metric | Formula | Level |
|--------|---------|-------|
| USG% | `100 * (FGA + 0.44*FTA + TOV) * (Team_Min/5) / (Player_Min * Team_Poss)` | Player |
| TS% | `PTS / (2 * (FGA + 0.44 * FTA))` | Player |
| AST% | `AST / (Team_FGM - Player_FGM)` | Player |
| TOV% | `TOV / (FGA + 0.44*FTA + TOV)` | Player |

**Categorical Labels**
| USG% | TS% vs Avg | Label |
|------|------------|-------|
| ≥25% | ≥Avg | ★ High Volume + Efficient |
| ≥25% | <Avg | ⚠ High Volume, Struggled |
| <25% | ≥Avg | ✓ Efficient Role Player |
| <25% | <Avg | Quiet Game |

---

## Categorical Label Definitions

### Percentile Tiers

| Percentile Range | Label | Color Code |
|------------------|-------|------------|
| ≥90 | Elite | Dark Green |
| 75–89 | Great | Light Green |
| 60–74 | Above Average | Light Blue |
| 40–59 | Average | Gray |
| 25–39 | Below Average | Light Orange |
| <25 | Low | Red |

### Game Context Tags

| Condition | Tag |
|-----------|-----|
| Margin ≤ 5 | Close Game |
| Margin ≥ 15 | Blowout |
| Both teams AP Top 25 | Ranked Matchup |
| Loser ranked higher | Upset |
| Game went to OT | Overtime |

### Player Role Labels

| Criteria | Label |
|----------|-------|
| USG% ≥30%, TS% ≥55% | Primary Scorer (Efficient) |
| USG% ≥30%, TS% <55% | Primary Scorer (Struggling) |
| AST% ≥20%, TOV% <15% | Primary Playmaker |
| USG% <20%, TS% ≥55% | Efficient Role Player |
| OREB% ≥15% or BLK ≥2 | Rim Presence |

---

## D1 Benchmark Values (2024-25 Reference)

*To be computed from full season data*

| Metric | D1 Average | P25 | P50 | P75 | P90 |
|--------|------------|-----|-----|-----|-----|
| eFG% | ~47% | TBD | TBD | TBD | TBD |
| TS% | ~52% | TBD | TBD | TBD | TBD |
| TOV% | ~18% | TBD | TBD | TBD | TBD |
| OREB% | ~30% | TBD | TBD | TBD | TBD |
| Pace | ~72 | TBD | TBD | TBD | TBD |

*Note: These will be calculated from wehoop/sportsdataverse season data and stored in `data/benchmarks/d1_benchmarks_2025.csv`*

---

## Tableau Implementation Notes

### Data Source Structure

**Primary Table: `game_analysis`**
One row per team per game.

```
game_id, game_date, team_id, team_name, team_logo, opponent_id, opponent_name,
pts, opp_pts, margin, win, 
fgm, fga, fg3m, fg3a, ftm, fta, orb, drb, ast, stl, blk, tov, pf,
opp_fgm, opp_fga, opp_fg3m, opp_fg3a, opp_ftm, opp_fta, opp_orb, opp_drb,
poss, opp_poss, pace,
efg_pct, ts_pct, tov_pct, oreb_pct, dreb_pct, ftr, fg3_rate, ast_tov,
ortg, drtg, net_rtg,
efg_pctile, ts_pctile, tov_pctile, oreb_pctile, net_rtg_pctile,
efg_label, tov_label, oreb_label, net_rtg_label,
game_tag, ranked_matchup, close_game
```

**Secondary Table: `player_game`**
One row per player per game.

```
game_id, player_id, player_name, team_id, team_name,
minutes, pts, reb, ast, stl, blk, tov, pf,
fgm, fga, fg3m, fg3a, ftm, fta, orb, drb,
usg_pct, ts_pct, ast_pct, tov_pct,
usg_ts_label, role_label
```

### Calculated Fields in Tableau

*Prefer pre-computed fields, but these can be Tableau calcs if needed:*

```
// Why They Won — Top Differential
IF [efg_pctile] - [opp_efg_pctile] >= 15 THEN "Shooting efficiency"
ELSEIF [oreb_pctile] - [opp_oreb_pctile] >= 15 THEN "Offensive rebounding"
ELSEIF [tov_pctile] - [opp_tov_pctile] >= 15 THEN "Ball security"
ELSE "Execution edge"
END

// Percentile Label
IF [efg_pctile] >= 90 THEN "Elite"
ELSEIF [efg_pctile] >= 75 THEN "Great"
ELSEIF [efg_pctile] >= 60 THEN "Above Average"
ELSEIF [efg_pctile] >= 40 THEN "Average"
ELSEIF [efg_pctile] >= 25 THEN "Below Average"
ELSE "Low"
END
```

### Color Encoding

**Percentile Diverging Scale**
- 0–25: Red (#D73027)
- 25–40: Light Orange (#FC8D59)
- 40–60: Gray (#EEEEEE)
- 60–75: Light Blue (#91BFDB)
- 75–90: Light Green (#91CF60)
- 90–100: Dark Green (#1A9850)

**Win/Loss**
- Win: #1A9850 (green)
- Loss: #D73027 (red)

**Team Colors**
- Pull from `team_color` and `team_alternate_color` fields
- Use for logos/headers only, not data encoding

---

## Production Workflow

### Weekly Process

1. **Monday AM:** GitHub Action triggers, pulls new games
2. **Monday:** Review available games, select 1–3 for report
3. **Tuesday:** Generate Tableau views, write "Why They Won" insights
4. **Wednesday:** Publish to Tableau Public, share links

### Game Selection Criteria

Priority order:
1. AP Top 25 matchups
2. Games with margin ≤5 points
3. Games with notable individual performances (30+ points, triple-double)
4. Conference rivalry games

### Quality Checks

Before publishing:
- [ ] Percentiles align with expected ranges
- [ ] Scores match official box scores
- [ ] Labels correctly assigned
- [ ] "Why They Won" makes logical sense
- [ ] All team logos render correctly
