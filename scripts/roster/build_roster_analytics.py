"""
Build Roster Analytics Tables for WBB 2025-26 Season.

This script creates two analytics tables:
1. player_season_analytic_2026 - Player-level season aggregates with roster info
2. team_season_analytic_2026 - Team-level season aggregates with roster composition metrics

Focus: AP Top 25 teams for the 2025-26 season

Usage:
    python scripts/roster/build_roster_analytics.py

Output:
    data/processed/roster/player_season_analytic_2026.csv
    data/processed/roster/team_season_analytic_2026.csv
"""

import argparse
from pathlib import Path
import numpy as np
import pandas as pd

# Configuration
DATA_DIR = Path("data")
RAW_DIR = DATA_DIR / "raw" / "2026"
PROCESSED_DIR = DATA_DIR / "processed" / "roster"

# Ensure output directory exists
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# Year-to-numeric mapping for experience calculations
YEAR_MAP = {
    'Freshman': 1, 'Fr.': 1, 'FR': 1,
    'Sophomore': 2, 'So.': 2, 'SO': 2,
    'Junior': 3, 'Jr.': 3, 'JR': 3,
    'Senior': 4, 'Sr.': 4, 'SR': 4,
    'Graduate': 5, 'Gr.': 5, 'GR': 5, 'Graduate Student': 5,
    'Redshirt Freshman': 1, 'RS Fr.': 1, 'R-Fr.': 1,
    'Redshirt Sophomore': 2, 'RS So.': 2, 'R-So.': 2,
    'Redshirt Junior': 3, 'RS Jr.': 3, 'R-Jr.': 3,
    'Redshirt Senior': 4, 'RS Sr.': 4, 'R-Sr.': 4,
}

# Team name standardization mapping (source -> canonical)
TEAM_NAME_MAP = {
    'Connecticut': 'UConn',
    'Louisiana State': 'LSU',
    'Southern California': 'USC',
    'Mississippi': 'Ole Miss',
    'North Carolina': 'UNC',
    'Michigan St.': 'Michigan State',
    'Ohio St.': 'Ohio State',
    'Oklahoma St.': 'Oklahoma State',
    'Iowa St.': 'Iowa State',
    'Mississippi St.': 'Mississippi State',
    'Miami': 'Miami (FL)',
    'Arizona St.': 'Arizona State',
    'Brigham Young': 'BYU',
}


def standardize_team_name(name):
    """Standardize team name using mapping."""
    if pd.isna(name):
        return name
    return TEAM_NAME_MAP.get(name, name)


def load_data():
    """Load all required data sources."""
    print("Loading data sources...")

    # Load roster data
    rosters = pd.read_csv(RAW_DIR / "wbb_rosters_2025_26.csv")
    print(f"  Rosters: {len(rosters)} players")

    # Load player box scores
    player_box = pd.read_parquet(RAW_DIR / "player_box_2026.parquet")
    print(f"  Player box scores: {len(player_box)} rows")

    # Load team box scores
    team_box = pd.read_parquet(RAW_DIR / "team_box_2026.parquet")
    print(f"  Team box scores: {len(team_box)} rows")

    # Load schedule (for AP rankings)
    schedule = pd.read_parquet(RAW_DIR / "wbb_schedule_2026.parquet")
    print(f"  Schedule: {len(schedule)} games")

    return rosters, player_box, team_box, schedule


def get_ap_top25_teams(schedule):
    """
    Extract teams that have been in AP Top 25 at any point during the season.
    Returns DataFrame with team_id, team_name, and best_rank.
    """
    print("\nIdentifying AP Top 25 teams...")

    # Get home teams with rankings
    home_ranked = schedule[schedule['home_current_rank'] <= 25][
        ['home_id', 'home_display_name', 'home_current_rank']
    ].rename(columns={
        'home_id': 'team_id',
        'home_display_name': 'team_name',
        'home_current_rank': 'rank'
    })

    # Get away teams with rankings
    away_ranked = schedule[schedule['away_current_rank'] <= 25][
        ['away_id', 'away_display_name', 'away_current_rank']
    ].rename(columns={
        'away_id': 'team_id',
        'away_display_name': 'team_name',
        'away_current_rank': 'rank'
    })

    # Combine and get best (lowest) rank for each team
    all_ranked = pd.concat([home_ranked, away_ranked])
    best_ranks = all_ranked.groupby('team_id').agg({
        'team_name': 'first',
        'rank': 'min'
    }).reset_index().rename(columns={'rank': 'best_ap_rank'})

    print(f"  Found {len(best_ranks)} teams that have been in AP Top 25")

    return best_ranks


