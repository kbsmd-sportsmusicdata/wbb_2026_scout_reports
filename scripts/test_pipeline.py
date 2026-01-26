"""
WBB Scout Reports - Pipeline Test Script
=========================================
Run this locally to test the data pipeline and validate metric calculations.

Usage:
    python test_pipeline.py                    # Test with default game
    python test_pipeline.py --game-id 401697627  # Test with specific game

This script will:
1. Pull team and player box data from wehoop
2. Calculate all derived metrics
3. Compare to ESPN source data
4. Generate validation report
"""

import pandas as pd
import numpy as np
import json
import argparse
from datetime import datetime
from pathlib import Path

# Try to import requests for API access
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    print("Note: 'requests' not installed. Install with: pip install requests")

# ============================================================================
# CONFIGURATION
# ============================================================================

# ESPN API endpoint (unofficial but public)
ESPN_SUMMARY_URL = "http://site.api.espn.com/apis/site/v2/sports/basketball/womens-college-basketball/summary"

# wehoop GitHub releases
WEHOOP_BASE = "https://github.com/sportsdataverse/wehoop-wbb-data/releases/download"

# Sample game IDs from 2024-25 season (known good games)
SAMPLE_GAMES = {
    # Format: game_id: "description"
    401697627: "2025 SEC Game - Example",
    401697584: "2025 Big Ten Game - Example", 
    401697512: "2025 ACC Game - Example",
}

# Output paths
OUTPUT_DIR = Path("test_output")
OUTPUT_DIR.mkdir(exist_ok=True)


# ============================================================================
# DATA LOADING FUNCTIONS
# ============================================================================

def load_wehoop_team_box(season=2025):
    """
    Load team box score data from wehoop releases.
    
    The wehoop repo uses this URL pattern:
    https://github.com/sportsdataverse/wehoop-wbb-data/releases/download/
    espn_womens_college_basketball_team_boxscore/team_box_{year}.parquet
    """
    # Try multiple URL patterns (wehoop has changed structure over time)
    url_patterns = [
        f"{WEHOOP_BASE}/espn_womens_college_basketball_team_boxscore/team_box_{season}.parquet",
        f"{WEHOOP_BASE}/wbb_team_box/team_box_{season}.parquet",
        f"{WEHOOP_BASE}/wbb_team_box/wbb_team_box_{season}.parquet",
    ]
    
    for url in url_patterns:
        try:
            print(f"Trying: {url}")
            df = pd.read_parquet(url)
            print(f"✓ Loaded {len(df)} rows from wehoop")
            return df
        except Exception as e:
            print(f"  ✗ Failed: {e}")
            continue
    
    print("ERROR: Could not load wehoop data from any URL pattern")
    return pd.DataFrame()


def load_wehoop_player_box(season=2025):
    """Load player box score data from wehoop releases."""
    url_patterns = [
        f"{WEHOOP_BASE}/espn_womens_college_basketball_player_boxscore/player_box_{season}.parquet",
        f"{WEHOOP_BASE}/wbb_player_box/player_box_{season}.parquet",
        f"{WEHOOP_BASE}/wbb_player_box/wbb_player_box_{season}.parquet",
    ]
    
    for url in url_patterns:
        try:
            print(f"Trying: {url}")
            df = pd.read_parquet(url)
            print(f"✓ Loaded {len(df)} rows from wehoop")
            return df
        except Exception as e:
            print(f"  ✗ Failed: {e}")
            continue
    
    return pd.DataFrame()


def fetch_espn_game(game_id):
    """
    Fetch game data directly from ESPN API for comparison.
    Returns dict with team and player box scores.
    """
    if not HAS_REQUESTS:
        print("Cannot fetch ESPN data without 'requests' package")
        return None
        
    url = f"{ESPN_SUMMARY_URL}?event={game_id}"
    print(f"Fetching ESPN data: {url}")
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # Parse team box scores
        teams = []
        if 'boxscore' in data and 'teams' in data['boxscore']:
            for team in data['boxscore']['teams']:
                team_data = {
                    'team_id': team.get('team', {}).get('id'),
                    'team_name': team.get('team', {}).get('displayName'),
                    'team_abbrev': team.get('team', {}).get('abbreviation'),
                }
                
                # Extract statistics
                for stat in team.get('statistics', []):
                    stat_name = stat.get('name', '').lower().replace(' ', '_')
                    stat_value = stat.get('displayValue', stat.get('value'))
                    team_data[stat_name] = stat_value
                
                teams.append(team_data)
        
        # Parse player box scores  
        players = []
        if 'boxscore' in data and 'players' in data['boxscore']:
            for team in data['boxscore']['players']:
                team_id = team.get('team', {}).get('id')
                team_name = team.get('team', {}).get('displayName')
                
                for stat_group in team.get('statistics', []):
                    for athlete in stat_group.get('athletes', []):
                        player_data = {
                            'athlete_id': athlete.get('athlete', {}).get('id'),
                            'athlete_name': athlete.get('athlete', {}).get('displayName'),
                            'team_id': team_id,
                            'team_name': team_name,
                            'starter': athlete.get('starter', False),
                        }
                        
                        # Extract stats
                        stat_names = stat_group.get('labels', [])
                        stat_values = athlete.get('stats', [])
                        for name, value in zip(stat_names, stat_values):
                            player_data[name.lower()] = value
                        
                        players.append(player_data)
        
        return {
            'game_id': game_id,
            'teams': pd.DataFrame(teams),
            'players': pd.DataFrame(players),
            'raw': data
        }
        
    except Exception as e:
        print(f"ERROR fetching ESPN data: {e}")
        return None


