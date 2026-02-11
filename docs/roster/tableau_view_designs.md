# NCAA D1 WBB Roster Analytics - Tableau View Designs

This document outlines the recommended Tableau views for analyzing roster construction among AP Top 25 teams in the 2025-26 season.

---

## Data Sources

Connect these CSVs from `data/processed/roster/`:

| File | Grain | Primary Use |
|------|-------|-------------|
| `team_season_analytic_2026_top25.csv` | Team-season | Cross-team comparisons |
| `player_season_analytic_2026_top25.csv` | Player-season | Player-level deep dives |

### Recommended Folder Organization in Tableau

```
📁 Identity
   - team_display_name, team_id, best_ap_rank, conference

📁 Performance
   - wins, losses, win_pct, ppg, opp_ppg, point_diff

📁 Experience_Profile
   - exp_minutes_weighted
   - minutes_share_freshman, minutes_share_sophomore
   - minutes_share_junior, minutes_share_senior_plus

📁 Portal_Acquisition
   - minutes_share_transfer, num_transfers_in_rotation
   - transfer_count, transfer_pct

📁 Size_Position
   - avg_height_inches, height_gap_vs_league
   - minutes_share_guard, minutes_share_wing, minutes_share_big
   - avg_height_guard, avg_height_wing, avg_height_big

📁 Bench_Depth
   - rotation_size_10mpg, bench_minutes_pct
   - total_players_used, bench_players
```

---

## View 1: Age/Experience vs Portal Usage

**Question:** Do Top 25 teams rely more on experienced rosters or portal acquisitions?

### Main Scatter Plot

| Element | Field | Notes |
|---------|-------|-------|
| **X-Axis** | `minutes_share_transfer` | % of minutes from transfers (0-100) |
| **Y-Axis** | `exp_minutes_weighted` | Minutes-weighted experience (1-5 scale) |
| **Color** | `conference` | SEC, Big Ten, ACC, etc. |
| **Size** | `point_diff` | Team success proxy |
| **Label** | `best_ap_rank` + `team_display_name` | Show rank # and team |

### Configuration
- Filter: `is_ap_top25 = True`
- Add reference lines at median for both axes
- Tooltip: Show `wins`, `losses`, `num_transfers_in_rotation`

### Quadrant Interpretation
| Quadrant | Profile | Example Teams |
|----------|---------|---------------|
| Top-Right | Experienced + Portal Heavy | Kentucky (3.53 exp, 88% transfer mins) |
| Top-Left | Experienced + Homegrown | UCLA (3.94 exp, 52% transfer) |
| Bottom-Right | Young + Portal Heavy | LSU (2.39 exp, 32% transfer) |
| Bottom-Left | Young + Homegrown | Michigan (2.14 exp, 23% transfer) |

### Companion Bar Chart
- Stacked bar of class shares by team
- Fields: `minutes_share_freshman`, `_sophomore`, `_junior`, `_senior_plus`
- Sort by `best_ap_rank`

---

## View 2: Size & Positional Profile vs Performance

**Question:** Are taller teams or specific positional mixes correlated with success?

### Main Scatter Plot

| Element | Field | Notes |
|---------|-------|-------|
| **X-Axis** | `avg_height_inches` or `height_gap_vs_league` | Team height profile |
| **Y-Axis** | `point_diff` or `ppg` | Performance measure |
| **Color** | `minutes_share_big` | % minutes to bigs |
| **Size** | `rotation_size_10mpg` | Rotation depth |
| **Label** | `team_display_name` | On hover or selected |

