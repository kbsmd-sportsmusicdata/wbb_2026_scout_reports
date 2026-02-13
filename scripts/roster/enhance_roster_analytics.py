"""
Enhance Roster Analytics with Additional Metrics.

This script enriches team_season_analytic_2026_top25 with:
1. Fixed roster metrics for teams with data quality issues (USC, Ole Miss, TCU, etc.)
2. Team efficiency metrics (ORtg, DRtg, Net, Pace)
3. Role-weighted experience by position
4. Transfer impact metrics (star transfers, top-3 transfer minutes)
5. Points-weighted height
6. Guard-big balance index
7. Poll/game context fields (if polls_games data available)

Usage:
    python scripts/roster/enhance_roster_analytics.py
    python scripts/roster/enhance_roster_analytics.py --polls-games path/to/file.csv

Output:
    data/processed/roster/team_season_analytic_2026_top25_enriched.csv
"""

import argparse
from datetime import date
from pathlib import Path
import numpy as np
import pandas as pd

# Configuration
DATA_DIR = Path("data")
RAW_DIR = DATA_DIR / "raw" / "2026"
PROCESSED_DIR = DATA_DIR / "processed"
ROSTER_DIR = PROCESSED_DIR / "roster"

# Master mapping file for conference alignment and team name standardization
MASTER_MAPPING_PATH = RAW_DIR / "master_player_season_mapping_2026.csv"

# Allowed directories for file reads (security)
ALLOWED_DATA_DIRS = [DATA_DIR.resolve(), Path(".").resolve()]

# Extended team name mapping (box score team_location -> roster team name)
TEAM_NAME_MAP = {
    'Connecticut': 'UConn',
    'Louisiana State': 'LSU',
    'Southern California': 'Southern Cal',
    'USC': 'Southern Cal',
    'Ole Miss': 'Mississippi',  # Box shows "Ole Miss", roster has "Mississippi"
    'North Carolina': 'UNC',
    'Michigan St.': 'Michigan State',
    'Ohio St.': 'Ohio State',
    'Oklahoma St.': 'Oklahoma State',
    'Iowa St.': 'Iowa State',
    'Mississippi St.': 'Mississippi State',
    'Miami': 'Miami (FL)',
    'Arizona St.': 'Arizona State',
    'Brigham Young': 'BYU',
    'TCU': 'Texas Christian',
}


def get_archetype(pos):
    """
    Map position string to archetype (Guard/Wing/Big).
    Used for positional analysis across multiple functions.
    """
    if pd.isna(pos):
        return 'Unknown'
    pos = str(pos).upper()
    if 'GUARD' in pos or pos in ['G', 'PG', 'SG', 'POINT GUARD', 'SHOOTING GUARD']:
        return 'Guard'
    elif 'FORWARD' in pos or pos in ['F', 'SF', 'PF', 'SMALL FORWARD', 'POWER FORWARD', 'WING']:
        return 'Wing'
    elif 'CENTER' in pos or pos in ['C', 'POST']:
        return 'Big'
    return 'Unknown'


def validate_file_path(file_path, allowed_dirs=None):
    """
    Validate that a file path is within allowed directories.
    Prevents path traversal attacks.
    """
    if allowed_dirs is None:
        allowed_dirs = ALLOWED_DATA_DIRS

    resolved = Path(file_path).resolve()

    for allowed in allowed_dirs:
        try:
            resolved.relative_to(allowed)
            return resolved
        except ValueError:
            continue

    raise ValueError("File path is outside allowed directories")


def find_polls_games_file():
    """
    Search for polls_games file using flexible pattern matching.
    Returns path if found, None otherwise.
    """
    patterns = [
        "joined_polls_games_*.csv",
        "polls_games_joined*.csv",
        "*polls*games*.csv",
    ]

    search_dirs = [RAW_DIR, PROCESSED_DIR, DATA_DIR]

    all_matches = []
    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
        for pattern in patterns:
            all_matches.extend(search_dir.glob(pattern))

    if all_matches:
        # Return the most recently modified file among all unique matches.
        return max(set(all_matches), key=lambda p: p.stat().st_mtime)

    return None


