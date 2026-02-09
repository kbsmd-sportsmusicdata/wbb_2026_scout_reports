player_season = (
    player_box
    .groupby(["season", "team_id", "athlete_id", "athlete_display_name"], as_index=False)
    .agg(
        games_played=("game_id", "nunique"),
        minutes=("minutes", "sum"),
        points=("points", "sum"),        # whatever your field name is
        fgm=("field_goals_made", "sum"),
        fga=("field_goals_attempted", "sum"),
        fg3m=("three_point_field_goals_made", "sum"),
        fg3a=("three_point_field_goals_attempted", "sum"),
        ftm=("free_throws_made", "sum"),
        fta=("free_throws_attempted", "sum"),
        reb=("total_rebounds", "sum"),
        ast=("assists", "sum"),
        stl=("steals", "sum"),
        blk=("blocks", "sum"),
        tov=("turnovers", "sum"),
    )
)
