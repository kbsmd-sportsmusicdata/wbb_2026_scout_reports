"""
WBB Scout Reports - Metric Calculations
=======================================
All derived metric calculations for team and player analysis.

Formulas align with standard basketball analytics conventions.
Reference: Basketball-Reference, Cleaning the Glass, KenPom methodology.
"""

import pandas as pd
import numpy as np
from typing import Optional, Union


# =============================================================================
# POSSESSION ESTIMATION
# =============================================================================

def estimate_possessions(fga: Union[pd.Series, float],
                         fta: Union[pd.Series, float],
                         orb: Union[pd.Series, float],
                         tov: Union[pd.Series, float]) -> Union[pd.Series, float]:
    """
    Estimate possessions using the standard formula.

    Formula: Poss = FGA + 0.44 * FTA - ORB + TOV

    The 0.44 coefficient accounts for and-ones, technical FTs, etc.

    Args:
        fga: Field goal attempts
        fta: Free throw attempts
        orb: Offensive rebounds
        tov: Turnovers

    Returns:
        Estimated possessions
    """
    poss = fga + 0.44 * fta - orb + tov
    # Ensure minimum of 1 to avoid division by zero
    if isinstance(poss, pd.Series):
        return poss.clip(lower=1)
    return max(poss, 1)


def estimate_possessions_team(team_df: pd.DataFrame) -> pd.Series:
    """
    Estimate team possessions from a team box score DataFrame.

    Expects columns: field_goals_attempted, free_throws_attempted,
                     offensive_rebounds, turnovers
    """
    return estimate_possessions(
        fga=pd.to_numeric(team_df['field_goals_attempted'], errors='coerce').fillna(0),
        fta=pd.to_numeric(team_df['free_throws_attempted'], errors='coerce').fillna(0),
        orb=pd.to_numeric(team_df['offensive_rebounds'], errors='coerce').fillna(0),
        tov=pd.to_numeric(team_df['turnovers'], errors='coerce').fillna(0)
    )


# =============================================================================
# SHOOTING EFFICIENCY METRICS
# =============================================================================

def calc_efg_pct(fgm: Union[pd.Series, float],
                 fg3m: Union[pd.Series, float],
                 fga: Union[pd.Series, float]) -> Union[pd.Series, float]:
    """
    Effective Field Goal Percentage.

    Formula: eFG% = (FGM + 0.5 * 3PM) / FGA

    Weights 3-pointers appropriately (worth 1.5x a 2-pointer).
    """
    if isinstance(fga, pd.Series):
        return np.where(fga > 0, (fgm + 0.5 * fg3m) / fga, 0.0)
    return (fgm + 0.5 * fg3m) / fga if fga > 0 else 0.0


def calc_ts_pct(pts: Union[pd.Series, float],
                fga: Union[pd.Series, float],
                fta: Union[pd.Series, float]) -> Union[pd.Series, float]:
    """
    True Shooting Percentage.

    Formula: TS% = PTS / (2 * (FGA + 0.44 * FTA))

    Measures scoring efficiency accounting for FTs and 3s.
    """
    denom = 2 * (fga + 0.44 * fta)
    if isinstance(denom, pd.Series):
        return np.where(denom > 0, pts / denom, 0.0)
    return pts / denom if denom > 0 else 0.0


def calc_fg2_pct(fgm: Union[pd.Series, float],
                 fg3m: Union[pd.Series, float],
                 fga: Union[pd.Series, float],
                 fg3a: Union[pd.Series, float]) -> Union[pd.Series, float]:
    """
    Two-Point Field Goal Percentage.

    Formula: 2P% = (FGM - 3PM) / (FGA - 3PA)
    """
    fg2m = fgm - fg3m
    fg2a = fga - fg3a
    if isinstance(fg2a, pd.Series):
        return np.where(fg2a > 0, fg2m / fg2a, 0.0)
    return fg2m / fg2a if fg2a > 0 else 0.0


def calc_fg3_pct(fg3m: Union[pd.Series, float],
                 fg3a: Union[pd.Series, float]) -> Union[pd.Series, float]:
    """
    Three-Point Field Goal Percentage.

    Formula: 3P% = 3PM / 3PA
    """
    if isinstance(fg3a, pd.Series):
        return np.where(fg3a > 0, fg3m / fg3a, 0.0)
    return fg3m / fg3a if fg3a > 0 else 0.0