def load_data():
    """Load all required data sources."""
    print("Loading data sources...")

    # Load current Top 25 team analytics
    team_top25 = pd.read_csv(ROSTER_DIR / "team_season_analytic_2026_top25.csv")
    print(f"  Team Top 25: {len(team_top25)} teams")

    # Load player analytics for recomputing metrics
    player_top25 = pd.read_csv(ROSTER_DIR / "player_season_analytic_2026_top25.csv")
    print(f"  Player Top 25: {len(player_top25)} players")

    # Load full player data for missing teams
    player_full = pd.read_csv(ROSTER_DIR / "player_season_analytic_2026.csv")
    print(f"  Player Full: {len(player_full)} players")

    # Load roster data
    rosters = pd.read_csv(RAW_DIR / "wbb_rosters_2025_26.csv")
    print(f"  Rosters: {len(rosters)} players")

    # Load team box scores for efficiency metrics
    team_box = pd.read_parquet(RAW_DIR / "team_box_2026.parquet")
    print(f"  Team box: {len(team_box)} rows")

    # Load game analysis if available
    game_analysis_path = PROCESSED_DIR / "game_analysis.csv"
    game_analysis = None
    if game_analysis_path.exists():
        game_analysis = pd.read_csv(game_analysis_path)
        print(f"  Game analysis: {len(game_analysis)} rows")

    return team_top25, player_top25, player_full, rosters, team_box, game_analysis


