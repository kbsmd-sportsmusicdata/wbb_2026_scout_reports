"""
D1 Benchmark Table Builder
==========================
Builds percentile reference tables from NCAA D1 Women's Basketball data.

DECISION: Use 2024-25 complete season data (not current 2025-26 partial season)

Rationale:
- Complete seasons provide stable baselines with all conference/tournament games
- Partial seasons have selection bias (early-season games, non-conference)
- Conference play metrics differ significantly from non-conference
- Tournament games (March) are critical for accurate elite-tier benchmarks
- Once 2025-26 completes, we'll regenerate benchmarks

Usage:
    python build_benchmarks.py                  # Build from 2024-25 data
    python build_benchmarks.py --season 2024   # Specify season
    python build_benchmarks.py --output custom_benchmarks.csv
"""

import pandas as pd
import numpy as np
import argparse
from pathlib import Path
from datetime import datetime

# ============================================================================
# CONFIGURATION
# ============================================================================

WEHOOP_BASE = "https://github.com/sportsdataverse/wehoop-wbb-data/releases/download"

# Output paths
DATA_DIR = Path("data")
BENCHMARKS_DIR = DATA_DIR / "benchmarks"
BENCHMARKS_DIR.mkdir(parents=True, exist_ok=True)

# Metrics to benchmark
TEAM_METRICS = [
    # Four Factors
    'efg_pct',      # Effective FG%
    'tov_pct',      # Turnover %
    'oreb_pct',     # Offensive Rebound %
    'ftr',          # Free Throw Rate
    
    # Shooting
    'ts_pct',       # True Shooting %
    'fg2_pct',      # 2-Point %
    'fg3_pct',      # 3-Point %
    'ft_pct',       # Free Throw %
    'fg3_rate',     # 3-Point Attempt Rate
    
    # Ball Movement
    'ast_pct',      # Assist %
    'ast_tov',      # Assist/Turnover Ratio
    
    # Ratings
    'ortg',         # Offensive Rating
    'drtg',         # Defensive Rating
    'net_rtg',      # Net Rating
    'pace',         # Pace
]

PLAYER_METRICS = [
    'ts_pct',
    'usg_pct',
    'ast_pct',
    'tov_pct',
]

# Percentile breakpoints
PERCENTILES = [5, 10, 25, 50, 75, 90, 95]


# ============================================================================
# DATA LOADING
# ============================================================================

def load_team_box(season):
    """Load team box score data from wehoop."""
    url_patterns = [
        f"{WEHOOP_BASE}/espn_womens_college_basketball_team_boxscore/team_box_{season}.parquet",
        f"{WEHOOP_BASE}/wbb_team_box/team_box_{season}.parquet",
    ]
    
    for url in url_patterns:
        try:
            print(f"Trying: {url}")
            df = pd.read_parquet(url)
            print(f"✓ Loaded {len(df)} rows")
            return df
        except Exception as e:
            print(f"  ✗ {e}")
    
    return pd.DataFrame()


def load_player_box(season):
    """Load player box score data from wehoop."""
    url_patterns = [
        f"{WEHOOP_BASE}/espn_womens_college_basketball_player_boxscore/player_box_{season}.parquet",
        f"{WEHOOP_BASE}/wbb_player_box/player_box_{season}.parquet",
    ]
    
    for url in url_patterns:
        try:
            print(f"Trying: {url}")
            df = pd.read_parquet(url)
            print(f"✓ Loaded {len(df)} rows")
            return df
        except Exception as e:
            print(f"  ✗ {e}")
    
    return pd.DataFrame()


# ============================================================================
# METRIC CALCULATIONS
# ============================================================================

def calculate_possessions(row):
    """Dean Oliver possession estimate."""
    fga = float(row.get('field_goals_attempted', 0) or 0)
    fta = float(row.get('free_throws_attempted', 0) or 0)
    orb = float(row.get('offensive_rebounds', 0) or 0)
    tov = float(row.get('turnovers', 0) or row.get('total_turnovers', 0) or 0)
    return max(fga + 0.44 * fta - orb + tov, 1)