def calc_ft_pct(ftm: Union[pd.Series, float],
                fta: Union[pd.Series, float]) -> Union[pd.Series, float]:
    """
    Free Throw Percentage.

    Formula: FT% = FTM / FTA
    """
    if isinstance(fta, pd.Series):
        return np.where(fta > 0, ftm / fta, 0.0)
    return ftm / fta if fta > 0 else 0.0


def calc_fg3_rate(fg3a: Union[pd.Series, float],
                  fga: Union[pd.Series, float]) -> Union[pd.Series, float]:
    """
    Three-Point Attempt Rate.

    Formula: 3PAr = 3PA / FGA

    Measures reliance on 3-point shooting.
    """
    if isinstance(fga, pd.Series):
        return np.where(fga > 0, fg3a / fga, 0.0)
    return fg3a / fga if fga > 0 else 0.0


# =============================================================================
# FOUR FACTORS METRICS
# =============================================================================

def calc_tov_pct(tov: Union[pd.Series, float],
                 poss: Union[pd.Series, float]) -> Union[pd.Series, float]:
    """
    Turnover Percentage.

    Formula: TOV% = TOV / Poss

    Measures ball security (lower is better for offense).
    """
    if isinstance(poss, pd.Series):
        return np.where(poss > 0, tov / poss, 0.0)
    return tov / poss if poss > 0 else 0.0


def calc_oreb_pct(orb: Union[pd.Series, float],
                  orb_opp_drb: Union[pd.Series, float]) -> Union[pd.Series, float]:
    """
    Offensive Rebound Percentage.

    Formula: OREB% = ORB / (ORB + Opp_DRB)

    Measures second-chance opportunity creation.
    Note: Requires opponent's defensive rebounds for accurate calculation.
    """
    total = orb + orb_opp_drb
    if isinstance(total, pd.Series):
        return np.where(total > 0, orb / total, 0.0)
    return orb / total if total > 0 else 0.0


def calc_dreb_pct(drb: Union[pd.Series, float],
                  drb_opp_orb: Union[pd.Series, float]) -> Union[pd.Series, float]:
    """
    Defensive Rebound Percentage.

    Formula: DREB% = DRB / (DRB + Opp_ORB)

    Measures defensive rebounding (ending opponent possessions).
    Note: Requires opponent's offensive rebounds for accurate calculation.
    """
    total = drb + drb_opp_orb
    if isinstance(total, pd.Series):
        return np.where(total > 0, drb / total, 0.0)
    return drb / total if total > 0 else 0.0


def calc_ftr(fta: Union[pd.Series, float],
             fga: Union[pd.Series, float]) -> Union[pd.Series, float]:
    """
    Free Throw Rate.

    Formula: FTr = FTA / FGA

    Measures ability to get to the free throw line.
    """
    if isinstance(fga, pd.Series):
        return np.where(fga > 0, fta / fga, 0.0)
    return fta / fga if fga > 0 else 0.0


# =============================================================================
# EFFICIENCY RATINGS
# =============================================================================

def calc_ortg(pts: Union[pd.Series, float],
              poss: Union[pd.Series, float]) -> Union[pd.Series, float]:
    """
    Offensive Rating.

    Formula: ORtg = 100 * PTS / Poss

    Points scored per 100 possessions.
    """
    if isinstance(poss, pd.Series):
        return np.where(poss > 0, 100 * pts / poss, 0.0)
    return 100 * pts / poss if poss > 0 else 0.0


def calc_drtg(opp_pts: Union[pd.Series, float],
              poss: Union[pd.Series, float]) -> Union[pd.Series, float]:
    """
    Defensive Rating.

    Formula: DRtg = 100 * Opp_PTS / Poss

    Points allowed per 100 possessions (lower is better).
    """
    if isinstance(poss, pd.Series):
        return np.where(poss > 0, 100 * opp_pts / poss, 0.0)
    return 100 * opp_pts / poss if poss > 0 else 0.0


def calc_net_rtg(ortg: Union[pd.Series, float],
                 drtg: Union[pd.Series, float]) -> Union[pd.Series, float]:
    """
    Net Rating.

    Formula: Net = ORtg - DRtg

    Point differential per 100 possessions.
    """
    return ortg - drtg


