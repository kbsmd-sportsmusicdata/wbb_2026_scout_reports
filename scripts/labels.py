"""
WBB Scout Reports - Categorical Labels
======================================
Functions for creating categorical labels from metrics and percentiles.

Label Types:
- Percentile Tiers: Elite, Great, Above Average, Average, Below Average, Low
- Player Roles: Based on USG% and TS% combinations
- Game Context: Close Game, Blowout, Upset, Ranked Matchup
"""

import pandas as pd
import numpy as np
from typing import Optional, Union


# =============================================================================
# PERCENTILE TIER LABELS
# =============================================================================

# Tier definitions (percentile thresholds)
PERCENTILE_TIERS = {
    'Elite': (90, 100),
    'Great': (75, 89.99),
    'Above Average': (60, 74.99),
    'Average': (40, 59.99),
    'Below Average': (25, 39.99),
    'Low': (0, 24.99)
}

# Display colors for Tableau/visualization
TIER_COLORS = {
    'Elite': '#1a9850',        # Dark Green
    'Great': '#91cf60',        # Light Green
    'Above Average': '#d9ef8b', # Yellow-Green
    'Average': '#d9d9d9',      # Gray
    'Below Average': '#fdae61', # Light Orange
    'Low': '#d73027'           # Red
}


def get_percentile_tier(percentile: float) -> str:
    """
    Convert a percentile value to a tier label.

    Args:
        percentile: Percentile value (0-100)

    Returns:
        Tier label string
    """
    if pd.isna(percentile):
        return 'Unknown'

    for tier, (low, high) in PERCENTILE_TIERS.items():
        if low <= percentile <= high:
            return tier

    return 'Unknown'


def get_tier_color(tier: str) -> str:
    """Get the display color for a tier label."""
    return TIER_COLORS.get(tier, '#d9d9d9')


def add_percentile_tiers(df: pd.DataFrame,
                         pctile_columns: list = None,
                         suffix: str = '_tier') -> pd.DataFrame:
    """
    Add tier label columns for all percentile columns in DataFrame.

    Args:
        df: DataFrame with percentile columns (ending in '_pctile')
        pctile_columns: Specific columns to process (default: auto-detect)
        suffix: Suffix for tier columns (default: '_tier')

    Returns:
        DataFrame with new tier columns
    """
    result = df.copy()

    if pctile_columns is None:
        pctile_columns = [col for col in df.columns if col.endswith('_pctile')]

    for col in pctile_columns:
        # Create tier column name (replace _pctile with _tier)
        tier_col = col.replace('_pctile', suffix)
        result[tier_col] = result[col].apply(get_percentile_tier)

    return result


# =============================================================================
# PLAYER ROLE LABELS
# =============================================================================

# Role definitions based on USG% and TS%
# High Usage = top 25% USG%, Efficient = top 40% TS%

ROLE_DEFINITIONS = {
    'Star': {
        'description': 'High usage, high efficiency',
        'usg_min': 75,  # 75th percentile
        'ts_min': 60,   # 60th percentile
        'color': '#1a9850'
    },
    'High Volume Scorer': {
        'description': 'High usage, average efficiency',
        'usg_min': 75,
        'ts_min': 40,
        'ts_max': 59.99,
        'color': '#91cf60'
    },
    'Inefficient Volume': {
        'description': 'High usage, low efficiency',
        'usg_min': 75,
        'ts_max': 39.99,
        'color': '#fdae61'
    },
    'Efficient Role Player': {
        'description': 'Moderate usage, high efficiency',
        'usg_min': 40,
        'usg_max': 74.99,
        'ts_min': 60,
        'color': '#66bd63'
    },
    'Solid Contributor': {
        'description': 'Moderate usage, average efficiency',
        'usg_min': 40,
        'usg_max': 74.99,
        'ts_min': 40,
        'ts_max': 59.99,
        'color': '#d9d9d9'
    },
    'Struggling Scorer': {
        'description': 'Moderate usage, low efficiency',
        'usg_min': 40,
        'usg_max': 74.99,
        'ts_max': 39.99,
        'color': '#f46d43'
    },
    'Specialist': {
        'description': 'Low usage, high efficiency',
        'usg_max': 39.99,
        'ts_min': 60,
        'color': '#a6d96a'
    },
    'Limited Role': {
        'description': 'Low usage, average or low efficiency',
        'usg_max': 39.99,
        'ts_max': 59.99,
        'color': '#bdbdbd'
    }
}