def fix_missing_roster_metrics(team_top25, player_full, rosters):
    """
    Fix teams with missing roster metrics by recomputing from player/roster data.
    """
    print("\n" + "=" * 60)
    print("Fixing Missing Roster Metrics")
    print("=" * 60)

    # Identify teams with missing data
    missing_mask = (
        team_top25['roster_size'].isna() |
        team_top25['avg_height_inches'].isna() |
        (team_top25['exp_minutes_weighted'] == 0)
    )
    missing_teams = team_top25[missing_mask]['team_display_name'].tolist()
    print(f"  Teams with missing data: {missing_teams}")

    # Create standardized team name column for matching
    def standardize_for_roster(name):
        """Convert box score team name to roster team name."""
        if pd.isna(name):
            return name
        # Try direct mapping first
        if name in TEAM_NAME_MAP:
            return TEAM_NAME_MAP[name]
        # Try extracting from display name
        for key, val in TEAM_NAME_MAP.items():
            if key.lower() in name.lower():
                return val
        return name

    # For each missing team, try to find roster data
    for team_name in missing_teams:
        print(f"\n  Processing: {team_name}")

        # Get team_id and team_location from team_top25
        team_row = team_top25[team_top25['team_display_name'] == team_name].iloc[0]
        team_id = team_row['team_id']
        team_location = team_row.get('team_location', '')

        # Try to find matching roster
        roster_name = standardize_for_roster(team_location)
        print(f"    Looking for roster: {roster_name}")

        team_roster = rosters[rosters['team'].str.lower() == roster_name.lower()].copy()

        if len(team_roster) == 0:
            # Try partial match
            for roster_team in rosters['team'].unique():
                if roster_name.lower() in roster_team.lower() or roster_team.lower() in roster_name.lower():
                    team_roster = rosters[rosters['team'] == roster_team]
                    print(f"    Found partial match: {roster_team}")
                    break

        if len(team_roster) > 0:
            # Compute roster metrics
            roster_size = len(team_roster)
            avg_height = team_roster['total_inches'].mean()
            height_std = team_roster['total_inches'].std()

            # Year mapping
            year_map = {
                'Freshman': 1, 'Fr.': 1, 'FR': 1,
                'Sophomore': 2, 'So.': 2, 'SO': 2,
                'Junior': 3, 'Jr.': 3, 'JR': 3,
                'Senior': 4, 'Sr.': 4, 'SR': 4,
                'Graduate': 5, 'Gr.': 5, 'GR': 5, 'Graduate Student': 5,
            }
            team_roster['year_num'] = team_roster['year_clean'].map(year_map)
            avg_year = team_roster['year_num'].mean()

            # Transfer count
            transfer_count = team_roster['previous_school_clean'].notna().sum()
            transfer_pct = (transfer_count / roster_size * 100) if roster_size > 0 else 0

            # Position counts
            guard_count = (team_roster['primary_position'] == 'GUARD').sum()
            forward_count = (team_roster['primary_position'] == 'FORWARD').sum()
            center_count = (team_roster['primary_position'] == 'CENTER').sum()

            # Update team_top25
            idx = team_top25[team_top25['team_display_name'] == team_name].index[0]
            team_top25.loc[idx, 'roster_size'] = roster_size
            team_top25.loc[idx, 'avg_height_inches'] = round(avg_height, 1)
            team_top25.loc[idx, 'height_std'] = round(height_std, 1) if pd.notna(height_std) else None
            team_top25.loc[idx, 'avg_year'] = round(avg_year, 2)
            team_top25.loc[idx, 'transfer_count'] = transfer_count
            team_top25.loc[idx, 'transfer_pct'] = round(transfer_pct, 1)
            team_top25.loc[idx, 'guard_count'] = guard_count
            team_top25.loc[idx, 'forward_count'] = forward_count
            team_top25.loc[idx, 'center_count'] = center_count

            print(f"    Updated: roster_size={roster_size}, avg_height={avg_height:.1f}, transfers={transfer_count}")
        else:
            print(f"    WARNING: No roster data found for {team_name}")

    # Recompute minutes-weighted metrics from player data
    print("\n  Recomputing minutes-weighted metrics from player data...")

    for team_name in missing_teams:
        team_row = team_top25[team_top25['team_display_name'] == team_name]
        if len(team_row) == 0:
            continue

        team_id = team_row.iloc[0]['team_id']

        # Get players for this team from full player data
        team_players = player_full[player_full['team_id'] == team_id].copy()

        if len(team_players) == 0:
            print(f"    No player data for {team_name}")
            continue

        # Filter to players with minutes
        team_players = team_players[team_players['minutes'] > 0]

        if len(team_players) == 0:
            continue

        total_minutes = team_players['minutes'].sum()

        # Minutes-weighted experience
        team_players['year_num'] = team_players['year_numeric']
        exp_weighted = (team_players['minutes'] * team_players['year_num']).sum() / total_minutes if total_minutes > 0 else 0

        # Transfer minutes share
        transfer_minutes = team_players[team_players['is_transfer'] == True]['minutes'].sum()
        minutes_share_transfer = (transfer_minutes / total_minutes * 100) if total_minutes > 0 else 0

        # Class shares
        def get_class_share(year_val):
            class_mins = team_players[team_players['year_num'] == year_val]['minutes'].sum()
            return (class_mins / total_minutes * 100) if total_minutes > 0 else 0

        # Rotation size
        team_players['mpg'] = team_players['minutes'] / team_players['games_played'].replace(0, np.nan)
        rotation_size = (team_players['mpg'] >= 10).sum()
        transfers_in_rotation = ((team_players['mpg'] >= 10) & (team_players['is_transfer'] == True)).sum()

        # Update
        idx = team_top25[team_top25['team_display_name'] == team_name].index[0]
        team_top25.loc[idx, 'exp_minutes_weighted'] = round(exp_weighted, 2)
        team_top25.loc[idx, 'minutes_share_transfer'] = round(minutes_share_transfer, 1)
        team_top25.loc[idx, 'minutes_share_freshman'] = round(get_class_share(1), 1)
        team_top25.loc[idx, 'minutes_share_sophomore'] = round(get_class_share(2), 1)
        team_top25.loc[idx, 'minutes_share_junior'] = round(get_class_share(3), 1)
        team_top25.loc[idx, 'minutes_share_senior_plus'] = round(get_class_share(4) + get_class_share(5), 1)
        team_top25.loc[idx, 'rotation_size_10mpg'] = rotation_size
        team_top25.loc[idx, 'num_transfers_in_rotation'] = transfers_in_rotation

        print(f"    {team_name}: exp={exp_weighted:.2f}, transfer_mins={minutes_share_transfer:.1f}%, rotation={rotation_size}")

    return team_top25


