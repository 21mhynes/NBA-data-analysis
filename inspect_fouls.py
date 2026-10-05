import pandas as pd


FILE_PATH = "data/play_by_play_2025_26.csv"

print("Loading play-by-play data...")

data = pd.read_csv(
    FILE_PATH,
    dtype={"gameId": str},
    low_memory=False
)

print(f"Total rows: {len(data):,}")

print("\nCOLUMN NAMES:")
for column in data.columns:
    print(column)


print("\nACTION TYPES:")
print(
    data["actionType"]
    .fillna("MISSING")
    .value_counts()
    .to_string()
)


fouls = data[
    data["actionType"]
    .fillna("")
    .str.lower()
    .eq("foul")
].copy()

print(f"\nTOTAL FOUL EVENTS: {len(fouls):,}")

print("\nFOUL SUBTYPES:")
print(
    fouls["subType"]
    .fillna("MISSING")
    .value_counts()
    .to_string()
)


free_throws = data[
    data["actionType"]
    .fillna("")
    .str.lower()
    .eq("free throw")
].copy()

print(f"\nTOTAL FREE-THROW EVENTS: {len(free_throws):,}")

print("\nFREE-THROW SUBTYPES:")
print(
    free_throws["subType"]
    .fillna("MISSING")
    .value_counts()
    .to_string()
)


print("\nEXAMPLE FOULS:")
example_columns = [
    "gameId",
    "period",
    "clock",
    "teamTricode",
    "playerName",
    "subType",
    "description"
]

print(
    fouls[example_columns]
    .head(25)
    .to_string(index=False)
)