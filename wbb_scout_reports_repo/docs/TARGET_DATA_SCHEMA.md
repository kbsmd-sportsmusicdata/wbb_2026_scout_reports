# WBB Scout Reports — Target Data Schema

This document defines the complete data schema required to build professional-grade WBB scouting reports. Each table includes field definitions, data types, sources, and calculation notes.

---

## Schema Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                        DATA ARCHITECTURE                         │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  RAW LAYER (from wehoop-wbb-data)                               │
│  ├── team_box_raw          Game-level team stats                │
│  ├── player_box_raw        Game-level player stats              │
│  ├── pbp_raw               Play-by-play events                  │
│  └── schedule_raw          Game schedule + results              │
│                                                                  │
│  PROCESSED LAYER (analysis-ready)                               │
│  ├── game_summary          Team stats + derived metrics         │
│  ├── player_game           Player stats + advanced metrics      │
│  ├── shooting_by_zone      Spatial shooting breakdown           │
│  ├── rebounding_by_zone    Spatial rebounding breakdown         │
│  └── lineup_stints         Rotation segments + efficiency       │
│                                                                  │
│  REFERENCE LAYER (lookups + benchmarks)                         │
│  ├── ref_teams             Team name/ID mapping                 │
│  ├── ref_players           Player name/ID mapping               │
│  ├── ref_d1_benchmarks     League averages by season            │
│  └── ref_quality_tiers     Opponent strength ratings            │
│                                                                  │
│  OUTPUT LAYER (Tableau/Dashboard-ready)                         │
│  ├── viz_game_compare      Side-by-side team comparison         │
│  ├── viz_shot_chart        Zone-level shooting data             │
│  ├── viz_player_table      Player stats for sortable tables     │
│  └── viz_lineup_flow       Rotation timeline data               │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Table 1: `game_summary`

**Grain:** One row per team per game  
**Primary Key:** `game_id` + `team_id`  
**Purpose:** Core team-level statistics for game comparison dashboard

### Schema