def build_player_season_analytics(player_box, rosters, ap_teams):
    """
    Build player_season_analytic_2026 table.
    Aggregates player box scores to season totals and joins with roster info.
    """
    print("\nBuilding player_season_analytic_2026...")

    # Filter to players who actually played (have minutes)
    played = player_box[player_box['minutes'].notna() & (player_box['minutes'] > 0)].copy()
    print(f"  Players with minutes: {len(played)} game appearances")

    # Aggregate to season totals
    agg_cols = {
        'game_id': 'nunique',  # Games played
        'minutes': 'sum',
        'field_goals_made': 'sum',
        'field_goals_attempted': 'sum',
        'three_point_field_goals_made': 'sum',
        'three_point_field_goals_attempted': 'sum',
        'free_throws_made': 'sum',
        'free_throws_attempted': 'sum',
        'offensive_rebounds': 'sum',
        'defensive_rebounds': 'sum',
        'rebounds': 'sum',
        'assists': 'sum',
        'steals': 'sum',
        'blocks': 'sum',
        'turnovers': 'sum',
        'fouls': 'sum',
        'points': 'sum',
        'starter': 'sum',  # Games started
        'team_score': 'mean',  # Avg team score (context)
        'opponent_team_score': 'mean',  # Avg opp score (context)
    }

    player_season = played.groupby([
        'athlete_id', 'athlete_display_name', 'team_id', 'team_name',
        'team_display_name', 'team_location', 'athlete_position_name', 'athlete_position_abbreviation'
    ]).agg(agg_cols).reset_index()

    # Rename columns
    player_season = player_season.rename(columns={
        'game_id': 'games_played',
        'starter': 'games_started'
    })

    print(f"  Aggregated to {len(player_season)} player-seasons")

    # Calculate per-game averages
    for col in ['minutes', 'points', 'rebounds', 'assists', 'steals', 'blocks', 'turnovers']:
        player_season[f'{col}_per_game'] = (
            player_season[col] / player_season['games_played']
        ).round(1)

    # Calculate per-40 rates (per 40 minutes played)
    minutes_factor = 40 / player_season['minutes'].replace(0, np.nan)
    for col in ['points', 'rebounds', 'assists', 'steals', 'blocks', 'turnovers']:
        player_season[f'{col}_per_40'] = (
            player_season[col] * minutes_factor
        ).round(1)

    # Calculate shooting percentages
    player_season['fg_pct'] = (
        player_season['field_goals_made'] /
        player_season['field_goals_attempted'].replace(0, np.nan) * 100
    ).round(1)

    player_season['three_pt_pct'] = (
        player_season['three_point_field_goals_made'] /
        player_season['three_point_field_goals_attempted'].replace(0, np.nan) * 100
    ).round(1)

    player_season['ft_pct'] = (
        player_season['free_throws_made'] /
        player_season['free_throws_attempted'].replace(0, np.nan) * 100
    ).round(1)

    # Calculate effective FG%
    player_season['efg_pct'] = (
        (player_season['field_goals_made'] + 0.5 * player_season['three_point_field_goals_made']) /
        player_season['field_goals_attempted'].replace(0, np.nan) * 100
    ).round(1)

    # Calculate true shooting %
    player_season['ts_pct'] = (
        player_season['points'] /
        (2 * (player_season['field_goals_attempted'] + 0.44 * player_season['free_throws_attempted'])).replace(0, np.nan) * 100
    ).round(1)

    # Add AP Top 25 flag
    # Ensure team_id types match (operate on copy to avoid side effects)
    player_season['team_id'] = pd.to_numeric(player_season['team_id'], errors='coerce').fillna(0).astype(int)
    ap_teams_copy = ap_teams.copy()
    ap_teams_copy['team_id'] = pd.to_numeric(ap_teams_copy['team_id'], errors='coerce').fillna(0).astype(int)

    player_season = player_season.merge(
        ap_teams_copy[['team_id', 'best_ap_rank']],
        on='team_id',
        how='left'
    )
    player_season['is_ap_top25'] = player_season['best_ap_rank'].notna()

    # Join with roster data to get height, year, portal status
    print("  Joining with roster data...")

    # Prepare roster for join - match on team name and player name
    roster_info = rosters[[
        'team', 'name', 'total_inches', 'year_clean', 'primary_position',
        'previous_school_clean', 'redshirt', 'conference', 'division'
    ]].copy()

    roster_info = roster_info.rename(columns={
        'team': 'roster_team_location',  # Will be used for join
        'name': 'roster_name',
        'total_inches': 'height_inches',
        'year_clean': 'class_year',
        'primary_position': 'roster_position',
        'previous_school_clean': 'previous_school',
        'redshirt': 'is_redshirt'
    })

    # Add numeric year for experience calculations
    roster_info['year_numeric'] = roster_info['class_year'].map(YEAR_MAP).fillna(0).astype(int)

    # Add portal flag (has previous school)
    roster_info['is_transfer'] = roster_info['previous_school'].notna()

    # Apply team name standardization for better matching
    player_season['team_location_std'] = player_season['team_location'].apply(standardize_team_name)
    roster_info['team_location_std'] = roster_info['roster_team_location'].apply(standardize_team_name)

    # Normalize names for matching
    player_season['name_normalized'] = (
        player_season['athlete_display_name']
        .str.lower()
        .str.strip()
        .str.replace(r'[^a-z\s]', '', regex=True)
    )

    roster_info['name_normalized'] = (
        roster_info['roster_name']
        .str.lower()
        .str.strip()
        .str.replace(r'[^a-z\s]', '', regex=True)
    )

    # Join on both team AND name to avoid false matches for common names
    player_season = player_season.merge(
        roster_info.drop(columns=['roster_name', 'roster_team_location']),
        on=['team_location_std', 'name_normalized'],
        how='left'
    )

    # Clean up temporary columns
    player_season = player_season.drop(columns=['name_normalized', 'team_location_std'])

    # Fill missing values
    player_season['is_transfer'] = player_season['is_transfer'].fillna(False)
    player_season['is_redshirt'] = player_season['is_redshirt'].fillna(0).astype(bool)

    print(f"  Final player_season_analytic: {len(player_season)} rows")
    print(f"  AP Top 25 players: {player_season['is_ap_top25'].sum()}")
    print(f"  Transfer players: {player_season['is_transfer'].sum()}")

    return player_season


