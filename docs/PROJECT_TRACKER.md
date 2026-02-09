# WBB 2026 Scout Reports - Project Tracker

**Timeline:** 6 weeks • 37 hours total
**Last Updated:** 2026-02-09

---

## Overall Progress: 31/48 tasks (65%)

| Phase | Progress | Status |
|-------|----------|--------|
| Phase 1: Foundation | 17/17 (100%) | ✅ Complete |
| Phase 2: Tableau Build | 0/14 (0%) | 🟡 Ready to Start |
| Phase 3: Automation | 9/12 (75%) | 🟡 Near Complete |
| Phase 4: Portfolio | 0/5 (0%) | ⬜ Not Started |

---

## Phase 1: Foundation (Week 1-2) — 12 hrs ✅ COMPLETE

### Data Pipeline Setup

- [x] **Set Up Repository Structure** `HIGH`
  - Create wbb_2026_scout_reports/ with all subdirectories
  - _data/, scripts/, notebooks/, docs/, tableau/_

- [x] **Install sportsdataverse + Dependencies**
  - Set up Python environment with wehoop package
  - _pandas, numpy, sportsdataverse, pyarrow_

- [x] **Test API Access with 2025 Game**
  - Pull one test game from sportsdataverse to verify access
  - `data/raw/test_game.parquet`

- [x] **Build Incremental Pull Script** `HIGH`
  - Create script to skip existing games and pull new data
  - `scripts/weekly_pull.py`

- [x] **Create Tracking Parquet**
  - Track which games have been processed
  - `data/tracking/processed_games.parquet`

### Schema & Metrics Layer

- [x] **Define Canonical Tables** `HIGH`
  - Create game_summary and player_game table schemas
  - `docs/data_dictionary.md`

- [x] **Implement Possessions Formula**
  - FGA + 0.44*FTA - ORB + TOV
  - `scripts/metrics.py`
  - _Foundation for efficiency metrics_

- [x] **Implement ORtg/DRtg**
  - 100 * PTS / Poss
  - `scripts/metrics.py`

- [x] **Implement eFG% and TS%**
  - eFG = (FGM + 0.5*3PM) / FGA, TS = PTS / (2 * (FGA + 0.44*FTA))
  - `scripts/metrics.py`

- [x] **Implement TOV%**
  - TOV / Poss
  - `scripts/metrics.py`

- [x] **Implement OREB%/DREB%**
  - ORB / (ORB + OppDRB)
  - `scripts/metrics.py`

- [x] **Implement AST% and FTr**
  - AST / FGM, FTA / FGA
  - `scripts/metrics.py`

- [x] **Build D1 Benchmark Table** `HIGH`
  - Aggregate season data for percentile calculations
  - `data/benchmarks/d1_benchmarks_2025.csv`

- [x] **Compute Percentiles**
  - Calculate national and weekly percentile ranks
  - `scripts/benchmarks.py`
  - _Includes position-specific percentiles (Guard, Forward, Center)_

### Categorical Labels

- [x] **Create Percentile Tier Labels**
  - Elite (≥90), Great (75-89), Above Avg (60-74), etc.
  - `scripts/labels.py`
  - _6 tiers for categorical encoding_

- [x] **Create Player Role Labels**
  - High Usage/Efficient, Efficient Role Player, etc.
  - `scripts/labels.py`
  - _Based on USG% and TS% combinations_

- [x] **Create Game Outcome Context**
  - Close Game, Blowout, Upset, Ranked Matchup tags
  - `scripts/labels.py`

---

## Phase 2: Tableau Build (Week 3-4) — 15 hrs 🟡 READY TO START

**Data is ready!** The Tableau-ready CSVs are now available:
- `data/processed/game_summary.csv` - Team game stats with all derived metrics
- `data/processed/player_game.csv` - Player stats with advanced metrics
- `data/processed/shooting_zones.csv` - Zone-level shooting (from PBP)

### Dashboard Structure

- [ ] **Game Summary View** `HIGH`
  - Build team comparison table with Four Factors
  - _Include "Why They Won" callout box_

- [ ] **Metrics Breakdown View** `HIGH`
  - Shooting efficiency, ball control, rebounding sections
  - _Horizontal bar charts with percentile encoding_

- [ ] **Player Impact View** `HIGH`
  - Top performers table + efficiency vs volume scatterplot
  - _Role labels and categorical markers_

- [ ] **Game Selector Filter**
  - Dropdown to select which game to analyze
  - _Show game date, teams, score in selector_

- [ ] **Team Toggle Filter**
  - Switch between Team A/Team B perspective
  - _Dynamic reference lines and colors_

- [ ] **Metric Toggle Filters**
  - Show/hide specific metric categories
  - _Optional: filter by percentile threshold_

### Design Standards

