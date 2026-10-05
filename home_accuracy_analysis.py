from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# --------------------------------------------------
# FILE LOCATIONS
# --------------------------------------------------
TEAM_GAME_FILE = Path(
    "results/historical_bonus_team_games.csv"
)

ADJUSTED_FILE = Path(
    "results/historical_bonus_without_late_fouls.csv"
)

FIRST_IN_GAME_FILE = Path(
    "results/quarter_bonus_analysis/"
    "first_team_in_bonus_each_game.csv"
)

OUTPUT_FOLDER = Path(
    "results/home_accuracy_analysis"
)

CHART_FOLDER = Path(
    "results/charts/home_accuracy"
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
# HELPER FUNCTIONS
# --------------------------------------------------
def win_rate(frame):
    if len(frame) == 0:
        return np.nan

    return frame["win"].mean() * 100


def add_bar_labels(axis, bars, suffix="%"):
    for bar in bars:
        height = bar.get_height()

        if pd.notna(height):
            axis.text(
                bar.get_x()
                + bar.get_width() / 2,
                height + 0.4,
                f"{height:.2f}{suffix}",
                ha="center",
                va="bottom",
                fontweight="bold"
            )


# --------------------------------------------------
# LOAD TEAM-GAME RESULTS
# --------------------------------------------------
print("Loading historical team-game data...")

data = pd.read_csv(
    TEAM_GAME_FILE,
    dtype={"gameId": str},
    low_memory=False
)

data["gameId"] = (
    data["gameId"]
    .astype(str)
    .str.zfill(10)
)

numeric_columns = [
    "win",
    "point_difference",
    "periods_first_to_bonus",
    "bonus_fta",
    "bonus_ftm",
    "bonus_ft_percentage",
    "bonus_fta_difference"
]

for column in numeric_columns:
    data[column] = pd.to_numeric(
        data[column],
        errors="coerce"
    )


# --------------------------------------------------
# ADD ADJUSTED BONUS ATTEMPTS
# --------------------------------------------------
if ADJUSTED_FILE.exists():
    adjusted = pd.read_csv(
        ADJUSTED_FILE,
        dtype={"gameId": str},
        low_memory=False
    )

    adjusted["gameId"] = (
        adjusted["gameId"]
        .astype(str)
        .str.zfill(10)
    )

    adjusted_columns = adjusted[
        [
            "gameId",
            "team",
            "bonus_fta_before_final_2",
            "bonus_fta_difference_before_final_2"
        ]
    ].drop_duplicates(
        subset=[
            "gameId",
            "team"
        ]
    )

    data = data.merge(
        adjusted_columns,
        on=[
            "gameId",
            "team"
        ],
        how="left"
    )

else:
    data["bonus_fta_before_final_2"] = np.nan

    data[
        "bonus_fta_difference_before_final_2"
    ] = np.nan


# --------------------------------------------------
# IDENTIFY HOME AND AWAY TEAMS
# --------------------------------------------------
print("Identifying home and away teams...")

home_away_rows = []

seasons = sorted(
    data["season"]
    .dropna()
    .astype(str)
    .unique()
)

for season in seasons:
    season_tag = season.replace("-", "_")

    full_file = Path(
        f"data/games_full_{season_tag}.csv"
    )

    fallback_file = Path(
        f"data/games_{season_tag}.csv"
    )

    if full_file.exists():
        game_file = full_file
    elif fallback_file.exists():
        game_file = fallback_file
    else:
        print(
            f"Missing game file for {season}"
        )
        continue

    games = pd.read_csv(
        game_file,
        dtype={"GAME_ID": str},
        low_memory=False
    )

    required_columns = {
        "GAME_ID",
        "TEAM_ABBREVIATION",
        "MATCHUP"
    }

    if not required_columns.issubset(
        games.columns
    ):
        print(
            f"Home/away columns missing "
            f"for {season}"
        )
        continue

    games["GAME_ID"] = (
        games["GAME_ID"]
        .astype(str)
        .str.zfill(10)
    )

    games["MATCHUP"] = (
        games["MATCHUP"]
        .astype(str)
    )

    games["location"] = np.select(
        [
            games["MATCHUP"].str.contains(
                "vs.",
                regex=False,
                na=False
            ),
            games["MATCHUP"].str.contains(
                "@",
                regex=False,
                na=False
            )
        ],
        [
            "Home",
            "Away"
        ],
        default="Unknown"
    )

    season_locations = games[
        [
            "GAME_ID",
            "TEAM_ABBREVIATION",
            "location"
        ]
    ].drop_duplicates(
        subset=[
            "GAME_ID",
            "TEAM_ABBREVIATION"
        ]
    )

    season_locations = (
        season_locations.rename(
            columns={
                "GAME_ID": "gameId",
                "TEAM_ABBREVIATION": "team"
            }
        )
    )

    home_away_rows.append(
        season_locations
    )

if home_away_rows:
    locations = pd.concat(
        home_away_rows,
        ignore_index=True
    )

    data = data.merge(
        locations,
        on=[
            "gameId",
            "team"
        ],
        how="left"
    )

else:
    data["location"] = "Unknown"

data["location"] = (
    data["location"]
    .fillna("Unknown")
)


# --------------------------------------------------
# QUESTION 1:
# HOME VERSUS AWAY BONUS RESULTS
# --------------------------------------------------
known_locations = data[
    data["location"].isin(
        [
            "Home",
            "Away"
        ]
    )
].copy()

home_away_summary = (
    known_locations
    .groupby("location")
    .agg(
        team_games=("gameId", "count"),
        wins=("win", "sum"),
        average_periods_first_to_bonus=(
            "periods_first_to_bonus",
            "mean"
        ),
        average_bonus_fta=(
            "bonus_fta",
            "mean"
        ),
        average_adjusted_bonus_fta=(
            "bonus_fta_before_final_2",
            "mean"
        ),
        average_bonus_fta_difference=(
            "bonus_fta_difference",
            "mean"
        ),
        average_adjusted_fta_difference=(
            "bonus_fta_difference_before_final_2",
            "mean"
        ),
        average_point_difference=(
            "point_difference",
            "mean"
        )
    )
    .reset_index()
)

home_away_summary[
    "win_percentage"
] = (
    home_away_summary["wins"]
    / home_away_summary["team_games"]
    * 100
)

home_away_summary.to_csv(
    OUTPUT_FOLDER
    / "home_away_bonus_summary.csv",
    index=False
)


# --------------------------------------------------
# FIRST TEAM INTO BONUS:
# HOME OR AWAY?
# --------------------------------------------------
if FIRST_IN_GAME_FILE.exists():
    first_game = pd.read_csv(
        FIRST_IN_GAME_FILE,
        dtype={"gameId": str},
        low_memory=False
    )

    first_game["gameId"] = (
        first_game["gameId"]
        .astype(str)
        .str.zfill(10)
    )

    first_locations = locations.rename(
        columns={
            "team": "team_entering_bonus"
        }
    )

    first_game = first_game.merge(
        first_locations,
        on=[
            "gameId",
            "team_entering_bonus"
        ],
        how="left"
    )

    first_location_summary = (
        first_game[
            first_game["location"].isin(
                [
                    "Home",
                    "Away"
                ]
            )
        ]
        .groupby("location")
        .agg(
            games_first_to_bonus=(
                "gameId",
                "count"
            ),
            wins=("win", "sum")
        )
        .reset_index()
    )

    first_location_summary[
        "share_of_first_entries"
    ] = (
        first_location_summary[
            "games_first_to_bonus"
        ]
        / first_location_summary[
            "games_first_to_bonus"
        ].sum()
        * 100
    )

    first_location_summary[
        "win_percentage"
    ] = (
        first_location_summary["wins"]
        / first_location_summary[
            "games_first_to_bonus"
        ]
        * 100
    )

    first_location_summary.to_csv(
        OUTPUT_FOLDER
        / "home_away_first_in_game.csv",
        index=False
    )

else:
    first_location_summary = (
        pd.DataFrame()
    )


# --------------------------------------------------
# ADD OPPONENT BONUS ACCURACY
# --------------------------------------------------
opponent_accuracy = data[
    [
        "gameId",
        "team",
        "bonus_fta",
        "bonus_ftm",
        "bonus_ft_percentage"
    ]
].copy()

opponent_accuracy = (
    opponent_accuracy.rename(
        columns={
            "team": "opponent",
            "bonus_fta":
                "calculated_opponent_bonus_fta",
            "bonus_ftm":
                "opponent_bonus_ftm",
            "bonus_ft_percentage":
                "opponent_bonus_ft_percentage"
        }
    )
)

data = data.merge(
    opponent_accuracy,
    on=[
        "gameId",
        "opponent"
    ],
    how="left"
)


# --------------------------------------------------
# QUESTION 2:
# ATTEMPTS VERSUS ACCURACY
# --------------------------------------------------
data["attempt_result"] = np.select(
    [
        data["bonus_fta"]
        > data[
            "calculated_opponent_bonus_fta"
        ],
        data["bonus_fta"]
        < data[
            "calculated_opponent_bonus_fta"
        ]
    ],
    [
        "More attempts",
        "Fewer attempts"
    ],
    default="Tied attempts"
)

attempt_summary = (
    data
    .groupby("attempt_result")
    .agg(
        team_games=("gameId", "count"),
        wins=("win", "sum"),
        average_point_difference=(
            "point_difference",
            "mean"
        )
    )
    .reset_index()
)

attempt_summary["win_percentage"] = (
    attempt_summary["wins"]
    / attempt_summary["team_games"]
    * 100
)

attempt_summary.to_csv(
    OUTPUT_FOLDER
    / "bonus_attempt_results.csv",
    index=False
)

# Recalculate both teams' bonus percentages
# directly from makes and attempts.
data["bonus_ft_percentage"] = np.where(
    data["bonus_fta"] > 0,
    data["bonus_ftm"] / data["bonus_fta"],
    np.nan
)

data["opponent_bonus_ft_percentage"] = np.where(
    data["calculated_opponent_bonus_fta"] > 0,
    data["opponent_bonus_ftm"]
    / data["calculated_opponent_bonus_fta"],
    np.nan
)
# Only compare accuracy when both teams
# attempted at least one bonus free throw.
accuracy_data = data[
    (data["bonus_fta"] > 0)
    & (
        data[
            "calculated_opponent_bonus_fta"
        ] > 0
    )
    & data[
        "bonus_ft_percentage"
    ].notna()
    & data[
        "opponent_bonus_ft_percentage"
    ].notna()
].copy()

accuracy_data[
    "accuracy_difference"
] = (
    accuracy_data[
        "bonus_ft_percentage"
    ]
    - accuracy_data[
        "opponent_bonus_ft_percentage"
    ]
)

accuracy_data[
    "accuracy_result"
] = np.select(
    [
        accuracy_data[
            "accuracy_difference"
        ] > 0,
        accuracy_data[
            "accuracy_difference"
        ] < 0
    ],
    [
        "Higher accuracy",
        "Lower accuracy"
    ],
    default="Tied accuracy"
)

accuracy_summary = (
    accuracy_data
    .groupby("accuracy_result")
    .agg(
        team_games=("gameId", "count"),
        wins=("win", "sum"),
        average_point_difference=(
            "point_difference",
            "mean"
        ),
        average_accuracy_difference=(
            "accuracy_difference",
            "mean"
        )
    )
    .reset_index()
)

accuracy_summary[
    "win_percentage"
] = (
    accuracy_summary["wins"]
    / accuracy_summary["team_games"]
    * 100
)

accuracy_summary.to_csv(
    OUTPUT_FOLDER
    / "bonus_accuracy_results.csv",
    index=False
)


# --------------------------------------------------
# CALCULATE COMPARABLE WIN-RATE GAPS
# --------------------------------------------------
more_attempt_rate = win_rate(
    data[
        data["attempt_result"]
        == "More attempts"
    ]
)

fewer_attempt_rate = win_rate(
    data[
        data["attempt_result"]
        == "Fewer attempts"
    ]
)

attempt_win_gap = (
    more_attempt_rate
    - fewer_attempt_rate
)

higher_accuracy_rate = win_rate(
    accuracy_data[
        accuracy_data[
            "accuracy_result"
        ] == "Higher accuracy"
    ]
)

lower_accuracy_rate = win_rate(
    accuracy_data[
        accuracy_data[
            "accuracy_result"
        ] == "Lower accuracy"
    ]
)

accuracy_win_gap = (
    higher_accuracy_rate
    - lower_accuracy_rate
)

comparison = pd.DataFrame({
    "factor": [
        "More bonus attempts",
        "Higher bonus accuracy"
    ],
    "advantaged_win_percentage": [
        more_attempt_rate,
        higher_accuracy_rate
    ],
    "disadvantaged_win_percentage": [
        fewer_attempt_rate,
        lower_accuracy_rate
    ],
    "win_percentage_gap": [
        attempt_win_gap,
        accuracy_win_gap
    ]
})

comparison.to_csv(
    OUTPUT_FOLDER
    / "attempts_vs_accuracy.csv",
    index=False
)


# --------------------------------------------------
# CORRELATIONS WITH FINAL SCORE MARGIN
# --------------------------------------------------
correlations = pd.DataFrame({
    "measurement": [
        "Bonus attempt difference",
        "Bonus accuracy difference"
    ],
    "correlation_with_point_difference": [
        data[
            [
                "bonus_fta_difference",
                "point_difference"
            ]
        ].corr().iloc[0, 1],
        accuracy_data[
            [
                "accuracy_difference",
                "point_difference"
            ]
        ].corr().iloc[0, 1]
    ]
})

correlations.to_csv(
    OUTPUT_FOLDER
    / "attempt_accuracy_correlations.csv",
    index=False
)


# --------------------------------------------------
# CHART 1:
# HOME VERSUS AWAY BONUS ATTEMPTS
# --------------------------------------------------
chart_home_away = (
    home_away_summary
    .set_index("location")
    .reindex(
        [
            "Home",
            "Away"
        ]
    )
    .reset_index()
)

x = np.arange(
    len(chart_home_away)
)

width = 0.36

plt.figure(figsize=(10, 7))

bars1 = plt.bar(
    x - width / 2,
    chart_home_away[
        "average_bonus_fta"
    ],
    width,
    label="All bonus FTs",
    color="#FDB927"
)

bars2 = plt.bar(
    x + width / 2,
    chart_home_away[
        "average_adjusted_bonus_fta"
    ],
    width,
    label="Before final 2:00",
    color="#1D428A"
)

for bars in [
    bars1,
    bars2
]:
    for bar in bars:
        height = bar.get_height()

        plt.text(
            bar.get_x()
            + bar.get_width() / 2,
            height + 0.08,
            f"{height:.2f}",
            ha="center",
            fontweight="bold"
        )

plt.xticks(
    x,
    chart_home_away["location"]
)

plt.ylabel(
    "Average bonus free-throw attempts"
)

plt.title(
    "Home Versus Away Bonus Free Throws\n"
    "NBA Regular Seasons, 1996-97 through 2025-26"
)

plt.legend()
plt.tight_layout()

plt.savefig(
    CHART_FOLDER
    / "01_home_away_bonus_attempts.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()


# --------------------------------------------------
# CHART 2:
# WHO REACHES THE BONUS FIRST?
# --------------------------------------------------
if not first_location_summary.empty:
    first_chart = (
        first_location_summary
        .set_index("location")
        .reindex(
            [
                "Home",
                "Away"
            ]
        )
        .reset_index()
    )

    plt.figure(figsize=(9, 6))

    bars = plt.bar(
        first_chart["location"],
        first_chart[
            "share_of_first_entries"
        ],
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

    add_bar_labels(
        plt.gca(),
        bars
    )

    plt.ylabel(
        "Share of games reaching bonus first"
    )

    plt.title(
        "Home or Away: Who Reaches "
        "the Bonus First?"
    )

    plt.ylim(
        0,
        first_chart[
            "share_of_first_entries"
        ].max() + 10
    )

    plt.tight_layout()

    plt.savefig(
        CHART_FOLDER
        / "02_home_away_first_bonus.png",
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()


# --------------------------------------------------
# CHART 3:
# ATTEMPTS VERSUS ACCURACY
# --------------------------------------------------
plt.figure(figsize=(10, 7))

bars = plt.bar(
    comparison["factor"],
    comparison["win_percentage_gap"],
    color=[
        "#FDB927",
        "#1D428A"
    ]
)

for bar in bars:
    height = bar.get_height()

    plt.text(
        bar.get_x()
        + bar.get_width() / 2,
        height + 0.4,
        f"{height:.2f} points",
        ha="center",
        fontweight="bold"
    )

plt.ylabel(
    "Win-percentage-point advantage"
)

plt.title(
    "Which Matters More?\n"
    "Bonus Attempts Versus Bonus Accuracy"
)

plt.ylim(
    0,
    comparison[
        "win_percentage_gap"
    ].max() + 6
)

plt.tight_layout()

plt.savefig(
    CHART_FOLDER
    / "03_attempts_vs_accuracy.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()


# --------------------------------------------------
# DISPLAY RESULTS
# --------------------------------------------------
print(
    "\nHOME AND ACCURACY ANALYSIS COMPLETE"
)

print("\nHOME VERSUS AWAY:")
print(
    home_away_summary.to_string(
        index=False
    )
)

if not first_location_summary.empty:
    print(
        "\nWHO REACHES THE BONUS "
        "FIRST IN THE GAME?"
    )

    print(
        first_location_summary.to_string(
            index=False
        )
    )

print(
    "\nATTEMPTS VERSUS ACCURACY:"
)

print(
    comparison.to_string(
        index=False
    )
)

print(
    "\nCORRELATIONS WITH "
    "FINAL SCORE MARGIN:"
)

print(
    correlations.to_string(
        index=False
    )
)

if attempt_win_gap > accuracy_win_gap:
    print(
        "\nRESULT: Bonus-attempt advantage "
        "had the larger win-rate gap."
    )
else:
    print(
        "\nRESULT: Bonus accuracy had "
        "the larger win-rate gap."
    )

print("\nFiles created:")
print(OUTPUT_FOLDER)
print(CHART_FOLDER)