def get_player_role(usg_pctile: float,
                    ts_pctile: float) -> str:
    """
    Determine player role based on usage and efficiency percentiles.

    Args:
        usg_pctile: Usage rate percentile (0-100)
        ts_pctile: True shooting percentile (0-100)

    Returns:
        Role label string
    """
    if pd.isna(usg_pctile) or pd.isna(ts_pctile):
        return 'Unknown'

    # Star: High usage, high efficiency
    if usg_pctile >= 75 and ts_pctile >= 60:
        return 'Star'

    # High Volume Scorer: High usage, average efficiency
    if usg_pctile >= 75 and 40 <= ts_pctile < 60:
        return 'High Volume Scorer'

    # Inefficient Volume: High usage, low efficiency
    if usg_pctile >= 75 and ts_pctile < 40:
        return 'Inefficient Volume'

    # Efficient Role Player: Moderate usage, high efficiency
    if 40 <= usg_pctile < 75 and ts_pctile >= 60:
        return 'Efficient Role Player'

    # Solid Contributor: Moderate usage, average efficiency
    if 40 <= usg_pctile < 75 and 40 <= ts_pctile < 60:
        return 'Solid Contributor'

    # Struggling Scorer: Moderate usage, low efficiency
    if 40 <= usg_pctile < 75 and ts_pctile < 40:
        return 'Struggling Scorer'

    # Specialist: Low usage, high efficiency
    if usg_pctile < 40 and ts_pctile >= 60:
        return 'Specialist'

    # Limited Role: Low usage, average or low efficiency
    if usg_pctile < 40:
        return 'Limited Role'

    return 'Unknown'


def add_player_roles(df: pd.DataFrame,
                     usg_col: str = 'usg_pct_pctile',
                     ts_col: str = 'ts_pct_pctile') -> pd.DataFrame:
    """
    Add player role labels to DataFrame.

    Args:
        df: DataFrame with usage and TS percentile columns
        usg_col: Column name for usage percentile
        ts_col: Column name for TS percentile

    Returns:
        DataFrame with 'player_role' column
    """
    result = df.copy()

    if usg_col not in df.columns or ts_col not in df.columns:
        result['player_role'] = 'Unknown'
        return result

    result['player_role'] = result.apply(
        lambda row: get_player_role(row[usg_col], row[ts_col]),
        axis=1
    )

    return result


# =============================================================================
# GAME CONTEXT LABELS
# =============================================================================

# Game context thresholds
BLOWOUT_MARGIN = 20       # Point differential for blowout
CLOSE_GAME_MARGIN = 5     # Point differential for close game
UPSET_RANK_DIFF = 10      # Rank difference for upset consideration


def get_game_margin_context(point_diff: float) -> str:
    """
    Classify game by final margin.

    Args:
        point_diff: Point differential (winner - loser, always positive)

    Returns:
        Context label: 'Blowout', 'Comfortable', 'Close Game'
    """
    if pd.isna(point_diff):
        return 'Unknown'

    margin = abs(point_diff)

    if margin >= BLOWOUT_MARGIN:
        return 'Blowout'
    elif margin <= CLOSE_GAME_MARGIN:
        return 'Close Game'
    else:
        return 'Comfortable'


def get_game_context(winner_rank: Optional[int],
                     loser_rank: Optional[int],
                     point_diff: float) -> str:
    """
    Determine comprehensive game context.

    Args:
        winner_rank: AP rank of winner (None if unranked)
        loser_rank: AP rank of loser (None if unranked)
        point_diff: Point differential

    Returns:
        Context label
    """
    margin_context = get_game_margin_context(point_diff)

    # Handle ranking context
    winner_ranked = winner_rank is not None and winner_rank <= 25
    loser_ranked = loser_rank is not None and loser_rank <= 25

    # Ranked vs Ranked
    if winner_ranked and loser_ranked:
        if margin_context == 'Close Game':
            return 'Ranked Showdown (Close)'
        return 'Ranked Showdown'

    # Upset detection (unranked beats ranked, or lower-ranked beats higher-ranked by 10+)
    if loser_ranked and not winner_ranked:
        return 'Upset'

    if winner_ranked and loser_ranked:
        rank_diff = winner_rank - loser_rank
        if rank_diff >= UPSET_RANK_DIFF:
            return 'Upset'

    # Default to margin context
    if winner_ranked or loser_ranked:
        return f'Ranked Matchup ({margin_context})'

    return margin_context