def compute_minutes_weighted_team_metrics(player_season):
    """
    Compute minutes-weighted roster metrics per team from player_season data.

    Returns DataFrame with one row per team containing:
    - exp_minutes_weighted: minutes-weighted experience index
    - minutes_share_freshman/sophomore/junior/senior_plus: class distribution
    - minutes_share_transfer: share of minutes from transfers
    - num_transfers_in_rotation: count of transfers with ≥10 mpg
    - minutes_share_guard/wing/big: positional distribution
    - avg_height_guard/wing/big: height by position
    - rotation_size_10mpg: count of players with ≥10 mpg
    """
    print("  Computing minutes-weighted team metrics...")

    # Filter to players with meaningful minutes
    players = player_season[player_season['minutes'] > 0].copy()

    # Map positions to archetypes (Guard/Wing/Big)
    def get_archetype(pos):
        if pd.isna(pos):
            return 'Unknown'
        pos = str(pos).upper()
        if 'GUARD' in pos or pos in ['G', 'PG', 'SG', 'POINT GUARD', 'SHOOTING GUARD']:
            return 'Guard'
        elif 'FORWARD' in pos or pos in ['F', 'SF', 'PF', 'SMALL FORWARD', 'POWER FORWARD', 'WING']:
            return 'Wing'
        elif 'CENTER' in pos or pos in ['C', 'POST']:
            return 'Big'
        else:
            return 'Unknown'

    # Use roster_position if available, otherwise athlete_position_name
    players['archetype'] = players['roster_position'].fillna(
        players['athlete_position_name']
    ).apply(get_archetype)

    # Map class year to numeric (1-5)
    players['exp_numeric'] = players['year_numeric'].fillna(0)

    # Class groupings
    players['is_freshman'] = players['exp_numeric'] == 1
    players['is_sophomore'] = players['exp_numeric'] == 2
    players['is_junior'] = players['exp_numeric'] == 3
    players['is_senior_plus'] = players['exp_numeric'] >= 4

    # Calculate per-team metrics
    def team_minutes_metrics(group):
        total_minutes = group['minutes'].sum()
        total_players = len(group)

        if total_minutes == 0:
            return pd.Series({})

        # Minutes-weighted experience
        exp_weighted = (group['minutes'] * group['exp_numeric']).sum() / total_minutes

        # Class minute shares
        fr_minutes = group[group['is_freshman']]['minutes'].sum()
        so_minutes = group[group['is_sophomore']]['minutes'].sum()
        jr_minutes = group[group['is_junior']]['minutes'].sum()
        sr_minutes = group[group['is_senior_plus']]['minutes'].sum()

        # Transfer metrics
        transfer_minutes = group[group['is_transfer'] == True]['minutes'].sum()

        # Rotation (≥10 mpg)
        group['mpg'] = group['minutes'] / group['games_played'].replace(0, np.nan)
        rotation_players = group[group['mpg'] >= 10]
        rotation_size = len(rotation_players)
        transfers_in_rotation = len(rotation_players[rotation_players['is_transfer'] == True])

        # Positional minutes
        guard_minutes = group[group['archetype'] == 'Guard']['minutes'].sum()
        wing_minutes = group[group['archetype'] == 'Wing']['minutes'].sum()
        big_minutes = group[group['archetype'] == 'Big']['minutes'].sum()

        # Height by position
        guards = group[group['archetype'] == 'Guard']
        wings = group[group['archetype'] == 'Wing']
        bigs = group[group['archetype'] == 'Big']

        avg_height_guard = guards['height_inches'].mean() if len(guards) > 0 else np.nan
        avg_height_wing = wings['height_inches'].mean() if len(wings) > 0 else np.nan
        avg_height_big = bigs['height_inches'].mean() if len(bigs) > 0 else np.nan

        return pd.Series({
            'exp_minutes_weighted': exp_weighted,
            'minutes_share_freshman': fr_minutes / total_minutes,
            'minutes_share_sophomore': so_minutes / total_minutes,
            'minutes_share_junior': jr_minutes / total_minutes,
            'minutes_share_senior_plus': sr_minutes / total_minutes,
            'minutes_share_transfer': transfer_minutes / total_minutes,
            'num_transfers_in_rotation': transfers_in_rotation,
            'rotation_size_10mpg': rotation_size,
            'minutes_share_guard': guard_minutes / total_minutes,
            'minutes_share_wing': wing_minutes / total_minutes,
            'minutes_share_big': big_minutes / total_minutes,
            'avg_height_guard': avg_height_guard,
            'avg_height_wing': avg_height_wing,
            'avg_height_big': avg_height_big,
        })

    # Group by team and compute metrics
    team_metrics = players.groupby('team_id').apply(team_minutes_metrics).reset_index()

    # Round percentages
    pct_cols = [c for c in team_metrics.columns if 'share' in c]
    for col in pct_cols:
        team_metrics[col] = (team_metrics[col] * 100).round(1)

    team_metrics['exp_minutes_weighted'] = team_metrics['exp_minutes_weighted'].round(2)
    height_cols = [c for c in team_metrics.columns if 'avg_height' in c]
    for col in height_cols:
        team_metrics[col] = team_metrics[col].round(1)

    # Compute league average height for height_gap calculation
    all_heights = players[players['height_inches'].notna()]['height_inches']
    league_avg_height = all_heights.mean() if len(all_heights) > 0 else 70.0

    print(f"    League avg height: {league_avg_height:.1f} inches")
    print(f"    Computed metrics for {len(team_metrics)} teams")

    return team_metrics, league_avg_height


