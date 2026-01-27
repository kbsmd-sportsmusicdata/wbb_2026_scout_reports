# WBB Scout Reports — Revised Project Outline

## Project Summary

**Name:** `wbb_2026_scout_reports`  
**Goal:** Weekly automated scouting reports demonstrating repeatable analytics systems, contextual benchmarking, and data storytelling for non-technical audiences.

**Key Deliverables:**
- Team-agnostic Tableau dashboard template
- Weekly condensed reports (1–3 games per week)
- GitHub Action for incremental data pulls
- Documented metrics and methodology

**What This Demonstrates to Employers:**
1. **Data manipulation** — Calculated/derived metrics from raw box scores
2. **Repeatable systems** — Automated pipeline producing consistent outputs
3. **Context awareness** — Benchmarks, percentiles, categorical labels
4. **Data storytelling** — Insights digestible by non-technical stakeholders

---

## Scope Decisions

| Question | Decision |
|----------|----------|
| Team focus | Team-agnostic templates (any matchup) |
| Lineup analysis | Defer to Phase 2 |
| Primary deliverable | Tableau |
| Test data | 2025 games |
| Report depth | Condensed weekly (detailed version later) |
| Games per report | 1–3 games/week |
| Game selection | Ranked matchups + close games (≤5 pt margin) |

---

## Report Content: Condensed vs. Full

### Condensed Weekly Report (Phase 1)
*Focus: Benchmarks + derived metrics + categorical labels*

**Page 1: Game Summary Dashboard**
- Team comparison table (side-by-side)
- Four Factors with percentile ranks
- Categorical labels (Elite/Great/Average/Below Average/Low)
- Game vs. Last 5 context columns
- Margin analysis: "Why Team X Won" callout

**Page 2: Key Metrics Deep Dive**
- Shooting efficiency breakdown (eFG%, TS%, 2P%, 3P%, FT%)
- Ball control metrics (TOV%, AST/TOV, Steal %)
- Rebounding advantage (OREB%, DREB%)
- Tempo context (Pace vs league avg)

**Page 3: Player Impact**
- Top performers table (USG%, TS%, Points, +/-)
- Efficiency vs. volume scatterplot
- Categorical role labels (High Usage/Efficient, etc.)

### Full Detailed Report (Phase 2 / Deep Dives)
*Everything in condensed plus:*
- Shot charts by zone (11 zones)
- Rebounding by zone
- Lineup flow tables
- Rotation timeline visualization
- Stint-level plus/minus

---

## Revised Phase Breakdown

### Phase 1: Foundation (Week 1–2) — 12 hrs

**1.1 Data Pipeline Setup**
- [ ] Set up repo structure (`wbb_2026_scout_reports/`)
- [ ] Install sportsdataverse + dependencies
- [ ] Test API access with 2025 game
- [ ] Build incremental pull script (skip existing games)
- [ ] Create tracking parquet for processed games

**1.2 Schema & Metrics Layer**
- [ ] Define canonical tables: `game_summary`, `player_game`
- [ ] Implement derived metrics:
  - Possessions: `FGA + 0.44*FTA - ORB + TOV`
  - ORtg/DRtg: `100 * PTS / Poss`
  - eFG%: `(FGM + 0.5*3PM) / FGA`
  - TS%: `PTS / (2 * (FGA + 0.44*FTA))`
  - TOV%: `TOV / Poss`
  - OREB%/DREB%: `ORB / (ORB + OppDRB)`
  - AST%: `AST / FGM`
  - FTr: `FTA / FGA`
  - 3PAr: `3PA / FGA`
- [ ] Build D1 benchmark table from season data
- [ ] Compute percentiles (national, by week)

**1.3 Categorical Labels**
- [ ] Percentile tier labels:
  - ≥90: Elite
  - 75–89: Great
  - 60–74: Above Average
  - 40–59: Average
  - 25–39: Below Average
  - <25: Low
- [ ] Role labels (High Usage, Efficient Scorer, etc.)
- [ ] Game outcome context (Close Game, Blowout, Upset)

---

### Phase 2: Tableau Build (Week 3–4) — 15 hrs

