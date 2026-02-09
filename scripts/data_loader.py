"""
WBB Scout Reports - Data Loading Utilities
==========================================
Centralized data loading functions with remote + local fallback support.

Used by: weekly_pull.py, build_benchmarks.py, test_pipeline.py

Data Sources:
- Primary: sportsdataverse-data releases (parquet files)
- Fallback: wehoop-wbb-data releases (parquet or RDS)
- Local: data/raw/ or data/raw/{season}/ directory
"""

import pandas as pd
from pathlib import Path
from typing import List, Optional

# sportsdataverse GitHub releases (primary source - updated more frequently)
SPORTSDATAVERSE_BASE = "https://github.com/sportsdataverse/sportsdataverse-data/releases/download"

# wehoop-wbb-data releases (fallback source)
WEHOOP_BASE = "https://github.com/sportsdataverse/wehoop-wbb-data/releases/download"

# Default data directory (relative to repo root)
DEFAULT_DATA_DIR = Path("data")


def load_rds_file(filepath: Path) -> pd.DataFrame:
    """Load an RDS file (R data format) into a pandas DataFrame."""
    try:
        import pyreadr
        result = pyreadr.read_r(str(filepath))
        # RDS files contain a single object
        return list(result.values())[0]
    except ImportError:
        raise ImportError("pyreadr package required to read RDS files. Install with: pip install pyreadr")


def load_parquet_with_fallback(
    remote_patterns: List[str],
    local_patterns: List[Path],
    data_type: str = "data",
    verbose: bool = True
) -> pd.DataFrame:
    """
    Load parquet data from remote URLs with local file fallback.

    Args:
        remote_patterns: List of remote URLs to try (in order)
        local_patterns: List of local file paths to try if remote fails
        data_type: Description for logging (e.g., "team box", "player box")
        verbose: Whether to print status messages

    Returns:
        DataFrame with loaded data, or empty DataFrame if all sources fail
    """
    # Try remote URLs first
    for url in remote_patterns:
        try:
            if verbose:
                print(f"Trying remote: {url}")
            if url.endswith('.rds'):
                # RDS files need to be downloaded first
                import tempfile
                import urllib.request
                with tempfile.NamedTemporaryFile(suffix='.rds', delete=False) as tmp:
                    urllib.request.urlretrieve(url, tmp.name)
                    df = load_rds_file(Path(tmp.name))
            else:
                df = pd.read_parquet(url)
            if verbose:
                print(f"  ✓ Loaded {len(df)} {data_type} rows from remote")
            return df
        except Exception as e:
            if verbose:
                print(f"  ✗ Remote failed: {e}")

    # Fall back to local files
    for local_path in local_patterns:
        if local_path.exists():
            try:
                if verbose:
                    print(f"Trying local: {local_path}")
                if str(local_path).endswith('.rds'):
                    df = load_rds_file(local_path)
                else:
                    df = pd.read_parquet(local_path)
                if verbose:
                    print(f"  ✓ Loaded {len(df)} {data_type} rows from local")
                return df
            except Exception as e:
                if verbose:
                    print(f"  ✗ Local failed: {e}")

    if verbose:
        print(f"  ERROR: No {data_type} data available (remote or local)")
    return pd.DataFrame()


def load_team_box(season: int = 2025, data_dir: Optional[Path] = None, verbose: bool = True) -> pd.DataFrame:
    """
    Load team box score data from wehoop releases or local fallback.

    Args:
        season: Season year (e.g., 2025 for 2024-25 season)
        data_dir: Base data directory (defaults to 'data/')
        verbose: Whether to print status messages

    Returns:
        DataFrame with team box score data
    """
    if data_dir is None:
        data_dir = DEFAULT_DATA_DIR

    raw_dir = data_dir / "raw"
    season_dir = raw_dir / str(season)

    remote_patterns = [
        # Primary: sportsdataverse-data releases (most up-to-date)
        f"{SPORTSDATAVERSE_BASE}/espn_womens_college_basketball_team_boxscores/team_box_{season}.parquet",
        # Fallback: wehoop-wbb-data releases
        f"{WEHOOP_BASE}/wbb_team_box/wbb_team_box_{season}.parquet",
        f"{WEHOOP_BASE}/wbb_team_box/team_box_{season}.parquet",
    ]

    local_patterns = [
        # Season subdirectory first (e.g., data/raw/2026/)
        season_dir / f"team_box_{season}.parquet",
        season_dir / f"wbb_team_box_{season}.parquet",
        # Then flat raw directory
        raw_dir / f"team_box_{season}.parquet",
        raw_dir / f"wbb_team_box_{season}.parquet",
        # RDS files
        season_dir / f"team_box_{season}.rds",
        raw_dir / f"team_box_{season}.rds",
    ]

    return load_parquet_with_fallback(
        remote_patterns=remote_patterns,
        local_patterns=local_patterns,
        data_type="team box",
        verbose=verbose
    )


