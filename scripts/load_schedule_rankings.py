"""
Load WBB Schedule Data with Rankings from sportsdataverse wehoop-wbb-raw repository.

This script:
1. Downloads schedule parquet data from GitHub (contains rankings)
2. Saves raw schedule data
3. Creates a filtered game_summary with only ranked team games
4. Creates a filtered player_game with only players from ranked games

Usage:
    python scripts/load_schedule_rankings.py --season 2026

Output files:
- data/raw/{SEASON}/wbb_schedule_{SEASON}.parquet (raw schedule with rankings)
- data/processed/game_summary_ranked.csv (filtered: at least one ranked team)
- data/processed/player_game_ranked.csv (filtered: players from ranked games only)
"""

import argparse
import os
from datetime import datetime
from pathlib import Path
import numpy as np
import pandas as pd
import requests
import tempfile

# Configuration
DEFAULT_SEASON = 2026
DATA_DIR = Path("data")
PROCESSED_DIR = DATA_DIR / "processed"

# Ensure processed directory exists
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def download_schedule_data(season: int = DEFAULT_SEASON):
    """Download the WBB Schedule Parquet file with rankings."""
    url = f"https://raw.githubusercontent.com/sportsdataverse/wehoop-wbb-raw/main/wbb/schedules/parquet/wbb_schedule_{season}.parquet"
    print(f"Downloading schedule data from: {url}")

    response = requests.get(url, timeout=60)
    response.raise_for_status()

    with tempfile.NamedTemporaryFile(suffix=".parquet") as tmp:
        tmp.write(response.content)
        tmp.seek(0)
        df = pd.read_parquet(tmp)

    print(f"  ✓ Downloaded {len(df)} schedule rows")
    return df


def extract_rankings_lookup(schedule_df):
    """
    Extract a game_id -> (home_rank, away_rank, home_id, away_id) lookup.
    Rank of 99 means unranked.
    """
    # Get relevant columns
    cols = ['game_id', 'home_id', 'away_id', 'home_current_rank', 'away_current_rank']
    available = [c for c in cols if c in schedule_df.columns]

    if 'game_id' not in available:
        # Try alternate column names
        if 'id' in schedule_df.columns:
            schedule_df['game_id'] = schedule_df['id']
            available.append('game_id')

    lookup = schedule_df[available].copy()

    # Convert home_id and away_id to int for matching with team_id
    for col in ['home_id', 'away_id']:
        if col in lookup.columns:
            lookup[col] = pd.to_numeric(lookup[col], errors='coerce').fillna(0).astype(int)

    # Clean rank columns - convert to numeric, fill NaN with 99 (unranked)
    for col in ['home_current_rank', 'away_current_rank']:
        if col in lookup.columns:
            lookup[col] = pd.to_numeric(lookup[col], errors='coerce').fillna(99).astype(int)

    print(f"  Created rankings lookup for {len(lookup)} games")
    return lookup


def add_rankings_to_game_summary(game_summary_path, rankings_lookup):
    """
    Add team_rank and opponent_rank columns to game_summary.
    Uses vectorized operations for performance.
    """
    print(f"Loading game_summary from: {game_summary_path}")
    df = pd.read_csv(game_summary_path)

    print(f"  Loaded {len(df)} rows")

    # Ensure team_id is int for matching
    df['team_id'] = pd.to_numeric(df['team_id'], errors='coerce').fillna(0).astype(int)

    # Merge with rankings lookup
    df = df.merge(
        rankings_lookup[['game_id', 'home_id', 'away_id', 'home_current_rank', 'away_current_rank']],
        on='game_id',
        how='left'
    )

    # Fill missing ranks with 99 (unranked)
    df['home_current_rank'] = df['home_current_rank'].fillna(99).astype(int)
    df['away_current_rank'] = df['away_current_rank'].fillna(99).astype(int)
    df['home_id'] = df['home_id'].fillna(0).astype(int)
    df['away_id'] = df['away_id'].fillna(0).astype(int)

    # Vectorized assignment of team_rank and opponent_rank
    # If team_id matches home_id, team is home; otherwise team is away
    is_home = df['team_id'] == df['home_id']

    df['team_rank'] = np.where(is_home, df['home_current_rank'], df['away_current_rank'])
    df['opponent_rank'] = np.where(is_home, df['away_current_rank'], df['home_current_rank'])

    # For games not in schedule, default to 99
    df['team_rank'] = df['team_rank'].fillna(99).astype(int)
    df['opponent_rank'] = df['opponent_rank'].fillna(99).astype(int)

    # Drop the temporary merge columns
    df = df.drop(columns=['home_id', 'away_id', 'home_current_rank', 'away_current_rank'], errors='ignore')

    print(f"  Added team_rank and opponent_rank columns")

    # Stats on rankings
    ranked_teams = (df['team_rank'] <= 25).sum()
    ranked_opponents = (df['opponent_rank'] <= 25).sum()
    print(f"  Ranked teams: {ranked_teams}, Ranked opponents: {ranked_opponents}")

    return df


