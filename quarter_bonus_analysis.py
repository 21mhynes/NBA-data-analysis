from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# --------------------------------------------------
# FILE LOCATIONS
# --------------------------------------------------
ENTRY_FILE = Path(
    "results/historical_bonus_entries.csv"
)

TEAM_GAME_FILE = Path(
    "results/historical_bonus_team_games.csv"
)

OUTPUT_FOLDER = Path(
    "results/quarter_bonus_analysis"
)

CHART_FOLDER = Path(
    "results/charts/quarter_bonus"
)

OUTPUT_FOLDER.mkdir(
    parents=True,
    exist_ok=True
)

CHART_FOLDER.mkdir(
    parents=True,
    exist_ok=True
)


# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------
print("Loading historical bonus-entry data...")

entries = pd.read_csv(
    ENTRY_FILE,
    dtype={"gameId": str},
    low_memory=False
)

team_games = pd.read_csv(
    TEAM_GAME_FILE,
    dtype={"gameId": str},
    low_memory=False
)

entries["gameId"] = (
    entries["gameId"]
    .astype(str)
    .str.zfill(10)
)

team_games["gameId"] = (
    team_games["gameId"]
    .astype(str)
    .str.zfill(10)
)

entries["period"] = pd.to_numeric(
    entries["period"],
    errors="coerce"
)

entries["seconds_remaining"] = pd.to_numeric(
    entries["seconds_remaining"],
    errors="coerce"
)

entries["first_to_bonus_in_period"] = pd.to_numeric(
    entries["first_to_bonus_in_period"],
    errors="coerce"
)

team_games["win"] = pd.to_numeric(
    team_games["win"],
    errors="coerce"
)

team_games["point_difference"] = pd.to_numeric(
    team_games["point_difference"],
    errors="coerce"
)


# --------------------------------------------------
# FIND FIRST TEAM INTO THE BONUS IN EVERY PERIOD
# --------------------------------------------------
first_entries = entries[
    entries["first_to_bonus_in_period"] == 1
].copy()

first_entries = (
    first_entries
    .sort_values(
        [
            "gameId",
            "period",
            "seconds_remaining"
        ],
        ascending=[
            True,
            True,
            False
        ]
    )
    .drop_duplicates(
        subset=[
            "gameId",
            "period"
        ]
    )
)


# --------------------------------------------------
# ADD GAME OUTCOMES
# --------------------------------------------------
outcomes = (
    team_games[
        [
            "gameId",
            "team",
            "season",
            "win",
            "point_difference"
        ]
    ]
    .drop_duplicates(
        subset=[
            "gameId",
            "team"
        ]
    )
)

first_entries = first_entries.merge(
    outcomes,
    left_on=[
        "gameId",
        "team_entering_bonus"
    ],
    right_on=[
        "gameId",
        "team"
    ],
    how="left"
)
# Restore one season column after the merge.
if "season" not in first_entries.columns:
    if "season_y" in first_entries.columns:
        first_entries["season"] = first_entries["season_y"]
    elif "season_x" in first_entries.columns:
        first_entries["season"] = first_entries["season_x"]
first_entries = first_entries.dropna(
    subset=[
        "win",
        "period"
    ]
).copy()

first_entries["period"] = (
    first_entries["period"]
    .astype(int)
)


# --------------------------------------------------
# LABEL THE PERIODS
# --------------------------------------------------
def period_label(period):
    if period == 1:
        return "1st Quarter"

    if period == 2:
        return "2nd Quarter"

    if period == 3:
        return "3rd Quarter"

    if period == 4:
        return "4th Quarter"

    return "Overtime"


first_entries["period_label"] = (
    first_entries["period"]
    .apply(period_label)
)


# --------------------------------------------------
# QUESTION 1:
# WHICH QUARTER'S FIRST-TO-BONUS ADVANTAGE MATTERS MOST?
# --------------------------------------------------
period_order = [
    "1st Quarter",
    "2nd Quarter",
    "3rd Quarter",
    "4th Quarter",
    "Overtime"
]

quarter_summary = (
    first_entries
    .groupby("period_label")
    .agg(
        games=("gameId", "count"),
        wins=("win", "sum"),
        average_point_difference=(
            "point_difference",
            "mean"
        ),
        average_seconds_remaining=(
            "seconds_remaining",
            "mean"
        )
    )
    .reindex(period_order)
    .dropna(
        subset=["games"]
    )
    .reset_index()
)

quarter_summary["win_percentage"] = (
    quarter_summary["wins"]
    / quarter_summary["games"]
    * 100
)

quarter_summary[
    "win_percentage_advantage_over_50"
] = (
    quarter_summary["win_percentage"]
    - 50
)