### Configuration
- Add trend line (linear regression)
- Reference line at league avg height (69.8")
- Tooltip: Show positional breakdown

### Companion Stacked Bar
- For each Top 25 team, show positional minutes distribution
- Fields: `minutes_share_guard`, `minutes_share_wing`, `minutes_share_big`
- Sort by `best_ap_rank`
- Color scheme: Guards (blue), Wings (green), Bigs (orange)

### Height by Position View
- Grouped bar chart showing `avg_height_guard`, `avg_height_wing`, `avg_height_big`
- Compare across teams
- Highlight teams with unusual profiles (tall guards, short bigs)

---

## View 3: Bench Depth vs Team Success

**Question:** Do deeper rotations correlate with better performance?

### Main Scatter Plot

| Element | Field | Notes |
|---------|-------|-------|
| **X-Axis** | `bench_minutes_pct` | % minutes from non-starters |
| **Y-Axis** | `point_diff` | Net points per game |
| **Color** | `rotation_size_10mpg` | Categorical (8, 9, 10, 11+) |
| **Size** | `wins` | Win count |
| **Label** | `team_display_name` | |

### Configuration
- Add trend line
- Filter: `is_ap_top25 = True`
- Tooltip: Show `total_players_used`, `bench_players`

### Companion Bullet/Bar Chart
- Horizontal bars showing `rotation_size_10mpg` by team
- Sort by `best_ap_rank`
- Color-code by success tier (win_pct bands)

### Key Insights to Extract
- Is there an optimal bench % range for Top 25 teams?
- Do teams with 8-player rotations outperform 12-player rotations?
- How does bench depth relate to portal usage?

---

## View 4: Per-Team Roster Strip (Detail View)

**Question:** What does a specific team's roster look like by minutes, class, and origin?

### Data Source
- `player_season_analytic_2026_top25.csv`
- Filter to selected `team_display_name` (action from other views)

### Main Bar Chart

| Element | Field | Notes |
|---------|-------|-------|
| **Y-Axis** | `athlete_display_name` | Sorted by `minutes` (desc) |
| **X-Axis** | `minutes` | Total season minutes |
| **Color** | `class_year` group | FR, SO, JR, SR+ |
| **Shape/Icon** | `is_transfer` | ⬆️ for transfers |

### Configuration
- Add reference line at 10 MPG threshold
- Tooltip: `height_inches`, `roster_position`, `points_per_game`, `rebounds_per_game`
- Secondary row labels: Position, Height

### Annotations
- Mark starters (top 5 by minutes) with special indicator
- Show rotation cutoff (10 MPG line)

---

## Dashboard Layout Recommendations

### Dashboard 1: "Roster Construction Overview"
```
┌─────────────────────────────────────────────────────────────┐
│  FILTERS: Conference | AP Rank Range                        │
├───────────────────────────────┬─────────────────────────────┤
│                               │                             │
│   Age/Experience vs Portal    │   Bench Depth vs Success    │
│   (Scatter)                   │   (Scatter)                 │
│                               │                             │
├───────────────────────────────┴─────────────────────────────┤
│                                                             │
│   Size & Positional Profile (Scatter + Stacked Bars)        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Dashboard 2: "Team Deep Dive"
```
┌─────────────────────────────────────────────────────────────┐
│  SELECT TEAM: [Dropdown with Top 25 teams]                  │
├─────────────────────────────────┬───────────────────────────┤
│                                 │  Team Metrics Summary     │
│   Roster Strip                  │  - Exp: X.XX              │
│   (Player bars by minutes)      │  - Transfer %: XX%        │
│                                 │  - Height Gap: +X.X"      │
│                                 │  - Rotation: XX players   │
├─────────────────────────────────┴───────────────────────────┤
│                                                             │
│   Class Distribution Pie  │  Position Mix Pie  │  Stats    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Calculated Fields for Tableau

### Experience Category
```
IF [exp_minutes_weighted] >= 3.5 THEN "Very Experienced"
ELSEIF [exp_minutes_weighted] >= 2.5 THEN "Experienced"
ELSEIF [exp_minutes_weighted] >= 1.5 THEN "Young"
ELSE "Very Young"
END
```

### Portal Reliance Category
```
IF [minutes_share_transfer] >= 50 THEN "Portal Heavy"
ELSEIF [minutes_share_transfer] >= 25 THEN "Moderate Portal"
ELSEIF [minutes_share_transfer] >= 10 THEN "Light Portal"
ELSE "Homegrown"
END
```

### Rotation Depth Category
```
IF [rotation_size_10mpg] >= 11 THEN "Deep (11+)"
ELSEIF [rotation_size_10mpg] >= 9 THEN "Standard (9-10)"
ELSE "Tight (≤8)"
END
```

### Success Tier
```
IF [point_diff] >= 30 THEN "Elite"
ELSEIF [point_diff] >= 20 THEN "Strong"
ELSEIF [point_diff] >= 10 THEN "Good"
ELSE "Below Avg"
END
```

---

## Sample Insights (Based on 2025-26 Data)

### Age vs Portal Findings
- **Kentucky** stands out with 87.6% of minutes from transfers - highest portal reliance
- **Vanderbilt** is the most "homegrown" Top 25 team (0% transfer minutes)
- **UCLA** is most experienced (3.94 minutes-weighted) but still uses portal (52%)

### Size Findings
- **UCLA** is tallest (+4.4" above league avg)
- League average height: 69.8" (5'10")
- Top 10 teams average +3.0" above league

### Bench Depth Findings
- Rotation sizes range from 8 (Kentucky) to 13 (Vanderbilt)
- Bench minutes share varies from ~25% to ~44%
- No clear linear relationship between depth and margin

---

## Next Steps

1. **Build Views**: Create each view in Tableau using the specifications above
2. **Add Interactivity**: Use dashboard actions to link scatter selections to roster strips
3. **Export for Presentation**: Generate PNG/PDF exports for slide deck
4. **Narrative Summary**: Draft 5-10 slides summarizing key findings