def build_team_season_analytics(player_box, team_box, rosters, ap_teams, schedule, player_season=None):
    """
    Build team_season_analytic_2026 table.
    Aggregates team performance and roster composition metrics.

    If player_season is provided, computes minutes-weighted metrics.
    """
    print("\nBuilding team_season_analytic_2026...")

    # Compute minutes-weighted metrics if player_season available
    minutes_weighted_metrics = None
    league_avg_height = 70.0
    if player_season is not None:
        minutes_weighted_metrics, league_avg_height = compute_minutes_weighted_team_metrics(player_season)

    # Get team game-level aggregates
    team_games = team_box.groupby('team_id').agg({
        'game_id': 'nunique',
        'team_score': ['sum', 'mean'],
        'opponent_team_score': ['sum', 'mean'],
    }).reset_index()

    team_games.columns = [
        'team_id', 'games_played', 'total_points', 'ppg',
        'total_opp_points', 'opp_ppg'
    ]

    # Ensure team_id is int
    team_games['team_id'] = pd.to_numeric(team_games['team_id'], errors='coerce').fillna(0).astype(int)

    # Calculate W-L from schedule
    home_results = schedule[['home_id', 'home_winner']].copy()
    home_results['team_id'] = pd.to_numeric(home_results['home_id'], errors='coerce').fillna(0).astype(int)
    home_results['won'] = home_results['home_winner']
    home_results = home_results[['team_id', 'won']]

    away_results = schedule[['away_id', 'away_winner']].copy()
    away_results['team_id'] = pd.to_numeric(away_results['away_id'], errors='coerce').fillna(0).astype(int)
    away_results['won'] = away_results['away_winner']
    away_results = away_results[['team_id', 'won']]

    all_results = pd.concat([home_results, away_results])

    win_loss = all_results.groupby('team_id').agg({
        'won': ['sum', 'count']
    }).reset_index()
    win_loss.columns = ['team_id', 'wins', 'total_games']
    win_loss['losses'] = win_loss['total_games'] - win_loss['wins']
    win_loss['win_pct'] = (win_loss['wins'] / win_loss['total_games'].replace(0, np.nan) * 100).round(1)

    # Merge team games with W-L
    team_season = team_games.merge(win_loss[['team_id', 'wins', 'losses', 'win_pct']],
                                   on='team_id', how='left')

    # Get team names (include team_location for roster matching)
    team_names = team_box[['team_id', 'team_display_name', 'team_name', 'team_location']].drop_duplicates()
    team_season = team_season.merge(team_names, on='team_id', how='left')

    # Calculate point differential
    team_season['point_diff'] = (team_season['ppg'] - team_season['opp_ppg']).round(1)

    print(f"  Team game stats: {len(team_season)} teams")

    # =====================
    # Roster Composition Metrics
    # =====================
    print("  Calculating roster composition metrics...")

    # Prepare roster data with numeric year
    roster_data = rosters.copy()
    roster_data['year_numeric'] = roster_data['year_clean'].map(YEAR_MAP).fillna(0).astype(int)
    roster_data['is_transfer'] = roster_data['previous_school_clean'].notna()
    roster_data['is_guard'] = roster_data['primary_position'] == 'GUARD'
    roster_data['is_forward'] = roster_data['primary_position'] == 'FORWARD'
    roster_data['is_center'] = roster_data['primary_position'] == 'CENTER'

    # Aggregate roster metrics by team
    roster_agg = roster_data.groupby('team').agg({
        'name': 'count',  # roster size
        'total_inches': ['mean', 'std'],  # height stats
        'year_numeric': ['mean', 'min', 'max'],  # experience
        'is_transfer': 'sum',  # transfer count
        'is_guard': 'sum',
        'is_forward': 'sum',
        'is_center': 'sum',
        'conference': 'first',  # conference from roster
        'division': 'first',  # division from roster
    }).reset_index()

    roster_agg.columns = [
        'team', 'roster_size',
        'avg_height_inches', 'height_std',
        'avg_year', 'min_year', 'max_year',
        'transfer_count',
        'guard_count', 'forward_count', 'center_count',
        'conference', 'division'
    ]

    # Convert height to feet-inches string for readability
    roster_agg['avg_height_ft'] = roster_agg['avg_height_inches'].apply(
        lambda x: f"{int(x // 12)}'{int(x % 12)}\"" if pd.notna(x) else None
    )

    # Calculate experience distribution
    freshmen = roster_data[roster_data['year_numeric'] == 1].groupby('team').size().reset_index(name='freshmen_count')
    upperclassmen = roster_data[roster_data['year_numeric'] >= 3].groupby('team').size().reset_index(name='upperclassmen_count')

    roster_agg = roster_agg.merge(freshmen, on='team', how='left')
    roster_agg = roster_agg.merge(upperclassmen, on='team', how='left')
    roster_agg['freshmen_count'] = roster_agg['freshmen_count'].fillna(0).astype(int)
    roster_agg['upperclassmen_count'] = roster_agg['upperclassmen_count'].fillna(0).astype(int)

    # Calculate transfer percentage
    roster_agg['transfer_pct'] = (roster_agg['transfer_count'] / roster_agg['roster_size'] * 100).round(1)

    # Round numeric columns
    roster_agg['avg_height_inches'] = roster_agg['avg_height_inches'].round(1)
    roster_agg['height_std'] = roster_agg['height_std'].round(1)
    roster_agg['avg_year'] = roster_agg['avg_year'].round(2)

    print(f"  Roster metrics calculated for {len(roster_agg)} teams")

    # =====================
    # Bench Depth Metrics
    # =====================
    print("  Calculating bench depth metrics...")

    # Get players who played and their minutes
    played = player_box[player_box['minutes'].notna() & (player_box['minutes'] > 0)].copy()

    player_minutes = played.groupby(['team_id', 'athlete_id', 'athlete_display_name']).agg({
        'minutes': 'sum',
        'points': 'sum',
        'game_id': 'nunique'
    }).reset_index()

    # Calculate bench stats per team
    def get_bench_metrics(group):
        group = group.sort_values('minutes', ascending=False)
        total_minutes = group['minutes'].sum()
        total_points = group['points'].sum()

        # Top 5 = starters, rest = bench
        if len(group) >= 5:
            starter_minutes = group.head(5)['minutes'].sum()
            bench_minutes = group.iloc[5:]['minutes'].sum()
            bench_points = group.iloc[5:]['points'].sum()
            bench_players = len(group) - 5
        else:
            starter_minutes = total_minutes
            bench_minutes = 0
            bench_points = 0
            bench_players = 0

        return pd.Series({
            'total_players_used': len(group),
            'total_team_minutes': total_minutes,
            'starter_minutes': starter_minutes,
            'bench_minutes': bench_minutes,
            'bench_points': bench_points,
            'bench_players': bench_players,
            'bench_minutes_pct': (bench_minutes / total_minutes * 100) if total_minutes > 0 else 0,
            'bench_points_pct': (bench_points / total_points * 100) if total_points > 0 else 0,
        })

    bench_metrics = player_minutes.groupby('team_id').apply(get_bench_metrics).reset_index()
    bench_metrics = bench_metrics.round(1)
    bench_metrics['team_id'] = pd.to_numeric(bench_metrics['team_id'], errors='coerce').fillna(0).astype(int)

    # Merge bench metrics with team_season
    team_season = team_season.merge(bench_metrics, on='team_id', how='left')

    # =====================
    # Add AP Ranking Info
    # =====================
    # Ensure team_id types match
    team_season['team_id'] = pd.to_numeric(team_season['team_id'], errors='coerce').fillna(0).astype(int)
    ap_teams_copy = ap_teams.copy()
    ap_teams_copy['team_id'] = pd.to_numeric(ap_teams_copy['team_id'], errors='coerce').fillna(0).astype(int)

    team_season = team_season.merge(
        ap_teams_copy[['team_id', 'best_ap_rank']],
        on='team_id',
        how='left'
    )
    team_season['is_ap_top25'] = team_season['best_ap_rank'].notna()

    # =====================
    # Join Roster Metrics
    # =====================
    # Need to match team names between box scores and roster data
    # Box scores use team_location (e.g., "UC Riverside") which matches roster team names better

    # First try matching on team_location
    team_season = team_season.merge(
        roster_agg,
        left_on='team_location',
        right_on='team',
        how='left'
    )

    # For unmatched, try display_name
    unmatched_mask = team_season['roster_size'].isna()
    if unmatched_mask.sum() > 0:
        # Get team_display_name for unmatched teams
        unmatched_teams = team_season[unmatched_mask]['team_display_name'].unique()

        # Try matching display_name (e.g., "UC Riverside Highlanders") to roster team
        for display_name in unmatched_teams:
            # Check if roster team name is contained in display_name
            for roster_team in roster_agg['team'].unique():
                if roster_team.lower() in display_name.lower():
                    # Get the roster row
                    roster_row = roster_agg[roster_agg['team'] == roster_team].iloc[0]
                    # Update team_season where display_name matches
                    mask = team_season['team_display_name'] == display_name
                    for col in roster_agg.columns:
                        if col != 'team':
                            team_season.loc[mask, col] = roster_row[col]
                    break

    # Clean up duplicate columns
    if 'team' in team_season.columns:
        team_season = team_season.drop(columns=['team'])

    # =====================
    # Merge Minutes-Weighted Metrics
    # =====================
    if minutes_weighted_metrics is not None:
        print("  Merging minutes-weighted metrics...")
        # Ensure team_id types match
        minutes_weighted_metrics['team_id'] = pd.to_numeric(
            minutes_weighted_metrics['team_id'], errors='coerce'
        ).fillna(0).astype(int)

        team_season = team_season.merge(
            minutes_weighted_metrics,
            on='team_id',
            how='left'
        )

        # Calculate height gap vs league
        team_season['height_gap_vs_league'] = (
            team_season['avg_height_inches'] - league_avg_height
        ).round(1)

        print(f"    Added {len(minutes_weighted_metrics.columns) - 1} minutes-weighted metrics")

    print(f"  Final team_season_analytic: {len(team_season)} rows")
    print(f"  AP Top 25 teams: {team_season['is_ap_top25'].sum()}")

    return team_season