**2.1 Dashboard Structure**
- [ ] Game Summary view (team comparison table)
- [ ] Metrics breakdown view (shooting, ball control, rebounding)
- [ ] Player impact view (top performers + scatterplot)
- [ ] Filters: Game selector, Team toggle, Metric toggles

**2.2 Design Standards**
- [ ] Neutral palette with semantic highlights (positive=green, negative=red)
- [ ] Percentile color encoding (0-100 diverging scale)
- [ ] Clear visual hierarchy (title > section > chart > annotation)
- [ ] Mobile-friendly layout

**2.3 Annotations & Storytelling**
- [ ] "Why They Won" callout box
- [ ] Key stat highlights with context
- [ ] Benchmark reference lines
- [ ] Tooltip explanations for non-technical viewers

---

### Phase 3: Automation (Week 5) — 6 hrs

**3.1 Weekly Pull Script**
```
python scripts/weekly_pull.py --week 2025-01-06
```
- Pull new games from wehoop/sportsdataverse
- Skip already-processed game_ids
- Compute derived metrics
- Update benchmark tables
- Export Tableau-ready dataset

**3.2 GitHub Action Workflow**
- Scheduled: Every Monday at 6 AM EST
- Triggers: Manual dispatch option
- Steps:
  1. Install dependencies
  2. Run weekly_pull.py
  3. Commit updated data files
  4. (Optional) Notify via webhook

**3.3 Documentation**
- [ ] README with setup instructions
- [ ] Data dictionary (field definitions + sources)
- [ ] Methodology notes (formula references)
- [ ] Example outputs

---

### Phase 4: Portfolio Integration (Week 6) — 4 hrs

- [ ] Publish to Tableau Public
- [ ] Write portfolio case study (problem → approach → results)
- [ ] Create GitHub README with screenshots
- [ ] Link to future team analysis project

---

## File Structure

```
wbb_2026_scout_reports/
├── README.md
├── .github/
│   └── workflows/
│       └── weekly_pull.yml
├── data/
│   ├── raw/                    # Raw JSON/parquet from API
│   ├── processed/              # Cleaned tables
│   ├── benchmarks/             # D1 averages, percentiles
│   └── tracking/               # Games already processed
├── scripts/
│   ├── weekly_pull.py          # Main automation script
│   ├── metrics.py              # Metric calculation functions
│   ├── benchmarks.py           # Percentile computation
│   └── labels.py               # Categorical label assignment
├── notebooks/
│   ├── 01_explore_data.ipynb   # Initial exploration
│   ├── 02_build_metrics.ipynb  # Develop calculations
│   └── 03_validate.ipynb       # QA checks
├── docs/
│   ├── data_dictionary.md
│   ├── methodology.md
│   └── portfolio_writeup.md
└── tableau/
    ├── wbb_scout_condensed.twbx
    └── exports/                # Static images for portfolio
```

---

## Success Criteria

**Technical:**
- [ ] Pipeline runs without manual intervention
- [ ] Metrics match manual calculations (spot-check 5 games)
- [ ] Percentiles align with public sources (±2 percentile points)
- [ ] GitHub Action completes in <5 minutes

**Portfolio Value:**
- [ ] Non-technical viewer understands "why team won" in <30 seconds
- [ ] Demonstrates calculated fields (not just raw stats)
- [ ] Shows benchmark context for every key metric
- [ ] Code is documented and reproducible

---

## Next Steps

1. **Set up repository** — Create local folder structure
2. **Test data access** — Pull one 2025 game via sportsdataverse
3. **Build metrics module** — Implement calculation functions
4. **Create benchmark table** — Aggregate 2024-25 D1 data
5. **Prototype Tableau** — Build first dashboard with sample game

---

## Timeline

| Week | Focus | Hours |
|------|-------|-------|
| 1 | Data pipeline + schema | 6 |
| 2 | Metrics + benchmarks + labels | 6 |
| 3 | Tableau dashboard build | 8 |
| 4 | Tableau polish + annotations | 7 |
| 5 | GitHub Action + automation | 6 |
| 6 | Documentation + portfolio | 4 |
| **Total** | | **37 hrs** |

---

## Integration Notes

*In 1–2 months, this project will tie into a team analysis project. Plan for:*
- Shared D1 benchmark tables
- Consistent team_id/player_id mapping
- Reusable metrics module
- Combined Tableau data source
