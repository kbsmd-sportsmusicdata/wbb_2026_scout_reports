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


# =============================================================================
# ADVANCED PLAYER METRICS (Box Score Derived)
# =============================================================================

def calc_game_score(pts: Union[pd.Series, float],
                    fgm: Union[pd.Series, float],
                    fga: Union[pd.Series, float],
                    ftm: Union[pd.Series, float],
                    fta: Union[pd.Series, float],
                    orb: Union[pd.Series, float],
                    drb: Union[pd.Series, float],
                    stl: Union[pd.Series, float],
                    ast: Union[pd.Series, float],
                    blk: Union[pd.Series, float],
                    pf: Union[pd.Series, float],
                    tov: Union[pd.Series, float]) -> Union[pd.Series, float]:
    """
    Game Score (John Hollinger).

    Formula: GmSc = PTS + 0.4*FGM - 0.7*FGA - 0.4*(FTA-FTM) + 0.7*ORB + 0.3*DRB
                    + STL + 0.7*AST + 0.7*BLK - 0.4*PF - TOV

    Single-number measure of a player's game performance.
    Typical range: 0-40, with 10 being average starter performance.
    """
    return (pts + 0.4 * fgm - 0.7 * fga - 0.4 * (fta - ftm)
            + 0.7 * orb + 0.3 * drb + stl + 0.7 * ast
            + 0.7 * blk - 0.4 * pf - tov)


def calc_pie(pts: Union[pd.Series, float],
             fgm: Union[pd.Series, float],
             fga: Union[pd.Series, float],
             ftm: Union[pd.Series, float],
             fta: Union[pd.Series, float],
             orb: Union[pd.Series, float],
             drb: Union[pd.Series, float],
             stl: Union[pd.Series, float],
             ast: Union[pd.Series, float],
             blk: Union[pd.Series, float],
             pf: Union[pd.Series, float],
             tov: Union[pd.Series, float],
             game_pts: Union[pd.Series, float],
             game_fgm: Union[pd.Series, float],
             game_fga: Union[pd.Series, float],
             game_ftm: Union[pd.Series, float],
             game_fta: Union[pd.Series, float],
             game_orb: Union[pd.Series, float],
             game_drb: Union[pd.Series, float],
             game_stl: Union[pd.Series, float],
             game_ast: Union[pd.Series, float],
             game_blk: Union[pd.Series, float],
             game_pf: Union[pd.Series, float],
             game_tov: Union[pd.Series, float]) -> Union[pd.Series, float]:
    """
    Player Impact Estimate (PIE).

    Formula: PIE = (PTS + FGM + FTM - FGA - FTA + DRB + 0.5*ORB + AST + STL + 0.5*BLK - PF - TOV)
                   / (Game_PTS + Game_FGM + Game_FTM - Game_FGA - Game_FTA + Game_DRB
                      + 0.5*Game_ORB + Game_AST + Game_STL + 0.5*Game_BLK - Game_PF - Game_TOV)

    Measures player's overall contribution relative to game totals.
    Range: 0-1, with 0.10 (10%) being average for a 5-player rotation.
    """
    player_contribution = (pts + fgm + ftm - fga - fta + drb + 0.5 * orb
                           + ast + stl + 0.5 * blk - pf - tov)

    game_contribution = (game_pts + game_fgm + game_ftm - game_fga - game_fta
                         + game_drb + 0.5 * game_orb + game_ast + game_stl
                         + 0.5 * game_blk - game_pf - game_tov)

    if isinstance(game_contribution, pd.Series):
        return np.where(game_contribution != 0, player_contribution / game_contribution, 0.0)
    return player_contribution / game_contribution if game_contribution != 0 else 0.0


def calc_stl_pct(stl: Union[pd.Series, float],
                 minutes: Union[pd.Series, float],
                 opp_poss: Union[pd.Series, float],
                 team_minutes: float = 200.0) -> Union[pd.Series, float]:
    """
    Steal Percentage.

    Formula: STL% = (STL * Team_Min / 5) / (Min * Opp_Poss)

    Percentage of opponent possessions ending in a steal by this player.
    """
    if isinstance(minutes, pd.Series):
        denom = minutes * opp_poss
        return np.where(
            (denom > 0) & (minutes > 0),
            (stl * team_minutes / 5) / denom * 100,
            0.0
        )
    denom = minutes * opp_poss
    return (stl * team_minutes / 5) / denom * 100 if denom > 0 and minutes > 0 else 0.0


def calc_blk_pct(blk: Union[pd.Series, float],
                 minutes: Union[pd.Series, float],
                 opp_fga: Union[pd.Series, float],
                 opp_fg3a: Union[pd.Series, float],
                 team_minutes: float = 200.0) -> Union[pd.Series, float]:
    """
    Block Percentage.

    Formula: BLK% = (BLK * Team_Min / 5) / (Min * (Opp_FGA - Opp_3PA))

    Percentage of opponent 2-point attempts blocked by this player.
    """
    opp_2pa = opp_fga - opp_fg3a
    if isinstance(minutes, pd.Series):
        denom = minutes * opp_2pa
        return np.where(
            (denom > 0) & (minutes > 0),
            (blk * team_minutes / 5) / denom * 100,
            0.0
        )
    denom = minutes * opp_2pa
    return (blk * team_minutes / 5) / denom * 100 if denom > 0 and minutes > 0 else 0.0