def add_team_metrics(df):
    """Calculate derived team metrics."""
    df = df.copy()
    
    # Ensure numeric
    numeric_cols = [
        'field_goals_made', 'field_goals_attempted',
        'three_point_field_goals_made', 'three_point_field_goals_attempted',
        'free_throws_made', 'free_throws_attempted',
        'offensive_rebounds', 'defensive_rebounds',
        'assists', 'turnovers', 'total_turnovers',
        'team_score', 'opponent_team_score'
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # Shortcuts
    df['pts'] = df.get('team_score', df.get('points', 0))
    df['opp_pts'] = df.get('opponent_team_score', 0)
    df['fgm'] = df['field_goals_made']
    df['fga'] = df['field_goals_attempted']
    df['fg3m'] = df['three_point_field_goals_made']
    df['fg3a'] = df['three_point_field_goals_attempted']
    df['fg2m'] = df['fgm'] - df['fg3m']
    df['fg2a'] = df['fga'] - df['fg3a']
    df['ftm'] = df['free_throws_made']
    df['fta'] = df['free_throws_attempted']
    df['orb'] = df['offensive_rebounds']
    df['drb'] = df['defensive_rebounds']
    df['tov'] = df.get('turnovers', df.get('total_turnovers', 0))
    df['ast'] = df['assists']
    
    # Possessions
    df['poss_est'] = df.apply(calculate_possessions, axis=1)
    
    # === Calculate metrics ===
    
    # Four Factors
    df['efg_pct'] = np.where(df['fga'] > 0, (df['fgm'] + 0.5 * df['fg3m']) / df['fga'], np.nan)
    df['tov_pct'] = np.where(df['poss_est'] > 0, df['tov'] / df['poss_est'], np.nan)
    df['ftr'] = np.where(df['fga'] > 0, df['fta'] / df['fga'], np.nan)
    
    # OREB% requires opponent DRB - we'll compute game-level later
    # For now, use raw ORB
    
    # Shooting
    df['ts_pct'] = np.where(
        (df['fga'] + 0.44 * df['fta']) > 0,
        df['pts'] / (2 * (df['fga'] + 0.44 * df['fta'])),
        np.nan
    )
    df['fg2_pct'] = np.where(df['fg2a'] > 0, df['fg2m'] / df['fg2a'], np.nan)
    df['fg3_pct'] = np.where(df['fg3a'] > 0, df['fg3m'] / df['fg3a'], np.nan)
    df['ft_pct'] = np.where(df['fta'] > 0, df['ftm'] / df['fta'], np.nan)
    df['fg3_rate'] = np.where(df['fga'] > 0, df['fg3a'] / df['fga'], np.nan)
    
    # Ball movement
    df['ast_pct'] = np.where(df['fgm'] > 0, df['ast'] / df['fgm'], np.nan)
    df['ast_tov'] = np.where(df['tov'] > 0, df['ast'] / df['tov'], np.nan)
    
    # Ratings
    df['ortg'] = np.where(df['poss_est'] > 0, 100 * df['pts'] / df['poss_est'], np.nan)
    df['pace'] = df['poss_est']
    
    return df


def add_rebounding_context(df):
    """
    Add OREB% and DREB% by joining opponent data.
    Requires game_id to match teams.
    """
    if 'game_id' not in df.columns or 'team_id' not in df.columns:
        print("  Cannot compute OREB%/DREB% - missing game_id or team_id")
        return df
    
    # Create opponent lookup
    opp_data = df[['game_id', 'team_id', 'orb', 'drb']].copy()
    opp_data = opp_data.rename(columns={
        'team_id': 'opponent_team_id',
        'orb': 'opp_orb',
        'drb': 'opp_drb'
    })
    
    # For each game, there are 2 teams - need to cross-match
    # This requires knowing which team is the opponent
    
    # Simple approach: group by game, get the "other" team's rebounds
    game_groups = df.groupby('game_id')
    
    result_rows = []
    for game_id, group in game_groups:
        if len(group) != 2:
            # Skip games without exactly 2 teams
            result_rows.append(group)
            continue
        
        teams = group['team_id'].tolist()
        
        for idx, row in group.iterrows():
            row = row.copy()
            
            # Find opponent
            opp_team = [t for t in teams if t != row['team_id']]
            if opp_team:
                opp_row = group[group['team_id'] == opp_team[0]].iloc[0]
                row['opp_orb'] = opp_row['orb']
                row['opp_drb'] = opp_row['drb']
                
                # Calculate OREB% and DREB%
                if (row['orb'] + row['opp_drb']) > 0:
                    row['oreb_pct'] = row['orb'] / (row['orb'] + row['opp_drb'])
                if (row['drb'] + row['opp_orb']) > 0:
                    row['dreb_pct'] = row['drb'] / (row['drb'] + row['opp_orb'])
                
                # Calculate DRtg and Net Rtg
                opp_pts = opp_row['pts'] if 'pts' in opp_row else opp_row.get('team_score', 0)
                opp_poss = opp_row['poss_est']
                
                if opp_poss > 0:
                    row['drtg'] = 100 * opp_pts / opp_poss
                    row['net_rtg'] = row['ortg'] - row['drtg']
            
            result_rows.append(pd.DataFrame([row]))
    
    if result_rows:
        return pd.concat(result_rows, ignore_index=True)
    return df


# ============================================================================
# BENCHMARK BUILDING
# ============================================================================

def build_benchmarks(df, metrics, label="team"):
    """
    Build benchmark table with percentile breakpoints.
    """
    print(f"\n--- Building {label} benchmarks ---")
    
    rows = []
    
    for metric in metrics:
        if metric not in df.columns:
            print(f"  ⊘ {metric} not in data")
            continue
        
        values = df[metric].dropna()
        
        if len(values) < 10:
            print(f"  ⊘ {metric} has insufficient data ({len(values)} values)")
            continue
        
        row = {
            'metric': metric,
            'level': label,
            'n_observations': len(values),
            'mean': values.mean(),
            'std': values.std(),
            'min': values.min(),
            'max': values.max(),
        }
        
        for p in PERCENTILES:
            row[f'p{p}'] = np.percentile(values, p)
        
        rows.append(row)
        print(f"  ✓ {metric}: mean={row['mean']:.3f}, p50={row['p50']:.3f}")
    
    return pd.DataFrame(rows)


def generate_tier_lookup(benchmark_df):
    """
    Generate lookup table for assigning percentile tiers.
    """
    tiers = []
    
    for _, row in benchmark_df.iterrows():
        tiers.append({
            'metric': row['metric'],
            'elite_min': row['p90'],
            'great_min': row['p75'],
            'above_avg_min': row['p60'] if 'p60' in row else row['p50'],
            'avg_min': row['p40'] if 'p40' in row else row['p25'],
            'below_avg_min': row['p25'],
        })
    
    return pd.DataFrame(tiers)


# ============================================================================
# MAIN
# ============================================================================

def main(season=2024, output_path=None):
    """Build benchmark tables from specified season."""
    
    print("=" * 70)
    print(f"D1 BENCHMARK BUILDER - {season-1}-{str(season)[2:]} Season")
    print("=" * 70)
    print(f"Run Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nWhy 2024-25 (complete) vs 2025-26 (partial)?")
    print("- Complete seasons have balanced conference + non-conference games")
    print("- Includes tournament games which define 'elite' tier")
    print("- Partial seasons have early-season bias")
    print("- Will regenerate when 2025-26 completes")
    
    # Load data
    print("\n--- Loading Team Box Data ---")
    team_box = load_team_box(season)
    
    if team_box.empty:
        print("ERROR: Could not load team box data")
        print("\nTo run locally, ensure you have network access to GitHub.")
        print("Or download manually from:")
        print("  https://github.com/sportsdataverse/wehoop-wbb-data/releases")
        return
    
    # Calculate metrics
    print("\n--- Calculating Derived Metrics ---")
    team_box = add_team_metrics(team_box)
    team_box = add_rebounding_context(team_box)
    
    # Build benchmarks
    team_benchmarks = build_benchmarks(team_box, TEAM_METRICS, label="team_game")
    
    # Summary stats
    print("\n--- Season Summary ---")
    print(f"Total team-game observations: {len(team_box)}")
    print(f"Unique games: {team_box['game_id'].nunique() if 'game_id' in team_box.columns else 'N/A'}")
    print(f"Unique teams: {team_box['team_id'].nunique() if 'team_id' in team_box.columns else 'N/A'}")
    
    if 'game_date' in team_box.columns:
        print(f"Date range: {team_box['game_date'].min()} to {team_box['game_date'].max()}")
    
    # Save
    if output_path is None:
        output_path = BENCHMARKS_DIR / f'd1_benchmarks_{season}.csv'
    
    team_benchmarks.to_csv(output_path, index=False)
    print(f"\n✓ Saved benchmarks to {output_path}")
    
    # Also save as "current" for easy reference
    current_path = BENCHMARKS_DIR / 'd1_benchmarks_current.csv'
    team_benchmarks.to_csv(current_path, index=False)
    print(f"✓ Saved copy to {current_path}")
    
    # Display final table
    print("\n--- Final Benchmark Table ---")
    print(team_benchmarks.to_string(index=False))
    
    print("\n" + "=" * 70)
    print("BENCHMARK BUILD COMPLETE")
    print("=" * 70)
    
    return team_benchmarks


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Build D1 benchmark tables')
    parser.add_argument(
        '--season',
        type=int,
        default=2024,
        help='Season year (default: 2024 for 2023-24 complete season)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Output file path (default: data/benchmarks/d1_benchmarks_{season}.csv)'
    )
    
    args = parser.parse_args()
    main(season=args.season, output_path=args.output)