# ============================================================================
# METRIC CALCULATION FUNCTIONS
# ============================================================================

def calculate_possessions(row):
    """
    Estimate possessions using Dean Oliver formula.
    Poss = FGA + 0.44 * FTA - ORB + TOV
    """
    fga = float(row.get('field_goals_attempted', 0) or 0)
    fta = float(row.get('free_throws_attempted', 0) or 0)
    orb = float(row.get('offensive_rebounds', 0) or 0)
    tov = float(row.get('turnovers', 0) or row.get('total_turnovers', 0) or 0)
    
    poss = fga + 0.44 * fta - orb + tov
    return max(poss, 1)  # Avoid division by zero


def calculate_derived_metrics(df):
    """
    Calculate all derived metrics for team box score data.
    Returns dataframe with additional metric columns.
    """
    df = df.copy()
    
    # Ensure numeric columns
    numeric_cols = [
        'field_goals_made', 'field_goals_attempted',
        'three_point_field_goals_made', 'three_point_field_goals_attempted', 
        'free_throws_made', 'free_throws_attempted',
        'offensive_rebounds', 'defensive_rebounds', 'total_rebounds',
        'assists', 'steals', 'blocks', 'turnovers', 'total_turnovers',
        'team_score', 'points'
    ]
    
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # Shorthand columns
    df['pts'] = df.get('team_score', df.get('points', 0))
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
    
    # === FOUR FACTORS ===
    
    # Effective Field Goal % = (FGM + 0.5 * 3PM) / FGA
    df['efg_pct'] = np.where(
        df['fga'] > 0,
        (df['fgm'] + 0.5 * df['fg3m']) / df['fga'],
        0
    )
    
    # Turnover % = TOV / Poss
    df['tov_pct'] = np.where(
        df['poss_est'] > 0,
        df['tov'] / df['poss_est'],
        0
    )
    
    # Free Throw Rate = FTA / FGA
    df['ftr'] = np.where(
        df['fga'] > 0,
        df['fta'] / df['fga'],
        0
    )
    
    # === ADDITIONAL SHOOTING ===
    
    # True Shooting % = PTS / (2 * (FGA + 0.44 * FTA))
    df['ts_pct'] = np.where(
        (df['fga'] + 0.44 * df['fta']) > 0,
        df['pts'] / (2 * (df['fga'] + 0.44 * df['fta'])),
        0
    )
    
    # 2-Point %
    df['fg2_pct'] = np.where(df['fg2a'] > 0, df['fg2m'] / df['fg2a'], 0)
    
    # 3-Point %
    df['fg3_pct'] = np.where(df['fg3a'] > 0, df['fg3m'] / df['fg3a'], 0)
    
    # Free Throw %
    df['ft_pct'] = np.where(df['fta'] > 0, df['ftm'] / df['fta'], 0)
    
    # 3-Point Attempt Rate = 3PA / FGA
    df['fg3_rate'] = np.where(df['fga'] > 0, df['fg3a'] / df['fga'], 0)
    
    # === BALL MOVEMENT ===
    
    # Assist % = AST / FGM (what % of made shots were assisted)
    df['ast_pct'] = np.where(df['fgm'] > 0, df['ast'] / df['fgm'], 0)
    
    # Assist to Turnover Ratio
    df['ast_tov'] = np.where(df['tov'] > 0, df['ast'] / df['tov'], df['ast'])
    
    # === RATINGS ===
    
    # Offensive Rating = 100 * PTS / Poss
    df['ortg'] = np.where(
        df['poss_est'] > 0,
        100 * df['pts'] / df['poss_est'],
        0
    )
    
    # Pace = Possessions (per game)
    df['pace'] = df['poss_est']
    
    return df


# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================

