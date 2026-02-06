# WBB Scout Reports

Automated weekly scouting reports for NCAA Women's Basketball, demonstrating sports analytics workflows for portfolio projects.

## Project Goals

This project showcases:
- **Data manipulation** — Calculated metrics from raw box scores
- **Repeatable systems** — Automated pipelines producing consistent outputs
- **Context awareness** — D1 benchmarks, percentiles, categorical labels
- **Data storytelling** — Insights digestible by non-technical audiences

## Report Format

### Condensed Weekly Report (3 Views)

| View | Content |
|------|---------|
| **Game Summary** | Four Factors comparison, percentile ranks, "Why They Won" callout |
| **Metrics Breakdown** | Shooting efficiency, ball control, rebounding with D1 context |
| **Player Impact** | Top performers table, efficiency vs. volume scatterplot |

### Key Metrics

| Metric | Formula | Description |
|--------|---------|-------------|
| eFG% | `(FGM + 0.5×3PM) / FGA` | Effective field goal % |
| TS% | `PTS / (2×(FGA + 0.44×FTA))` | True shooting % |
| TOV% | `TOV / Poss` | Turnover rate |
| OREB% | `ORB / (ORB + Opp_DRB)` | Offensive rebound rate |
| ORtg | `100 × PTS / Poss` | Offensive rating (per 100 poss) |
| Pace | `Poss` | Possessions per game |

## Repository Structure

```
wbb_2026_scout_reports/
├── README.md                    # This file
├── .gitignore                   # Git ignore patterns
├── requirements.txt             # Python dependencies
│
├── .github/
│   └── workflows/
│       └── weekly_pull.yml      # GitHub Action for automated pulls
│
├── data/
│   ├── raw/                     # Raw API data (JSON/parquet)
│   ├── processed/               # Tableau-ready analysis tables
│   │   ├── game_summary.csv     # Team game stats + all derived metrics
│   │   ├── player_game.csv      # Player stats + advanced metrics
│   │   └── shooting_zones.csv   # Zone-level shooting (from PBP)
│   ├── benchmarks/              # D1 reference tables
│   │   └── d1_benchmarks_current.csv
│   └── tracking/                # Processing state
│       └── processed_games.csv
│
├── scripts/
│   ├── weekly_pull.py           # Main data collection script
│   ├── test_pipeline.py         # Pipeline validation
│   ├── metrics.py               # Metric calculation functions
│   └── build_benchmarks.py      # D1 benchmark builder
│
├── notebooks/
│   ├── 01_explore_data.ipynb    # Initial data exploration
│   ├── 02_build_metrics.ipynb   # Metric development
│   └── 03_validate.ipynb        # QA checks
│
├── docs/
│   ├── data_dictionary.md       # Field definitions
│   ├── methodology.md           # Calculation references
│   └── CONDENSED_REPORT_TEMPLATE.md
│
└── tableau/
    ├── wbb_scout_condensed.twbx # Tableau workbook
    └── exports/                  # Static images for portfolio
```

## Quick Start

### 1. Clone and Install

```bash
git clone https://github.com/YOUR_USERNAME/wbb_2026_scout_reports.git
cd wbb_2026_scout_reports
pip install -r requirements.txt
```

### 2. Test the Pipeline

```bash
# Run validation with sample game
python scripts/test_pipeline.py

# Build D1 benchmarks from season data
python scripts/test_pipeline.py --build-benchmarks-only
```

### 3. Pull Weekly Data

```bash
# Pull last 7 days of games
python scripts/weekly_pull.py

# Pull from specific date
python scripts/weekly_pull.py --start-date 2025-01-06
```

### 4. Open in Tableau

1. Open `tableau/wbb_scout_condensed.twbx`
2. Connect to the Tableau-ready CSVs:
   - `data/processed/game_summary.csv` - Team game data
   - `data/processed/player_game.csv` - Player game data
   - `data/processed/shooting_zones.csv` - Zone shooting (optional)
3. Select games to analyze
4. Publish to Tableau Public

## Tableau-Ready Data

The processed CSVs include all transformations needed for analysis:

### game_summary.csv
| Category | Metrics |
|----------|---------|
| **Identifiers** | game_id, team_id, team_name, opponent_name, game_date, is_home, result |
| **Box Score** | pts, fgm, fga, fg2m, fg2a, fg3m, fg3a, ftm, fta, orb, drb, ast, stl, blk, tov |
| **Opponent Stats** | opp_pts, opp_fgm, opp_fga, opp_orb, opp_drb, opp_tov, etc. |
| **Efficiency** | efg_pct, ts_pct, fg2_pct, fg3_pct, ft_pct, fg3_rate, ftr |
| **Ratings** | ortg, drtg, net_rtg, pace, poss_est |
| **Four Factors** | efg_pct, tov_pct, oreb_pct, dreb_pct, ftr |
| **Defense** | stl_pct, blk_pct |
| **Rolling Avg** | last5_ortg, last5_drtg, last5_net_rtg, etc. |
| **Percentiles** | ortg_pctile, efg_pct_pctile, etc. (vs D1 benchmarks) |
| **Labels** | ortg_label, efg_pct_label, etc. (Elite/Great/Average/etc.) |
| **Misc Scoring** | fb_pts, paint_pts, potov (if available) |

### player_game.csv
| Category | Metrics |
|----------|---------|
| **Identifiers** | game_id, player_id, player_name, team_name, position, starter |
| **Box Score** | mp, pts, fgm, fga, fg2m, fg2a, fg3m, fg3a, ftm, fta, reb, ast, stl, blk, tov |
| **Efficiency** | efg_pct, ts_pct, fg_pct, fg3_pct, ft_pct |
| **Advanced** | usg_pct, ast_ratio, tov_pct, ast_tov, ftr, fg3_rate |
| **Per 40 Min** | pts_40, reb_40, ast_40, stl_40, blk_40, tov_40 |
| **Percentiles** | ts_pct_pctile, usg_pct_pctile, efg_pct_pctile |
| **Labels** | ts_pct_label, usg_pct_label, efg_pct_label |
| **Flags** | dnq (did not qualify, <5 min) |

## GitHub Action

The `weekly_pull.yml` workflow runs every Monday at 6 AM EST:

1. Pulls new games from wehoop/sportsdataverse
2. Calculates derived metrics
3. Updates benchmark tables
4. Commits new data files

### Manual Trigger

```bash
# Via GitHub CLI
gh workflow run weekly_pull.yml

# With custom date range
gh workflow run weekly_pull.yml -f start_date=2025-01-01
```

## Percentile Labels

| Percentile | Label | Color |
|------------|-------|-------|
| ≥90 | Elite | Dark Green |
| 75-89 | Great | Light Green |
| 60-74 | Above Average | Light Blue |
| 40-59 | Average | Gray |
| 25-39 | Below Average | Light Orange |
| <25 | Low | Red |

## Data Sources

- **Primary**: [wehoop-wbb-data](https://github.com/sportsdataverse/wehoop-wbb-data) (GitHub releases)
- **Validation**: ESPN Summary API (unofficial)
- **Benchmark**: Aggregated 2024-25 D1 season data

## Future Enhancements

- [ ] Lineup analysis module (Phase 2)
- [ ] Shot chart visualizations
- [ ] Team style analysis integration
- [ ] Predictive game modeling

## License

MIT License - feel free to use for your own portfolio projects!

---

*Built as part of a sports analytics portfolio demonstrating data engineering, visualization, and storytelling skills.*