def add_efficiency_metrics(team_top25, team_box, game_analysis):
    """
    Add team efficiency metrics: ORtg, DRtg, Net Rating, Pace.
    Uses game_analysis if available, otherwise computes from team_box.
    """
    print("\n" + "=" * 60)
    print("Adding Efficiency Metrics")
    print("=" * 60)

    # Get team IDs we need
    team_ids = team_top25['team_id'].unique()

    if game_analysis is not None and 'offensive_rating' in game_analysis.columns:
        print("  Using game_analysis data...")

        # Aggregate to team-season
        team_eff = game_analysis[game_analysis['team_id'].isin(team_ids)].groupby('team_id').agg({
            'offensive_rating': 'mean',
            'defensive_rating': 'mean',
            'net_rating': 'mean',
            'possessions': 'mean',  # proxy for pace
        }).reset_index()

        team_eff.columns = ['team_id', 'offensive_eff', 'defensive_eff', 'net_eff', 'pace']

    else:
        print("  Computing from team_box data...")

        # Filter to Top 25 teams
        tb = team_box[team_box['team_id'].isin(team_ids)].copy()

        # Compute possessions per game (Dean Oliver formula)
        # Poss = FGA + 0.44 * FTA - ORB + TOV
        tb['possessions'] = (
            tb['field_goals_attempted'] +
            0.44 * tb['free_throws_attempted'] -
            tb['offensive_rebounds'] +
            tb['turnovers']
        )

        # Aggregate to team-season
        team_agg = tb.groupby('team_id').agg({
            'team_score': 'sum',
            'opponent_team_score': 'sum',
            'possessions': ['sum', 'mean'],
            'game_id': 'nunique'
        }).reset_index()

        team_agg.columns = ['team_id', 'total_pts', 'total_opp_pts', 'total_poss', 'avg_poss', 'games']

        # Calculate ratings (points per 100 possessions)
        team_agg['offensive_eff'] = (team_agg['total_pts'] / team_agg['total_poss'] * 100).round(1)
        team_agg['defensive_eff'] = (team_agg['total_opp_pts'] / team_agg['total_poss'] * 100).round(1)
        team_agg['net_eff'] = (team_agg['offensive_eff'] - team_agg['defensive_eff']).round(1)
        team_agg['pace'] = team_agg['avg_poss'].round(1)

        team_eff = team_agg[['team_id', 'offensive_eff', 'defensive_eff', 'net_eff', 'pace']]

    # Merge with team_top25
    team_top25 = team_top25.merge(team_eff, on='team_id', how='left')

    print(f"  Added efficiency metrics for {team_eff['team_id'].notna().sum()} teams")
    print(f"  ORtg range: {team_top25['offensive_eff'].min():.1f} - {team_top25['offensive_eff'].max():.1f}")
    print(f"  DRtg range: {team_top25['defensive_eff'].min():.1f} - {team_top25['defensive_eff'].max():.1f}")

    return team_top25


def add_role_weighted_experience(team_top25, player_full):
    """
    Add role-weighted experience by position archetype.
    exp_minutes_weighted_guard, exp_minutes_weighted_wing, exp_minutes_weighted_big
    """
    print("\n" + "=" * 60)
    print("Adding Role-Weighted Experience")
    print("=" * 60)

    team_ids = team_top25['team_id'].unique()
    players = player_full[player_full['team_id'].isin(team_ids)].copy()
    players = players[players['minutes'] > 0]

    # Map positions to archetypes (using module-level function)
    players['archetype'] = players['roster_position'].fillna(
        players['athlete_position_name']
    ).apply(get_archetype)

    players['year_num'] = players['year_numeric']

    # Compute per team
    results = []
    for team_id in team_ids:
        team_players = players[players['team_id'] == team_id]

        row = {'team_id': team_id}

        for arch in ['Guard', 'Wing', 'Big']:
            arch_players = team_players[team_players['archetype'] == arch]
            total_mins = arch_players['minutes'].sum()

            if total_mins > 0:
                exp_weighted = (arch_players['minutes'] * arch_players['year_num']).sum() / total_mins
                row[f'exp_minutes_weighted_{arch.lower()}'] = round(exp_weighted, 2)
            else:
                row[f'exp_minutes_weighted_{arch.lower()}'] = None

        results.append(row)

    role_exp = pd.DataFrame(results)
    team_top25 = team_top25.merge(role_exp, on='team_id', how='left')

    print(f"  Added role-weighted experience for {len(role_exp)} teams")

    return team_top25