def validate_metrics(calculated_df, espn_data):
    """
    Compare calculated metrics to ESPN source data.
    Returns validation report.
    """
    report = {
        'timestamp': datetime.now().isoformat(),
        'game_id': espn_data['game_id'] if espn_data else None,
        'checks': [],
        'passed': 0,
        'failed': 0,
    }
    
    if espn_data is None:
        report['error'] = "No ESPN data available for comparison"
        return report
    
    espn_teams = espn_data['teams']
    
    # Compare basic stats
    for idx, row in calculated_df.iterrows():
        team_id = str(row.get('team_id', ''))
        
        # Find matching ESPN row
        espn_row = espn_teams[espn_teams['team_id'].astype(str) == team_id]
        
        if espn_row.empty:
            report['checks'].append({
                'team_id': team_id,
                'status': 'SKIP',
                'reason': 'Team not found in ESPN data'
            })
            continue
        
        espn_row = espn_row.iloc[0]
        team_name = row.get('team_name', team_id)
        
        # Check key metrics
        checks = [
            ('pts', 'points'),
            ('fgm', 'field_goals_made'),
            ('fga', 'field_goals_attempted'),
            ('fg3m', 'three_point_field_goals_made'),
            ('fg3a', 'three_point_field_goals_attempted'),
            ('ftm', 'free_throws_made'),
            ('fta', 'free_throws_attempted'),
            ('orb', 'offensive_rebounds'),
            ('drb', 'defensive_rebounds'),
            ('ast', 'assists'),
            ('tov', 'turnovers'),
        ]
        
        for our_col, espn_col in checks:
            our_val = row.get(our_col, 0)
            
            # ESPN may have different column names
            espn_val = espn_row.get(espn_col, espn_row.get(our_col, None))
            
            if espn_val is not None:
                try:
                    espn_val = float(espn_val)
                    our_val = float(our_val)
                    
                    if abs(our_val - espn_val) < 0.01:
                        report['checks'].append({
                            'team': team_name,
                            'metric': our_col,
                            'our_value': our_val,
                            'espn_value': espn_val,
                            'status': 'PASS'
                        })
                        report['passed'] += 1
                    else:
                        report['checks'].append({
                            'team': team_name,
                            'metric': our_col,
                            'our_value': our_val,
                            'espn_value': espn_val,
                            'diff': our_val - espn_val,
                            'status': 'FAIL'
                        })
                        report['failed'] += 1
                except (ValueError, TypeError):
                    pass
    
    return report


def print_validation_report(report):
    """Print formatted validation report."""
    print("\n" + "=" * 70)
    print("VALIDATION REPORT")
    print("=" * 70)
    print(f"Game ID: {report.get('game_id', 'N/A')}")
    print(f"Timestamp: {report.get('timestamp', 'N/A')}")
    print(f"Passed: {report.get('passed', 0)}")
    print(f"Failed: {report.get('failed', 0)}")
    
    if report.get('error'):
        print(f"\nERROR: {report['error']}")
        return
    
    print("\n--- Check Details ---")
    
    for check in report.get('checks', []):
        status = check.get('status', 'UNKNOWN')
        
        if status == 'PASS':
            print(f"✓ {check['team']} | {check['metric']}: {check['our_value']}")
        elif status == 'FAIL':
            print(f"✗ {check['team']} | {check['metric']}: "
                  f"Ours={check['our_value']} vs ESPN={check['espn_value']} "
                  f"(diff={check['diff']:.2f})")
        elif status == 'SKIP':
            print(f"⊘ {check.get('team_id', 'Unknown')} | {check.get('reason', 'Skipped')}")


# ============================================================================
# BENCHMARK TABLE BUILDER
# ============================================================================

def build_d1_benchmarks(team_box_df, output_path=None):
    """
    Build D1 benchmark table from season data.
    Computes percentile breakpoints for key metrics.
    """
    print("\n--- Building D1 Benchmark Table ---")
    
    if team_box_df.empty:
        print("ERROR: No team box data to build benchmarks")
        return pd.DataFrame()
    
    # Calculate metrics if not already present
    if 'efg_pct' not in team_box_df.columns:
        team_box_df = calculate_derived_metrics(team_box_df)
    
    # Metrics to benchmark
    metrics = [
        'efg_pct', 'ts_pct', 'tov_pct', 'ftr', 'fg3_rate',
        'fg2_pct', 'fg3_pct', 'ft_pct', 
        'ast_pct', 'ast_tov',
        'ortg', 'pace'
    ]
    
    # Percentile breakpoints
    percentiles = [10, 25, 50, 75, 90]
    
    benchmark_rows = []
    
    for metric in metrics:
        if metric not in team_box_df.columns:
            continue
            
        values = team_box_df[metric].dropna()
        
        if len(values) == 0:
            continue
        
        row = {
            'metric': metric,
            'n_games': len(values),
            'mean': values.mean(),
            'std': values.std(),
            'min': values.min(),
            'max': values.max(),
        }
        
        for p in percentiles:
            row[f'p{p}'] = np.percentile(values, p)
        
        benchmark_rows.append(row)
    
    benchmark_df = pd.DataFrame(benchmark_rows)
    
    print(f"✓ Built benchmarks for {len(benchmark_df)} metrics")
    print(f"  Based on {team_box_df['game_id'].nunique()} unique games")
    
    # Save if path provided
    if output_path:
        benchmark_df.to_csv(output_path, index=False)
        print(f"✓ Saved to {output_path}")
    
    # Print summary
    print("\n--- Benchmark Summary ---")
    print(benchmark_df.to_string(index=False))
    
    return benchmark_df