quarter_summary.to_csv(
    OUTPUT_FOLDER
    / "first_to_bonus_by_quarter.csv",
    index=False
)


# --------------------------------------------------
# FOURTH-QUARTER SENSITIVITY TEST
# --------------------------------------------------
fourth_quarter = first_entries[
    first_entries["period"] == 4
].copy()

fourth_before_final_two = fourth_quarter[
    fourth_quarter["seconds_remaining"] > 120
]

fourth_final_two = fourth_quarter[
    fourth_quarter["seconds_remaining"] <= 120
]

q4_sensitivity = pd.DataFrame({
    "group": [
        "All fourth-quarter entries",
        "Entered before final two minutes",
        "Entered during final two minutes"
    ],
    "games": [
        len(fourth_quarter),
        len(fourth_before_final_two),
        len(fourth_final_two)
    ],
    "win_percentage": [
        fourth_quarter["win"].mean() * 100,
        fourth_before_final_two["win"].mean() * 100,
        fourth_final_two["win"].mean() * 100
    ]
})

q4_sensitivity.to_csv(
    OUTPUT_FOLDER
    / "fourth_quarter_sensitivity.csv",
    index=False
)


# --------------------------------------------------
# QUESTION 2:
# FIRST TEAM TO REACH THE BONUS ANYWHERE IN THE GAME
# --------------------------------------------------
first_in_game = (
    first_entries
    .sort_values(
        [
            "gameId",
            "period",
            "seconds_remaining"
        ],
        ascending=[
            True,
            True,
            False
        ]
    )
    .drop_duplicates(
        subset=["gameId"],
        keep="first"
    )
    .copy()
)

first_in_game.to_csv(
    OUTPUT_FOLDER
    / "first_team_in_bonus_each_game.csv",
    index=False
)

first_game_win_rate = (
    first_in_game["win"].mean()
    * 100
)

first_game_losses = (
    len(first_in_game)
    - first_in_game["win"].sum()
)

first_game_summary = pd.DataFrame({
    "games": [
        len(first_in_game)
    ],
    "wins": [
        int(first_in_game["win"].sum())
    ],
    "losses": [
        int(first_game_losses)
    ],
    "win_percentage": [
        first_game_win_rate
    ],
    "win_percentage_advantage_over_50": [
        first_game_win_rate - 50
    ]
})

first_game_summary.to_csv(
    OUTPUT_FOLDER
    / "first_in_game_summary.csv",
    index=False
)


# --------------------------------------------------
# FIRST-IN-GAME RESULT BY SEASON
# --------------------------------------------------
season_summary = (
    first_in_game
    .groupby("season")
    .agg(
        games=("gameId", "count"),
        wins=("win", "sum"),
        average_point_difference=(
            "point_difference",
            "mean"
        )
    )
    .reset_index()
)

season_summary["win_percentage"] = (
    season_summary["wins"]
    / season_summary["games"]
    * 100
)

season_summary["start_year"] = (
    season_summary["season"]
    .astype(str)
    .str[:4]
    .astype(int)
)

season_summary = season_summary.sort_values(
    "start_year"
)

season_summary.to_csv(
    OUTPUT_FOLDER
    / "first_in_game_by_season.csv",
    index=False
)


# --------------------------------------------------
# CHART 1:
# WIN RATE OF FIRST TEAM INTO BONUS BY QUARTER
# --------------------------------------------------
plt.figure(figsize=(11, 7))

colors = [
    "#1D428A",
    "#4F81BD",
    "#FDB927",
    "#C8102E",
    "#6A1B9A"
]

bars = plt.bar(
    quarter_summary["period_label"],
    quarter_summary["win_percentage"],
    color=colors[
        :len(quarter_summary)
    ]
)

plt.axhline(
    50,
    color="black",
    linestyle="--",
    linewidth=1
)

for bar, games in zip(
    bars,
    quarter_summary["games"]
):
    height = bar.get_height()

    plt.text(
        bar.get_x()
        + bar.get_width() / 2,
        height + 0.4,
        f"{height:.1f}%\n"
        f"n={int(games):,}",
        ha="center",
        va="bottom",
        fontsize=10,
        fontweight="bold"
    )

plt.ylabel("Win percentage")
plt.xlabel("Period")
plt.title(
    "Win Rate of the First Team to Reach the Bonus\n"
    "by Quarter, 1996-97 through 2025-26"
)

plt.ylim(
    0,
    quarter_summary[
        "win_percentage"
    ].max() + 10
)

plt.tight_layout()

