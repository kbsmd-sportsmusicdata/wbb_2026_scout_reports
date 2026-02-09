# NCAA D1 WBB Roster Analytics – Project Overview

This project explores roster analytics for NCAA Division I women’s basketball, with an initial focus on exploratory analysis of AP Top 25 teams in the 2025–26 season.[web:10][web:25][web:26]

---

## 1. Conceptual Overview: Roster Analytics for NCAA D1 WBB

### 1.1 Core Questions

For this project, roster analytics focuses on:

- **Age / experience**  
  - How “old” are Top 25 rotations relative to peers? (minutes‑weighted experience, class minutes shares).[web:2]
- **Portal usage and origin**  
  - Do contenders rely more on transfers or homegrown HS recruits? (minutes from transfers, freshmen, internationals).[web:1][web:4][web:16]
- **Size and positional profile**  
  - Are Top 25 teams undersized or oversized at key positions vs the broader D1 landscape? (height by role, minutes by archetype).[web:1][web:4][web:17]
- **Bench depth and rotation**  
  - How deep are successful teams? (rotation size, bench minutes share).[web:10][web:34]
- **Performance linkage (EDA only)**  
  - How do these roster traits align with season offensive/defensive efficiency, pace, and margin?[web:10][web:32][web:33]

For this first phase, the emphasis is **descriptive and comparative EDA** (no predictive modeling yet).

---

## 2. Project Framing: AP Top 25 EDA

### 2.1 Unit of Analysis

- Primary grain: **team–season** (2025–26), filtered to teams that appear in the AP Top 25 poll for a chosen week/date.[web:25][web:26][web:29]
- Supporting grain: **player–season**, used to derive team‑level roster metrics from aggregated player stats and roster attributes.[web:1][web:4][web:17][web:42]

### 2.2 Data Sources

- **Rosters (identity, class, height, origin)**  
  - 2025–26 roster CSV from the Sports‑Roster‑Data / Derek Willis ecosystem.[web:1][web:4][web:17][web:42]
- **Team & player box scores (performance)**  
  - wehoop / ESPN‑style `wbb_team_box` and `wbb_player_box` for the 2025–26 season (parquet), already used in the WBB scout‑reports project.[file:43]
- **Team metadata & mapping**  
  - `teams_sports_roster_data.csv` with team name, NCAA ID, conference, state, and other metadata.[file:44]
- **Rankings (AP Top 25)**  
  - AP Top 25 women’s rankings from NCAA/ESPN/CBS pages.[web:25][web:26][web:27]

---

## 3. Recommended Schema – Top 25 Focus

### 3.1 `ap_polls` (Top 25 metadata)

**Grain:** one row per poll entry (team per poll date)  
**Fields:**

- `season` (int) – season year, e.g., 2026.[web:29]
- `poll_date` (date) – date of the AP poll.[web:25][web:26]
- `ap_rank` (int) – AP rank 1–25.
- `team_name_poll` (string) – name as shown in poll.
- `poll_source` (string) – “AP”.

You can standardize `team_name_poll` to your internal `team_id` via a lookup.

---

### 3.2 `team_season_analytic` (primary Tableau table)

**Grain:** one row per team–season (D1 WBB)  
**Join keys:** `season`, `team_id` (your wehoop/ESPN team ID)

#### Identity / join

- `season` (int)
- `team_id` (int or string)
- `team_name` (string) – standardized display name.
- `conference` (string) – from `teams_sports_roster_data.csv`.[file:44]
- `ap_rank` (int, nullable) – for the selected poll date.
- `ap_poll_date` (date, nullable)

#### Performance summary (from team‑level metrics)

Derived either from `team_box` or from an existing `game_analysis` / `game_summary` table that already computes ortg, drtg, pace, net rating.[file:43][web:32][web:33]

- `games_played` (int)
- `offensive_eff` (float) – season average offensive rating.
- `defensive_eff` (float)
- `margin` (float) – net rating or points per game margin.
- `tempo` (float) – possessions per game.

#### Experience and age

Computed from player‑season minutes by class.[web:2]

- `exp_minutes_weighted` (float) – minutes‑weighted experience index.
- `minutes_share_freshman` (float, 0–1)
- `minutes_share_sophomore` (float)
- `minutes_share_junior` (float)
- `minutes_share_senior_plus` (float)
- `continuity_minutes_share` (float) – share of minutes from returning players.

#### Portal / origin profile

Using flags derived from roster data.[web:1][web:4][web:16][web:17]

- `minutes_share_transfer` (float)
- `minutes_share_freshmen` (float)
- `minutes_share_intl` (float)
- `num_transfers_in_rotation` (int) – transfers playing ≥10 mpg.

#### Positional / size profile

Requires an archetype for each player (Guard/Wing/Big) and height in inches.[web:1][web:4][web:17]

- `minutes_share_guard` (float)
- `minutes_share_wing` (float)
- `minutes_share_big` (float)
- `avg_height_team` (float)
- `avg_height_guard` (float)
- `avg_height_wing` (float)
- `avg_height_big` (float)
- `height_gap_vs_league` (float) – team avg minus D1 league avg height.

#### Bench depth / rotation

Derived from player‑season minutes and games played.

- `rotation_size_10mpg` (int) – number of players with ≥10 mpg.
- `bench_minutes_share` (float) – minutes from players ranked 6+ by minutes.
- `bench_minutes_share_10mpg` (float) – minutes from bench players who also average ≥10 mpg.