# ============================================================================
# MAIN TEST WORKFLOW
# ============================================================================

def run_pipeline_test(game_id=None):
    """Run full pipeline test for a single game."""
    
    print("=" * 70)
    print("WBB SCOUT REPORTS - PIPELINE TEST")
    print("=" * 70)
    print(f"Run Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Use default game if not specified
    if game_id is None:
        game_id = list(SAMPLE_GAMES.keys())[0]
        print(f"Using default game: {game_id}")
    
    # Step 1: Load wehoop data
    print("\n--- Step 1: Load wehoop Team Box Data ---")
    team_box = load_wehoop_team_box(season=2025)
    
    if team_box.empty:
        # Try 2024 as fallback
        print("Trying 2024 season as fallback...")
        team_box = load_wehoop_team_box(season=2024)
    
    if team_box.empty:
        print("ERROR: Could not load any wehoop data")
        print("\nTo test locally, you can manually download data from:")
        print("  https://github.com/sportsdataverse/wehoop-wbb-data/releases")
        return
    
    # Filter to specific game
    if 'game_id' in team_box.columns:
        game_data = team_box[team_box['game_id'] == game_id]
        
        if game_data.empty:
            print(f"Game {game_id} not found. Available games: {team_box['game_id'].nunique()}")
            # Use first available game
            game_id = team_box['game_id'].iloc[0]
            game_data = team_box[team_box['game_id'] == game_id]
            print(f"Using game {game_id} instead")
    else:
        game_data = team_box.head(2)  # Assume first 2 rows are one game
    
    print(f"\nGame data shape: {game_data.shape}")
    print(f"Teams in game: {game_data['team_display_name'].tolist() if 'team_display_name' in game_data.columns else 'Unknown'}")
    
    # Step 2: Calculate derived metrics
    print("\n--- Step 2: Calculate Derived Metrics ---")
    calculated = calculate_derived_metrics(game_data)
    
    # Show calculated metrics
    metric_cols = ['efg_pct', 'ts_pct', 'tov_pct', 'ftr', 'ortg', 'pace']
    print("\nCalculated Metrics:")
    for col in metric_cols:
        if col in calculated.columns:
            print(f"  {col}: {calculated[col].tolist()}")
    
    # Step 3: Fetch ESPN data for comparison
    print("\n--- Step 3: Fetch ESPN Source Data ---")
    espn_data = fetch_espn_game(game_id)
    
    # Step 4: Validate
    print("\n--- Step 4: Validate Against ESPN ---")
    report = validate_metrics(calculated, espn_data)
    print_validation_report(report)
    
    # Step 5: Build benchmarks
    print("\n--- Step 5: Build D1 Benchmarks ---")
    benchmark_df = build_d1_benchmarks(
        team_box, 
        output_path=OUTPUT_DIR / 'd1_benchmarks.csv'
    )
    
    # Save test results
    report_path = OUTPUT_DIR / 'validation_report.json'
    with open(report_path, 'w') as f:
        # Convert non-serializable items
        json.dump(report, f, indent=2, default=str)
    print(f"\n✓ Validation report saved to {report_path}")
    
    print("\n" + "=" * 70)
    print("PIPELINE TEST COMPLETE")
    print("=" * 70)


# ============================================================================
# CLI ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Test WBB Scout Reports Pipeline')
    parser.add_argument(
        '--game-id',
        type=int,
        default=None,
        help='ESPN game ID to test (default: use sample game)'
    )
    parser.add_argument(
        '--build-benchmarks-only',
        action='store_true',
        help='Only build benchmark table, skip game validation'
    )
    
    args = parser.parse_args()
    
    if args.build_benchmarks_only:
        print("Building benchmarks only...")
        team_box = load_wehoop_team_box(2025)
        if team_box.empty:
            team_box = load_wehoop_team_box(2024)
        build_d1_benchmarks(team_box, OUTPUT_DIR / 'd1_benchmarks.csv')
    else:
        run_pipeline_test(game_id=args.game_id)