def validate_data(player_season, team_season):
    """Run validation checks on the analytics tables."""
    print("\n" + "=" * 60)
    print("Data Validation")
    print("=" * 60)

    # Player validation
    print("\n[Player Season Analytics]")
    print(f"  Total players: {len(player_season)}")
    print(f"  Players with height data: {player_season['height_inches'].notna().sum()}")
    print(f"  Players with class year: {player_season['class_year'].notna().sum()}")
    print(f"  AP Top 25 team players: {player_season['is_ap_top25'].sum()}")
    print(f"  Transfer players: {player_season['is_transfer'].sum()}")

    # Check for key columns
    key_cols = ['points', 'rebounds', 'assists', 'minutes', 'games_played']
    missing = [c for c in key_cols if c not in player_season.columns]
    if missing:
        print(f"  WARNING: Missing columns: {missing}")
    else:
        print(f"  All key stat columns present")

    # Team validation
    print("\n[Team Season Analytics]")
    print(f"  Total teams: {len(team_season)}")
    print(f"  Teams with roster data: {team_season['roster_size'].notna().sum()}")
    print(f"  AP Top 25 teams: {team_season['is_ap_top25'].sum()}")

    # Check for expected range values
    if 'win_pct' in team_season.columns:
        print(f"  Win pct range: {team_season['win_pct'].min():.1f}% - {team_season['win_pct'].max():.1f}%")
    if 'avg_height_inches' in team_season.columns:
        avg_h = team_season['avg_height_inches'].dropna()
        if len(avg_h) > 0:
            print(f"  Avg height range: {avg_h.min():.1f}\" - {avg_h.max():.1f}\"")

    print("\nValidation complete!")