def add_game_context(df: pd.DataFrame,
                     winner_rank_col: str = 'winner_rank',
                     loser_rank_col: str = 'loser_rank',
                     margin_col: str = 'point_diff') -> pd.DataFrame:
    """
    Add game context labels to DataFrame.

    Args:
        df: DataFrame with game data
        winner_rank_col: Column for winner's AP rank
        loser_rank_col: Column for loser's AP rank
        margin_col: Column for point differential

    Returns:
        DataFrame with 'game_context' column
    """
    result = df.copy()

    # Simple margin context if ranking columns don't exist
    if margin_col in df.columns:
        result['margin_context'] = result[margin_col].apply(get_game_margin_context)

    # Full context if ranking columns exist
    if winner_rank_col in df.columns and loser_rank_col in df.columns and margin_col in df.columns:
        result['game_context'] = result.apply(
            lambda row: get_game_context(
                row.get(winner_rank_col),
                row.get(loser_rank_col),
                row.get(margin_col, 0)
            ),
            axis=1
        )
    elif margin_col in df.columns:
        result['game_context'] = result['margin_context']

    return result


# =============================================================================
# PERFORMANCE LABELS
# =============================================================================

def get_performance_label(pctile: float, metric_name: str = '') -> str:
    """
    Generate a human-readable performance description.

    Args:
        pctile: Percentile value (0-100)
        metric_name: Optional metric name for context

    Returns:
        Performance description string
    """
    if pd.isna(pctile):
        return ''

    tier = get_percentile_tier(pctile)

    # Contextual descriptions
    descriptions = {
        'Elite': f'Elite ({pctile:.0f}th percentile)',
        'Great': f'Great ({pctile:.0f}th percentile)',
        'Above Average': f'Above average ({pctile:.0f}th percentile)',
        'Average': f'Average ({pctile:.0f}th percentile)',
        'Below Average': f'Below average ({pctile:.0f}th percentile)',
        'Low': f'Needs improvement ({pctile:.0f}th percentile)'
    }

    return descriptions.get(tier, f'{pctile:.0f}th percentile')


def get_comparative_label(team_value: float,
                          opp_value: float,
                          team_pctile: float,
                          metric_name: str = '') -> str:
    """
    Generate comparative performance description.

    Args:
        team_value: Team's metric value
        opp_value: Opponent's metric value
        team_pctile: Team's percentile for context
        metric_name: Metric name for context

    Returns:
        Comparative description string
    """
    if pd.isna(team_value) or pd.isna(opp_value):
        return ''

    diff = team_value - opp_value
    tier = get_percentile_tier(team_pctile)

    if abs(diff) < 0.01:
        return 'Even matchup'

    direction = 'advantage' if diff > 0 else 'disadvantage'

    # Higher is better for most metrics
    # Exception: TOV% where lower is better
    if 'tov' in metric_name.lower():
        direction = 'disadvantage' if diff > 0 else 'advantage'

    return f'{tier} ({direction})'


# =============================================================================
# BATCH LABELING
# =============================================================================

def add_all_labels(df: pd.DataFrame,
                   add_tiers: bool = True,
                   add_roles: bool = True,
                   add_context: bool = True) -> pd.DataFrame:
    """
    Add all applicable labels to a DataFrame.

    Args:
        df: DataFrame with metrics and percentiles
        add_tiers: Add percentile tier labels
        add_roles: Add player role labels (if player data)
        add_context: Add game context labels (if game data)

    Returns:
        DataFrame with all labels added
    """
    result = df.copy()

    if add_tiers:
        result = add_percentile_tiers(result)

    if add_roles and 'usg_pct_pctile' in result.columns:
        result = add_player_roles(result)

    if add_context and 'point_diff' in result.columns:
        result = add_game_context(result)

    return result