def load_player_box(season: int = 2025, data_dir: Optional[Path] = None, verbose: bool = True) -> pd.DataFrame:
    """
    Load player box score data from wehoop releases or local fallback.

    Args:
        season: Season year (e.g., 2025 for 2024-25 season)
        data_dir: Base data directory (defaults to 'data/')
        verbose: Whether to print status messages

    Returns:
        DataFrame with player box score data
    """
    if data_dir is None:
        data_dir = DEFAULT_DATA_DIR

    raw_dir = data_dir / "raw"
    season_dir = raw_dir / str(season)

    remote_patterns = [
        # Primary: sportsdataverse-data releases (most up-to-date)
        f"{SPORTSDATAVERSE_BASE}/espn_womens_college_basketball_player_boxscores/player_box_{season}.parquet",
        # Fallback: wehoop-wbb-data releases
        f"{WEHOOP_BASE}/wbb_player_box/wbb_player_box_{season}.parquet",
        f"{WEHOOP_BASE}/wbb_player_box/player_box_{season}.parquet",
    ]

    local_patterns = [
        # Season subdirectory first (e.g., data/raw/2026/)
        season_dir / f"player_box_{season}.parquet",
        season_dir / f"wbb_player_box_{season}.parquet",
        # Then flat raw directory
        raw_dir / f"player_box_{season}.parquet",
        raw_dir / f"wbb_player_box_{season}.parquet",
        # RDS files
        season_dir / f"player_box_{season}.rds",
        raw_dir / f"player_box_{season}.rds",
    ]

    return load_parquet_with_fallback(
        remote_patterns=remote_patterns,
        local_patterns=local_patterns,
        data_type="player box",
        verbose=verbose
    )


def load_pbp(season: int = 2025, data_dir: Optional[Path] = None, verbose: bool = True) -> pd.DataFrame:
    """
    Load play-by-play data from wehoop releases or local fallback.

    Args:
        season: Season year (e.g., 2025 for 2024-25 season)
        data_dir: Base data directory (defaults to 'data/')
        verbose: Whether to print status messages

    Returns:
        DataFrame with play-by-play data
    """
    if data_dir is None:
        data_dir = DEFAULT_DATA_DIR

    raw_dir = data_dir / "raw"
    season_dir = raw_dir / str(season)

    remote_patterns = [
        # Primary: sportsdataverse-data releases (parquet)
        f"{SPORTSDATAVERSE_BASE}/espn_womens_college_basketball_pbp/play_by_play_{season}.parquet",
        # Fallback: wehoop-wbb-data releases
        f"{WEHOOP_BASE}/wbb_pbp/wbb_pbp_{season}.parquet",
        # RDS format (used by wehoop R package)
        f"{SPORTSDATAVERSE_BASE}/espn_womens_college_basketball_pbp/play_by_play_{season}.rds",
    ]

    local_patterns = [
        # Season subdirectory first (e.g., data/raw/2026/)
        season_dir / f"play_by_play_{season}.parquet",
        season_dir / f"pbp_{season}.parquet",
        season_dir / f"wbb_pbp_{season}.parquet",
        # Then flat raw directory
        raw_dir / f"play_by_play_{season}.parquet",
        raw_dir / f"pbp_{season}.parquet",
        raw_dir / f"wbb_pbp_{season}.parquet",
        # RDS files
        season_dir / f"play_by_play_{season}.rds",
        raw_dir / f"play_by_play_{season}.rds",
    ]

    return load_parquet_with_fallback(
        remote_patterns=remote_patterns,
        local_patterns=local_patterns,
        data_type="play-by-play",
        verbose=verbose
    )