def main():
    """Main entry point."""
    print("=" * 60)
    print("Building Roster Analytics Tables")
    print("=" * 60)

    # Load all data
    rosters, player_box, team_box, schedule = load_data()

    # Get AP Top 25 teams
    ap_teams = get_ap_top25_teams(schedule)

    # Build player season analytics
    player_season = build_player_season_analytics(player_box, rosters, ap_teams)

    # Build team season analytics (pass player_season for minutes-weighted metrics)
    team_season = build_team_season_analytics(
        player_box, team_box, rosters, ap_teams, schedule, player_season=player_season
    )

    # Run validation
    validate_data(player_season, team_season)

    # Save outputs
    print("\n" + "=" * 60)
    print("Saving Output Files")
    print("=" * 60)

    player_path = PROCESSED_DIR / "player_season_analytic_2026.csv"
    player_season.to_csv(player_path, index=False)
    print(f"  Saved: {player_path} ({len(player_season)} rows)")

    team_path = PROCESSED_DIR / "team_season_analytic_2026.csv"
    team_season.to_csv(team_path, index=False)
    print(f"  Saved: {team_path} ({len(team_season)} rows)")

    # Also save AP Top 25 filtered versions
    player_top25 = player_season[player_season['is_ap_top25'] == True]
    player_top25_path = PROCESSED_DIR / "player_season_analytic_2026_top25.csv"
    player_top25.to_csv(player_top25_path, index=False)
    print(f"  Saved: {player_top25_path} ({len(player_top25)} rows)")

    team_top25 = team_season[team_season['is_ap_top25'] == True]
    team_top25_path = PROCESSED_DIR / "team_season_analytic_2026_top25.csv"
    team_top25.to_csv(team_top25_path, index=False)
    print(f"  Saved: {team_top25_path} ({len(team_top25)} rows)")

    # Show file sizes
    print("\nFile sizes:")
    for path in [player_path, team_path, player_top25_path, team_top25_path]:
        size_kb = path.stat().st_size / 1024
        print(f"  {path.name}: {size_kb:.1f} KB")

    print("\nDone!")


if __name__ == "__main__":
    main()
