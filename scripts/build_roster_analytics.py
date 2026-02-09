import pandas as pd

roster = pd.read_csv(
    "data/raw/2026/teams_sports_roster_data.csv"
)  # this should include or map to wbb_rosters_2025_26.csv fields
# Reads roster CSV and team mapping:

# If wbb_rosters_2025_26.csv is not already copied locally, download it once and save as data/raw/2026/wbb_rosters_2025_26.csv
wbb_rosters = pd.read_csv("data/raw/2026/wbb_rosters_2025_26.csv")

# Reads parquet player and team boxes:

player_box = pd.read_parquet("data/raw/2026/player_box_2026.parquet")
team_box = pd.read_parquet("data/raw/2026/team_box_2026.parquet")

# Harmonizes team identifiers: 
# use teams_sports_roster_data.csv to map the Sports‑Roster‑Data team code/name to the ID used in player_box/team_box (e.g., ESPN team_id).