| Field | Type | Source | Description |
|-------|------|--------|-------------|
| **Identifiers** | | | |
| `game_id` | STRING | wehoop | Unique game identifier |
| `season` | INTEGER | wehoop | Season year (e.g., 2025) |
| `game_date` | DATE | wehoop | Game date (YYYY-MM-DD) |
| `team_id` | STRING | wehoop | Team identifier |
| `team_name` | STRING | derived | Team display name |
| `team_abbrev` | STRING | derived | 3-4 letter abbreviation |
| `opponent_id` | STRING | wehoop | Opponent team identifier |
| `opponent_name` | STRING | derived | Opponent display name |
| `is_home` | BOOLEAN | wehoop | True if home team |
| `result` | STRING | derived | "W" or "L" |
| **Box Score Stats** | | | |
| `pts` | INTEGER | wehoop | Points scored |
| `fgm` | INTEGER | wehoop | Field goals made |
| `fga` | INTEGER | wehoop | Field goal attempts |
| `fg_pct` | FLOAT | wehoop | Field goal percentage |
| `fg2m` | INTEGER | wehoop | 2-point FG made |
| `fg2a` | INTEGER | wehoop | 2-point FG attempts |
| `fg2_pct` | FLOAT | derived | 2P% = fg2m / fg2a |
| `fg3m` | INTEGER | wehoop | 3-point FG made |
| `fg3a` | INTEGER | wehoop | 3-point FG attempts |
| `fg3_pct` | FLOAT | wehoop | 3-point percentage |
| `ftm` | INTEGER | wehoop | Free throws made |
| `fta` | INTEGER | wehoop | Free throw attempts |
| `ft_pct` | FLOAT | wehoop | Free throw percentage |
| `orb` | INTEGER | wehoop | Offensive rebounds |
| `drb` | INTEGER | wehoop | Defensive rebounds |
| `reb` | INTEGER | wehoop | Total rebounds |
| `ast` | INTEGER | wehoop | Assists |
| `stl` | INTEGER | wehoop | Steals |
| `blk` | INTEGER | wehoop | Blocks |
| `tov` | INTEGER | wehoop | Turnovers |
| `pf` | INTEGER | wehoop | Personal fouls |
| **Opponent Box Stats** | | | |
| `opp_pts` | INTEGER | wehoop | Opponent points |
| `opp_fgm` | INTEGER | wehoop | Opponent FG made |
| `opp_fga` | INTEGER | wehoop | Opponent FG attempts |
| `opp_orb` | INTEGER | wehoop | Opponent offensive rebounds |
| `opp_drb` | INTEGER | wehoop | Opponent defensive rebounds |
| `opp_tov` | INTEGER | wehoop | Opponent turnovers |
| **Derived Metrics** | | | |
| `poss_est` | FLOAT | calc | FGA + 0.44×FTA − ORB + TOV |
| `opp_poss_est` | FLOAT | calc | Opponent possessions |
| `pace` | FLOAT | calc | Possessions per 40 min |
| `ortg` | FLOAT | calc | 100 × PTS / poss_est |
| `drtg` | FLOAT | calc | 100 × opp_pts / opp_poss_est |
| `net_rtg` | FLOAT | calc | ortg − drtg |
| `efg_pct` | FLOAT | calc | (FGM + 0.5×3PM) / FGA |
| `ts_pct` | FLOAT | calc | PTS / (2×(FGA + 0.44×FTA)) |
| `tov_pct` | FLOAT | calc | TOV / poss_est |
| `oreb_pct` | FLOAT | calc | ORB / (ORB + opp_DRB) |
| `dreb_pct` | FLOAT | calc | DRB / (DRB + opp_ORB) |
| `ftr` | FLOAT | calc | FTA / FGA |
| `fg3_rate` | FLOAT | calc | 3PA / FGA |
| `ast_pct` | FLOAT | calc | AST / FGM |
| `ast_tov_ratio` | FLOAT | calc | AST / TOV |
| `stl_pct` | FLOAT | calc | STL / opp_poss_est |
| `blk_pct` | FLOAT | calc | BLK / opp_fga (2PA only ideally) |
| **Misc Scoring** | | | |
| `fb_pts` | INTEGER | wehoop/pbp | Fast break points |
| `paint_pts` | INTEGER | wehoop/pbp | Points in the paint |
| `second_pts` | INTEGER | wehoop/pbp | Second chance points |
| `potov` | INTEGER | wehoop/pbp | Points off turnovers |
| `bench_pts` | INTEGER | wehoop/pbp | Bench points |
| **Context Fields** | | | |
| `last5_ortg` | FLOAT | calc | Rolling 5-game offensive rating |
| `last5_drtg` | FLOAT | calc | Rolling 5-game defensive rating |
| `last5_net_rtg` | FLOAT | calc | Rolling 5-game net rating |
| **Percentiles** | | | |
| `ortg_pctile` | INTEGER | calc | 0-100 vs D1 (season) |
| `drtg_pctile` | INTEGER | calc | 0-100 vs D1 (inverted, lower=better) |
| `net_rtg_pctile` | INTEGER | calc | 0-100 vs D1 |
| `efg_pctile` | INTEGER | calc | 0-100 vs D1 |
| `tov_pctile` | INTEGER | calc | 0-100 vs D1 (inverted) |
| `oreb_pctile` | INTEGER | calc | 0-100 vs D1 |
| `ftr_pctile` | INTEGER | calc | 0-100 vs D1 |

### Percentile Labels

| Percentile | Label |
|------------|-------|
| ≥ 90 | Elite |
| 75-89 | Great |
| 60-74 | Above Average |
| 40-59 | Average |
| 25-39 | Below Average |
| < 25 | Low |

---

## Table 2: `player_game`

**Grain:** One row per player per game  
**Primary Key:** `game_id` + `player_id`  
**Purpose:** Player-level statistics for box score and advanced metrics tables

### Schema

