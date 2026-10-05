from pathlib import Path
import pandas as pd

RAW_FILE = Path("data/play_by_play_2025_26.csv")
BONUS_FILE = Path("results/bonus_entries_2025_26.csv")
REPORT_FILE = Path("results/bonus_accuracy_report.csv")

print("Loading data...")

pbp = pd.read_csv(RAW_FILE, low_memory=False)
bonus = pd.read_csv(BONUS_FILE, low_memory=False)

required_columns = [
    "gameId",
    "period",
    "team_entering_bonus",
    "opponent_committing_fouls",
    "clock",
    "seconds_remaining",
    "official_team_foul_number",
    "first_to_bonus_in_period",
]

missing = [column for column in required_columns if column not in bonus.columns]

if missing:
    raise ValueError(f"Missing required columns: {missing}")

# Make matching values consistent
for frame in [pbp, bonus]:
    frame["gameId"] = frame["gameId"].astype(str)
    frame["period"] = pd.to_numeric(frame["period"], errors="coerce")

pbp["clock"] = pbp["clock"].astype(str)
bonus["clock"] = bonus["clock"].astype(str)

# Get all foul events from the raw play-by-play data
fouls = pbp[
    pbp["actionType"].astype(str).str.lower().eq("foul")
].copy()

foul_keys = set(
    zip(
        fouls["gameId"],
        fouls["period"],
        fouls["teamTricode"].astype(str),
        fouls["clock"],
    )
)

# Check whether each recorded bonus entry matches a real foul
bonus["matching_raw_foul"] = bonus.apply(
    lambda row: (
        row["gameId"],
        row["period"],
        str(row["opponent_committing_fouls"]),
        row["clock"],
    )
    in foul_keys,
    axis=1,
)

# Additional accuracy checks
bonus["teams_are_different"] = (
    bonus["team_entering_bonus"].astype(str)
    != bonus["opponent_committing_fouls"].astype(str)
)

bonus["valid_seconds_remaining"] = (
    pd.to_numeric(bonus["seconds_remaining"], errors="coerce").ge(0)
    & (
        (
            bonus["period"].le(4)
            & pd.to_numeric(
                bonus["seconds_remaining"], errors="coerce"
            ).le(720)
        )
        |
        (
            bonus["period"].gt(4)
            & pd.to_numeric(
                bonus["seconds_remaining"], errors="coerce"
            ).le(300)
        )
    )
)

duplicate_entries = bonus.duplicated(
    subset=["gameId", "period", "team_entering_bonus"],
    keep=False,
)

first_counts = (
    bonus.groupby(["gameId", "period"])["first_to_bonus_in_period"]
    .sum()
)

too_many_first = int((first_counts > 1).sum())

bonus["duplicate_team_period_entry"] = duplicate_entries

bonus.to_csv(REPORT_FILE, index=False)

match_rate = bonus["matching_raw_foul"].mean() * 100
different_team_rate = bonus["teams_are_different"].mean() * 100
valid_time_rate = bonus["valid_seconds_remaining"].mean() * 100

print("\nACCURACY CHECK COMPLETE")
print(f"Bonus entries checked: {len(bonus):,}")
print(f"Entries matching a real foul: {match_rate:.2f}%")
print(f"Correct opposing teams: {different_team_rate:.2f}%")
print(f"Valid game-clock times: {valid_time_rate:.2f}%")
print(f"Duplicate team-period entries: {duplicate_entries.sum():,}")
print(f"Periods with multiple teams marked first: {too_many_first}")
print(f"Full report saved here: {REPORT_FILE}")
print("\nYour original data was not changed.")