---

### 3.3 `player_season_analytic`

**Grain:** one row per player–season (D1 WBB)

Key fields:

- Identifiers: `season`, `team_id`, `athlete_id`, `athlete_display_name`.[file:43]
- Usage: `games_played`, `minutes` (sum of minutes across games), `minutes_per_game`.
- Counting stats: points, FGM/FGA, 3PM/3PA, FTM/FTA, rebounds, assists, steals, blocks, turnovers.[file:43]
- Roster attributes (from Sports‑Roster‑Data + mapping): class label, numeric experience, height in inches, position, archetype (Guard/Wing/Big), transfer flag, international flag.[web:1][web:4][web:17][web:42][file:44]

This table is primarily an input to build `team_season_analytic` and to power player‑level visuals (e.g., minutes vs value).

---

## 4. Tableau Views & Outlines

### 4.1 Age vs Portal Usage (Top 25 focus)

**Grain:** team–season (`team_season_analytic`)  

View ideas:

- Scatter plot:
  - X: `minutes_share_transfer`
  - Y: `exp_minutes_weighted`
  - Color: `conference`
  - Size: `margin`
  - Label: `team_name` or `ap_rank`
- Filters:
  - AP Top 25 only (non‑null `ap_rank`).
  - Conference, season type (regular vs full season).

### 4.2 Size and Positional Profile vs Performance

**Grain:** team–season  

Views:

- Scatter: `avg_height_big` vs `offensive_eff`, color by `minutes_share_big`.
- Bar chart: for a selected team, stacked bar of `minutes_share_guard`, `minutes_share_wing`, `minutes_share_big`.
- Highlight table: `height_gap_vs_league` vs `margin`, conditioned on `ap_rank`.

### 4.3 Bench Depth vs Success

**Grain:** team–season  

Views:

- Scatter: `bench_minutes_share` vs `margin`.
- Bar: `rotation_size_10mpg` sorted by `ap_rank` (Top 25).
- Tooltip: show `bench_minutes_share_10mpg` and `minutes_share_transfer`.

### 4.4 Team Roster Strip (per‑team detail)

**Grain:** player–season (filtered to one team)  

Views:

- Horizontal bar chart:
  - X: `minutes`
  - Y: player (sorted by minutes).
  - Color: class group (FR/SO/JR/SR+).
  - Shape or label: transfer vs non‑transfer.
  - Tooltip: height, position, minutes_per_game, key per‑game stats.

---

## 5. Code / Scripts – Logical Breakdown

### 5.1 New scripts

You can add:

- `scripts/build_roster_analytics.py`  
  Purpose:
  - Load 2025–26 rosters, `teams_sports_roster_data.csv`, `player_box_2026.parquet`, `team_box_2026.parquet`.
  - Build `player_season_analytic` and `team_season_analytic`.
  - Export to `data/processed/` as CSV or parquet for Tableau.

- Optional: `scripts/build_ap_polls.py`  
  - Scrape or manually assemble AP Top 25 table for a chosen date.
  - Save as `data/processed/ap_polls_2026.csv`.

### 5.2 High‑level build order

1. **Load base tables**
   - Team mapping (`teams_sports_roster_data.csv`).
   - Team and player box (`team_box_2026.parquet`, `player_box_2026.parquet`).
   - Rosters (`wbb_rosters_2025_26.csv` copied into your repo).
2. **Normalize IDs and names**
   - Map roster teams to your `team_id` (wehoop/ESPN) via NCAA IDs or standardized names using `teams_sports_roster_data.csv`.[file:44]
3. **Build `player_season_analytic`**
   - Aggregate player box to season level.
   - Join roster attributes (class, height, origin, position → archetype).
   - Compute class groups, experience level, flags (transfer, intl), minutes share within team.
4. **Build `team_performance`**
   - Aggregate your existing game‑level metrics (ortg, drtg, net_rtg, pace) or compute from `team_box`.
   - Produce one row per team–season with performance metrics.
5. **Compute roster metrics**
   - From `player_season_analytic`, groupby `season + team_id` to compute:
     - Experience metrics.
     - Origin/portal metrics.
     - Positional minutes and height profile.
     - Bench depth metrics.
6. **Assemble `team_season_analytic`**
   - Join roster metrics + performance metrics + team metadata + AP Top 25 rankings.
7. **Export for Tableau**
   - `data/processed/player_season_analytic_2026.csv`
   - `data/processed/team_season_analytic_2026.csv`

---

## 6. Mapping & Join Strategy

### 6.1 Team Mapping

- Roster `team_name` / `ncaa_id` → `teams_sports_roster_data.ncaa_id` → `team_id` used in box scores.
- Ensure you maintain a single canonical `team_id` across all analytic tables.

### 6.2 Player Mapping

- Box scores: `athlete_id` is already stable; use it as the primary key for player‑season tables.[file:43]
- Rosters may not have `athlete_id`; use `athlete_display_name` + `team_id` for the 2025–26 season with some name cleaning, or add an ID alignment step if you choose.

---

## 7. Future Extensions

Later phases can extend this infrastructure:

- Predictive models: efficiency vs roster features, injury‑robustness, portal strategies.
- Lineup‑level models using your play‑by‑play and stint tables.
- Team style and shot profile integration (from pbp zone data).
- Integration of external rating systems (CBB Analytics, EvanMiya, etc.) as light benchmarking layers.