| Field | Type | Source | Description |
|-------|------|--------|-------------|
| **Identifiers** | | | |
| `game_id` | STRING | wehoop | Unique game identifier |
| `player_id` | STRING | wehoop | Unique player identifier |
| `player_name` | STRING | wehoop | Player display name |
| `team_id` | STRING | wehoop | Team identifier |
| `team_name` | STRING | derived | Team display name |
| `position` | STRING | wehoop | Position (G, F, C or PG, SG, SF, PF, C) |
| `starter` | BOOLEAN | wehoop | True if started game |
| **Traditional Box Score** | | | |
| `mp` | INTEGER | wehoop | Minutes played |
| `pts` | INTEGER | wehoop | Points |
| `fgm` | INTEGER | wehoop | Field goals made |
| `fga` | INTEGER | wehoop | Field goal attempts |
| `fg_pct` | FLOAT | wehoop | Field goal % |
| `fg2m` | INTEGER | wehoop | 2-point FG made |
| `fg2a` | INTEGER | wehoop | 2-point FG attempts |
| `fg2_pct` | FLOAT | calc | 2P% |
| `fg3m` | INTEGER | wehoop | 3-point FG made |
| `fg3a` | INTEGER | wehoop | 3-point FG attempts |
| `fg3_pct` | FLOAT | wehoop | 3P% |
| `ftm` | INTEGER | wehoop | Free throws made |
| `fta` | INTEGER | wehoop | Free throw attempts |
| `ft_pct` | FLOAT | wehoop | FT% |
| `orb` | INTEGER | wehoop | Offensive rebounds |
| `drb` | INTEGER | wehoop | Defensive rebounds |
| `reb` | INTEGER | wehoop | Total rebounds |
| `ast` | INTEGER | wehoop | Assists |
| `stl` | INTEGER | wehoop | Steals |
| `blk` | INTEGER | wehoop | Blocks |
| `tov` | INTEGER | wehoop | Turnovers |
| `pf` | INTEGER | wehoop | Personal fouls |
| **Advanced Metrics** | | | |
| `usg_pct` | FLOAT | calc | Usage rate |
| `ts_pct` | FLOAT | calc | True shooting % |
| `efg_pct` | FLOAT | calc | Effective FG% |
| `ast_pct` | FLOAT | calc | Assist % (team FGM assisted by player) |
| `ast_ratio` | FLOAT | calc | AST / (FGA + 0.44×FTA + TOV) |
| `tov_pct` | FLOAT | calc | TOV / (FGA + 0.44×FTA + TOV) |
| `ast_tov` | FLOAT | calc | AST / TOV ratio |
| `orb_pct` | FLOAT | calc | Offensive rebound % |
| `drb_pct` | FLOAT | calc | Defensive rebound % |
| `ftr` | FLOAT | calc | FTA / FGA |
| `fg3_rate` | FLOAT | calc | 3PA / FGA |
| **Per 40 Min Rates** | | | |
| `pts_40` | FLOAT | calc | Points per 40 minutes |
| `reb_40` | FLOAT | calc | Rebounds per 40 minutes |
| `ast_40` | FLOAT | calc | Assists per 40 minutes |
| `stl_40` | FLOAT | calc | Steals per 40 minutes |
| `blk_40` | FLOAT | calc | Blocks per 40 minutes |
| **Percentiles** | | | |
| `ts_pctile` | INTEGER | calc | 0-100 vs D1 players |
| `usg_pctile` | INTEGER | calc | 0-100 vs D1 players |
| `ast_pctile` | INTEGER | calc | 0-100 vs D1 players |
| **Flags** | | | |
| `dnq` | BOOLEAN | calc | Did not qualify (< min threshold) |

---

## Table 3: `shooting_by_zone`

**Grain:** One row per zone per team per game  
**Primary Key:** `game_id` + `team_id` + `zone_id`  
**Purpose:** Spatial shooting breakdown for shot chart visualizations

### Court Zones (11 standard zones)

| zone_id | zone_name | Zone Type |
|---------|-----------|-----------|
| 1 | At The Rim | Paint |
| 2 | In The Paint | Paint |
| 3 | Left Baseline 2s | Midrange |
| 4 | Right Baseline 2s | Midrange |
| 5 | Left Elbow 2s | Midrange |
| 6 | Right Elbow 2s | Midrange |
| 7 | Left Corner 3s | 3PT |
| 8 | Right Corner 3s | 3PT |
| 9 | Left Wing 3s | 3PT |
| 10 | Right Wing 3s | 3PT |
| 11 | Top of Key 3s | 3PT |

### Schema

| Field | Type | Source | Description |
|-------|------|--------|-------------|
| `game_id` | STRING | wehoop | Unique game identifier |
| `team_id` | STRING | wehoop | Team identifier |
| `zone_id` | INTEGER | derived | Zone identifier (1-11) |
| `zone_name` | STRING | derived | Zone display name |
| `zone_type` | STRING | derived | "Paint", "Midrange", "3PT" |
| `fgm` | INTEGER | pbp | Field goals made in zone |
| `fga` | INTEGER | pbp | Field goal attempts in zone |
| `fg_pct` | FLOAT | calc | FGM / FGA |
| `fga_pct` | FLOAT | calc | Share of total FGA |
| `fg_pctile` | INTEGER | calc | FG% vs D1 avg for zone |
| `fga_pctile` | INTEGER | calc | FGA% vs D1 avg for zone |
| `d1_avg_fg_pct` | FLOAT | ref | D1 average FG% for this zone |

---

## Table 4: `rebounding_by_zone`

**Grain:** One row per zone per team per game  
**Primary Key:** `game_id` + `team_id` + `reb_zone_id`  
**Purpose:** Spatial rebounding breakdown

### Rebounding Zones (5 zones)

| reb_zone_id | zone_name |
|-------------|-----------|
| 1 | At The Rim |
| 2 | In The Paint |
| 3 | Mid Range 2s |
| 4 | Above Break 3s |
| 5 | Corner 3s |