# =============================================================================
# BALL MOVEMENT & PLAYMAKING
# =============================================================================

def calc_ast_pct(ast: Union[pd.Series, float],
                 fgm: Union[pd.Series, float]) -> Union[pd.Series, float]:
    """
    Assist Percentage (Team).

    Formula: AST% = AST / FGM

    Percentage of made field goals that were assisted.
    """
    if isinstance(fgm, pd.Series):
        return np.where(fgm > 0, ast / fgm, 0.0)
    return ast / fgm if fgm > 0 else 0.0


def calc_ast_tov(ast: Union[pd.Series, float],
                 tov: Union[pd.Series, float]) -> Union[pd.Series, float]:
    """
    Assist to Turnover Ratio.

    Formula: AST/TOV = AST / TOV

    Measures playmaking efficiency (higher is better).
    """
    with np.errstate(divide='ignore', invalid='ignore'):
        ratio = np.divide(ast, tov)
    return np.nan_to_num(ratio, nan=0.0)

# =============================================================================
# PLAYER-SPECIFIC METRICS
# =============================================================================

def calc_usg_pct(fga: Union[pd.Series, float],
                 fta: Union[pd.Series, float],
                 tov: Union[pd.Series, float],
                 minutes: Union[pd.Series, float],
                 team_fga: Union[pd.Series, float],
                 team_fta: Union[pd.Series, float],
                 team_tov: Union[pd.Series, float],
                 team_minutes: float = 200.0) -> Union[pd.Series, float]:
    """
    Usage Percentage (simplified).

    Formula: USG% = (FGA + 0.44*FTA + TOV) * (Team_Min / 5) /
                    (Min * (Team_FGA + 0.44*Team_FTA + Team_TOV))

    Estimates percentage of team plays used by player while on court.
    """
    player_usage = fga + 0.44 * fta + tov
    team_usage = team_fga + 0.44 * team_fta + team_tov

    if isinstance(minutes, pd.Series):
        denom = minutes * team_usage
        return np.where(
            (denom > 0) & (minutes > 0),
            player_usage * (team_minutes / 5) / denom,
            0.0
        )

    denom = minutes * team_usage
    if denom > 0 and minutes > 0:
        return player_usage * (team_minutes / 5) / denom
    return 0.0


def calc_per_minute(stat: Union[pd.Series, float],
                    minutes: Union[pd.Series, float],
                    per: float = 40.0) -> Union[pd.Series, float]:
    """
    Calculate per-minute rate (default per 40 minutes).

    Formula: Stat_Per40 = Stat * 40 / Minutes
    """
    if isinstance(minutes, pd.Series):
        return np.where(minutes > 0, stat * per / minutes, 0.0)
    return stat * per / minutes if minutes > 0 else 0.0


# =============================================================================
# BATCH CALCULATION FUNCTIONS
# =============================================================================

