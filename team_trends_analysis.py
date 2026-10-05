from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd


# ---------------------------------------------------------
# FILE LOCATIONS
# ---------------------------------------------------------

INPUT_FILE = Path("results/historical_bonus_team_games.csv")
OUTPUT_FOLDER = Path("results/team_trends")
CHART_FOLDER = Path("results/charts/team_trends")

OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)
CHART_FOLDER.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------

print("Loading 30 seasons of historical data...")

if not INPUT_FILE.exists():
    raise SystemExit(
        "Could not find results/historical_bonus_team_games.csv"
    )

data = pd.read_csv(INPUT_FILE)

print(f"Rows loaded: {len(data):,}")


# ---------------------------------------------------------
# FIND THE CORRECT COLUMN NAMES
# ---------------------------------------------------------

def find_column(possible_names):
    for name in possible_names:
        if name in data.columns:
            return name
    return None


season_column = find_column(
    ["season", "season_label", "season_name"]
)

team_column = find_column(
    [
        "team_name",
        "team",
        "team_abbreviation",
        "team_tricode",
        "team_id",
    ]
)

win_column = find_column(
    ["won", "win", "is_winner"]
)

if season_column is None:
    raise SystemExit(
        "The program could not find the season column."
    )

if team_column is None:
    raise SystemExit(
        "The program could not find the team column."
    )

if win_column is None:
    raise SystemExit(
        "The program could not find the win column."
    )

print(f"Season column: {season_column}")
print(f"Team column: {team_column}")
print(f"Win column: {win_column}")


# ---------------------------------------------------------
# CLEAN NUMERIC COLUMNS
# ---------------------------------------------------------

numeric_columns = [
    win_column,
    "bonus_fta",
    "bonus_ftm",
    "bonus_ft_percentage",
    "adjusted_bonus_fta",
    "periods_first_to_bonus",
    "point_difference",
]

for column in numeric_columns:
    if column in data.columns:
        data[column] = pd.to_numeric(
            data[column], errors="coerce"
        )

data[win_column] = data[win_column].fillna(0)


# ---------------------------------------------------------
# CREATE TEAM-BY-SEASON SUMMARY
# ---------------------------------------------------------

aggregation = {
    "games": (win_column, "size"),
    "wins": (win_column, "sum"),
    "average_bonus_fta": ("bonus_fta", "mean"),
    "total_bonus_fta": ("bonus_fta", "sum"),
    "total_bonus_ftm": ("bonus_ftm", "sum"),
}

if "adjusted_bonus_fta" in data.columns:
    aggregation["average_adjusted_bonus_fta"] = (
        "adjusted_bonus_fta",
        "mean",
    )

if "periods_first_to_bonus" in data.columns:
    aggregation["average_periods_first_to_bonus"] = (
        "periods_first_to_bonus",
        "mean",
    )

if "point_difference" in data.columns:
    aggregation["average_point_difference"] = (
        "point_difference",
        "mean",
    )

team_season = (
    data.groupby([season_column, team_column])
    .agg(**aggregation)
    .reset_index()
)

team_season["win_percentage"] = (
    team_season["wins"] / team_season["games"] * 100
)

team_season["bonus_ft_percentage"] = (
    team_season["total_bonus_ftm"]
    / team_season["total_bonus_fta"].replace(0, pd.NA)
    * 100
)

team_season = team_season.sort_values(
    [team_column, season_column]
)

team_season.to_csv(
    OUTPUT_FOLDER / "team_by_season_summary.csv",
    index=False,
)


# ---------------------------------------------------------
# CREATE LEAGUE-WIDE SEASON SUMMARY
# ---------------------------------------------------------

league_season = (
    data.groupby(season_column)
    .agg(
        team_game_rows=(win_column, "size"),
        average_bonus_fta=("bonus_fta", "mean"),
        total_bonus_fta=("bonus_fta", "sum"),
        total_bonus_ftm=("bonus_ftm", "sum"),
    )
    .reset_index()
)

league_season["bonus_ft_percentage"] = (
    league_season["total_bonus_ftm"]
    / league_season["total_bonus_fta"].replace(0, pd.NA)
    * 100
)

if "adjusted_bonus_fta" in data.columns:
    adjusted_by_season = (
        data.groupby(season_column)["adjusted_bonus_fta"]
        .mean()
        .reset_index(
            name="average_adjusted_bonus_fta"
        )
    )

    league_season = league_season.merge(
        adjusted_by_season,
        on=season_column,
        how="left",
    )

if "periods_first_to_bonus" in data.columns:
    first_by_season = (
        data.groupby(season_column)["periods_first_to_bonus"]
        .mean()
        .reset_index(
            name="average_periods_first_to_bonus"
        )
    )

    league_season = league_season.merge(
        first_by_season,
        on=season_column,
        how="left",
    )

