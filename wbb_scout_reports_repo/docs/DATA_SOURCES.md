# WBB Data Sources — Quick Reference

## Primary Source: wehoop-wbb-data

**Repository:** https://github.com/sportsdataverse/wehoop-wbb-data

**Best For:** Bulk historical data, automated pipelines, reproducibility

### Data Access Patterns

**Option 1: GitHub Releases (Recommended for Portfolio)**

```python
import pandas as pd

# Base URL for parquet files
base_url = "https://github.com/sportsdataverse/wehoop-wbb-data/releases/download"

# Available datasets
datasets = {
    "team_box": f"{base_url}/wbb_team_box/wbb_team_box_{{year}}.parquet",
    "player_box": f"{base_url}/wbb_player_box/wbb_player_box_{{year}}.parquet",
    "pbp": f"{base_url}/wbb_pbp/wbb_pbp_{{year}}.parquet",
    "schedules": f"{base_url}/wbb_schedules/wbb_schedules_{{year}}.parquet",
}

# Example: Load 2024 team box scores
year = 2024
df = pd.read_parquet(datasets["team_box"].format(year=year))
```

**Option 2: Clone Repository (For Local Development)**

```bash
git clone https://github.com/sportsdataverse/wehoop-wbb-data.git
```

**Option 3: R Package (Original API)**

```r
# Install wehoop
install.packages("wehoop")
library(wehoop)

# Load team box scores
team_box <- wehoop::load_wbb_team_box(seasons = 2024)
player_box <- wehoop::load_wbb_player_box(seasons = 2024)
pbp <- wehoop::load_wbb_pbp(seasons = 2024)
```

---

## Data Availability Matrix

| Dataset | Years Available | Update Frequency | Format |
|---------|-----------------|------------------|--------|
| Team Box Scores | 2002-present | Daily (during season) | Parquet |
| Player Box Scores | 2002-present | Daily (during season) | Parquet |
| Play-by-Play | 2006-present | Daily (during season) | Parquet |
| Schedules | 2002-present | Weekly | Parquet |
| Team Rosters | 2007-present | Seasonally | Parquet |

---

## Alternative Data Sources

### HerHoopStats (herhoopstats.com)

**Best For:** Advanced metrics, shot charts, lineup data

**Access:** Subscription required ($)  
**Coverage:** NCAA WBB, WNBA  
**Unique Features:**
- Pre-computed Four Factors
- Shot chart coordinates
- Lineup efficiency data
- Player tracking metrics

**API:** Unofficial; check terms of service

---

### NCAA Stats Portal

**URL:** https://stats.ncaa.org/

**Best For:** Official verification, historical records

**Access:** Free, manual download  
**Coverage:** All NCAA sports  
**Format:** HTML tables, CSV export

**Limitations:**
- Clunky interface
- Rate limiting
- No API

---

### ESPN Hidden API

**Best For:** Quick lookups, game-by-game data

**Example Endpoints:**
```
# Game summary
https://site.api.espn.com/apis/site/v2/sports/basketball/womens-college-basketball/summary?event={game_id}

# Team schedule
https://site.api.espn.com/apis/site/v2/sports/basketball/womens-college-basketball/teams/{team_id}/schedule
```

**Limitations:**
- Unofficial, may break
- Rate limiting
- Limited historical depth

---

## Recommended Data Stack

For your portfolio project, I recommend:

| Layer | Tool | Reason |
|-------|------|--------|
| **Storage** | Local parquet files | Fast, portable, version-controlled |
| **Processing** | Python (pandas) | Flexible, reproducible |
| **Visualization** | Tableau Public | Portfolio standard, interactive |
| **Backup** | Google Sheets | Quick sharing, non-technical review |
| **Documentation** | Markdown in repo | Professional, searchable |

---

## Sample Data Pull Script

```python
"""
fetch_wbb_data.py
Fetch WBB data for a specific season and save locally.
"""
import pandas as pd
from pathlib import Path

def fetch_wbb_data(season: int, output_dir: str = "./data/raw"):
    """
    Download WBB data for a season from wehoop-wbb-data.
    
    Args:
        season: Year (e.g., 2024)
        output_dir: Directory to save files
    """
    base_url = "https://github.com/sportsdataverse/wehoop-wbb-data/releases/download"
    
    datasets = {
        "team_box": f"{base_url}/wbb_team_box/wbb_team_box_{season}.parquet",
        "player_box": f"{base_url}/wbb_player_box/wbb_player_box_{season}.parquet",
        "pbp": f"{base_url}/wbb_pbp/wbb_pbp_{season}.parquet",
    }
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    results = {}
    
    for name, url in datasets.items():
        print(f"Fetching {name}...")
        try:
            df = pd.read_parquet(url)
            output_file = output_path / f"wbb_{name}_{season}.parquet"
            df.to_parquet(output_file)
            print(f"  ✓ Saved {len(df):,} rows to {output_file}")
            results[name] = df
        except Exception as e:
            print(f"  ✗ Error: {e}")
            results[name] = None
    
    return results


if __name__ == "__main__":
    # Fetch 2024 season data
    data = fetch_wbb_data(2024)
    
    # Quick validation
    if data["team_box"] is not None:
        print(f"\nTeam box columns: {list(data['team_box'].columns)[:10]}...")
```

---

## Key Fields to Validate

When you first pull data, verify these critical fields exist:

### Team Box Score
- [ ] `game_id` — unique game identifier
- [ ] `team_id` — unique team identifier  
- [ ] `game_date` — game date
- [ ] `team_score` — points scored
- [ ] `field_goals_made/attempted` — FGM/FGA
- [ ] `three_point_field_goals_made/attempted` — 3PM/3PA
- [ ] `free_throws_made/attempted` — FTM/FTA
- [ ] `offensive_rebounds`, `defensive_rebounds` — ORB/DRB
- [ ] `assists`, `steals`, `blocks`, `turnovers` — box stats

### Player Box Score
- [ ] `athlete_id` — unique player identifier
- [ ] `athlete_display_name` — player name
- [ ] `minutes` — minutes played
- [ ] All box score stats at player level

### Play-by-Play
- [ ] `game_id` — links to box scores
- [ ] `period` — game period
- [ ] `clock_display_value` — game clock
- [ ] `type_text` — event type
- [ ] `text` — play description
- [ ] `coordinate_x`, `coordinate_y` — shot location (if available)

---

## Data Gaps & Workarounds

| Gap | Impact | Workaround |
|-----|--------|------------|
| Shot coordinates missing | No precise shot charts | Use zone inference from play text |
| Lineup stints not pre-computed | Must derive from PBP | Build lineup parser from substitution events |
| D1 benchmarks not included | No percentile context | Compute from full season data |
| Rebounding "chances" missing | Can't compute true REB% | Use team-level approximation |
| Play type tags missing | Limited shot type analysis | Use play text parsing (regex) |

---

## Next Steps

1. **Test data access locally** — Run the sample script
2. **Inspect schema** — Compare actual columns to target schema
3. **Identify gaps** — Document any missing fields
4. **Build D1 benchmarks** — Aggregate full season for percentiles
5. **Start transformation layer** — Build cleaning/metric scripts