def add_transfer_impact_metrics(team_top25, player_full):
    """
    Add transfer impact metrics:
    - transfer_minutes_top3: Total minutes by top 3 transfers
    - has_star_transfer: Boolean if any transfer averages 15+ PPG
    - transfer_ppg_leader: PPG of highest-scoring transfer
    """
    print("\n" + "=" * 60)
    print("Adding Transfer Impact Metrics")
    print("=" * 60)

    team_ids = team_top25['team_id'].unique()
    players = player_full[player_full['team_id'].isin(team_ids)].copy()
    players = players[players['minutes'] > 0]

    # Identify transfers
    transfers = players[players['is_transfer'] == True].copy()

    results = []
    for team_id in team_ids:
        team_transfers = transfers[transfers['team_id'] == team_id].copy()

        row = {'team_id': team_id}

        if len(team_transfers) > 0:
            # Sort by minutes and get top 3
            team_transfers = team_transfers.sort_values('minutes', ascending=False)
            top3 = team_transfers.head(3)

            row['transfer_minutes_top3'] = top3['minutes'].sum()
            row['transfer_ppg_leader'] = team_transfers['points_per_game'].max()
            row['has_star_transfer'] = (team_transfers['points_per_game'] >= 15).any()
            row['num_transfers_10mpg'] = (team_transfers['minutes'] / team_transfers['games_played'].replace(0, np.nan) >= 10).sum()
        else:
            row['transfer_minutes_top3'] = 0
            row['transfer_ppg_leader'] = 0
            row['has_star_transfer'] = False
            row['num_transfers_10mpg'] = 0

        results.append(row)

    transfer_metrics = pd.DataFrame(results)
    team_top25 = team_top25.merge(transfer_metrics, on='team_id', how='left')

    star_count = team_top25['has_star_transfer'].sum()
    print(f"  Teams with star transfer (15+ PPG): {star_count}")

    return team_top25


def add_points_weighted_height(team_top25, player_full):
    """
    Add points-weighted height metrics:
    - points_weighted_height: Team height weighted by scoring
    - points_weighted_height_guard/wing/big: By position
    """
    print("\n" + "=" * 60)
    print("Adding Points-Weighted Height")
    print("=" * 60)

    team_ids = team_top25['team_id'].unique()
    players = player_full[player_full['team_id'].isin(team_ids)].copy()
    players = players[(players['points'] > 0) & (players['height_inches'].notna())]

    # Map positions (using module-level function)
    players['archetype'] = players['roster_position'].fillna(
        players['athlete_position_name']
    ).apply(get_archetype)

    results = []
    for team_id in team_ids:
        team_players = players[players['team_id'] == team_id]

        row = {'team_id': team_id}

        # Team-level points-weighted height
        total_pts = team_players['points'].sum()
        if total_pts > 0:
            pts_weighted_ht = (team_players['points'] * team_players['height_inches']).sum() / total_pts
            row['points_weighted_height'] = round(pts_weighted_ht, 1)
        else:
            row['points_weighted_height'] = None

        # By position
        for arch in ['Guard', 'Wing', 'Big']:
            arch_players = team_players[team_players['archetype'] == arch]
            arch_pts = arch_players['points'].sum()

            if arch_pts > 0:
                arch_ht = (arch_players['points'] * arch_players['height_inches']).sum() / arch_pts
                row[f'points_weighted_height_{arch.lower()}'] = round(arch_ht, 1)
            else:
                row[f'points_weighted_height_{arch.lower()}'] = None

        results.append(row)

    height_metrics = pd.DataFrame(results)
    team_top25 = team_top25.merge(height_metrics, on='team_id', how='left')

    print(f"  Points-weighted height range: {team_top25['points_weighted_height'].min():.1f} - {team_top25['points_weighted_height'].max():.1f}")

    return team_top25


def add_guard_big_balance(team_top25):
    """
    Add guard-big balance index.
    Ranges from -1 (big-heavy) to +1 (guard-heavy).
    Formula: (guard_mins - big_mins) / (guard_mins + big_mins)
    """
    print("\n" + "=" * 60)
    print("Adding Guard-Big Balance Index")
    print("=" * 60)

    # Use existing minutes_share columns
    guard_share = team_top25['minutes_share_guard'].fillna(0)
    big_share = team_top25['minutes_share_big'].fillna(0)

    total = guard_share + big_share
    team_top25['guard_big_balance'] = np.where(
        total > 0,
        ((guard_share - big_share) / total).round(2),
        0
    )

    print(f"  Balance range: {team_top25['guard_big_balance'].min():.2f} to {team_top25['guard_big_balance'].max():.2f}")
    print(f"  Most guard-heavy: {team_top25.loc[team_top25['guard_big_balance'].idxmax(), 'team_display_name']}")
    print(f"  Most big-heavy: {team_top25.loc[team_top25['guard_big_balance'].idxmin(), 'team_display_name']}")

    return team_top25


