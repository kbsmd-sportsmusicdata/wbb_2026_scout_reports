"""
Weekly WBB Data Pull Script
===========================
Pulls game data from wehoop/sportsdataverse, processes into Tableau-ready format.
Computes all derived metrics per TARGET_DATA_SCHEMA.md.

Usage:
    python weekly_pull.py                          # Pull last 7 days
    python weekly_pull.py --start-date 2025-01-01  # Pull from specific date
    python weekly_pull.py --force-refresh true     # Re-pull all games in range
    python weekly_pull.py --full-season true       # Process entire season

Outputs (Tableau-ready CSVs):
    data/processed/game_summary.csv      - Team game stats with all derived metrics
    data/processed/player_game.csv       - Player game stats with advanced metrics
    data/processed/shooting_zones.csv    - Zone-level shooting breakdown (from PBP)
"""

import argparse
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import warnings

from data_loader import load_team_box, load_player_box, load_pbp, WEHOOP_BASE

warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURATION
# ============================================================================

DATA_DIR = Path("data")
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
BENCHMARKS_DIR = DATA_DIR / "benchmarks"
TRACKING_DIR = DATA_DIR / "tracking"

for dir_path in [RAW_DIR, PROCESSED_DIR, BENCHMARKS_DIR, TRACKING_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

PROCESSED_GAMES_FILE = TRACKING_DIR / "processed_games.parquet"
PULL_LOG_FILE = TRACKING_DIR / "pull_log.txt"

CURRENT_SEASON = 2026

# Metrics to calculate percentiles for (team-level)
TEAM_PCTILE_METRICS = [
    'efg_pct', 'ts_pct', 'tov_pct', 'oreb_pct', 'dreb_pct', 'ftr', 'fg3_rate',
    'ortg', 'drtg', 'net_rtg', 'pace', 'ast_pct', 'ast_tov', 'stl_pct', 'blk_pct'
]

# Metrics where LOWER is better (invert percentile)
INVERTED_METRICS = ['tov_pct', 'drtg']

# ============================================================================
# DATA LOADING
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
    df.to_csv(PROCESSED_GAMES_FILE.with_suffix('.csv'), index=False)


def load_benchmarks():
    """Load D1 benchmark data for percentile calculations."""
    benchmark_file = BENCHMARKS_DIR / 'd1_benchmarks_current.csv'
    if benchmark_file.exists():
        return pd.read_csv(benchmark_file)
    return pd.DataFrame()


# ============================================================================
# OPPONENT JOINING
# ============================================================================

def join_opponent_stats(df):
    """
    Join opponent stats for each team-game row.
    Creates opp_* columns for all relevant stats.
    Uses vectorized merge for O(N) performance.
    """
    print("Joining opponent stats...")

    if 'game_id' not in df.columns or 'team_id' not in df.columns:
        print("  Cannot join opponent stats - missing game_id or team_id")
        return df

    # Create opponent lookup from same data
    opp_cols = [
        'game_id', 'team_id', 'team_display_name', 'team_abbreviation',
        'field_goals_made', 'field_goals_attempted',
        'three_point_field_goals_made', 'three_point_field_goals_attempted',
        'free_throws_made', 'free_throws_attempted',
        'offensive_rebounds', 'defensive_rebounds', 'total_rebounds',
        'assists', 'steals', 'blocks', 'turnovers', 'total_turnovers',
        'team_score', 'poss_est', 'pts'
    ]

    # Filter to columns that exist
    available_cols = [c for c in opp_cols if c in df.columns]
    opp_data = df[available_cols].copy()

    # Rename for opponent
    rename_map = {c: f'opp_{c}' for c in available_cols if c not in ['game_id', 'team_id']}
    rename_map['team_id'] = 'opponent_id'
    rename_map['team_display_name'] = 'opponent_name'
    rename_map['team_abbreviation'] = 'opponent_abbrev'
    opp_data = opp_data.rename(columns=rename_map)

    # Vectorized join: merge df with opp_data on game_id, then filter where team_id != opponent_id
    # This assumes exactly 2 teams per game_id
    # Handle games without exactly 2 teams to prevent data loss or duplication.
    game_counts = df.groupby('game_id')['team_id'].transform('nunique')
    
    # Vectorized join for games with 2 teams
    merged = df.loc[game_counts == 2].merge(opp_data, on='game_id', how='left')
    merged = merged.query('team_id != opponent_id')
    
    # Combine with unprocessed games
    df = pd.concat([merged, df.loc[game_counts != 2]], ignore_index=True)

    print(f"  Joined opponent stats for {df['game_id'].nunique()} games")
    return df


# ============================================================================
# TEAM METRIC CALCULATIONS
# ============================================================================

def calculate_possessions(row):
    """Dean Oliver possession estimate: Poss = FGA + 0.44 * FTA - ORB + TOV"""
    fga = row.get('field_goals_attempted', 0) or 0
    fta = row.get('free_throws_attempted', 0) or 0
    orb = row.get('offensive_rebounds', 0) or 0
    tov = row.get('turnovers', 0) or row.get('total_turnovers', 0) or 0
    return max(fga + 0.44 * fta - orb + tov, 1)


def calculate_team_metrics(df):
    """
    Calculate all derived team metrics per TARGET_DATA_SCHEMA.
    """
    print("Calculating team metrics...")
    df = df.copy()

    # Ensure numeric types
    numeric_cols = [
        'field_goals_made', 'field_goals_attempted',
        'three_point_field_goals_made', 'three_point_field_goals_attempted',
        'free_throws_made', 'free_throws_attempted',
        'offensive_rebounds', 'defensive_rebounds', 'total_rebounds',
        'assists', 'steals', 'blocks', 'turnovers', 'total_turnovers',
        'team_score', 'opponent_team_score',
        'fast_break_points', 'points_in_paint', 'turnovers_points', 'largest_lead'
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # === STANDARDIZED COLUMN NAMES ===
    df['pts'] = df.get('team_score', df.get('points', pd.Series([0]*len(df))))
    df['opp_pts'] = df.get('opponent_team_score', pd.Series([0]*len(df)))
    df['fgm'] = df['field_goals_made']
    df['fga'] = df['field_goals_attempted']
    df['fg3m'] = df['three_point_field_goals_made']
    df['fg3a'] = df['three_point_field_goals_attempted']
    df['ftm'] = df['free_throws_made']
    df['fta'] = df['free_throws_attempted']
    df['fg2m'] = df['fgm'] - df['fg3m']
    df['fg2a'] = df['fga'] - df['fg3a']
    df['orb'] = df['offensive_rebounds']
    df['drb'] = df['defensive_rebounds']
    df['reb'] = df.get('total_rebounds', df['orb'] + df['drb'])
    df['ast'] = df['assists']
    df['stl'] = df['steals']
    df['blk'] = df['blocks']
    df['tov'] = df.get('turnovers', df.get('total_turnovers', pd.Series([0]*len(df))))
    df['pf'] = df.get('fouls', pd.Series([0]*len(df)))

    # Team display name mapping (use existing or create)
    if 'team_display_name' in df.columns:
        df['team_name'] = df['team_display_name']
    if 'team_abbreviation' in df.columns:
        df['team_abbrev'] = df['team_abbreviation']

    # Home/Away indicator
    if 'team_home_away' in df.columns:
        df['is_home'] = df['team_home_away'] == 'home'

    # Result
    if 'team_winner' in df.columns:
        df['result'] = np.where(df['team_winner'], 'W', 'L')
    else:
        df['result'] = np.where(df['pts'] > df['opp_pts'], 'W', 'L')

    # === POSSESSIONS ===
    df['poss_est'] = df.apply(calculate_possessions, axis=1)

    # === SHOOTING METRICS ===
    df['fg_pct'] = np.where(df['fga'] > 0, df['fgm'] / df['fga'], 0)
    df['fg2_pct'] = np.where(df['fg2a'] > 0, df['fg2m'] / df['fg2a'], 0)
    df['fg3_pct'] = np.where(df['fg3a'] > 0, df['fg3m'] / df['fg3a'], 0)
    df['ft_pct'] = np.where(df['fta'] > 0, df['ftm'] / df['fta'], 0)
    df['efg_pct'] = np.where(df['fga'] > 0, (df['fgm'] + 0.5 * df['fg3m']) / df['fga'], 0)
    df['ts_pct'] = np.where(
        (df['fga'] + 0.44 * df['fta']) > 0,
        df['pts'] / (2 * (df['fga'] + 0.44 * df['fta'])),
        0
    )
    df['fg3_rate'] = np.where(df['fga'] > 0, df['fg3a'] / df['fga'], 0)
    df['ftr'] = np.where(df['fga'] > 0, df['fta'] / df['fga'], 0)

    # === BALL MOVEMENT ===
    df['tov_pct'] = np.where(df['poss_est'] > 0, df['tov'] / df['poss_est'], 0)
    df['ast_pct'] = np.where(df['fgm'] > 0, df['ast'] / df['fgm'], 0)
    df['ast_tov'] = np.where(df['tov'] > 0, df['ast'] / df['tov'], df['ast'])

    # === OFFENSIVE RATING ===
    df['ortg'] = np.where(df['poss_est'] > 0, 100 * df['pts'] / df['poss_est'], 0)
    df['pace'] = df['poss_est']

    # === MISC SCORING (if available) ===
    if 'fast_break_points' in df.columns:
        df['fb_pts'] = df['fast_break_points']
    if 'points_in_paint' in df.columns:
        df['paint_pts'] = df['points_in_paint']
    if 'turnovers_points' in df.columns:
        df['potov'] = df['turnovers_points']

    # === GAME CONTEXT ===
    df['margin'] = df['pts'] - df['opp_pts']
    df['abs_margin'] = df['margin'].abs()
    df['close_game'] = df['abs_margin'] <= 5
    df['blowout'] = df['abs_margin'] >= 15
    df['win'] = df['margin'] > 0

    print(f"  Calculated base metrics for {len(df)} team-game rows")
    return df


def calculate_defensive_metrics(df):
    """
    Calculate defensive metrics that require opponent data.
    Must be called after join_opponent_stats().
    """
    print("Calculating defensive metrics...")
    df = df.copy()

    # Get opponent points - handle various column names from join
    opp_pts_cols = ['opp_team_score', 'opp_pts_y', 'opp_pts_x', 'opp_pts', 'opponent_team_score']
    opp_pts_col = next(
        (col for col in opp_pts_cols if col in df.columns and df[col].notna().any()),
        None
    )

    if opp_pts_col:
        df['opp_pts'] = pd.to_numeric(df[opp_pts_col], errors='coerce').fillna(0)
    else:
        df['opp_pts'] = 0

    # Opponent possessions
    if 'opp_poss_est' not in df.columns or df['opp_poss_est'].isna().all():
        # Estimate from opponent stats
        if all(c in df.columns for c in ['opp_field_goals_attempted', 'opp_free_throws_attempted',
                                          'opp_offensive_rebounds']):
            opp_tov = df.get('opp_turnovers', df.get('opp_total_turnovers', 0))
            df['opp_poss_est'] = (
                df['opp_field_goals_attempted'] +
                0.44 * df['opp_free_throws_attempted'] -
                df['opp_offensive_rebounds'] +
                opp_tov
            ).clip(lower=1)
        else:
            df['opp_poss_est'] = df['poss_est']  # Approximate as same

    # Defensive Rating
    df['drtg'] = np.where(
        df['opp_poss_est'] > 0,
        100 * df['opp_pts'] / df['opp_poss_est'],
        0
    )

    # Net Rating
    df['net_rtg'] = df['ortg'] - df['drtg']

    # OREB% and DREB%
    if 'opp_drb' in df.columns or 'opp_defensive_rebounds' in df.columns:
        opp_drb = df.get('opp_drb', df.get('opp_defensive_rebounds', 0))
        df['oreb_pct'] = np.where(
            (df['orb'] + opp_drb) > 0,
            df['orb'] / (df['orb'] + opp_drb),
            0
        )

    if 'opp_orb' in df.columns or 'opp_offensive_rebounds' in df.columns:
        opp_orb = df.get('opp_orb', df.get('opp_offensive_rebounds', 0))
        df['dreb_pct'] = np.where(
            (df['drb'] + opp_orb) > 0,
            df['drb'] / (df['drb'] + opp_orb),
            0
        )

    # Steal % (per opp possession)
    df['stl_pct'] = np.where(df['opp_poss_est'] > 0, df['stl'] / df['opp_poss_est'], 0)

    # Block % (per opp 2PA - ideally)
    if 'opp_fg2a' in df.columns:
        df['blk_pct'] = np.where(df['opp_fg2a'] > 0, df['blk'] / df['opp_fg2a'], 0)
    elif 'opp_field_goals_attempted' in df.columns:
        opp_fga = df['opp_field_goals_attempted']
        df['blk_pct'] = np.where(opp_fga > 0, df['blk'] / opp_fga, 0)

    # Clean up merge artifacts
    drop_cols = [c for c in df.columns if c.endswith('_x') or c.endswith('_y')]
    if drop_cols:
        df = df.drop(columns=drop_cols, errors='ignore')

    print(f"  Added defensive metrics (DRtg, Net Rtg, OREB%, DREB%, etc.)")
    return df


def calculate_rolling_averages(df, window=5):
    """
    Calculate rolling averages for key metrics (last N games per team).
    """
    print(f"Calculating rolling {window}-game averages...")
    df = df.copy()

    if 'game_date' not in df.columns or 'team_id' not in df.columns:
        print("  Cannot calculate rolling averages - missing required columns")
        return df

    # Sort by team and date
    df = df.sort_values(['team_id', 'game_date'])

    rolling_metrics = ['ortg', 'drtg', 'net_rtg', 'efg_pct', 'ts_pct', 'tov_pct', 'pace']

    for metric in rolling_metrics:
        if metric in df.columns:
            col_name = f'last{window}_{metric}'
            df[col_name] = df.groupby('team_id')[metric].transform(
                lambda x: x.shift(1).rolling(window=window, min_periods=1).mean()
            )

    print(f"  Added rolling averages for {len(rolling_metrics)} metrics")
    return df


# ============================================================================
# PLAYER METRIC CALCULATIONS
# ============================================================================

def calculate_player_metrics(df, team_totals=None):
    """
    Calculate all derived player metrics per TARGET_DATA_SCHEMA.
    """
    print("Calculating player metrics...")
    df = df.copy()

    # Ensure numeric types
    numeric_cols = [
        'minutes', 'points', 'field_goals_made', 'field_goals_attempted',
        'three_point_field_goals_made', 'three_point_field_goals_attempted',
        'free_throws_made', 'free_throws_attempted',
        'offensive_rebounds', 'defensive_rebounds', 'rebounds',
        'assists', 'steals', 'blocks', 'turnovers'
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # === STANDARDIZED COLUMN NAMES ===
    df['mp'] = df.get('minutes', 0)
    df['pts'] = df['points']
    df['fgm'] = df['field_goals_made']
    df['fga'] = df['field_goals_attempted']
    df['fg3m'] = df['three_point_field_goals_made']
    df['fg3a'] = df['three_point_field_goals_attempted']
    df['fg2m'] = df['fgm'] - df['fg3m']
    df['fg2a'] = df['fga'] - df['fg3a']
    df['ftm'] = df['free_throws_made']
    df['fta'] = df['free_throws_attempted']
    df['orb'] = df.get('offensive_rebounds', 0)
    df['drb'] = df.get('defensive_rebounds', 0)
    df['reb'] = df.get('rebounds', df['orb'] + df['drb'])
    df['ast'] = df['assists']
    df['stl'] = df['steals']
    df['blk'] = df['blocks']
    df['tov'] = df['turnovers']
    df['pf'] = df.get('fouls', 0)

    # Player display name mapping
    if 'athlete_display_name' in df.columns:
        df['player_name'] = df['athlete_display_name']
    if 'athlete_id' in df.columns:
        df['player_id'] = df['athlete_id']
    if 'team_display_name' in df.columns:
        df['team_name'] = df['team_display_name']
    if 'athlete_position_abbreviation' in df.columns:
        df['position'] = df['athlete_position_abbreviation']

    # === SHOOTING METRICS ===
    df['fg_pct'] = np.where(df['fga'] > 0, df['fgm'] / df['fga'], 0)
    df['fg2_pct'] = np.where(df['fg2a'] > 0, df['fg2m'] / df['fg2a'], 0)
    df['fg3_pct'] = np.where(df['fg3a'] > 0, df['fg3m'] / df['fg3a'], 0)
    df['ft_pct'] = np.where(df['fta'] > 0, df['ftm'] / df['fta'], 0)
    df['efg_pct'] = np.where(df['fga'] > 0, (df['fgm'] + 0.5 * df['fg3m']) / df['fga'], 0)
    df['ts_pct'] = np.where(
        (df['fga'] + 0.44 * df['fta']) > 0,
        df['pts'] / (2 * (df['fga'] + 0.44 * df['fta'])),
        0
    )
    df['fg3_rate'] = np.where(df['fga'] > 0, df['fg3a'] / df['fga'], 0)
    df['ftr'] = np.where(df['fga'] > 0, df['fta'] / df['fga'], 0)

    # === BALL MOVEMENT ===
    df['ast_ratio'] = np.where(
        (df['fga'] + 0.44 * df['fta'] + df['tov']) > 0,
        df['ast'] / (df['fga'] + 0.44 * df['fta'] + df['tov']),
        0
    )
    df['tov_pct'] = np.where(
        (df['fga'] + 0.44 * df['fta'] + df['tov']) > 0,
        df['tov'] / (df['fga'] + 0.44 * df['fta'] + df['tov']),
        0
    )
    df['ast_tov'] = np.where(df['tov'] > 0, df['ast'] / df['tov'], df['ast'])

    # === PER 40 MINUTE RATES ===
    df['mp'] = pd.to_numeric(df['mp'], errors='coerce').fillna(0)
    per_40_stats = ['pts', 'reb', 'ast', 'stl', 'blk', 'tov']
    for stat in per_40_stats:
        df[f'{stat}_40'] = np.where(df['mp'] > 0, df[stat] * 40 / df['mp'], 0)

    # === USAGE % (requires team totals) ===
    if team_totals is not None:
        df = calculate_usage_pct(df, team_totals)
    else:
        # Simplified usage proxy
        df['usg_pct'] = np.where(
            df['mp'] > 0,
            (df['fga'] + 0.44 * df['fta'] + df['tov']) / df['mp'] * 5,  # Rough scaling
            0
        )

    # DNQ flag (< 5 minutes)
    df['dnq'] = df['mp'] < 5

    print(f"  Calculated metrics for {len(df)} player-game rows")
    return df


def calculate_usage_pct(player_df, team_df):
    """
    Calculate true Usage % using team totals.
    USG% = 100 * ((FGA + 0.44*FTA + TOV) * (Team_MP / 5)) / (MP * (Team_FGA + 0.44*Team_FTA + Team_TOV))
    """
    player_df = player_df.copy()

    # Prepare team totals per game
    team_totals = team_df.groupby('game_id').agg({
        'fga': 'sum',
        'fta': 'sum',
        'tov': 'sum',
        'mp': 'sum'  # Will be 200 for 5 players * 40 min
    }).reset_index()
    team_totals.columns = ['game_id', 'team_fga', 'team_fta', 'team_tov', 'team_mp']

    # Merge team totals
    player_df = player_df.merge(team_totals, on='game_id', how='left')

    # Calculate true USG%
    player_df['usg_pct'] = np.where(
        (player_df['mp'] > 0) & (player_df['team_fga'] + 0.44 * player_df['team_fta'] + player_df['team_tov'] > 0),
        100 * (
            (player_df['fga'] + 0.44 * player_df['fta'] + player_df['tov']) *
            (player_df['team_mp'] / 5)
        ) / (
            player_df['mp'] *
            (player_df['team_fga'] + 0.44 * player_df['team_fta'] + player_df['team_tov'])
        ),
        0
    )

    # Drop temp columns
    player_df = player_df.drop(columns=['team_fga', 'team_fta', 'team_tov', 'team_mp'], errors='ignore')

    return player_df


# ============================================================================
# PERCENTILE CALCULATIONS
# ============================================================================

def calculate_percentiles_vs_benchmarks(df, benchmark_df, metrics):
    """
    Calculate percentiles against D1 benchmarks.
    Uses linear interpolation between benchmark percentile breakpoints.
    """
    print("Calculating percentiles vs D1 benchmarks...")
    df = df.copy()

    if benchmark_df.empty:
        print("  No benchmark data - using within-sample percentiles")
        for metric in metrics:
            if metric in df.columns:
                df[f'{metric}_pctile'] = df[metric].rank(pct=True) * 100
        return df

    for metric in metrics:
        if metric not in df.columns:
            continue

        bench_row = benchmark_df[benchmark_df['metric'] == metric]
        if bench_row.empty:
            # Fall back to within-sample
            df[f'{metric}_pctile'] = df[metric].rank(pct=True) * 100
            continue

        bench_row = bench_row.iloc[0]

        # Get percentile breakpoints
        breakpoints = []
        for p in [5, 10, 25, 50, 75, 90, 95]:
            col = f'p{p}'
            if col in bench_row:
                breakpoints.append((p, bench_row[col]))

        if not breakpoints:
            df[f'{metric}_pctile'] = df[metric].rank(pct=True) * 100
            continue

        # Interpolate percentiles using np.interp (optimized)
        breakpoints = sorted(breakpoints, key=lambda x: x[1])

        # Extract x (benchmark values) and y (percentiles) for np.interp
        xp = [b[1] for b in breakpoints]  # benchmark values (must be increasing)
        fp = [b[0] for b in breakpoints]  # percentile values

        def interpolate_pctile(value):
            if pd.isna(value):
                return np.nan

            # np.interp handles edge cases with left/right bounds
            pctile = np.interp(value, xp, fp, left=fp[0], right=fp[-1])

            # Invert for metrics where lower is better
            if metric in INVERTED_METRICS:
                return 100 - pctile
            return pctile

        df[f'{metric}_pctile'] = df[metric].apply(interpolate_pctile)

    print(f"  Calculated percentiles for {len(metrics)} metrics")
    return df


def assign_percentile_labels(df, metrics):
    """
    Assign categorical labels based on percentile values.
    """
    for metric in metrics:
        pctile_col = f'{metric}_pctile'
        if pctile_col not in df.columns:
            continue

        label_col = f'{metric}_label'
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


# ============================================================================
# PLAY-BY-PLAY PROCESSING
# ============================================================================

def process_pbp_shooting_zones(pbp_df, team_box_df):
    """
    Derive zone-level shooting from play-by-play data.
    Returns shooting_zones DataFrame.
    """
    print("Processing PBP for shooting zones...")

    if pbp_df.empty:
        print("  No PBP data available")
        return pd.DataFrame()

    # Filter to shot events
    shot_types = ['Made Shot', 'Missed Shot', 'made', 'missed']
    shot_events = pbp_df[
        pbp_df['type_text'].str.contains('|'.join(shot_types), case=False, na=False) |
        pbp_df['text'].str.contains('shot|jumper|layup|dunk|three|3-pointer', case=False, na=False)
    ].copy()

    if shot_events.empty:
        print("  No shot events found in PBP")
        return pd.DataFrame()

    print(f"  Found {len(shot_events)} shot events")

    # Determine shot zones from description
    def classify_shot_zone(row):
        text = str(row.get('text', '')).lower()

        # Check for 3-pointers
        if any(x in text for x in ['three', '3-pt', '3-pointer', '3pt']):
            if 'corner' in text:
                if 'left' in text:
                    return ('Left Corner 3s', '3PT', 7)
                elif 'right' in text:
                    return ('Right Corner 3s', '3PT', 8)
                return ('Corner 3s', '3PT', 7)  # Default to left
            elif 'wing' in text:
                if 'left' in text:
                    return ('Left Wing 3s', '3PT', 9)
                elif 'right' in text:
                    return ('Right Wing 3s', '3PT', 10)
                return ('Wing 3s', '3PT', 9)
            else:
                return ('Top of Key 3s', '3PT', 11)

        # Check for paint/rim shots
        if any(x in text for x in ['layup', 'dunk', 'at the rim', 'at rim']):
            return ('At The Rim', 'Paint', 1)
        if any(x in text for x in ['in the paint', 'paint', 'close range']):
            return ('In The Paint', 'Paint', 2)

        # Check for midrange
        if any(x in text for x in ['jumper', 'jump shot', 'mid-range', 'midrange', 'elbow']):
            if 'baseline' in text:
                if 'left' in text:
                    return ('Left Baseline 2s', 'Midrange', 3)
                elif 'right' in text:
                    return ('Right Baseline 2s', 'Midrange', 4)
            if 'elbow' in text or 'free throw' in text:
                if 'left' in text:
                    return ('Left Elbow 2s', 'Midrange', 5)
                elif 'right' in text:
                    return ('Right Elbow 2s', 'Midrange', 6)
            return ('Midrange', 'Midrange', 5)  # Default

        # Default: try to infer from coordinates if available
        if 'coordinate_x' in row and 'coordinate_y' in row:
            x, y = row.get('coordinate_x'), row.get('coordinate_y')
            if pd.notna(x) and pd.notna(y):
                # Basic coordinate classification (would need court dimensions)
                pass

        # Unknown - classify as general 2-pointer
        return ('Unknown 2PT', 'Midrange', 5)

    # Classify shots
    shot_events[['zone_name', 'zone_type', 'zone_id']] = shot_events.apply(
        classify_shot_zone, axis=1, result_type='expand'
    )

    # Determine if made or missed
    shot_events['made'] = (
        shot_events['type_text'].str.contains('Made', case=False, na=False) |
        shot_events['scoring_play'].fillna(False).astype(bool)
    )

    # Aggregate by game, team, zone
    if 'team_id' not in shot_events.columns:
        # Try to get from athlete_id_1 or other columns
        if 'athlete_id_1' in shot_events.columns:
            # Would need player->team mapping
            pass

    # If we can't identify team, skip zone aggregation
    if 'team_id' not in shot_events.columns:
        print("  Cannot aggregate zones - no team_id in PBP")
        return pd.DataFrame()

    # Aggregate
    zone_agg = shot_events.groupby(['game_id', 'team_id', 'zone_id', 'zone_name', 'zone_type']).agg(
        fgm=('made', 'sum'),
        fga=('made', 'count')
    ).reset_index()

    zone_agg['fg_pct'] = np.where(zone_agg['fga'] > 0, zone_agg['fgm'] / zone_agg['fga'], 0)

    # Calculate FGA share per game/team
    team_fga = zone_agg.groupby(['game_id', 'team_id'])['fga'].transform('sum')
    zone_agg['fga_pct'] = np.where(team_fga > 0, zone_agg['fga'] / team_fga, 0)

    print(f"  Generated {len(zone_agg)} zone-level shooting rows")
    return zone_agg


def extract_misc_scoring_from_pbp(pbp_df, team_df):
    """
    Extract additional scoring categories from PBP if not in box score.
    - Second chance points
    - Bench points
    """
    # This is a simplified version - full implementation would track sequences
    return team_df


# ============================================================================
# MAIN WORKFLOW
# ============================================================================

def process_games(start_date=None, force_refresh=False, full_season=False):
    """Main processing workflow - creates Tableau-ready datasets."""

    print("=" * 70)
    print(f"WBB Weekly Data Pull - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # Determine date range
    if full_season:
        start = datetime(CURRENT_SEASON - 1, 11, 1)  # Season starts ~Nov 1
        print("Full season mode - processing all available games")
    elif start_date:
        start = pd.to_datetime(start_date)
    else:
        start = datetime.now() - timedelta(days=7)

    end = datetime.now()
    print(f"\nDate range: {start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}")

    # Load tracking
    if force_refresh:
        processed_games = set()
        print("Force refresh enabled - will re-process all games")
    else:
        processed_games = load_processed_games()
        print(f"Already processed: {len(processed_games)} games")

    # Load source data
    print("\n--- Loading source data ---")
    team_box = load_team_box(CURRENT_SEASON, DATA_DIR)
    player_box = load_player_box(CURRENT_SEASON, DATA_DIR)
    pbp = load_pbp(CURRENT_SEASON, DATA_DIR)

    if team_box.empty:
        print("ERROR: No team box data loaded. Exiting.")
        return

    # Load benchmarks
    benchmark_df = load_benchmarks()
    if not benchmark_df.empty:
        print(f"Loaded D1 benchmarks with {len(benchmark_df)} metrics")

    # Filter to date range
    if 'game_date' in team_box.columns:
        team_box['game_date'] = pd.to_datetime(team_box['game_date'])
        team_box = team_box[
            (team_box['game_date'] >= start) &
            (team_box['game_date'] <= end)
        ]

    print(f"\nGames in date range: {team_box['game_id'].nunique()}")

    # Filter out already-processed (unless force refresh)
    if not force_refresh:
        new_games = team_box[~team_box['game_id'].isin(processed_games)]
    else:
        new_games = team_box

    new_game_ids = set(new_games['game_id'].unique())
    print(f"Games to process: {len(new_game_ids)}")

    if len(new_game_ids) == 0:
        print("No new games to process. Exiting.")
        log_pull(0, 0)
        return

    # ===== TEAM PROCESSING =====
    print("\n--- Processing team data ---")
    team_processed = calculate_team_metrics(new_games)
    team_processed = join_opponent_stats(team_processed)
    team_processed = calculate_defensive_metrics(team_processed)
    team_processed = calculate_rolling_averages(team_processed, window=5)
    team_processed = calculate_percentiles_vs_benchmarks(team_processed, benchmark_df, TEAM_PCTILE_METRICS)
    team_processed = assign_percentile_labels(team_processed, TEAM_PCTILE_METRICS)

    # ===== PLAYER PROCESSING =====
    print("\n--- Processing player data ---")
    if not player_box.empty:
        player_filtered = player_box[player_box['game_id'].isin(new_game_ids)]

        # Get team totals for USG% calculation
        team_totals_for_usg = player_filtered.groupby(['game_id', 'team_id']).agg({
            'field_goals_attempted': 'sum',
            'free_throws_attempted': 'sum',
            'turnovers': 'sum',
            'minutes': 'sum'
        }).reset_index()
        team_totals_for_usg.columns = ['game_id', 'team_id', 'fga', 'fta', 'tov', 'mp']

        player_processed = calculate_player_metrics(player_filtered)

        # Calculate USG% with team totals
        player_processed = player_processed.merge(
            team_totals_for_usg,
            on=['game_id', 'team_id'],
            how='left',
            suffixes=('', '_team')
        )

        player_processed['usg_pct'] = np.where(
            (player_processed['mp'] > 0) & (player_processed['fga_team'] + 0.44 * player_processed['fta_team'] + player_processed['tov_team'] > 0),
            100 * (
                (player_processed['fga'] + 0.44 * player_processed['fta'] + player_processed['tov']) *
                (player_processed['mp_team'] / 5)
            ) / (
                player_processed['mp'] *
                (player_processed['fga_team'] + 0.44 * player_processed['fta_team'] + player_processed['tov_team'])
            ),
            0
        )

        # Drop temp team columns
        player_processed = player_processed.drop(
            columns=['fga_team', 'fta_team', 'tov_team', 'mp_team'],
            errors='ignore'
        )

        # Player percentiles (simplified - within sample)
        player_metrics = ['ts_pct', 'usg_pct', 'efg_pct']
        for metric in player_metrics:
            if metric in player_processed.columns:
                player_processed[f'{metric}_pctile'] = player_processed[metric].rank(pct=True) * 100
        player_processed = assign_percentile_labels(player_processed, player_metrics)
    else:
        player_processed = pd.DataFrame()

    # ===== PBP PROCESSING =====
    print("\n--- Processing play-by-play data ---")
    if not pbp.empty:
        pbp_filtered = pbp[pbp['game_id'].isin(new_game_ids)]
        shooting_zones = process_pbp_shooting_zones(pbp_filtered, team_processed)
    else:
        shooting_zones = pd.DataFrame()

    # ===== SAVE OUTPUTS =====
    print("\n--- Saving Tableau-ready datasets ---")

    # Team game summary
    team_output = PROCESSED_DIR / "game_summary"
    if team_output.with_suffix('.parquet').exists() and not force_refresh:
        existing = pd.read_parquet(team_output.with_suffix('.parquet'))
        team_final = pd.concat([existing, team_processed], ignore_index=True)
        team_final = team_final.drop_duplicates(subset=['game_id', 'team_id'], keep='last')
    else:
        team_final = team_processed

    team_final.to_parquet(team_output.with_suffix('.parquet'), index=False)
    team_final.to_csv(team_output.with_suffix('.csv'), index=False)
    print(f"  ✓ game_summary: {len(team_final)} rows ({team_final['game_id'].nunique()} games)")

    # Player game
    if not player_processed.empty:
        player_output = PROCESSED_DIR / "player_game"
        if player_output.with_suffix('.parquet').exists() and not force_refresh:
            existing = pd.read_parquet(player_output.with_suffix('.parquet'))
            player_final = pd.concat([existing, player_processed], ignore_index=True)
            player_final = player_final.drop_duplicates(subset=['game_id', 'athlete_id'], keep='last')
        else:
            player_final = player_processed

        player_final.to_parquet(player_output.with_suffix('.parquet'), index=False)
        player_final.to_csv(player_output.with_suffix('.csv'), index=False)
        print(f"  ✓ player_game: {len(player_final)} rows")

    # Shooting zones
    if not shooting_zones.empty:
        zones_output = PROCESSED_DIR / "shooting_zones"
        if zones_output.with_suffix('.parquet').exists() and not force_refresh:
            existing = pd.read_parquet(zones_output.with_suffix('.parquet'))
            zones_final = pd.concat([existing, shooting_zones], ignore_index=True)
            zones_final = zones_final.drop_duplicates(
                subset=['game_id', 'team_id', 'zone_id'], keep='last'
            )
        else:
            zones_final = shooting_zones

        zones_final.to_parquet(zones_output.with_suffix('.parquet'), index=False)
        zones_final.to_csv(zones_output.with_suffix('.csv'), index=False)
        print(f"  ✓ shooting_zones: {len(zones_final)} rows")

    # Update tracking
    all_processed = processed_games.union(new_game_ids)
    save_processed_games(all_processed)
    print(f"  Updated tracking: {len(all_processed)} total games")

    # Log
    log_pull(len(new_game_ids), len(team_processed))

    print("\n" + "=" * 70)
    print("WEEKLY PULL COMPLETE - Data is Tableau-ready!")
    print("=" * 70)
    print("\nOutput files:")
    print(f"  • {PROCESSED_DIR}/game_summary.csv")
    print(f"  • {PROCESSED_DIR}/player_game.csv")
    if not shooting_zones.empty:
        print(f"  • {PROCESSED_DIR}/shooting_zones.csv")


def log_pull(games_pulled, rows_added):
    """Log pull statistics."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"{timestamp} | Games: {games_pulled} | Rows: {rows_added}\n"
    with open(PULL_LOG_FILE, 'a') as f:
        f.write(log_entry)


# ============================================================================
# CLI
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
    parser.add_argument(
        '--full-season',
        type=str,
        default='false',
        help='Process entire season (true/false)'
    )

    args = parser.parse_args()

    start_date = args.start_date if args.start_date else None
    force_refresh = args.force_refresh.lower() == 'true'
    full_season = args.full_season.lower() == 'true'

    process_games(
        start_date=start_date,
        force_refresh=force_refresh,
        full_season=full_season
    )