def calc_trb_pct(orb: Union[pd.Series, float],
                 drb: Union[pd.Series, float],
                 minutes: Union[pd.Series, float],
                 team_orb: Union[pd.Series, float],
                 team_drb: Union[pd.Series, float],
                 opp_orb: Union[pd.Series, float],
                 opp_drb: Union[pd.Series, float],
                 team_minutes: float = 200.0) -> Union[pd.Series, float]:
    """
    Total Rebound Percentage.

    Formula: TRB% = (TRB * Team_Min / 5) / (Min * (Team_TRB + Opp_TRB))

    Percentage of available rebounds grabbed by this player.
    """
    trb = orb + drb
    total_reb = team_orb + team_drb + opp_orb + opp_drb

    if isinstance(minutes, pd.Series):
        denom = minutes * total_reb
        return np.where(
            (denom > 0) & (minutes > 0),
            (trb * team_minutes / 5) / denom * 100,
            0.0
        )
    denom = minutes * total_reb
    return (trb * team_minutes / 5) / denom * 100 if denom > 0 and minutes > 0 else 0.0


def calc_floor_pct(fgm: Union[pd.Series, float],
                   ast: Union[pd.Series, float],
                   fga: Union[pd.Series, float],
                   fta: Union[pd.Series, float],
                   tov: Union[pd.Series, float],
                   team_fgm: Union[pd.Series, float],
                   orb: Union[pd.Series, float],
                   team_orb: Union[pd.Series, float]) -> Union[pd.Series, float]:
    """
    Floor Percentage (simplified).

    Formula: Floor% ≈ Scoring_Poss / Total_Poss

    Simplified: (FGM + 0.5*AST) / (FGA + 0.44*FTA + TOV)

    Percentage of a player's possessions that end in points scored.
    """
    # Simplified scoring possessions estimate
    scoring_poss = fgm + 0.5 * ast

    # Total possessions used
    total_poss = fga + 0.44 * fta + tov

    if isinstance(total_poss, pd.Series):
        return np.where(total_poss > 0, scoring_poss / total_poss, 0.0)
    return scoring_poss / total_poss if total_poss > 0 else 0.0


def calc_ppp(pts: Union[pd.Series, float],
             fga: Union[pd.Series, float],
             fta: Union[pd.Series, float],
             tov: Union[pd.Series, float]) -> Union[pd.Series, float]:
    """
    Points Per Possession (individual).

    Formula: PPP = PTS / (FGA + 0.44*FTA + TOV)

    Points scored per possession used.
    """
    poss = fga + 0.44 * fta + tov
    if isinstance(poss, pd.Series):
        return np.where(poss > 0, pts / poss, 0.0)
    return pts / poss if poss > 0 else 0.0


def calc_ppsa(pts: Union[pd.Series, float],
              fga: Union[pd.Series, float],
              fta: Union[pd.Series, float]) -> Union[pd.Series, float]:
    """
    Points Per Shot Attempt.

    Formula: PPsA = PTS / (FGA + 0.44*FTA)

    Similar to TS% but in points rather than percentage.
    Expected range: 0.8-1.4 for efficient scorers.
    """
    attempts = fga + 0.44 * fta
    if isinstance(attempts, pd.Series):
        return np.where(attempts > 0, pts / attempts, 0.0)
    return pts / attempts if attempts > 0 else 0.0


def calc_player_ortg(pts: Union[pd.Series, float],
                     fgm: Union[pd.Series, float],
                     fga: Union[pd.Series, float],
                     ftm: Union[pd.Series, float],
                     fta: Union[pd.Series, float],
                     orb: Union[pd.Series, float],
                     ast: Union[pd.Series, float],
                     tov: Union[pd.Series, float],
                     team_pts: Union[pd.Series, float],
                     team_fgm: Union[pd.Series, float],
                     team_fga: Union[pd.Series, float],
                     team_fta: Union[pd.Series, float],
                     team_orb: Union[pd.Series, float],
                     team_ast: Union[pd.Series, float]) -> Union[pd.Series, float]:
    """
    Individual Offensive Rating (simplified Dean Oliver method).

    Formula: ORtg = 100 * Points_Produced / Possessions_Used

    Simplified approximation:
    - Points_Produced ≈ PTS + AST * (Team_PTS / Team_FGM) * 0.5
    - Poss_Used ≈ FGA + 0.44*FTA + TOV - ORB_Contribution

    Points produced per 100 possessions used.
    """
    # Estimate points from assists (half credit)
    team_pts_per_fgm = np.where(
        team_fgm > 0 if isinstance(team_fgm, pd.Series) else team_fgm > 0,
        team_pts / team_fgm if not isinstance(team_pts, pd.Series) else np.where(team_fgm > 0, team_pts / team_fgm, 2.0),
        2.0
    )
    if isinstance(team_fgm, pd.Series):
        team_pts_per_fgm = np.where(team_fgm > 0, team_pts / team_fgm, 2.0)

    points_produced = pts + ast * team_pts_per_fgm * 0.5

    # Estimate possessions used
    poss_used = fga + 0.44 * fta + tov

    if isinstance(poss_used, pd.Series):
        return np.where(poss_used > 0, 100 * points_produced / poss_used, 0.0)
    return 100 * points_produced / poss_used if poss_used > 0 else 0.0