def add_poll_game_context(team_top25, polls_games_path=None):
    """
    Add poll/game context fields if polls_games data is available.

    Args:
        team_top25: DataFrame with team data
        polls_games_path: Optional path to polls_games CSV. If provided, will be
                         validated to ensure it's within allowed data directories.
    """
    print("\n" + "=" * 60)
    print("Adding Poll/Game Context")
    print("=" * 60)

    # Check for polls_games file
    if polls_games_path is not None:
        # Validate provided path is within allowed directories
        try:
            polls_games_path = validate_file_path(polls_games_path)
        except ValueError as e:
            print(f"  ERROR: {e}")
            return team_top25
    else:
        # Use flexible file finder to locate polls_games data
        polls_games_path = find_polls_games_file()

    if polls_games_path is None or not Path(polls_games_path).exists():
        print("  No polls_games data found. Skipping poll context metrics.")
        print("  To add these metrics, place a file matching pattern:")
        print("    - data/raw/2026/joined_polls_games_*.csv")
        print("    - data/raw/2026/polls_games_joined*.csv")
        print("  Or specify path via --polls-games argument")
        return team_top25

    print(f"  Loading: {polls_games_path}")
    polls_games = pd.read_csv(polls_games_path)
    print(f"  Loaded {len(polls_games)} rows")

    # Known team name mismatches: team_top25 team_location -> polls_games team
    TEAM_NAME_MAPPING = {
        'North Carolina': 'UNC',
        # Add other mismatches here in the future
    }
    location_to_pg = {
        loc: TEAM_NAME_MAPPING.get(loc, loc)
        for loc in team_top25['team_location'].unique()
    }

    # Deduplicate game rows: each (team, game_id) should appear once
    if 'game_id' in polls_games.columns:
        polls_games = polls_games.drop_duplicates(subset=['team', 'game_id'])

    # Aggregate per team
    results = []
    for _, team_row in team_top25.iterrows():
        team_location = team_row['team_location']
        team_id = team_row['team_id']

        # Find matching polls_games team name
        pg_name = location_to_pg.get(team_location, team_location)

        team_games = polls_games[polls_games['team'] == pg_name]
        if len(team_games) == 0:
            continue

        row = {'team_id': team_id}

        # Top 25 games (opponent ranked <= 25; unranked coded as 99)
        opp_rank_col = 'game_Opponent Rank'
        if opp_rank_col in team_games.columns:
            top25_mask = team_games[opp_rank_col].fillna(99) <= 25
            top25_games = team_games[top25_mask]
            row['top25_games'] = len(top25_games)
            if 'game_is_win' in top25_games.columns:
                row['top25_wins'] = int(top25_games['game_is_win'].sum())
            else:
                row['top25_wins'] = 0
            row['top25_win_pct'] = round(row['top25_wins'] / row['top25_games'] * 100, 1) if row['top25_games'] > 0 else None

        # Blowout rate (wins by 20+)
        margin_col = 'game_scoring_margin'
        if margin_col in team_games.columns:
            blowouts = (team_games[margin_col] >= 20).sum()
            row['blowout_rate'] = round(blowouts / len(team_games) * 100, 1)

        # Weeks in Top 25 (use pre-computed max from poll-level column)
        if 'weeks_in_top25' in team_games.columns:
            weeks_in_top25 = team_games['weeks_in_top25'].max()
            if pd.notna(weeks_in_top25):
                row['weeks_in_top25'] = int(weeks_in_top25)

        # Best and worst rank (pre-computed in polls_games)
        if 'best_rank' in team_games.columns:
            best_rank = team_games['best_rank'].min()
            if pd.notna(best_rank):
                row['best_rank'] = int(best_rank)
        if 'worst_rank' in team_games.columns:
            worst_rank = team_games['worst_rank'].max()
            if pd.notna(worst_rank):
                row['worst_rank'] = int(worst_rank)
        if 'best_rank' in row and 'worst_rank' in row:
            row['rank_range'] = row['worst_rank'] - row['best_rank']

        results.append(row)

    if len(results) > 0:
        poll_context = pd.DataFrame(results)
        team_top25 = team_top25.merge(poll_context, on='team_id', how='left')
        print(f"  Added poll context for {len(poll_context)} teams")

    return team_top25


