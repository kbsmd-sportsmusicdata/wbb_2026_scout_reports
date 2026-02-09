# NCAA D1 WBB Roster Analytics – Project Handoff & Task Tracker

This document is designed for continued work with an AI assistant (e.g., Claude/Claude Cowork) to manage tasks, run analyses, and build dashboards and presentations.

---

## 1. Project Summary

**Goal:**  
Analyze roster construction for NCAA D1 women’s basketball, starting with an exploratory analysis of AP Top 25 teams in 2025–26. Focus on age/experience, portal usage, positional balance, size, and bench depth, and how these relate to team performance (off/def efficiency, pace, margin). No predictive modeling in this phase.[web:10][web:25][web:26][web:32][web:33]

**Key deliverables:**

1. `player_season_analytic_2026` table.  
2. `team_season_analytic_2026` table.  
3. Tableau workbook(s) for Top 25 EDA.  
4. Slide deck or narrative summary of findings.

---

## 2. Current Assets & Locations

### 2.1 Repositories

- WBB scout reports repo (primary code base):  
  - `https://github.com/kbsmd-sportsmusicdata/wbb_2026_scout_reports`[file:43]

### 2.2 Data Files

- Team mapping:
  - `data/raw/2026/teams_sports_roster_data.csv` – team name, NCAA ID, conference, division, etc.[file:44]
- Team box scores:
  - `data/raw/2026/team_box_2026.parquet` – `wbb_team_box` schema (per game per team).[file:43]
- Player box scores:
  - `data/raw/2026/player_box_2026.parquet` – `wbb_player_box` schema (per game per player).[file:43]
- Roster data:
  - `wbb_rosters_2025_26.csv` (to be placed under `data/raw/2026/` or similar).
- Processed scout‑reports data (optional but useful):
  - `data/processed/game_analysis.parquet` – includes metrics like ortg, drtg, pace, etc.[file:43]

### 2.3 Documentation

- Target data schema (for scout reports, box, pbp, benchmarks):  
  - `docs/TARGET_DATA_SCHEMA.md` – contains expected schemas for `wbb_team_box`, `wbb_player_box`, `wbb_pbp`, benchmarks.[file:43]

---

## 3. Target Tables for This Project

### 3.1 `player_season_analytic_2026`

**Grain:** one row per player–season (D1 WBB, 2025–26)

**Key fields (planned):**

- Identifiers:
  - `season`
  - `team_id`
  - `team_name`
  - `athlete_id`
  - `athlete_display_name`
- Usage and stats (from player box):
  - `games_played`
  - `minutes`
  - `minutes_per_game`
  - box‑score counting stats (points, FGM/FGA, 3PM/3PA, FTM/FTA, REB, AST, STL, BLK, TOV)
- Roster attributes (from roster CSV + mapping):
  - `class_label` (FR/SO/JR/SR/GR)
  - `class_group` (FR, SO, JR, SR+)
  - `exp_level` (numeric)
  - `height_in`
  - `position_raw`, `archetype` (Guard/Wing/Big)
  - `transfer_flag`
  - `intl_flag`

### 3.2 `team_season_analytic_2026`

**Grain:** one row per team–season  

See Document 1, Section 3.2 for the full field list (identity, performance, experience, portal, positional, bench depth).

---

## 4. Workstreams & Task Lists

### 4.1 Data Ingestion & Mapping

**Objective:** Align roster, box scores, and team metadata under a consistent `team_id`.

**Tasks:**

1. **Add 2025–26 roster CSV to repo**
   - [ ] Download `wbb_rosters_2025_26.csv` from Sports‑Roster‑Data.
   - [ ] Save to `data/raw/2026/wbb_rosters_2025_26.csv`.
   - [ ] Inspect columns and note team identifier fields and player identity fields.