### Schema

| Field | Type | Source | Description |
|-------|------|--------|-------------|
| `game_id` | STRING | wehoop | Unique game identifier |
| `team_id` | STRING | wehoop | Team identifier |
| `reb_zone_id` | INTEGER | derived | Zone identifier (1-5) |
| `zone_name` | STRING | derived | Zone display name |
| `orb` | INTEGER | pbp | Offensive rebounds |
| `orb_chances` | INTEGER | pbp | Offensive rebound opportunities |
| `orb_pct` | FLOAT | calc | ORB / ORB_CHANCES |
| `orb_pctile` | INTEGER | calc | vs D1 avg |
| `drb` | INTEGER | pbp | Defensive rebounds |
| `drb_chances` | INTEGER | pbp | Defensive rebound opportunities |
| `drb_pct` | FLOAT | calc | DRB / DRB_CHANCES |
| `drb_pctile` | INTEGER | calc | vs D1 avg |

---

## Table 5: `lineup_stints`

**Grain:** One row per rotation segment per team per game  
**Primary Key:** `game_id` + `team_id` + `stint_num`  
**Purpose:** Lineup flow table and rotation timeline

### Schema

| Field | Type | Source | Description |
|-------|------|--------|-------------|
| **Identifiers** | | | |
| `game_id` | STRING | wehoop | Unique game identifier |
| `team_id` | STRING | wehoop | Team identifier |
| `stint_num` | INTEGER | derived | Sequential stint number |
| **Lineup** | | | |
| `player_1_id` | STRING | pbp | Player 1 ID |
| `player_1_name` | STRING | derived | Player 1 display name |
| `player_2_id` | STRING | pbp | Player 2 ID |
| `player_2_name` | STRING | derived | Player 2 display name |
| `player_3_id` | STRING | pbp | Player 3 ID |
| `player_3_name` | STRING | derived | Player 3 display name |
| `player_4_id` | STRING | pbp | Player 4 ID |
| `player_4_name` | STRING | derived | Player 4 display name |
| `player_5_id` | STRING | pbp | Player 5 ID |
| `player_5_name` | STRING | derived | Player 5 display name |
| `lineup_key` | STRING | derived | Sorted player IDs concatenated |
| **Time** | | | |
| `period` | INTEGER | pbp | Game period (1-4, OT=5+) |
| `start_time` | STRING | pbp | Period start time (MM:SS) |
| `end_time` | STRING | pbp | Period end time (MM:SS) |
| `duration_sec` | INTEGER | calc | Stint duration in seconds |
| `duration_display` | STRING | calc | Duration as MM:SS |
| **Offense** | | | |
| `pts_for` | INTEGER | pbp | Points scored during stint |
| `poss_for` | FLOAT | pbp | Possessions during stint |
| `ppp_for` | FLOAT | calc | Points per possession |
| `fga_for` | INTEGER | pbp | FG attempts |
| `fg2m_for` | INTEGER | pbp | 2PT FGM |
| `fg2a_for` | INTEGER | pbp | 2PT FGA |
| `fg3m_for` | INTEGER | pbp | 3PT FGM |
| `fg3a_for` | INTEGER | pbp | 3PT FGA |
| `ast_for` | INTEGER | pbp | Assists |
| `tov_for` | INTEGER | pbp | Turnovers |
| **Defense** | | | |
| `pts_against` | INTEGER | pbp | Points allowed during stint |
| `poss_against` | FLOAT | pbp | Opponent possessions |
| `ppp_against` | FLOAT | calc | Opp points per possession |
| **Other** | | | |
| `reb_for` | INTEGER | pbp | Total rebounds |
| `stl_for` | INTEGER | pbp | Steals |
| **Plus/Minus** | | | |
| `plus_minus` | INTEGER | calc | pts_for − pts_against |
| `net_ppp` | FLOAT | calc | ppp_for − ppp_against |

---

## Table 6: `ref_d1_benchmarks`

**Grain:** One row per metric per season  
**Primary Key:** `season` + `metric_id`  
**Purpose:** League averages for percentile calculations

### Schema

| Field | Type | Source | Description |
|-------|------|--------|-------------|
| `season` | INTEGER | derived | Season year |
| `metric_id` | STRING | derived | Metric identifier |
| `metric_name` | STRING | derived | Display name |
| `d1_mean` | FLOAT | calc | D1 average |
| `d1_median` | FLOAT | calc | D1 median |
| `d1_std` | FLOAT | calc | D1 standard deviation |
| `d1_p10` | FLOAT | calc | 10th percentile |
| `d1_p25` | FLOAT | calc | 25th percentile |
| `d1_p50` | FLOAT | calc | 50th percentile |
| `d1_p75` | FLOAT | calc | 75th percentile |
| `d1_p90` | FLOAT | calc | 90th percentile |
| `updated_at` | DATETIME | system | Last update timestamp |