def build_conference_overrides_from_master(master_path=None):
    """
    Build conference override map from master_player_season_mapping.

    Compares the raw roster conference for each team against the master mapping's
    conference_short_name. Where they differ (e.g. due to conference realignment),
    the master mapping value is used as the authoritative current conference.

    Returns dict of {standardized_team_name: master_conference}.
    """
    if master_path is None:
        master_path = MASTER_MAPPING_PATH

    if not Path(master_path).exists():
        print(f"  WARNING: Master mapping not found at {master_path}")
        return {}

    master = pd.read_csv(master_path)
    master_conf = master.drop_duplicates('standardized_team_name')[
        ['standardized_team_name', 'conference_short_name']
    ]
    return dict(zip(master_conf['standardized_team_name'], master_conf['conference_short_name']))


def add_conference(team_top25, rosters):
    """
    Add conference field to team_top25 from raw roster data.

    Maps team_location (box score name) to roster team name to look up conference.
    Falls back to the TEAM_NAME_MAP for known mismatches (USC, Ole Miss, TCU, etc.).

    After the roster lookup, applies overrides derived at runtime from the
    master_player_season_mapping for teams whose conference changed between
    the 2024-25 roster season and the current 2025-26 season.
    """
    print("\n" + "=" * 60)
    print("Adding Conference Field")
    print("=" * 60)

    # Build a team -> conference lookup from rosters (one conference per team)
    roster_conf = rosters.drop_duplicates('team')[['team', 'conference', 'division']].copy()
    roster_conf_dict = dict(zip(roster_conf['team'], roster_conf['conference']))
    roster_div_dict = dict(zip(roster_conf['team'], roster_conf['division']))

    conferences = []
    divisions = []
    for _, row in team_top25.iterrows():
        team_loc = row['team_location']

        # Direct match first
        if team_loc in roster_conf_dict:
            conferences.append(roster_conf_dict[team_loc])
            divisions.append(roster_div_dict.get(team_loc))
            continue

        # Try mapped name
        mapped = TEAM_NAME_MAP.get(team_loc, team_loc)
        if mapped in roster_conf_dict:
            conferences.append(roster_conf_dict[mapped])
            divisions.append(roster_div_dict.get(mapped))
            continue

        # Try case-insensitive partial match
        found = False
        for roster_team in roster_conf_dict:
            if roster_team.lower() == team_loc.lower() or team_loc.lower() in roster_team.lower():
                conferences.append(roster_conf_dict[roster_team])
                divisions.append(roster_div_dict.get(roster_team))
                found = True
                break
        if not found:
            conferences.append(None)
            divisions.append(None)

    team_top25['conference'] = conferences
    team_top25['division'] = divisions

    matched = sum(1 for c in conferences if c is not None)
    print(f"  Matched conference for {matched}/{len(team_top25)} teams from roster")
    if matched < len(team_top25):
        missing = team_top25[team_top25['conference'].isna()]['team_location'].tolist()
        print(f"  Missing: {missing}")

    # Apply conference overrides and team_state_long from master mapping
    if Path(MASTER_MAPPING_PATH).exists():
        master = pd.read_csv(MASTER_MAPPING_PATH)
        master_teams = master.drop_duplicates('standardized_team_name')[
            ['standardized_team_name', 'conference_short_name', 'team_state_long']
        ]
        master_conf_dict = dict(zip(master_teams['standardized_team_name'], master_teams['conference_short_name']))
        master_state_dict = dict(zip(master_teams['standardized_team_name'], master_teams['team_state_long']))

        overrides_applied = 0
        for index, row in team_top25.iterrows():
            team_loc = row['team_location']
            if team_loc in master_conf_dict:
                master_conf = master_conf_dict[team_loc]
                current_conf = row['conference']
                if current_conf != master_conf:
                    team_top25.loc[index, 'conference'] = master_conf
                    overrides_applied += 1
                    print(f"  Override: {team_loc} conference {current_conf} -> {master_conf}")

        print(f"  Applied {overrides_applied} conference overrides from master mapping")

        # Add team_state_long from master mapping
        team_top25['team_state_long'] = team_top25['team_location'].map(master_state_dict)
        state_matched = team_top25['team_state_long'].notna().sum()
        print(f"  Added team_state_long for {state_matched}/{len(team_top25)} teams")
    else:
        print("  WARNING: Master mapping not found, skipping conference overrides and team_state_long")

    return team_top25