2. **Standardize team identifiers**
   - [ ] Confirm how `team_id` in `team_box_2026.parquet` maps to `ncaa_id`/`team` in `teams_sports_roster_data.csv`.[file:44]
   - [ ] If needed, create `team_id` ↔ `ncaa_id` mapping table and store under `data/processed/team_id_mapping_2026.csv`.
   - [ ] Verify mapping for a subset of teams (e.g., South Carolina, Iowa, LSU, UConn).

3. **Link roster teams to `team_id`**
   - [ ] Use `ncaa_id` or cleaned team names to join `wbb_rosters_2025_26.csv` to `teams_sports_roster_data.csv`.
   - [ ] Add a `team_id` column (matching box score tables) to the roster data.

### 4.2 Player‑Season Table Construction

**Objective:** Build `player_season_analytic_2026` from box and roster data.

**Tasks:**

1. **Aggregate player box to player‑season**
   - [ ] Group `player_box_2026.parquet` by `season`, `team_id`, `athlete_id`, `athlete_display_name`.
   - [ ] Compute total minutes, games played, and sum of counting stats.
   - [ ] Compute `minutes_per_game`.

2. **Join roster attributes**
   - [ ] Join aggregated player table to roster table using `team_id` + name (or a future ID link).
   - [ ] Bring in `class`, `height`, `position`, hometown, previous school.

3. **Derive flags and archetypes**
   - [ ] Derive `class_group` and `exp_level` (FR=1, SO=2, JR=3, SR+=4).
   - [ ] Derive `archetype` (Guard/Wing/Big) from position fields.
   - [ ] Derive `transfer_flag` using previous school/historical info.
   - [ ] Derive `intl_flag` using country/state fields.

4. **Export**
   - [ ] Save `data/processed/player_season_analytic_2026.parquet` and/or `.csv`.

### 4.3 Team Performance Table

**Objective:** Build a season‑level team performance table compatible with roster metrics.

**Tasks:**

1. **Leverage existing scout‑report pipeline (preferred)**
   - [ ] Confirm `game_analysis.parquet` includes ortg, drtg, net_rtg, pace for each team–game.[file:43]
   - [ ] Group by `season`, `team_id` to compute season means:
     - `games_played`, `offensive_eff`, `defensive_eff`, `margin`, `tempo`.
   - [ ] Save as `data/processed/team_performance_2026.parquet`.

2. **OR compute directly from `team_box`**
   - [ ] Derive possessions, eFG%, etc. using formulas in `TARGET_DATA_SCHEMA.md`.
   - [ ] Compute per‑game and season‑average metrics.

### 4.4 Roster Metrics & `team_season_analytic`

**Objective:** From `player_season_analytic_2026` and `team_performance_2026`, build `team_season_analytic_2026`.

**Tasks:**

1. **Experience and class shares**
   - [ ] Compute minutes‑weighted `exp_minutes_weighted`.
   - [ ] Compute `minutes_share_freshman`, `minutes_share_sophomore`, `minutes_share_junior`, `minutes_share_senior_plus`.

2. **Continuity and origin**
   - [ ] Define `returning_flag` (players who were on the same team in previous season, if data available).
   - [ ] Compute `continuity_minutes_share`.
   - [ ] Compute `minutes_share_transfer`, `minutes_share_freshmen`, `minutes_share_intl`.

3. **Positional and size profile**
   - [ ] Compute `minutes_share_guard`, `minutes_share_wing`, `minutes_share_big`.
   - [ ] Compute `avg_height_team`, `avg_height_guard`, `avg_height_wing`, `avg_height_big`.
   - [ ] Compute league‑average team height and `height_gap_vs_league`.

4. **Bench depth**
   - [ ] For each team, rank players by minutes; compute:
     - `rotation_size_10mpg`
     - `bench_minutes_share`
     - `bench_minutes_share_10mpg`

5. **Assemble final table**
   - [ ] Join roster metrics with `team_performance_2026`.
   - [ ] Join team metadata (conference, division) from `teams_sports_roster_data.csv`.
   - [ ] Save as `data/processed/team_season_analytic_2026.parquet`/`.csv`.