def calculate_team_metrics(team_df: pd.DataFrame,
                           include_opponent: bool = True) -> pd.DataFrame:
    """
    Calculate all team metrics for a team box score DataFrame.

    Args:
        team_df: DataFrame with team box score data
        include_opponent: If True, expects opponent data for OREB%/DREB%

    Returns:
        DataFrame with all calculated metrics added
    """
    df = team_df.copy()

    # Ensure numeric columns
    numeric_cols = [
        'field_goals_made', 'field_goals_attempted',
        'three_point_field_goals_made', 'three_point_field_goals_attempted',
        'free_throws_made', 'free_throws_attempted',
        'offensive_rebounds', 'defensive_rebounds',
        'assists', 'turnovers', 'team_score'
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # Shorthand aliases
    fgm = df['field_goals_made']
    fga = df['field_goals_attempted']
    fg3m = df['three_point_field_goals_made']
    fg3a = df['three_point_field_goals_attempted']
    ftm = df['free_throws_made']
    fta = df['free_throws_attempted']
    orb = df['offensive_rebounds']
    drb = df['defensive_rebounds']
    ast = df['assists']
    tov = df['turnovers']
    pts = df['team_score']

    # Possessions
    df['possessions'] = estimate_possessions(fga, fta, orb, tov)

    # Shooting efficiency
    df['efg_pct'] = calc_efg_pct(fgm, fg3m, fga)
    df['ts_pct'] = calc_ts_pct(pts, fga, fta)
    df['fg2_pct'] = calc_fg2_pct(fgm, fg3m, fga, fg3a)
    df['fg3_pct'] = calc_fg3_pct(fg3m, fg3a)
    df['ft_pct'] = calc_ft_pct(ftm, fta)
    df['fg3_rate'] = calc_fg3_rate(fg3a, fga)

    # Four Factors
    df['tov_pct'] = calc_tov_pct(tov, df['possessions'])
    df['ftr'] = calc_ftr(fta, fga)

    # Ball movement
    df['ast_pct'] = calc_ast_pct(ast, fgm)
    df['ast_tov'] = calc_ast_tov(ast, tov)

    # Efficiency ratings
    df['ortg'] = calc_ortg(pts, df['possessions'])
    df['pace'] = df['possessions']

    return df


def calculate_player_metrics(player_df: pd.DataFrame,
                             team_totals: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """
    Calculate all player metrics for a player box score DataFrame.

    Args:
        player_df: DataFrame with player box score data
        team_totals: Optional DataFrame with team totals for USG% calculation

    Returns:
        DataFrame with all calculated metrics added
    """
    df = player_df.copy()

    # Ensure numeric columns
    numeric_cols = [
        'minutes', 'field_goals_made', 'field_goals_attempted',
        'three_point_field_goals_made', 'three_point_field_goals_attempted',
        'free_throws_made', 'free_throws_attempted',
        'offensive_rebounds', 'defensive_rebounds', 'rebounds',
        'assists', 'turnovers', 'steals', 'blocks', 'points'
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # Parse minutes if string format (e.g., "32:45")
    if df['minutes'].dtype == object:
        df['minutes'] = df['minutes'].apply(_parse_minutes)

    # Shorthand aliases
    fgm = df['field_goals_made']
    fga = df['field_goals_attempted']
    fg3m = df['three_point_field_goals_made']
    fg3a = df['three_point_field_goals_attempted']
    ftm = df['free_throws_made']
    fta = df['free_throws_attempted']
    pts = df['points']
    minutes = df['minutes']
    ast = df['assists']
    tov = df['turnovers']

    # Shooting efficiency
    df['efg_pct'] = calc_efg_pct(fgm, fg3m, fga)
    df['ts_pct'] = calc_ts_pct(pts, fga, fta)
    df['fg3_pct'] = calc_fg3_pct(fg3m, fg3a)
    df['ft_pct'] = calc_ft_pct(ftm, fta)

    # Per-40 minute stats
    df['pts_per40'] = calc_per_minute(pts, minutes, 40)
    df['reb_per40'] = calc_per_minute(df['rebounds'], minutes, 40)
    df['ast_per40'] = calc_per_minute(ast, minutes, 40)

    # Assist/Turnover
    df['ast_tov'] = calc_ast_tov(ast, tov)

    return df


def _parse_minutes(min_str) -> float:
    """Parse minutes from string format (e.g., '32:45' or '32')."""
    if pd.isna(min_str):
        return 0.0
    if isinstance(min_str, (int, float)):
        return float(min_str)
    try:
        if ':' in str(min_str):
            parts = str(min_str).split(':')
            return float(parts[0]) + float(parts[1]) / 60
        return float(min_str)
    except (ValueError, IndexError):
        return 0.0


# =============================================================================
# POSITION GROUPING
# =============================================================================

def normalize_position(position: str) -> str:
    """
    Normalize position names to standard groups.

    Groups:
    - Guard: Guard, Point Guard, Shooting Guard
    - Forward: Forward, Small Forward, Power Forward
    - Center: Center
    - Other: Athlete, Not Available, etc.
    """
    if pd.isna(position):
        return 'Other'

    pos = str(position).lower().strip()

    if 'guard' in pos:
        return 'Guard'
    elif 'forward' in pos:
        return 'Forward'
    elif 'center' in pos:
        return 'Center'
    else:
        return 'Other'


def add_position_group(df: pd.DataFrame,
                       position_col: str = 'athlete_position_name') -> pd.DataFrame:
    """Add normalized position group column."""
    df = df.copy()
    if position_col in df.columns:
        df['position_group'] = df[position_col].apply(normalize_position)
    else:
        df['position_group'] = 'Other'
    return df
