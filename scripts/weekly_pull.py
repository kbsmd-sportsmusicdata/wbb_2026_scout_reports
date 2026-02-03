"""
Weekly WBB Data Pull Script
Pulls new game data from wehoop/sportsdataverse, skipping already-processed games.
Computes derived metrics and updates benchmark tables.

Usage:
    python weekly_pull.py                          # Pull last 7 days
    python weekly_pull.py --start-date 2025-01-01  # Pull from specific date
    python weekly_pull.py --force-refresh true     # Re-pull all games in range
"""

import argparse
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import json
import warnings

warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURATION
# ============================================================================

# Data paths
DATA_DIR = Path("data")
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
BENCHMARKS_DIR = DATA_DIR / "benchmarks"
TRACKING_DIR = DATA_DIR / "tracking"

# Create directories if they don't exist
for dir_path in [RAW_DIR, PROCESSED_DIR, BENCHMARKS_DIR, TRACKING_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# Tracking file for processed games
PROCESSED_GAMES_FILE = TRACKING_DIR / "processed_games.parquet"
PULL_LOG_FILE = TRACKING_DIR / "pull_log.txt"

# wehoop data URLs
WEHOOP_BASE = "https://github.com/sportsdataverse/wehoop-wbb-data/releases/download"

# Current season (update annually)
CURRENT_SEASON = 2025


# ============================================================================
# DATA LOADING FUNCTIONS
# ============================================================================

def load_processed_games():
    """Load list of already-processed game IDs."""
    if PROCESSED_GAMES_FILE.exists():
        df = pd.read_parquet(PROCESSED_GAMES_FILE)
        return set(df['game_id'].tolist())
    return set()


def save_processed_games(game_ids):
    """Save updated list of processed game IDs."""
    df = pd.DataFrame({'game_id': list(game_ids)})
    df.to_parquet(PROCESSED_GAMES_FILE, index=False)


def load_team_box_data(season):
    """Load team box score data from wehoop releases or local fallback."""
    # Try remote URLs first
    url_patterns = [
        f"{WEHOOP_BASE}/wbb_team_box/wbb_team_box_{season}.parquet",
        f"{WEHOOP_BASE}/wbb_team_box/team_box_{season}.parquet",
    ]

    for url in url_patterns:
        print(f"Trying remote: {url}")
        try:
            df = pd.read_parquet(url)
            print(f"  ✓ Loaded {len(df)} team-game rows from remote")
            return df
        except Exception as e:
            print(f"  ✗ Remote failed: {e}")

    # Fall back to local files
    local_patterns = [
        RAW_DIR / f"team_box_{season}.parquet",
        RAW_DIR / f"wbb_team_box_{season}.parquet",
    ]

    for local_path in local_patterns:
        print(f"Trying local: {local_path}")
        if local_path.exists():
            try:
                df = pd.read_parquet(local_path)
                print(f"  ✓ Loaded {len(df)} team-game rows from local")
                return df
            except Exception as e:
                print(f"  ✗ Local failed: {e}")

    print("  ERROR: No team box data available (remote or local)")
    return pd.DataFrame()


def load_player_box_data(season):
    """Load player box score data from wehoop releases or local fallback."""
    # Try remote URLs first
    url_patterns = [
        f"{WEHOOP_BASE}/wbb_player_box/wbb_player_box_{season}.parquet",
        f"{WEHOOP_BASE}/wbb_player_box/player_box_{season}.parquet",
    ]

    for url in url_patterns:
        print(f"Trying remote: {url}")
        try:
            df = pd.read_parquet(url)
            print(f"  ✓ Loaded {len(df)} player-game rows from remote")
            return df
        except Exception as e:
            print(f"  ✗ Remote failed: {e}")

    # Fall back to local files
    local_patterns = [
        RAW_DIR / f"player_box_{season}.parquet",
        RAW_DIR / f"wbb_player_box_{season}.parquet",
    ]

    for local_path in local_patterns:
        print(f"Trying local: {local_path}")
        if local_path.exists():
            try:
                df = pd.read_parquet(local_path)
                print(f"  ✓ Loaded {len(df)} player-game rows from local")
                return df
            except Exception as e:
                print(f"  ✗ Local failed: {e}")

    print("  WARNING: No player box data available (remote or local)")
    return pd.DataFrame()


def load_schedule_data(season):
    """Load schedule data to get game metadata."""
    url = f"{WEHOOP_BASE}/wbb_schedule/wbb_schedule_{season}.parquet"
    print(f"Loading schedule from: {url}")
    
    try:
        df = pd.read_parquet(url)
        print(f"  Loaded {len(df)} scheduled games")
        return df
    except Exception as e:
        print(f"  ERROR loading schedule: {e}")
        return pd.DataFrame()


# ============================================================================
# METRIC CALCULATION FUNCTIONS
# ============================================================================

def calculate_possessions(row):
    """
    Estimate possessions using Dean Oliver formula.
    Poss = FGA + 0.44 * FTA - ORB + TOV
    """
    fga = row.get('field_goals_attempted', 0) or 0
    fta = row.get('free_throws_attempted', 0) or 0
    orb = row.get('offensive_rebounds', 0) or 0
    tov = row.get('turnovers', 0) or row.get('total_turnovers', 0) or 0
    
    return fga + 0.44 * fta - orb + tov


def calculate_team_metrics(df):
    """
    Add derived metrics to team box score data.
    Expects one row per team per game.
    """
    print("Calculating team metrics...")
    
    # Make a copy to avoid modifying original
    df = df.copy()
    
    # Ensure numeric types
    numeric_cols = ['field_goals_made', 'field_goals_attempted', 
                    'three_point_field_goals_made', 'three_point_field_goals_attempted',
                    'free_throws_made', 'free_throws_attempted',
                    'offensive_rebounds', 'defensive_rebounds', 'total_rebounds',
                    'assists', 'steals', 'blocks', 'turnovers', 'total_turnovers',
                    'team_score', 'opponent_team_score']
    
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # Calculate possessions
    df['poss_est'] = df.apply(calculate_possessions, axis=1)
    df['poss_est'] = df['poss_est'].clip(lower=1)  # Avoid division by zero
    
    # Points
    df['pts'] = df.get('team_score', df.get('points', 0))
    df['opp_pts'] = df.get('opponent_team_score', 0)
    
    # Shooting splits
    df['fgm'] = df['field_goals_made']
    df['fga'] = df['field_goals_attempted']
    df['fg3m'] = df['three_point_field_goals_made']
    df['fg3a'] = df['three_point_field_goals_attempted']
    df['ftm'] = df['free_throws_made']
    df['fta'] = df['free_throws_attempted']
    
    # Derived 2PT stats
    df['fg2m'] = df['fgm'] - df['fg3m']
    df['fg2a'] = df['fga'] - df['fg3a']
    
    # Rebounds
    df['orb'] = df['offensive_rebounds']
    df['drb'] = df['defensive_rebounds']
    
    # Turnovers (handle both column names)
    df['tov'] = df.get('turnovers', df.get('total_turnovers', 0))
    
    # === DERIVED METRICS ===
    
    # Effective Field Goal %
    # eFG% = (FGM + 0.5 * 3PM) / FGA
    df['efg_pct'] = np.where(
        df['fga'] > 0,
        (df['fgm'] + 0.5 * df['fg3m']) / df['fga'],
        0
    )
    
    # True Shooting %
    # TS% = PTS / (2 * (FGA + 0.44 * FTA))
    df['ts_pct'] = np.where(
        (df['fga'] + 0.44 * df['fta']) > 0,
        df['pts'] / (2 * (df['fga'] + 0.44 * df['fta'])),
        0
    )
    
    # Turnover %
    # TOV% = TOV / Poss
    df['tov_pct'] = np.where(
        df['poss_est'] > 0,
        df['tov'] / df['poss_est'],
        0
    )
    
    # Free Throw Rate
    # FTr = FTA / FGA
    df['ftr'] = np.where(
        df['fga'] > 0,
        df['fta'] / df['fga'],
        0
    )
    
    # 3-Point Attempt Rate
    # 3PAr = 3PA / FGA
    df['fg3_rate'] = np.where(
        df['fga'] > 0,
        df['fg3a'] / df['fga'],
        0
    )
    
    # 2-Point %
    df['fg2_pct'] = np.where(
        df['fg2a'] > 0,
        df['fg2m'] / df['fg2a'],
        0
    )
    
    # 3-Point %
    df['fg3_pct'] = np.where(
        df['fg3a'] > 0,
        df['fg3m'] / df['fg3a'],
        0
    )
    
    # Free Throw %
    df['ft_pct'] = np.where(
        df['fta'] > 0,
        df['ftm'] / df['fta'],
        0
    )
    
    # Assist %
    # AST% = AST / FGM
    df['ast_pct'] = np.where(
        df['fgm'] > 0,
        df['assists'] / df['fgm'],
        0
    )
    
    # Assist to Turnover Ratio
    df['ast_tov'] = np.where(
        df['tov'] > 0,
        df['assists'] / df['tov'],
        df['assists']  # If no turnovers, just use assists
    )
    
    # Offensive Rating (per 100 possessions)
    df['ortg'] = np.where(
        df['poss_est'] > 0,
        100 * df['pts'] / df['poss_est'],
        0
    )
    
    # Pace (possessions per game - already have this)
    df['pace'] = df['poss_est']
    
    print(f"  Added {len([c for c in df.columns if c.endswith('_pct') or c in ['ortg', 'pace', 'poss_est']])} derived metrics")
    
    return df


def calculate_rebounding_metrics(df):
    """
    Calculate OREB% and DREB% which require opponent data.
    Must be run after opponent data is joined.
    """
    df = df.copy()
    
    # OREB% = ORB / (ORB + Opp_DRB)
    if 'opp_drb' in df.columns:
        df['oreb_pct'] = np.where(
            (df['orb'] + df['opp_drb']) > 0,
            df['orb'] / (df['orb'] + df['opp_drb']),
            0
        )
    
    # DREB% = DRB / (DRB + Opp_ORB)
    if 'opp_orb' in df.columns:
        df['dreb_pct'] = np.where(
            (df['drb'] + df['opp_orb']) > 0,
            df['drb'] / (df['drb'] + df['opp_orb']),
            0
        )
    
    return df


def calculate_player_metrics(df):
    """
    Add derived metrics to player box score data.
    """
    print("Calculating player metrics...")
    
    df = df.copy()
    
    # Ensure numeric types
    numeric_cols = ['minutes', 'points', 'field_goals_made', 'field_goals_attempted',
                    'three_point_field_goals_made', 'three_point_field_goals_attempted',
                    'free_throws_made', 'free_throws_attempted',
                    'offensive_rebounds', 'defensive_rebounds', 'rebounds',
                    'assists', 'steals', 'blocks', 'turnovers']
    
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # Shorthand columns
    df['pts'] = df['points']
    df['fgm'] = df['field_goals_made']
    df['fga'] = df['field_goals_attempted']
    df['fg3m'] = df['three_point_field_goals_made']
    df['fg3a'] = df['three_point_field_goals_attempted']
    df['ftm'] = df['free_throws_made']
    df['fta'] = df['free_throws_attempted']
    df['reb'] = df['rebounds']
    df['ast'] = df['assists']
    df['stl'] = df['steals']
    df['blk'] = df['blocks']
    df['tov'] = df['turnovers']
    
    # True Shooting %
    df['ts_pct'] = np.where(
        (df['fga'] + 0.44 * df['fta']) > 0,
        df['pts'] / (2 * (df['fga'] + 0.44 * df['fta'])),
        0
    )
    
    # Usage % (simplified - needs team totals for full calculation)
    # USG% approximation = (FGA + 0.44*FTA + TOV) / Minutes * scaling factor
    df['usage_proxy'] = np.where(
        df['minutes'] > 0,
        (df['fga'] + 0.44 * df['fta'] + df['tov']) / df['minutes'],
        0
    )
    
    print(f"  Added player metrics to {len(df)} rows")
    
    return df


# ============================================================================
# PERCENTILE & LABELING FUNCTIONS
# ============================================================================

def calculate_percentiles(df, metric_cols, benchmark_df=None):
    """
    Calculate percentile ranks for specified metrics.
    If benchmark_df provided, use those values; otherwise use current df.
    """
    df = df.copy()
    
    for col in metric_cols:
        if col not in df.columns:
            continue
            
        pctile_col = f"{col}_pctile"
        
        if benchmark_df is not None and col in benchmark_df.columns:
            # Use external benchmarks
            # This would require interpolation logic
            pass
        else:
            # Use current data percentile rank
            df[pctile_col] = df[col].rank(pct=True) * 100
    
    return df


def assign_percentile_labels(df, pctile_col):
    """
    Assign categorical labels based on percentile values.
    """
    label_col = pctile_col.replace('_pctile', '_label')
    
    conditions = [
        df[pctile_col] >= 90,
        df[pctile_col] >= 75,
        df[pctile_col] >= 60,
        df[pctile_col] >= 40,
        df[pctile_col] >= 25,
    ]
    choices = ['Elite', 'Great', 'Above Average', 'Average', 'Below Average']
    
    df[label_col] = np.select(conditions, choices, default='Low')
    
    return df


def add_game_context_tags(df):
    """
    Add game context tags (Close Game, Blowout, etc.)
    """
    df = df.copy()
    
    # Margin
    df['margin'] = df['pts'] - df['opp_pts']
    df['abs_margin'] = df['margin'].abs()
    
    # Close game flag (within 5 points)
    df['close_game'] = df['abs_margin'] <= 5
    
    # Blowout flag (15+ points)
    df['blowout'] = df['abs_margin'] >= 15
    
    # Win flag
    df['win'] = df['margin'] > 0
    
    return df


# ============================================================================
# MAIN WORKFLOW
# ============================================================================

def process_games(start_date=None, force_refresh=False):
    """
    Main processing workflow.
    """
    print("=" * 60)
    print(f"WBB Weekly Data Pull - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Determine date range
    if start_date:
        start = pd.to_datetime(start_date)
    else:
        start = datetime.now() - timedelta(days=7)
    
    end = datetime.now()
    print(f"\nDate range: {start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}")
    
    # Load already-processed games
    if force_refresh:
        processed_games = set()
        print("Force refresh enabled - will re-process all games")
    else:
        processed_games = load_processed_games()
        print(f"Already processed: {len(processed_games)} games")
    
    # Load source data
    print("\n--- Loading source data ---")
    team_box = load_team_box_data(CURRENT_SEASON)
    player_box = load_player_box_data(CURRENT_SEASON)
    
    if team_box.empty:
        print("ERROR: No team box data loaded. Exiting.")
        return
    
    # Filter to date range
    if 'game_date' in team_box.columns:
        team_box['game_date'] = pd.to_datetime(team_box['game_date'])
        team_box = team_box[
            (team_box['game_date'] >= start) & 
            (team_box['game_date'] <= end)
        ]
    
    print(f"\nGames in date range: {team_box['game_id'].nunique()}")
    
    # Filter out already-processed
    new_games = team_box[~team_box['game_id'].isin(processed_games)]
    new_game_ids = set(new_games['game_id'].unique())
    
    print(f"New games to process: {len(new_game_ids)}")
    
    if len(new_game_ids) == 0:
        print("No new games to process. Exiting.")
        log_pull(0, 0)
        return
    
    # Calculate team metrics
    print("\n--- Processing team data ---")
    team_processed = calculate_team_metrics(new_games)
    team_processed = add_game_context_tags(team_processed)
    
    # Calculate percentiles
    metric_cols = ['efg_pct', 'ts_pct', 'tov_pct', 'ftr', 'fg3_rate', 'ortg', 'pace']
    team_processed = calculate_percentiles(team_processed, metric_cols)
    
    # Add labels
    for col in metric_cols:
        pctile_col = f"{col}_pctile"
        if pctile_col in team_processed.columns:
            team_processed = assign_percentile_labels(team_processed, pctile_col)
    
    # Process player data
    print("\n--- Processing player data ---")
    if not player_box.empty:
        player_filtered = player_box[player_box['game_id'].isin(new_game_ids)]
        player_processed = calculate_player_metrics(player_filtered)
    else:
        player_processed = pd.DataFrame()
    
    # Save processed data
    print("\n--- Saving processed data ---")
    
    # Append to existing or create new
    team_output_file = PROCESSED_DIR / "game_analysis.parquet"
    player_output_file = PROCESSED_DIR / "player_game.parquet"
    
    if team_output_file.exists() and not force_refresh:
        existing_team = pd.read_parquet(team_output_file)
        team_final = pd.concat([existing_team, team_processed], ignore_index=True)
        team_final = team_final.drop_duplicates(subset=['game_id', 'team_id'], keep='last')
    else:
        team_final = team_processed
    
    team_final.to_parquet(team_output_file, index=False)
    print(f"  Saved {len(team_final)} team-game rows to {team_output_file}")
    
    if not player_processed.empty:
        if player_output_file.exists() and not force_refresh:
            existing_player = pd.read_parquet(player_output_file)
            player_final = pd.concat([existing_player, player_processed], ignore_index=True)
            player_final = player_final.drop_duplicates(
                subset=['game_id', 'athlete_id'], keep='last'
            )
        else:
            player_final = player_processed
        
        player_final.to_parquet(player_output_file, index=False)
        print(f"  Saved {len(player_final)} player-game rows to {player_output_file}")
    
    # Update tracking
    all_processed = processed_games.union(new_game_ids)
    save_processed_games(all_processed)
    print(f"  Updated tracking: {len(all_processed)} total games processed")
    
    # Log the pull
    log_pull(len(new_game_ids), len(team_processed))
    
    print("\n" + "=" * 60)
    print("Pull complete!")
    print("=" * 60)


def log_pull(games_pulled, rows_added):
    """Log pull statistics."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"{timestamp} | Games: {games_pulled} | Rows: {rows_added}\n"
    
    with open(PULL_LOG_FILE, 'a') as f:
        f.write(log_entry)


# ============================================================================
# CLI ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Weekly WBB Data Pull')
    parser.add_argument(
        '--start-date', 
        type=str, 
        default='',
        help='Start date (YYYY-MM-DD). Defaults to 7 days ago.'
    )
    parser.add_argument(
        '--force-refresh',
        type=str,
        default='false',
        help='Force re-process all games in range (true/false)'
    )
    
    args = parser.parse_args()
    
    start_date = args.start_date if args.start_date else None
    force_refresh = args.force_refresh.lower() == 'true'
    
    process_games(start_date=start_date, force_refresh=force_refresh)