- [ ] **Neutral Palette with Semantic Highlights**
  - Gray base, green for positive, red for negative
  - _Avoid team colors in data encoding_

- [ ] **Percentile Color Encoding**
  - 0-100 diverging scale (red → gray → green)
  - _Consistent across all percentile fields_

- [ ] **Clear Visual Hierarchy**
  - Title > Section > Chart > Annotation
  - _Font sizes: 24pt → 18pt → 12pt → 10pt_

- [ ] **Mobile-Friendly Layout**
  - Test on phone viewport, ensure readability
  - _Consider vertical stacking for small screens_

### Annotations & Storytelling

- [ ] **"Why They Won" Callout Box** `HIGH`
  - Auto-generated from top 3 metric differentials
  - _Rules: OREB% > TOV% > eFG% > FTr priority_

- [ ] **Key Stat Highlights**
  - Pull out standout performances (e.g., "42% OREB - Elite")
  - _Use conditional formatting for emphasis_

- [ ] **Benchmark Reference Lines**
  - Show D1 average on charts where relevant
  - _Dotted gray line with label_

- [ ] **Tooltip Explanations**
  - Define metrics for non-technical viewers
  - _Example: "eFG% weights 3-pointers appropriately"_

---

## Phase 3: Automation (Week 5) — 6 hrs 🟡 NEAR COMPLETE

### Weekly Pull Script

- [x] **Weekly Pull Script** `HIGH`
  - python scripts/weekly_pull.py --week 2025-01-06
  - `scripts/weekly_pull.py`
  - _Completely rewritten with comprehensive Tableau-ready processing_

- [x] **Skip Already-Processed Games**
  - Check processed_games.parquet, skip existing game_ids
  - _Prevent duplicate processing_

- [x] **Compute Derived Metrics**
  - Call metrics.py functions for new games
  - _All Four Factors + efficiency metrics + DRtg + Net Rtg + Rolling Averages_

- [ ] **Update Benchmark Tables**
  - Recalculate D1 percentiles with new data
  - `data/benchmarks/d1_benchmarks_2025.csv`
  - _Note: Currently uses existing benchmarks; could add auto-rebuild_

- [x] **Export Tableau-Ready Dataset** `HIGH`
  - Generate final CSV for Tableau consumption
  - `data/processed/game_summary.csv`, `player_game.csv`, `shooting_zones.csv`

### GitHub Action Workflow

- [x] **GitHub Action Schedule**
  - Cron: Every Monday at 6 AM EST (activation date: 2026-02-06)
  - `.github/workflows/weekly_pull.yml`
  - _cron: "0 11 * * 1" (6 AM EST = 11 AM UTC)_

- [x] **Manual Dispatch Option**
  - workflow_dispatch trigger for on-demand runs
  - _Useful for testing and one-off pulls_

- [x] **Complete Workflow Steps**
  - 1. Install deps 2. Run weekly_pull.py 3. Commit files
  - _Fixed permissions (contents: write), added PYTHONPATH_

### Documentation

- [x] **README with Setup Instructions** `HIGH`
  - Installation, usage, project overview
  - `README.md`
  - _Updated with Tableau-ready data documentation_

- [x] **Data Dictionary** `HIGH`
  - Field definitions + sources for all tables
  - `docs/data_dictionary.md`
  - _Comprehensive 674-line documentation with formula sources_

- [ ] **Methodology Notes**
  - Formula references, calculation explanations
  - `docs/methodology.md`
  - _Partially covered in data_dictionary.md_

- [ ] **Example Outputs**
  - Screenshots or sample CSVs
  - `docs/examples/`

---

## Phase 4: Portfolio Integration (Week 6) — 4 hrs

- [ ] **Publish to Tableau Public** `HIGH`
  - Upload dashboard with public sharing enabled
  - _Test all filters and interactions live_

- [ ] **Write Portfolio Case Study** `HIGH`
  - Problem → Approach → Results format
  - `docs/portfolio_writeup.md`
  - _1-page summary for portfolio website_

- [ ] **Create GitHub README** `HIGH`
  - Project overview, key findings, technical skills
  - _Include badges for Python, Tableau, automation_

- [ ] **Add Screenshots**
  - Dashboard views and example outputs
  - `tableau/exports/`
  - _High-res PNGs for visual appeal_

- [ ] **Link to Future Team Analysis Project**
  - Note integration path with team-focused project
  - _Shared benchmarks, metrics module, combined data source_

---

## Success Criteria

### Technical
- [x] Pipeline runs without manual intervention
- [ ] Metrics match manual calculations (spot-check 5 games)
- [ ] Percentiles align ±2 percentile points
- [ ] GitHub Action completes in <5 minutes

### Portfolio Value
- [ ] Non-technical viewer understands "why won" in <30s
- [ ] Demonstrates calculated fields (not raw stats)
- [ ] Shows benchmark context for every key metric
- [x] Code is documented and reproducible