def filter_ranked_games(df):
    """
    Filter to only include games where at least one team is ranked (1-25).
    Both team_rank=99 AND opponent_rank=99 means both unranked -> exclude.
    """
    original_count = len(df)

    # Keep games where at least one team is ranked
    filtered = df[(df['team_rank'] <= 25) | (df['opponent_rank'] <= 25)].copy()

    filtered_count = len(filtered)
    removed = original_count - filtered_count

    print(f"  Filtered: {original_count} -> {filtered_count} rows ({removed} unranked-vs-unranked removed)")

    return filtered


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Load WBB schedule data with rankings and create filtered datasets."
    )
    parser.add_argument(
        "--season",
        type=int,
        default=DEFAULT_SEASON,
        help=f"Season year (default: {DEFAULT_SEASON})"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    season = args.season

    # Set up season-specific raw directory
    raw_dir = DATA_DIR / "raw" / str(season)
    raw_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print(f"Loading Schedule Data with Rankings (Season {season})")
    print("=" * 60)

    # 1. Download schedule data
    try:
        schedule_df = download_schedule_data(season)
    except requests.exceptions.RequestException as e:
        print(f"Error downloading schedule: {e}")
        return

    # Save raw schedule
    schedule_path = raw_dir / f"wbb_schedule_{season}.parquet"
    schedule_df.to_parquet(schedule_path, index=False)
    print(f"  ✓ Saved schedule to {schedule_path}")

    # Show available columns
    print(f"\nSchedule columns: {list(schedule_df.columns)}")

    # 2. Extract rankings lookup
    rankings_lookup = extract_rankings_lookup(schedule_df)

    # 3. Check if game_summary exists
    game_summary_path = PROCESSED_DIR / "game_summary.csv"
    if not game_summary_path.exists():
        print(f"\nWARNING: {game_summary_path} not found.")
        print("Run weekly_pull.py first to generate game_summary.csv")
        return

    # 4. Add rankings to game_summary
    print(f"\nAdding rankings to game_summary...")
    df_with_ranks = add_rankings_to_game_summary(game_summary_path, rankings_lookup)

    # 5. Filter to ranked games only
    print(f"\nFiltering to ranked games...")
    df_ranked = filter_ranked_games(df_with_ranks)

    # 6. Save outputs
    # Save full game_summary with rankings (overwrites original)
    df_with_ranks.to_csv(game_summary_path, index=False)
    print(f"\n✓ Updated {game_summary_path} with rankings ({len(df_with_ranks)} rows)")

    # Save filtered version
    ranked_path = PROCESSED_DIR / "game_summary_ranked.csv"
    df_ranked.to_csv(ranked_path, index=False)
    print(f"✓ Saved filtered ranked games to {ranked_path} ({len(df_ranked)} rows)")

    # 7. Filter player_game to only include players from ranked games
    print(f"\nFiltering player_game to ranked games...")
    player_game_path = PROCESSED_DIR / "player_game.csv"
    if player_game_path.exists():
        player_game = pd.read_csv(player_game_path)
        print(f"  Loaded {len(player_game)} player rows")

        # Get unique game_ids from ranked games
        ranked_game_ids = set(df_ranked['game_id'].unique())
        print(f"  Ranked games: {len(ranked_game_ids)} unique game_ids")

        # Filter to ranked games only
        player_ranked = player_game[player_game['game_id'].isin(ranked_game_ids)].copy()
        filtered_count = len(player_ranked)
        removed = len(player_game) - filtered_count
        print(f"  Filtered: {len(player_game)} -> {filtered_count} rows ({removed} removed)")

        # Save filtered version
        player_ranked_path = PROCESSED_DIR / "player_game_ranked.csv"
        player_ranked.to_csv(player_ranked_path, index=False)
        print(f"✓ Saved filtered player data to {player_ranked_path} ({len(player_ranked)} rows)")
    else:
        print(f"  WARNING: {player_game_path} not found. Skipping player filtering.")

    # Show file sizes
    full_size = game_summary_path.stat().st_size / (1024 * 1024)
    ranked_size = ranked_path.stat().st_size / (1024 * 1024)
    print(f"\nFile sizes:")
    print(f"  game_summary.csv: {full_size:.1f} MB")
    print(f"  game_summary_ranked.csv: {ranked_size:.1f} MB")

    if player_game_path.exists():
        player_full_size = player_game_path.stat().st_size / (1024 * 1024)
        player_ranked_path = PROCESSED_DIR / "player_game_ranked.csv"
        if player_ranked_path.exists():
            player_ranked_size = player_ranked_path.stat().st_size / (1024 * 1024)
            print(f"  player_game.csv: {player_full_size:.1f} MB")
            print(f"  player_game_ranked.csv: {player_ranked_size:.1f} MB")


if __name__ == "__main__":
    main()