league_season = league_season.sort_values(season_column)

league_season.to_csv(
    OUTPUT_FOLDER / "league_season_trends.csv",
    index=False,
)


# ---------------------------------------------------------
# COMPARE FIRST FIVE SEASONS WITH LAST FIVE SEASONS
# ---------------------------------------------------------

season_list = list(league_season[season_column])

first_five = season_list[:5]
last_five = season_list[-5:]

early = team_season[
    team_season[season_column].isin(first_five)
].groupby(team_column).agg(
    early_games=("games", "sum"),
    early_bonus_fta=("average_bonus_fta", "mean"),
    early_bonus_ft_percentage=(
        "bonus_ft_percentage",
        "mean",
    ),
    early_win_percentage=("win_percentage", "mean"),
)

recent = team_season[
    team_season[season_column].isin(last_five)
].groupby(team_column).agg(
    recent_games=("games", "sum"),
    recent_bonus_fta=("average_bonus_fta", "mean"),
    recent_bonus_ft_percentage=(
        "bonus_ft_percentage",
        "mean",
    ),
    recent_win_percentage=("win_percentage", "mean"),
)

team_changes = early.join(recent, how="outer").reset_index()

team_changes["bonus_fta_change"] = (
    team_changes["recent_bonus_fta"]
    - team_changes["early_bonus_fta"]
)

team_changes["bonus_ft_percentage_change"] = (
    team_changes["recent_bonus_ft_percentage"]
    - team_changes["early_bonus_ft_percentage"]
)

team_changes["win_percentage_change"] = (
    team_changes["recent_win_percentage"]
    - team_changes["early_win_percentage"]
)

team_changes.to_csv(
    OUTPUT_FOLDER / "team_changes_first5_vs_last5.csv",
    index=False,
)


# ---------------------------------------------------------
# CREATE LEAGUE TREND CHARTS
# ---------------------------------------------------------

plt.figure(figsize=(14, 7))
plt.plot(
    league_season[season_column].astype(str),
    league_season["average_bonus_fta"],
    marker="o",
    linewidth=2,
)
plt.title("Average Bonus Free-Throw Attempts by NBA Season")
plt.xlabel("Season")
plt.ylabel("Average bonus FTA per team-game")
plt.xticks(rotation=60, ha="right")
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(
    CHART_FOLDER / "league_bonus_fta_by_season.png",
    dpi=200,
)
plt.close()


plt.figure(figsize=(14, 7))
plt.plot(
    league_season[season_column].astype(str),
    league_season["bonus_ft_percentage"],
    marker="o",
    color="darkorange",
    linewidth=2,
)
plt.title("Bonus Free-Throw Accuracy by NBA Season")
plt.xlabel("Season")
plt.ylabel("Bonus free-throw percentage")
plt.xticks(rotation=60, ha="right")
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(
    CHART_FOLDER / "league_bonus_accuracy_by_season.png",
    dpi=200,
)
plt.close()


# ---------------------------------------------------------
# PRINT RESULTS
# ---------------------------------------------------------

first_season = league_season.iloc[0]
last_season = league_season.iloc[-1]

attempt_change = (
    last_season["average_bonus_fta"]
    - first_season["average_bonus_fta"]
)

accuracy_change = (
    last_season["bonus_ft_percentage"]
    - first_season["bonus_ft_percentage"]
)

print()
print("=" * 65)
print("TEAM TREND ANALYSIS COMPLETE")
print("=" * 65)

print(f"Seasons analyzed: {len(league_season)}")
print(
    f"First season: {first_season[season_column]}"
)
print(
    f"Most recent season: {last_season[season_column]}"
)

print()
print("LEAGUE-WIDE CHANGE:")
print(
    f"Bonus FTA changed from "
    f"{first_season['average_bonus_fta']:.2f} to "
    f"{last_season['average_bonus_fta']:.2f}"
)
print(
    f"Overall bonus FTA change: {attempt_change:+.2f}"
)

print(
    f"Bonus accuracy changed from "
    f"{first_season['bonus_ft_percentage']:.2f}% to "
    f"{last_season['bonus_ft_percentage']:.2f}%"
)
print(
    f"Overall accuracy change: {accuracy_change:+.2f} percentage points"
)

print()
print("FILES CREATED:")
print(
    "results/team_trends/team_by_season_summary.csv"
)
print(
    "results/team_trends/league_season_trends.csv"
)
print(
    "results/team_trends/team_changes_first5_vs_last5.csv"
)
print(
    "results/charts/team_trends/"
)