---

## Tableau-Ready Data Summary

### game_summary.csv
| Category | Fields |
|----------|--------|
| **Identifiers** | game_id, team_id, team_name, team_abbrev, opponent_id, opponent_name, game_date, season |
| **Results** | pts, opp_pts, margin, win, result, is_home, close_game, blowout |
| **Box Score** | fgm, fga, fg2m, fg2a, fg3m, fg3a, ftm, fta, orb, drb, reb, ast, stl, blk, tov, pf |
| **Opponent Stats** | opp_fgm, opp_fga, opp_orb, opp_drb, opp_tov, opp_poss_est, etc. |
| **Efficiency** | efg_pct, ts_pct, fg_pct, fg2_pct, fg3_pct, ft_pct, fg3_rate, ftr |
| **Four Factors** | efg_pct, tov_pct, oreb_pct, dreb_pct, ftr |
| **Ratings** | ortg, drtg, net_rtg, pace, poss_est |
| **Defense** | stl_pct, blk_pct |
| **Rolling Avg** | last5_ortg, last5_drtg, last5_net_rtg, last5_efg_pct, last5_ts_pct, last5_tov_pct, last5_pace |
| **Percentiles** | efg_pct_pctile, ts_pct_pctile, tov_pct_pctile, oreb_pct_pctile, ortg_pctile, drtg_pctile, net_rtg_pctile, etc. |
| **Labels** | efg_pct_label, ts_pct_label, tov_pct_label, ortg_label, net_rtg_label, etc. |
| **Misc Scoring** | fb_pts, paint_pts, potov (if available in source data) |

### player_game.csv
| Category | Fields |
|----------|--------|
| **Identifiers** | game_id, player_id, player_name, team_id, team_name, position, starter |
| **Box Score** | mp, pts, fgm, fga, fg2m, fg2a, fg3m, fg3a, ftm, fta, orb, drb, reb, ast, stl, blk, tov, pf |
| **Efficiency** | efg_pct, ts_pct, fg_pct, fg2_pct, fg3_pct, ft_pct, fg3_rate, ftr |
| **Advanced** | usg_pct, ast_ratio, tov_pct, ast_tov |
| **Per 40 Min** | pts_40, reb_40, ast_40, stl_40, blk_40, tov_40 |
| **Percentiles** | ts_pct_pctile, usg_pct_pctile, efg_pct_pctile |
| **Labels** | ts_pct_label, usg_pct_label, efg_pct_label |
| **Flags** | dnq (did not qualify, <5 min) |

### shooting_zones.csv (from PBP)
| Category | Fields |
|----------|--------|
| **Identifiers** | game_id, team_id, zone_id, zone_name, zone_type |
| **Stats** | fgm, fga, fg_pct, fga_pct (shot distribution) |

---

## Notes

_Add session notes, blockers, and decisions here:_

### 2026-02-09
- **Major weekly_pull.py Rewrite:**
  - Added play-by-play data loading for zone shooting analysis
  - Implemented vectorized opponent stats joining (O(N) performance)
  - Added DRtg, Net Rating, OREB%, DREB% with opponent data
  - Added rolling 5-game averages (last5_ortg, last5_drtg, etc.)
  - Added per 40 minute rates for players
  - Implemented true USG% calculation using team totals
  - Added np.interp-based percentile calculations for performance
  - Added percentile labels (Elite/Great/Above Average/etc.)
  - Output files renamed: game_summary.csv, player_game.csv, shooting_zones.csv
- Fixed GitHub Actions permissions (contents: write)
- Comprehensive README update with Tableau data documentation
- **Data is now Tableau-ready!** Ready to begin Phase 2 dashboard build.

### 2026-02-01
- **Phase 1 Complete!**
- Created `scripts/metrics.py` with all metric calculations:
  - Possessions, ORtg/DRtg, eFG%, TS%, TOV%, OREB%/DREB%, AST%, FTr
- Created `scripts/benchmarks.py` with percentile functions:
  - Team benchmarks (12 metrics)
  - Player benchmarks with position-specific percentiles (Guard, Forward, Center)
- Created `scripts/labels.py` with categorical labels:
  - Percentile tiers (Elite, Great, Above Average, Average, Below Average, Low)
  - Player roles (Star, Efficient Role Player, etc.)
  - Game context (Blowout, Close Game, Upset, etc.)
- Initialized `data/tracking/processed_games.parquet`
- Built D1 benchmarks from 11,252 team-games and 164,618 player-games

### 2026-01-28
- Organized repository structure per project spec
- Built D1 benchmark table from local wehoop data (11,252 team-games)
- Validated metric calculations (eFG%, TS%) with sample games
- Created GitHub Action workflow for Monday 6 AM EST runs
- Remote wehoop URLs returning 404; using local parquet files
