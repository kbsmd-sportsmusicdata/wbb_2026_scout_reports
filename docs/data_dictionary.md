# Data Dictionary

## Overview

This document defines all fields in the processed data tables used for scout reports.

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

### Derived Metrics

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

### Player Metrics

| Field | Type | Formula | Description |
|-------|------|---------|-------------|
| `ts_pct` | float | `PTS / (2*(FGA + 0.44*FTA))` | True shooting % |
| `usg_pct` | float | See notes | Usage rate (% of team possessions used) |
| `ast_pct` | float | `AST / (Team_FGM - Player_FGM)` | Assist % |
| `tov_pct` | float | `TOV / (FGA + 0.44*FTA + TOV)` | Individual turnover rate |

### Player Labels

| Field | Type | Values | Description |
|-------|------|--------|-------------|
| `usg_ts_label` | str | "High Volume + Efficient" / "High Volume, Struggled" / "Efficient Role Player" / "Quiet Game" | Performance category |

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