plt.savefig(
    CHART_FOLDER
    / "01_first_to_bonus_by_quarter.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()


# --------------------------------------------------
# CHART 2:
# FIRST TEAM INTO BONUS ANYWHERE IN GAME
# --------------------------------------------------
game_labels = [
    "First team into bonus",
    "Opponent"
]

game_values = [
    first_game_win_rate,
    100 - first_game_win_rate
]

plt.figure(figsize=(9, 6))

bars = plt.bar(
    game_labels,
    game_values,
    color=[
        "#1D428A",
        "#C8102E"
    ]
)

plt.axhline(
    50,
    color="black",
    linestyle="--",
    linewidth=1
)

for bar in bars:
    height = bar.get_height()

    plt.text(
        bar.get_x()
        + bar.get_width() / 2,
        height + 0.5,
        f"{height:.1f}%",
        ha="center",
        fontweight="bold"
    )

plt.ylabel("Win percentage")
plt.title(
    "Does the First Team to Reach the Bonus\n"
    "Anywhere in the Game Win More Often?"
)

plt.ylim(
    0,
    max(game_values) + 10
)

plt.tight_layout()

plt.savefig(
    CHART_FOLDER
    / "02_first_in_game_win_percentage.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()


# --------------------------------------------------
# CHART 3:
# FIRST-IN-GAME WIN RATE OVER TIME
# --------------------------------------------------
x = np.arange(
    len(season_summary)
)

plt.figure(figsize=(15, 7))

plt.plot(
    x,
    season_summary["win_percentage"],
    marker="o",
    linewidth=2.5,
    color="#1D428A"
)

plt.axhline(
    50,
    color="black",
    linestyle="--",
    linewidth=1
)

plt.xticks(
    x,
    season_summary["season"],
    rotation=65
)

plt.ylabel("Win percentage")
plt.xlabel("Season")

plt.title(
    "Win Rate of the First Team to Reach the Bonus\n"
    "Across 30 NBA Regular Seasons"
)

plt.grid(
    axis="y",
    alpha=0.25
)

plt.tight_layout()

plt.savefig(
    CHART_FOLDER
    / "03_first_in_game_over_time.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()


# --------------------------------------------------
# CHART 4:
# FOURTH-QUARTER SENSITIVITY
# --------------------------------------------------
plt.figure(figsize=(11, 7))

bars = plt.bar(
    q4_sensitivity["group"],
    q4_sensitivity["win_percentage"],
    color=[
        "#1D428A",
        "#4F81BD",
        "#C8102E"
    ]
)

plt.axhline(
    50,
    color="black",
    linestyle="--",
    linewidth=1
)

for bar, games in zip(
    bars,
    q4_sensitivity["games"]
):
    height = bar.get_height()

    plt.text(
        bar.get_x()
        + bar.get_width() / 2,
        height + 0.4,
        f"{height:.1f}%\n"
        f"n={int(games):,}",
        ha="center",
        fontweight="bold"
    )

plt.ylabel("Win percentage")

plt.title(
    "Fourth-Quarter First-to-Bonus Win Rate\n"
    "Before and During the Final Two Minutes"
)

plt.xticks(rotation=8)

plt.ylim(
    0,
    q4_sensitivity[
        "win_percentage"
    ].max() + 10
)

plt.tight_layout()

plt.savefig(
    CHART_FOLDER
    / "04_fourth_quarter_sensitivity.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()


# --------------------------------------------------
# DISPLAY RESULTS
# --------------------------------------------------
best_quarter = (
    quarter_summary
    .sort_values(
        "win_percentage",
        ascending=False
    )
    .iloc[0]
)

print(
    "\nQUARTER BONUS ANALYSIS COMPLETE"
)

print(
    f"\nGames with a recorded first "
    f"bonus team: {len(first_in_game):,}"
)

print(
    "\nFIRST TEAM INTO BONUS ANYWHERE "
    "IN THE GAME:"
)

print(
    f"Win percentage: "
    f"{first_game_win_rate:.2f}%"
)

print(
    f"Advantage over 50%: "
    f"{first_game_win_rate - 50:.2f} "
    "percentage points"
)

print(
    "\nWIN RATE BY QUARTER:"
)

print(
    quarter_summary[
        [
            "period_label",
            "games",
            "win_percentage",
            "average_point_difference"
        ]
    ].to_string(
        index=False
    )
)

print(
    "\nSTRONGEST QUARTER:"
)

print(
    f"{best_quarter['period_label']} "
    f"at {best_quarter['win_percentage']:.2f}%"
)

print(
    "\nFOURTH-QUARTER SENSITIVITY:"
)

print(
    q4_sensitivity.to_string(
        index=False
    )
)

print("\nFiles created:")
print(OUTPUT_FOLDER)
print(CHART_FOLDER)