def calc_player_drtg(opp_pts: Union[pd.Series, float],
                     minutes: Union[pd.Series, float],
                     team_minutes: float,
                     team_poss: Union[pd.Series, float],
                     stl: Union[pd.Series, float],
                     blk: Union[pd.Series, float],
                     drb: Union[pd.Series, float],
                     pf: Union[pd.Series, float]) -> Union[pd.Series, float]:
    """
    Individual Defensive Rating (simplified estimate).

    Note: True DRtg requires play-by-play data. This is an approximation
    based on defensive box score stats.

    Formula: DRtg ≈ Team_DRtg - Defensive_Contribution_Adjustment

    The adjustment factors in steals, blocks, defensive rebounds, and fouls.
    Lower is better (fewer points allowed per 100 possessions).
    """
    # Base team defensive rating
    team_drtg = np.where(
        team_poss > 0 if isinstance(team_poss, pd.Series) else team_poss > 0,
        100 * opp_pts / team_poss if not isinstance(opp_pts, pd.Series) else np.where(team_poss > 0, 100 * opp_pts / team_poss, 100.0),
        100.0
    )
    if isinstance(team_poss, pd.Series):
        team_drtg = np.where(team_poss > 0, 100 * opp_pts / team_poss, 100.0)

    # Defensive contribution (positive stats reduce rating)
    # Weights are approximate based on typical impact
    def_contribution = (stl * 2.0 + blk * 1.5 + drb * 0.5 - pf * 0.5)

    # Scale by minutes played
    if isinstance(minutes, pd.Series):
        min_pct = np.where(team_minutes > 0, minutes / team_minutes, 0.0)
        adjustment = np.where(min_pct > 0, def_contribution / (min_pct * 100 + 1), 0.0)
        return team_drtg - adjustment
    else:
        min_pct = minutes / team_minutes if team_minutes > 0 else 0.0
        adjustment = def_contribution / (min_pct * 100 + 1) if min_pct > 0 else 0.0
        return team_drtg - adjustment


# =============================================================================
# ADVANCED PLAYER METRICS - BATCH CALCULATION
# =============================================================================

def calculate_advanced_player_metrics(player_df: pd.DataFrame,
                                      team_df: pd.DataFrame = None,
                                      opp_df: pd.DataFrame = None) -> pd.DataFrame:
    """
    Calculate all advanced player metrics from box score data.

    Args:
        player_df: DataFrame with player box scores
        team_df: DataFrame with team totals (for PIE, STL%, etc.)
        opp_df: DataFrame with opponent totals (for defensive metrics)

    Returns:
        DataFrame with advanced metrics added
    """
    df = player_df.copy()

    # Ensure numeric columns
    numeric_cols = [
        'minutes', 'points', 'field_goals_made', 'field_goals_attempted',
        'three_point_field_goals_made', 'three_point_field_goals_attempted',
        'free_throws_made', 'free_throws_attempted',
        'offensive_rebounds', 'defensive_rebounds', 'rebounds',
        'assists', 'steals', 'blocks', 'turnovers', 'fouls'
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # Shorthand
    pts = df['points']
    fgm = df['field_goals_made']
    fga = df['field_goals_attempted']
    fg3m = df.get('three_point_field_goals_made', 0)
    fg3a = df.get('three_point_field_goals_attempted', 0)
    ftm = df['free_throws_made']
    fta = df['free_throws_attempted']
    orb = df['offensive_rebounds']
    drb = df['defensive_rebounds']
    ast = df['assists']
    stl = df['steals']
    blk = df['blocks']
    tov = df['turnovers']
    pf = df.get('fouls', 0)
    minutes = df['minutes']

    # Game Score - always calculable
    df['game_score'] = calc_game_score(pts, fgm, fga, ftm, fta, orb, drb, stl, ast, blk, pf, tov)

    # Points Per Possession
    df['ppp'] = calc_ppp(pts, fga, fta, tov)

    # Points Per Shot Attempt
    df['ppsa'] = calc_ppsa(pts, fga, fta)

    # Floor Percentage (simplified)
    if team_df is not None and 'field_goals_made' in team_df.columns:
        # Merge team data
        team_fgm = pd.to_numeric(team_df.get('field_goals_made', 0), errors='coerce').fillna(0)
        team_orb = pd.to_numeric(team_df.get('offensive_rebounds', 0), errors='coerce').fillna(0)
        df['floor_pct'] = calc_floor_pct(fgm, ast, fga, fta, tov, team_fgm, orb, team_orb)
    else:
        # Simplified version without team context
        df['floor_pct'] = calc_floor_pct(fgm, ast, fga, fta, tov, fgm, orb, orb)

    return df
