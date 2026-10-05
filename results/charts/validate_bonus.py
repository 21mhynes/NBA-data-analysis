from pathlib import Path
import pandas as pd

RAW_FILE = Path("data/play_by_play_2025_26.csv")
BONUS_FILE = Path("results/bonus_entries_2025_26.csv")
OUTPUT_FILE = Path("results/bonus_validation_sample.csv")

# Load the existing files without modifying them
pbp = pd.read_csv(RAW_FILE, low_memory=False)
bonus = pd.read_csv(BONUS_FILE, low_memory=False)

print("\nRAW DATA COLUMNS:")
print(pbp.columns.tolist())

print("\nBONUS DATA COLUMNS:")
print(bonus.columns.tolist())

# Find the game-ID column
possible_game_columns = ["gameId", "game_id", "GAME_ID"]

game_column = next(
    (column for column in possible_game_columns if column in pbp.columns),
    None
)

if game_column is None:
    raise ValueError("The game ID column could not be found.")

# Select five games that contain bonus entries
bonus_game_column = next(
    (column for column in possible_game_columns if column in bonus.columns),
    None
)

if bonus_game_column is not None:
    sample_games = (
        bonus[bonus_game_column]
        .dropna()
        .astype(str)
        .drop_duplicates()
        .head(5)
        .tolist()
    )
else:
    sample_games = (
        pbp[game_column]
        .dropna()
        .astype(str)
        .drop_duplicates()
        .head(5)
        .tolist()
    )

pbp[game_column] = pbp[game_column].astype(str)

sample = pbp[pbp[game_column].isin(sample_games)].copy()

# Keep only foul and free-throw events
if "actionType" not in sample.columns:
    raise ValueError("The actionType column could not be found.")

sample = sample[
    sample["actionType"]
    .astype(str)
    .str.lower()
    .isin(["foul", "free throw"])
].copy()

# Put events into game order
sort_columns = [
    column
    for column in [game_column, "period", "actionNumber"]
    if column in sample.columns
]

sample = sample.sort_values(sort_columns)

# Keep the most useful columns
wanted_columns = [
    game_column,
    "period",
    "clock",
    "actionNumber",
    "teamId",
    "teamTricode",
    "personId",
    "playerName",
    "actionType",
    "subType",
    "description",
    "scoreHome",
    "scoreAway",
]

output_columns = [
    column for column in wanted_columns if column in sample.columns
]

sample[output_columns].to_csv(OUTPUT_FILE, index=False)

print("\nVALIDATION SAMPLE COMPLETE")
print(f"Games checked: {len(sample_games)}")
print(f"Foul and free-throw events exported: {len(sample)}")
print(f"Saved here: {OUTPUT_FILE}")
print("\nYour original data was not changed.")