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
│   ├── processed/               # Cleaned, analysis-ready tables
│   │   ├── game_analysis.parquet
│   │   └── player_game.parquet
│   ├── benchmarks/              # D1 reference tables
│   │   └── d1_benchmarks.csv
│   └── tracking/                # Processing state
│       └── processed_games.parquet
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
2. Connect to `data/processed/game_analysis.parquet`
3. Select games to analyze
4. Publish to Tableau Public

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
