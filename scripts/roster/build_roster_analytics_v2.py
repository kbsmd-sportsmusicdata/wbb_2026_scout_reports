import pandas as pd

team_lookup = pd.read_csv("data/raw/2026/teams_sports_roster_data.csv")
team_box = pd.read_parquet("data/raw/2026/team_box_2026.parquet")
player_box = pd.read_parquet("data/raw/2026/player_box_2026.parquet")

# Optionally, your existing processed game_summary if you want advanced metrics:
# game_summary = pd.read_parquet("data/processed/game_analysis.parquet")