def validate_enriched_data(team_top25):
    """Validate the enriched dataset."""
    print("\n" + "=" * 60)
    print("Validation Summary")
    print("=" * 60)

    # Check for remaining missing values in key columns
    key_cols = [
        'roster_size', 'avg_height_inches', 'exp_minutes_weighted',
        'offensive_eff', 'defensive_eff', 'guard_big_balance'
    ]

    print("\nMissing values in key columns:")
    for col in key_cols:
        if col in team_top25.columns:
            missing = team_top25[col].isna().sum()
            print(f"  {col}: {missing} missing")

    # Show sample of enriched data
    print("\nSample enriched data (top 5 by AP rank):")
    sample_cols = [
        'team_display_name', 'best_ap_rank', 'win_pct',
        'offensive_eff', 'net_eff', 'exp_minutes_weighted',
        'has_star_transfer', 'guard_big_balance'
    ]
    available_cols = [c for c in sample_cols if c in team_top25.columns]
    print(team_top25.nsmallest(5, 'best_ap_rank')[available_cols].to_string())

    return team_top25


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Enhance roster analytics with additional metrics.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python scripts/roster/enhance_roster_analytics.py
    python scripts/roster/enhance_roster_analytics.py --polls-games data/raw/2026/joined_polls_games_20260209.csv
        """
    )
    parser.add_argument(
        "--polls-games",
        dest="polls_games_path",
        type=str,
        default=None,
        help="Path to polls_games CSV file (optional). If not provided, script will search for matching files."
    )
    args = parser.parse_args()

    print("=" * 60)
    print("Enriching Roster Analytics")
    print("=" * 60)

    # Load data
    team_top25, player_top25, player_full, rosters, team_box, game_analysis = load_data()

    # 1. Fix missing roster metrics
    team_top25 = fix_missing_roster_metrics(team_top25, player_full, rosters)

    # 2. Add efficiency metrics
    team_top25 = add_efficiency_metrics(team_top25, team_box, game_analysis)

    # 3. Add role-weighted experience
    team_top25 = add_role_weighted_experience(team_top25, player_full)

    # 4. Add transfer impact metrics
    team_top25 = add_transfer_impact_metrics(team_top25, player_full)

    # 5. Add points-weighted height
    team_top25 = add_points_weighted_height(team_top25, player_full)

    # 6. Add guard-big balance
    team_top25 = add_guard_big_balance(team_top25)

    # 7. Add poll/game context (if available)
    team_top25 = add_poll_game_context(team_top25, polls_games_path=args.polls_games_path)

    # 8. Add conference from raw roster data
    team_top25 = add_conference(team_top25, rosters)

    # 9. Add run_date
    run_date_str = date.today().isoformat()
    team_top25['run_date'] = run_date_str
    print(f"\n  Added run_date: {run_date_str}")

    # Validate
    team_top25 = validate_enriched_data(team_top25)

    # Save enriched dataset
    print("\n" + "=" * 60)
    print("Saving Enriched Dataset")
    print("=" * 60)

    output_path = ROSTER_DIR / "team_season_analytic_2026_top25_enriched.csv"
    team_top25.to_csv(output_path, index=False)
    print(f"  Saved: {output_path}")
    print(f"  Shape: {team_top25.shape}")
    print(f"  Columns: {len(team_top25.columns)}")

    # Also save as parquet for Tableau
    parquet_path = ROSTER_DIR / "team_season_analytic_2026_top25_enriched.parquet"
    team_top25.to_parquet(parquet_path, index=False)
    print(f"  Saved: {parquet_path}")

    # List new columns added
    original_cols = pd.read_csv(ROSTER_DIR / "team_season_analytic_2026_top25.csv").columns
    new_cols = [c for c in team_top25.columns if c not in original_cols]
    print(f"\nNew columns added ({len(new_cols)}):")
    for col in new_cols:
        print(f"  - {col}")

    print("\nDone!")


if __name__ == "__main__":
    main()