### 4.5 AP Top 25 Integration

**Objective:** Tag Top 25 teams and enable Top 25‑only EDA.

**Tasks:**

1. **Collect rankings**
   - [ ] Choose a poll date (e.g., late January 2026).
   - [ ] Scrape or manually enter AP Top 25 teams and ranks into `data/processed/ap_polls_2026.csv`.

2. **Standardize names and join**
   - [ ] Align poll team names with `team_season_analytic` `team_name` and/or `team_id`.
   - [ ] Add `ap_rank` and `ap_poll_date` to `team_season_analytic`.

3. **Create Top 25 subset**
   - [ ] Filter to `ap_rank <= 25` for EDA file:
     - `data/processed/team_season_analytic_2026_top25.csv`.

---

## 5. Tableau & Presentation Work

### 5.1 Tableau Data Model

**Sources to connect:**

- `team_season_analytic_2026_top25.csv` (primary for cross‑team views).
- `player_season_analytic_2026.csv` (for roster strips and per‑team deep dives).

Use folders in Tableau’s data pane:

- `Roster_Composition` – experience, class shares, continuity.
- `Roster_Size_Profile` – height metrics, positional minutes.
- `Roster_Acquisition` – transfer, freshmen, intl shares.
- `Performance_Team` – offensive_eff, defensive_eff, margin, tempo.
- `AP_Rankings` – ap_rank, ap_poll_date.

### 5.2 Core Views to Build

**Views and tasks:**

1. **Age vs Portal Scatter**
   - [ ] Build scatter: exp_minutes_weighted vs minutes_share_transfer (Top 25).
   - [ ] Color by conference, size by margin, label by ap_rank.

2. **Size & Positional Profile vs Performance**
   - [ ] Scatter: avg_height_big vs offensive_eff, color by minutes_share_big.
   - [ ] Stacked bars of positional minutes for selected teams.

3. **Bench Depth vs Success**
   - [ ] Scatter: bench_minutes_share vs margin.
   - [ ] Add reference lines and annotations for outlier teams.

4. **Per‑Team Roster View**
   - [ ] Bar chart of minutes by player with class, transfer flag, and height displayed.
   - [ ] Action filter from Top 25 scatter to this roster view.

---

## 6. Analysis & Storytelling Tasks

**Analytic questions to answer in a notebook / narrative:**

- [ ] Do Top 25 teams skew older (higher exp_minutes_weighted) than the D1 average?  
- [ ] Are Top 25 teams more portal‑heavy (minutes_share_transfer) than non‑Top 25 teams?  
- [ ] How does height by position correlate with offensive_eff and defensive_eff?  
- [ ] Are teams with deeper rotations (higher bench_minutes_share or rotation_size_10mpg) more successful (higher margin)?  
- [ ] Are there distinct “profiles” among Top 25 teams (e.g., young/high‑pace vs older/low‑pace)?

**Presentation tasks:**

- [ ] Export key Tableau views for slides (PNG/SVG).  
- [ ] Draft a 5–10 slide deck summarizing:
  - Data & methodology.
  - Roster construction patterns among Top 25.
  - Notable outlier teams.
  - Implications for recruiting/portal strategy.

---

## 7. How to Work With an AI Assistant

When using Claude/Claude Cowork:

- For **coding tasks**, paste:
  - Relevant schema snippets (from `TARGET_DATA_SCHEMA.md`).
  - Small `head()` outputs of DataFrames when debugging.
- For **analysis tasks**, ask specific questions:
  - “Given this `team_season_analytic` CSV, suggest statistical tests or plots to compare Top 25 vs non‑Top 25 on transfer minutes share.”
- For **presentation tasks**, provide:
  - Screenshots or field lists from Tableau views.
  - A rough narrative; ask for help tightening wording, headlines, and annotations.

Use this document as a living tracker: check off tasks, add new ones, and note decisions (e.g., thresholds for rotation, how transfer_flag is defined).

