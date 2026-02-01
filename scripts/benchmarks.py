"""
WBB Scout Reports - Benchmark & Percentile Calculations
=======================================================
Functions for computing D1 benchmarks and percentile ranks.

Supports:
- Overall D1 percentiles (all teams/players)
- Position-specific percentiles (Guard, Forward, Center)
- Conference-level benchmarks
- Weekly/rolling percentiles
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Union

from metrics import (
    calculate_team_metrics,
    calculate_player_metrics,
    add_position_group,
    normalize_position
)


# =============================================================================
# CONFIGURATION
# =============================================================================

# Standard percentile breakpoints
PERCENTILE_BREAKPOINTS = [5, 10, 25, 50, 75, 90, 95]

# Team metrics to benchmark
TEAM_METRICS = [
    'efg_pct', 'ts_pct', 'tov_pct', 'ftr', 'fg3_rate',
    'fg2_pct', 'fg3_pct', 'ft_pct', 'ast_pct', 'ast_tov',
    'ortg', 'pace'
]

# Player metrics to benchmark
PLAYER_METRICS = [
    'efg_pct', 'ts_pct', 'fg3_pct', 'ft_pct',
    'pts_per40', 'reb_per40', 'ast_per40', 'ast_tov'
]

# Minimum thresholds for inclusion
MIN_PLAYER_MINUTES = 10  # Per game
MIN_PLAYER_FGA = 5       # Per game for shooting metrics


# =============================================================================
# PERCENTILE CALCULATION
# =============================================================================

def compute_percentile(value: float,
                       distribution: pd.Series) -> float:
    """
    Compute the percentile rank of a value within a distribution.

    Args:
        value: The value to rank
        distribution: Series of values representing the distribution

    Returns:
        Percentile rank (0-100)
    """
    if pd.isna(value) or len(distribution) == 0:
        return np.nan

    # Remove NaN values from distribution
    clean_dist = distribution.dropna()
    if len(clean_dist) == 0:
        return np.nan

    # Count how many values are less than or equal
    rank = (clean_dist <= value).sum()
    percentile = 100 * rank / len(clean_dist)

    return round(percentile, 1)


def compute_percentiles_for_metric(values: pd.Series,
                                   percentiles: List[int] = None) -> Dict[str, float]:
    """
    Compute percentile breakpoints for a metric distribution.

    Args:
        values: Series of metric values
        percentiles: List of percentile breakpoints (default: standard list)

    Returns:
        Dictionary with percentile values
    """
    if percentiles is None:
        percentiles = PERCENTILE_BREAKPOINTS

    clean_values = values.dropna()

    if len(clean_values) == 0:
        return {f'p{p}': np.nan for p in percentiles}

    result = {
        'count': len(clean_values),
        'mean': clean_values.mean(),
        'std': clean_values.std()
    }

    for p in percentiles:
        result[f'p{p}'] = np.percentile(clean_values, p)

    return result


# =============================================================================
# TEAM BENCHMARKS
# =============================================================================

def build_team_benchmarks(team_df: pd.DataFrame,
                          metrics: List[str] = None) -> pd.DataFrame:
    """
    Build D1 team benchmark table from team box score data.

    Args:
        team_df: DataFrame with team box scores (already has metrics calculated)
        metrics: List of metrics to benchmark (default: TEAM_METRICS)

    Returns:
        DataFrame with percentile breakpoints for each metric
    """
    if metrics is None:
        metrics = TEAM_METRICS

    benchmark_rows = []

    for metric in metrics:
        if metric not in team_df.columns:
            continue

        percentiles = compute_percentiles_for_metric(team_df[metric])
        percentiles['metric'] = metric
        percentiles['category'] = 'team'
        percentiles['position'] = 'all'
        benchmark_rows.append(percentiles)

    return pd.DataFrame(benchmark_rows)


# =============================================================================
# PLAYER BENCHMARKS (WITH POSITION)
# =============================================================================

def build_player_benchmarks(player_df: pd.DataFrame,
                            metrics: List[str] = None,
                            by_position: bool = True,
                            min_minutes: float = None,
                            min_fga: float = None) -> pd.DataFrame:
    """
    Build D1 player benchmark table from player box score data.

    Args:
        player_df: DataFrame with player box scores (already has metrics calculated)
        metrics: List of metrics to benchmark (default: PLAYER_METRICS)
        by_position: If True, compute separate benchmarks by position group
        min_minutes: Minimum minutes threshold (default: MIN_PLAYER_MINUTES)
        min_fga: Minimum FGA threshold for shooting metrics (default: MIN_PLAYER_FGA)

    Returns:
        DataFrame with percentile breakpoints for each metric (and position)
    """
    if metrics is None:
        metrics = PLAYER_METRICS
    if min_minutes is None:
        min_minutes = MIN_PLAYER_MINUTES
    if min_fga is None:
        min_fga = MIN_PLAYER_FGA

    df = player_df.copy()

    # Ensure numeric minutes
    df['minutes'] = pd.to_numeric(df['minutes'], errors='coerce').fillna(0)

    # Add position group if not present
    if 'position_group' not in df.columns:
        df = add_position_group(df)

    # Filter by minimum minutes
    qualified = df[df['minutes'] >= min_minutes].copy()

    benchmark_rows = []

    # Overall benchmarks (all positions)
    for metric in metrics:
        if metric not in qualified.columns:
            continue

        # For shooting metrics, apply FGA filter
        if metric in ['efg_pct', 'ts_pct', 'fg3_pct']:
            if 'field_goals_attempted' in qualified.columns:
                fga = pd.to_numeric(qualified['field_goals_attempted'], errors='coerce').fillna(0)
                metric_data = qualified.loc[fga >= min_fga, metric]
            else:
                metric_data = qualified[metric]
        else:
            metric_data = qualified[metric]

        percentiles = compute_percentiles_for_metric(metric_data)
        percentiles['metric'] = metric
        percentiles['category'] = 'player'
        percentiles['position'] = 'all'
        benchmark_rows.append(percentiles)

    # Position-specific benchmarks
    if by_position:
        for position in ['Guard', 'Forward', 'Center']:
            pos_data = qualified[qualified['position_group'] == position]

            if len(pos_data) < 50:  # Skip if too few players
                continue

            for metric in metrics:
                if metric not in pos_data.columns:
                    continue

                # For shooting metrics, apply FGA filter
                if metric in ['efg_pct', 'ts_pct', 'fg3_pct']:
                    if 'field_goals_attempted' in pos_data.columns:
                        fga = pd.to_numeric(pos_data['field_goals_attempted'], errors='coerce').fillna(0)
                        metric_data = pos_data.loc[fga >= min_fga, metric]
                    else:
                        metric_data = pos_data[metric]
                else:
                    metric_data = pos_data[metric]

                percentiles = compute_percentiles_for_metric(metric_data)
                percentiles['metric'] = metric
                percentiles['category'] = 'player'
                percentiles['position'] = position
                benchmark_rows.append(percentiles)

    return pd.DataFrame(benchmark_rows)


# =============================================================================
# PERCENTILE LOOKUP
# =============================================================================

class BenchmarkLookup:
    """
    Lookup class for computing percentile ranks from benchmark tables.

    Usage:
        lookup = BenchmarkLookup(team_benchmarks, player_benchmarks)
        pctile = lookup.get_team_percentile('efg_pct', 0.52)
        pctile = lookup.get_player_percentile('ts_pct', 0.55, position='Guard')
    """

    def __init__(self,
                 team_benchmarks: pd.DataFrame = None,
                 player_benchmarks: pd.DataFrame = None):
        """
        Initialize lookup with benchmark tables.

        Args:
            team_benchmarks: DataFrame from build_team_benchmarks()
            player_benchmarks: DataFrame from build_player_benchmarks()
        """
        self.team_benchmarks = team_benchmarks
        self.player_benchmarks = player_benchmarks

        # Build lookup dictionaries for faster access
        self._team_lookup = {}
        self._player_lookup = {}

        if team_benchmarks is not None:
            self._build_team_lookup()

        if player_benchmarks is not None:
            self._build_player_lookup()

    def _build_team_lookup(self):
        """Build team benchmark lookup dictionary."""
        for _, row in self.team_benchmarks.iterrows():
            metric = row['metric']
            self._team_lookup[metric] = {
                'mean': row.get('mean', np.nan),
                'std': row.get('std', np.nan),
                'percentiles': {
                    p: row.get(f'p{p}', np.nan)
                    for p in PERCENTILE_BREAKPOINTS
                }
            }

    def _build_player_lookup(self):
        """Build player benchmark lookup dictionary."""
        for _, row in self.player_benchmarks.iterrows():
            metric = row['metric']
            position = row.get('position', 'all')

            if metric not in self._player_lookup:
                self._player_lookup[metric] = {}

            self._player_lookup[metric][position] = {
                'mean': row.get('mean', np.nan),
                'std': row.get('std', np.nan),
                'percentiles': {
                    p: row.get(f'p{p}', np.nan)
                    for p in PERCENTILE_BREAKPOINTS
                }
            }

    def get_team_percentile(self, metric: str, value: float) -> float:
        """
        Get percentile rank for a team metric value.

        Args:
            metric: Metric name (e.g., 'efg_pct')
            value: Metric value to rank

        Returns:
            Percentile rank (0-100) or NaN if not found
        """
        if metric not in self._team_lookup:
            return np.nan

        return self._interpolate_percentile(
            value,
            self._team_lookup[metric]['percentiles']
        )

    def get_player_percentile(self,
                              metric: str,
                              value: float,
                              position: str = 'all') -> float:
        """
        Get percentile rank for a player metric value.

        Args:
            metric: Metric name (e.g., 'ts_pct')
            value: Metric value to rank
            position: Position group ('Guard', 'Forward', 'Center', or 'all')

        Returns:
            Percentile rank (0-100) or NaN if not found
        """
        if metric not in self._player_lookup:
            return np.nan

        # Normalize position
        pos = normalize_position(position) if position != 'all' else 'all'

        # Fall back to 'all' if position not found
        if pos not in self._player_lookup[metric]:
            pos = 'all'

        if pos not in self._player_lookup[metric]:
            return np.nan

        return self._interpolate_percentile(
            value,
            self._player_lookup[metric][pos]['percentiles']
        )

    def _interpolate_percentile(self,
                                value: float,
                                percentiles: Dict[int, float]) -> float:
        """
        Interpolate percentile rank from breakpoint values.

        Args:
            value: Value to rank
            percentiles: Dictionary of percentile breakpoints

        Returns:
            Interpolated percentile rank
        """
        if pd.isna(value):
            return np.nan

        # Get sorted percentile breakpoints
        breakpoints = sorted(percentiles.keys())
        values = [percentiles[p] for p in breakpoints]

        # Handle edge cases
        if value <= values[0]:
            return float(breakpoints[0])
        if value >= values[-1]:
            return float(breakpoints[-1])

        # Linear interpolation between breakpoints
        for i in range(len(breakpoints) - 1):
            if values[i] <= value <= values[i + 1]:
                # Interpolate
        frac = (value - values[i]) / (values[i + 1] - values[i]) if (values[i + 1] - values[i]) > 0 else 0.0
        return np.nan


# =============================================================================
# BATCH PERCENTILE COMPUTATION
# =============================================================================

def add_team_percentiles(team_df: pd.DataFrame,
                         benchmarks: pd.DataFrame,
                         metrics: List[str] = None) -> pd.DataFrame:
    """
    Add percentile columns to a team DataFrame.

    Args:
        team_df: DataFrame with team metrics
        benchmarks: Benchmark table from build_team_benchmarks()
        metrics: List of metrics to add percentiles for

    Returns:
        DataFrame with new *_pctile columns
    """
    if metrics is None:
        metrics = TEAM_METRICS

    df = team_df.copy()
    lookup = BenchmarkLookup(team_benchmarks=benchmarks)

    for metric in metrics:
        if metric not in df.columns:
            continue

        pctile_col = f'{metric}_pctile'
        df[pctile_col] = df[metric].apply(
            lambda x: lookup.get_team_percentile(metric, x)
        )

    return df


def add_player_percentiles(player_df: pd.DataFrame,
                           benchmarks: pd.DataFrame,
                           metrics: List[str] = None,
                           use_position: bool = True) -> pd.DataFrame:
    """
    Add percentile columns to a player DataFrame.

    Args:
        player_df: DataFrame with player metrics
        benchmarks: Benchmark table from build_player_benchmarks()
        metrics: List of metrics to add percentiles for
        use_position: If True, use position-specific percentiles

    Returns:
        DataFrame with new *_pctile columns
    """
    if metrics is None:
        metrics = PLAYER_METRICS

    df = player_df.copy()
    lookup = BenchmarkLookup(player_benchmarks=benchmarks)

    # Ensure position group exists
    if use_position and 'position_group' not in df.columns:
        df = add_position_group(df)

    for metric in metrics:
        if metric not in df.columns:
            continue

        pctile_col = f'{metric}_pctile'

        if use_position:
            df[pctile_col] = df.apply(
                lambda row: lookup.get_player_percentile(
                    metric,
                    row[metric],
                    position=row.get('position_group', 'all')
                ),
                axis=1
            )
        else:
            df[pctile_col] = df[metric].apply(
                lambda x: lookup.get_player_percentile(metric, x, position='all')
            )

    return df


# =============================================================================
# SAVE/LOAD BENCHMARKS
# =============================================================================

def save_benchmarks(team_benchmarks: pd.DataFrame,
                    player_benchmarks: pd.DataFrame,
                    output_dir: Path = None,
                    suffix: str = '2025') -> None:
    """
    Save benchmark tables to CSV files.

    Args:
        team_benchmarks: Team benchmark DataFrame
        player_benchmarks: Player benchmark DataFrame
        output_dir: Output directory (default: data/benchmarks/)
        suffix: Filename suffix (e.g., '2025' for season)
    """
    if output_dir is None:
        output_dir = Path('data/benchmarks')

    output_dir.mkdir(parents=True, exist_ok=True)

    team_benchmarks.to_csv(
        output_dir / f'd1_team_benchmarks_{suffix}.csv',
        index=False
    )

    player_benchmarks.to_csv(
        output_dir / f'd1_player_benchmarks_{suffix}.csv',
        index=False
    )

    print(f"✓ Saved benchmarks to {output_dir}")


def load_benchmarks(input_dir: Path = None,
                    suffix: str = '2025') -> tuple:
    """
    Load benchmark tables from CSV files.

    Args:
        input_dir: Input directory (default: data/benchmarks/)
        suffix: Filename suffix

    Returns:
        Tuple of (team_benchmarks, player_benchmarks)
    """
    if input_dir is None:
        input_dir = Path('data/benchmarks')

    team_benchmarks = pd.read_csv(input_dir / f'd1_team_benchmarks_{suffix}.csv')
    player_benchmarks = pd.read_csv(input_dir / f'd1_player_benchmarks_{suffix}.csv')

    return team_benchmarks, player_benchmarks
