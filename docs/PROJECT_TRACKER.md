# WBB 2026 Scout Reports - Project Tracker

**Timeline:** 6 weeks • 37 hours total
**Last Updated:** 2026-01-28

---

## Overall Progress: 10/48 tasks (21%)

| Phase | Progress | Status |
|-------|----------|--------|
| Phase 1: Foundation | 7/17 (41%) | 🟡 In Progress |
| Phase 2: Tableau Build | 0/14 (0%) | ⬜ Not Started |
| Phase 3: Automation | 3/12 (25%) | 🟡 In Progress |
| Phase 4: Portfolio | 0/5 (0%) | ⬜ Not Started |

---

## Phase 1: Foundation (Week 1-2) — 12 hrs

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

- [ ] **Create Tracking Parquet**
  - Track which games have been processed
  - `data/tracking/processed_games.parquet`

### Schema & Metrics Layer

- [x] **Define Canonical Tables** `HIGH`
  - Create game_summary and player_game table schemas
  - `docs/data_dictionary.md`

- [ ] **Implement Possessions Formula**
  - FGA + 0.44*FTA - ORB + TOV
  - `scripts/metrics.py`
  - _Foundation for efficiency metrics_

- [ ] **Implement ORtg/DRtg**
  - 100 * PTS / Poss
  - `scripts/metrics.py`

- [ ] **Implement eFG% and TS%**
  - eFG = (FGM + 0.5*3PM) / FGA, TS = PTS / (2 * (FGA + 0.44*FTA))
  - `scripts/metrics.py`

- [ ] **Implement TOV%**
  - TOV / Poss
  - `scripts/metrics.py`

- [ ] **Implement OREB%/DREB%**
  - ORB / (ORB + OppDRB)
  - `scripts/metrics.py`

- [ ] **Implement AST% and FTr**
  - AST / FGM, FTA / FGA
  - `scripts/metrics.py`

- [x] **Build D1 Benchmark Table** `HIGH`
  - Aggregate season data for percentile calculations
  - `data/benchmarks/d1_benchmarks_2025.csv`

- [ ] **Compute Percentiles**
  - Calculate national and weekly percentile ranks
  - `scripts/benchmarks.py`

### Categorical Labels

- [ ] **Create Percentile Tier Labels**
  - Elite (≥90), Great (75-89), Above Avg (60-74), etc.
  - `scripts/labels.py`
  - _6 tiers for categorical encoding_

- [ ] **Create Player Role Labels**
  - High Usage/Efficient, Efficient Role Player, etc.
  - `scripts/labels.py`
  - _Based on USG% and TS% combinations_

- [ ] **Create Game Outcome Context**
  - Close Game, Blowout, Upset, Ranked Matchup tags
  - `scripts/labels.py`

---

## Phase 2: Tableau Build (Week 3-4) — 15 hrs

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

## Phase 3: Automation (Week 5) — 6 hrs

### Weekly Pull Script

- [x] **Weekly Pull Script** `HIGH`
  - python scripts/weekly_pull.py --week 2025-01-06
  - `scripts/weekly_pull.py`

- [ ] **Skip Already-Processed Games**
  - Check processed_games.parquet, skip existing game_ids
  - _Prevent duplicate processing_

- [ ] **Compute Derived Metrics**
  - Call metrics.py functions for new games
  - _All Four Factors + efficiency metrics_

- [ ] **Update Benchmark Tables**
  - Recalculate D1 percentiles with new data
  - `data/benchmarks/d1_benchmarks_2025.csv`

- [ ] **Export Tableau-Ready Dataset** `HIGH`
  - Generate final CSV for Tableau consumption
  - `data/processed/tableau_export.csv`

### GitHub Action Workflow

- [x] **GitHub Action Schedule**
  - Cron: Every Monday at 6 AM EST
  - `.github/workflows/weekly_pull.yml`
  - _cron: "0 11 * * 1" (6 AM EST = 11 AM UTC)_

- [x] **Manual Dispatch Option**
  - workflow_dispatch trigger for on-demand runs
  - _Useful for testing and one-off pulls_

- [ ] **Complete Workflow Steps**
  - 1. Install deps 2. Run weekly_pull.py 3. Commit files
  - _Add optional webhook notification_

### Documentation

- [ ] **README with Setup Instructions** `HIGH`
  - Installation, usage, project overview
  - `README.md`

- [ ] **Data Dictionary** `HIGH`
  - Field definitions + sources for all tables
  - `docs/data_dictionary.md`

- [ ] **Methodology Notes**
  - Formula references, calculation explanations
  - `docs/methodology.md`

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
- [ ] Pipeline runs without manual intervention
- [ ] Metrics match manual calculations (spot-check 5 games)
- [ ] Percentiles align ±2 percentile points
- [ ] GitHub Action completes in <5 minutes

### Portfolio Value
- [ ] Non-technical viewer understands "why won" in <30s
- [ ] Demonstrates calculated fields (not raw stats)
- [ ] Shows benchmark context for every key metric
- [ ] Code is documented and reproducible

---

## Notes

_Add session notes, blockers, and decisions here:_

### 2026-01-28
- Organized repository structure per project spec
- Built D1 benchmark table from local wehoop data (11,252 team-games)
- Validated metric calculations (eFG%, TS%) with sample games
- Created GitHub Action workflow for Monday 6 AM EST runs
- Remote wehoop URLs returning 404; using local parquet files