### Metrics to Benchmark

- `ortg`, `drtg`, `net_rtg`, `pace`
- `efg_pct`, `ts_pct`, `fg_pct`, `fg3_pct`, `ft_pct`
- `tov_pct`, `oreb_pct`, `dreb_pct`, `ftr`, `fg3_rate`
- `ast_pct`, `stl_pct`, `blk_pct`
- Zone-specific FG% (11 zones)

---

## wehoop-wbb-data Source Schema

### Expected Columns: `wbb_team_box`

Based on sportsdataverse/wehoop-wbb-data format:

| Column | Type | Notes |
|--------|------|-------|
| `game_id` | int64 | Unique game identifier |
| `season` | int64 | Season year |
| `season_type` | int64 | 2=regular, 3=postseason |
| `game_date` | datetime | Game date |
| `team_id` | int64 | Team ID |
| `team_display_name` | string | Full team name |
| `team_abbreviation` | string | Team abbreviation |
| `team_home_away` | string | "home" or "away" |
| `team_winner` | bool | True if team won |
| `team_score` | int64 | Team final score |
| `opponent_team_id` | int64 | Opponent ID |
| `opponent_team_score` | int64 | Opponent score |
| `field_goals_made` | int64 | FGM |
| `field_goals_attempted` | int64 | FGA |
| `field_goal_pct` | float64 | FG% |
| `three_point_field_goals_made` | int64 | 3PM |
| `three_point_field_goals_attempted` | int64 | 3PA |
| `three_point_field_goal_pct` | float64 | 3P% |
| `free_throws_made` | int64 | FTM |
| `free_throws_attempted` | int64 | FTA |
| `free_throw_pct` | float64 | FT% |
| `offensive_rebounds` | int64 | ORB |
| `defensive_rebounds` | int64 | DRB |
| `total_rebounds` | int64 | REB |
| `assists` | int64 | AST |
| `steals` | int64 | STL |
| `blocks` | int64 | BLK |
| `turnovers` | int64 | TOV |
| `fouls` | int64 | PF |
| `fast_break_points` | int64 | FB points |
| `points_in_paint` | int64 | Paint points |
| `turnovers_points` | int64 | Points off TOV |
| `largest_lead` | int64 | Largest lead |

### Expected Columns: `wbb_player_box`

Similar structure with player-level granularity:
- `athlete_id`, `athlete_display_name`, `athlete_position_abbreviation`
- All box score stats per player
- `starter` flag, `minutes` played

### Expected Columns: `wbb_pbp`

Play-by-play event log:
- `game_id`, `period`, `clock_display_value`
- `type_text` (event type: shot, rebound, turnover, etc.)
- `text` (play description)
- `scoring_play`, `score_value`
- `coordinate_x`, `coordinate_y` (shot location - may be limited)
- `athlete_id_1`, `athlete_id_2` (players involved)

---

## Data Transformation Checklist

When processing raw data to analysis-ready format:

- [ ] Rename columns to snake_case standard
- [ ] Map team IDs to consistent display names
- [ ] Map player IDs to consistent display names
- [ ] Compute 2PT stats from FG stats minus 3PT stats
- [ ] Compute possession estimates using Dean Oliver formula
- [ ] Compute all rate metrics (per 100 poss, per 40 min)
- [ ] Join opponent stats for comparison
- [ ] Compute rolling averages (last 5 games)
- [ ] Compute percentiles against D1 benchmarks
- [ ] Derive lineup stints from PBP substitution events
- [ ] Derive zone shooting from PBP shot locations
- [ ] Add percentile labels (Elite, Great, Average, etc.)
- [ ] Validate all calculated metrics against known games

---

## Notes & Caveats

1. **Shot Location Data**: wehoop may have limited coordinate data; zone aggregations may need to be derived from play descriptions rather than exact coordinates.

2. **Lineup Stints**: Must be derived from play-by-play substitution events; requires careful handling of period boundaries and dead balls.

3. **Rebounding Chances**: This advanced metric requires tracking missed shots and subsequent rebound opportunities; may need proxy calculation.

4. **D1 Benchmarks**: Need to build these from season data; should update weekly during season.

5. **Data Freshness**: wehoop-wbb-data typically updates 1-2 days after games; account for this in weekly workflow.
