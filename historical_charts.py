from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# --------------------------------------------------
# FILE LOCATIONS
# --------------------------------------------------
DATA_FILE = Path("results/historical_bonus_team_games.csv")
CHART_FOLDER = Path("results/charts/historical")
CHART_FOLDER.mkdir(parents=True, exist_ok=True)

SUMMARY_FILE = Path("results/final_historical_findings.txt")
SEASON_RESULTS_FILE = Path(
    "results/final_historical_season_results.csv"
)


# --------------------------------------------------
# LOAD AND PREPARE DATA
# --------------------------------------------------
print("Loading the 30-season historical dataset...")

data = pd.read_csv(DATA_FILE, low_memory=False)

numeric_columns = [
    "win",
    "point_difference",
    "periods_first_to_bonus",
    "opponent_periods_first_to_bonus",
    "first_bonus_difference",
    "bonus_fta",
    "opponent_bonus_fta",
    "bonus_fta_difference"
]

for column in numeric_columns:
    data[column] = pd.to_numeric(
        data[column],
        errors="coerce"
    )

data = data.dropna(
    subset=[
        "season",
        "win",
        "first_bonus_difference",
        "bonus_fta_difference"
    ]
).copy()

data["won"] = data["win"].astype(int)

data["first_bonus_category"] = np.select(
    [
        data["first_bonus_difference"] > 0,
        data["first_bonus_difference"] < 0
    ],
    [
        "Reached bonus first more often",
        "Reached bonus first less often"
    ],
    default="Tied"
)

data["bonus_fta_category"] = np.select(
    [
        data["bonus_fta_difference"] > 0,
        data["bonus_fta_difference"] < 0
    ],
    [
        "More bonus free throws",
        "Fewer bonus free throws"
    ],
    default="Tied"
)

data["combined_category"] = np.select(
    [
        (
            (data["first_bonus_difference"] > 0)
            & (data["bonus_fta_difference"] > 0)
        ),
        (
            (data["first_bonus_difference"] > 0)
            & (data["bonus_fta_difference"] <= 0)
        ),
        (
            (data["first_bonus_difference"] <= 0)
            & (data["bonus_fta_difference"] > 0)
        )
    ],
    [
        "First more often\nand more bonus FTs",
        "First more often\nwithout more bonus FTs",
        "More bonus FTs\nwithout first advantage"
    ],
    default="Neither advantage"
)


# --------------------------------------------------
# HELPER FUNCTIONS
# --------------------------------------------------
def win_rate(frame):
    if len(frame) == 0:
        return np.nan

    return frame["won"].mean() * 100


def sample_size(frame):
    return len(frame)


def add_bar_labels(axis, bars):
    for bar in bars:
        height = bar.get_height()

        if pd.notna(height):
            axis.text(
                bar.get_x() + bar.get_width() / 2,
                height + 0.7,
                f"{height:.1f}%",
                ha="center",
                va="bottom",
                fontsize=10,
                fontweight="bold"
            )


def save_chart(filename):
    plt.tight_layout()
    plt.savefig(
        CHART_FOLDER / filename,
        dpi=300,
        bbox_inches="tight"
    )
    plt.close()


# --------------------------------------------------
# OVERALL CALCULATIONS
# --------------------------------------------------
first_more = data[data["first_bonus_difference"] > 0]
first_fewer = data[data["first_bonus_difference"] < 0]
first_tied = data[data["first_bonus_difference"] == 0]

fta_more = data[data["bonus_fta_difference"] > 0]
fta_fewer = data[data["bonus_fta_difference"] < 0]
fta_tied = data[data["bonus_fta_difference"] == 0]

both_advantages = data[
    (data["first_bonus_difference"] > 0)
    & (data["bonus_fta_difference"] > 0)
]

both_disadvantages = data[
    (data["first_bonus_difference"] < 0)
    & (data["bonus_fta_difference"] < 0)
]

first_only = data[
    (data["first_bonus_difference"] > 0)
    & (data["bonus_fta_difference"] <= 0)
]

fta_only = data[
    (data["first_bonus_difference"] <= 0)
    & (data["bonus_fta_difference"] > 0)
]

first_more_rate = win_rate(first_more)
first_fewer_rate = win_rate(first_fewer)
first_tied_rate = win_rate(first_tied)

fta_more_rate = win_rate(fta_more)
fta_fewer_rate = win_rate(fta_fewer)
fta_tied_rate = win_rate(fta_tied)

both_rate = win_rate(both_advantages)
both_disadvantages_rate = win_rate(both_disadvantages)
first_only_rate = win_rate(first_only)
fta_only_rate = win_rate(fta_only)

first_bonus_effect = first_more_rate - first_fewer_rate
bonus_fta_effect = fta_more_rate - fta_fewer_rate
combined_effect = both_rate - both_disadvantages_rate

correlation = data[
    ["bonus_fta_difference", "point_difference"]
].corr().iloc[0, 1]


# --------------------------------------------------
# CHART 1: REACHING THE BONUS FIRST
# --------------------------------------------------
labels = [
    "First more often",
    "Tied",
    "First less often"
]

values = [
    first_more_rate,
    first_tied_rate,
    first_fewer_rate
]

colors = [
    "#1D428A",
    "#B0B7BC",
    "#C8102E"
]

plt.figure(figsize=(10, 6))
bars = plt.bar(labels, values, color=colors)

plt.axhline(
    50,
    color="black",
    linestyle="--",
    linewidth=1
)

plt.ylim(0, max(values) + 10)
plt.ylabel("Win percentage")
plt.title(
    "Win Percentage Based on Reaching the Bonus First\n"
    "NBA Regular Seasons, 1996-97 through 2025-26"
)

add_bar_labels(plt.gca(), bars)
save_chart("01_first_bonus_win_percentage.png")


# --------------------------------------------------
# CHART 2: BONUS FREE-THROW ADVANTAGE
# --------------------------------------------------
labels = [
    "More bonus FTs",
    "Tied",
    "Fewer bonus FTs"
]

values = [
    fta_more_rate,
    fta_tied_rate,
    fta_fewer_rate
]

plt.figure(figsize=(10, 6))
bars = plt.bar(labels, values, color=colors)

plt.axhline(
    50,
    color="black",
    linestyle="--",
    linewidth=1
)

plt.ylim(0, max(values) + 10)
plt.ylabel("Win percentage")
plt.title(
    "Win Percentage Based on Bonus Free-Throw Advantage\n"
    "NBA Regular Seasons, 1996-97 through 2025-26"
)

add_bar_labels(plt.gca(), bars)
save_chart("02_bonus_fta_win_percentage.png")


# --------------------------------------------------
# CHART 3: COMBINED EFFECT
# --------------------------------------------------
combined_order = [
    "First more often\nand more bonus FTs",
    "First more often\nwithout more bonus FTs",
    "More bonus FTs\nwithout first advantage",
    "Neither advantage"
]

combined_summary = (
    data.groupby("combined_category")
    .agg(
        team_game_rows=("gameId", "count"),
        wins=("won", "sum")
    )
    .reindex(combined_order)
    .reset_index()
)

combined_summary["win_percentage"] = (
    combined_summary["wins"]
    / combined_summary["team_game_rows"]
    * 100
)

plt.figure(figsize=(12, 7))

bars = plt.bar(
    combined_summary["combined_category"],
    combined_summary["win_percentage"],
    color=[
        "#17408B",
        "#4F81BD",
        "#FDB927",
        "#C8102E"
    ]
)

plt.axhline(
    50,
    color="black",
    linestyle="--",
    linewidth=1
)

plt.ylabel("Win percentage")
plt.title(
    "Combined Effect of Bonus Timing and Bonus Free Throws\n"
    "NBA Regular Seasons, 1996-97 through 2025-26"
)

plt.xticks(rotation=8)
plt.ylim(
    0,
    combined_summary["win_percentage"].max() + 10
)

add_bar_labels(plt.gca(), bars)
save_chart("03_combined_bonus_effect.png")


# --------------------------------------------------
# SEASON-BY-SEASON CALCULATIONS
# --------------------------------------------------
season_rows = []

for season, season_data in data.groupby(
    "season",
    sort=False
):
    season_first_more = season_data[
        season_data["first_bonus_difference"] > 0
    ]

    season_first_fewer = season_data[
        season_data["first_bonus_difference"] < 0
    ]

    season_fta_more = season_data[
        season_data["bonus_fta_difference"] > 0
    ]

    season_fta_fewer = season_data[
        season_data["bonus_fta_difference"] < 0
    ]

    season_both = season_data[
        (season_data["first_bonus_difference"] > 0)
        & (season_data["bonus_fta_difference"] > 0)
    ]

    season_neither = season_data[
        (season_data["first_bonus_difference"] < 0)
        & (season_data["bonus_fta_difference"] < 0)
    ]

    season_rows.append({
        "season": season,
        "team_game_rows": len(season_data),
        "first_more_win_percentage":
            win_rate(season_first_more),
        "first_fewer_win_percentage":
            win_rate(season_first_fewer),
        "first_bonus_win_gap":
            win_rate(season_first_more)
            - win_rate(season_first_fewer),
        "more_bonus_fta_win_percentage":
            win_rate(season_fta_more),
        "fewer_bonus_fta_win_percentage":
            win_rate(season_fta_fewer),
        "bonus_fta_win_gap":
            win_rate(season_fta_more)
            - win_rate(season_fta_fewer),
        "both_advantages_win_percentage":
            win_rate(season_both),
        "both_disadvantages_win_percentage":
            win_rate(season_neither),
        "combined_win_gap":
            win_rate(season_both)
            - win_rate(season_neither)
    })

season_results = pd.DataFrame(season_rows)

season_results["start_year"] = (
    season_results["season"]
    .astype(str)
    .str[:4]
    .astype(int)
)

season_results = season_results.sort_values(
    "start_year"
).reset_index(drop=True)

season_results.to_csv(
    SEASON_RESULTS_FILE,
    index=False
)


# --------------------------------------------------
# CHART 4: WIN PERCENTAGE OVER TIME
# --------------------------------------------------
x = np.arange(len(season_results))

plt.figure(figsize=(15, 8))

plt.plot(
    x,
    season_results[
        "first_more_win_percentage"
    ],
    marker="o",
    linewidth=2,
    label="Reached bonus first more often"
)

plt.plot(
    x,
    season_results[
        "more_bonus_fta_win_percentage"
    ],
    marker="o",
    linewidth=2,
    label="Shot more bonus free throws"
)

plt.plot(
    x,
    season_results[
        "both_advantages_win_percentage"
    ],
    marker="o",
    linewidth=2.5,
    label="Had both advantages"
)

plt.axhline(
    50,
    color="black",
    linestyle="--",
    linewidth=1
)

plt.xticks(
    x,
    season_results["season"],
    rotation=65
)

plt.ylabel("Win percentage")
plt.xlabel("Season")
plt.title(
    "How the Bonus Advantage Has Shifted Over 30 Seasons"
)
plt.legend()
plt.grid(axis="y", alpha=0.25)

save_chart("04_bonus_advantage_over_time.png")


# --------------------------------------------------
# CHART 5: WIN-PERCENTAGE GAPS OVER TIME
# --------------------------------------------------
plt.figure(figsize=(15, 8))

plt.plot(
    x,
    season_results["first_bonus_win_gap"],
    marker="o",
    linewidth=2,
    label="First-to-bonus win gap"
)

plt.plot(
    x,
    season_results["bonus_fta_win_gap"],
    marker="o",
    linewidth=2,
    label="Bonus-FTA win gap"
)

plt.plot(
    x,
    season_results["combined_win_gap"],
    marker="o",
    linewidth=2.5,
    label="Combined win gap"
)

plt.axhline(
    0,
    color="black",
    linestyle="--",
    linewidth=1
)

plt.xticks(
    x,
    season_results["season"],
    rotation=65
)

plt.ylabel("Win-percentage-point advantage")
plt.xlabel("Season")
plt.title(
    "Change in the Bonus-Related Winning Advantage"
)
plt.legend()
plt.grid(axis="y", alpha=0.25)

save_chart("05_bonus_win_gap_over_time.png")


# --------------------------------------------------
# CHART 6: BONUS FTA DIFFERENCE AND SCORE MARGIN
# --------------------------------------------------
plot_data = data[
    [
        "bonus_fta_difference",
        "point_difference"
    ]
].dropna()

if len(plot_data) > 10000:
    plot_data = plot_data.sample(
        10000,
        random_state=42
    )

x_scatter = plot_data["bonus_fta_difference"]
y_scatter = plot_data["point_difference"]

slope, intercept = np.polyfit(
    x_scatter,
    y_scatter,
    1
)

line_x = np.linspace(
    x_scatter.min(),
    x_scatter.max(),
    100
)

line_y = slope * line_x + intercept

plt.figure(figsize=(11, 7))

plt.scatter(
    x_scatter,
    y_scatter,
    alpha=0.15,
    s=16,
    color="#1D428A"
)

plt.plot(
    line_x,
    line_y,
    color="#C8102E",
    linewidth=3
)

plt.axhline(0, color="black", linewidth=0.8)
plt.axvline(0, color="black", linewidth=0.8)

plt.xlabel(
    "Bonus free-throw difference"
)
plt.ylabel(
    "Point difference"
)
plt.title(
    "Bonus Free-Throw Advantage and Final Score Margin\n"
    f"Correlation: {correlation:.3f}"
)

save_chart("06_bonus_fta_and_score_margin.png")


# --------------------------------------------------
# CREATE WRITTEN FINDINGS
# --------------------------------------------------
earliest = season_results.iloc[0]
latest = season_results.iloc[-1]

findings = f"""
FINAL HISTORICAL NBA BONUS ANALYSIS
===================================

DATASET
-------
Seasons analyzed: {data['season'].nunique():,}
Games analyzed: {data['gameId'].nunique():,}
Team-game rows: {len(data):,}
First season: {season_results.iloc[0]['season']}
Most recent season: {season_results.iloc[-1]['season']}

QUESTION 1: DOES REACHING THE BONUS FIRST MATTER?
-------------------------------------------------
Win percentage when a team reached the bonus first
in more periods: {first_more_rate:.2f}%

Win percentage when it reached the bonus first in
fewer periods: {first_fewer_rate:.2f}%

Difference: {first_bonus_effect:.2f} percentage points

QUESTION 2: DOES SHOOTING MORE BONUS FREE THROWS MATTER?
--------------------------------------------------------
Win percentage with more bonus free throws:
{fta_more_rate:.2f}%

Win percentage with fewer bonus free throws:
{fta_fewer_rate:.2f}%

Difference: {bonus_fta_effect:.2f} percentage points

QUESTION 3: WHAT HAPPENS WHEN A TEAM HAS BOTH ADVANTAGES?
---------------------------------------------------------
Win percentage with both advantages:
{both_rate:.2f}%

Win percentage with both disadvantages:
{both_disadvantages_rate:.2f}%

Difference: {combined_effect:.2f} percentage points

OTHER RESULTS
-------------
Win percentage with first-to-bonus advantage only:
{first_only_rate:.2f}%

Win percentage with bonus-FTA advantage only:
{fta_only_rate:.2f}%

Correlation between bonus-FTA difference and final
point difference: {correlation:.3f}

CHANGE OVER TIME
----------------
First-to-bonus win gap in {earliest['season']}:
{earliest['first_bonus_win_gap']:.2f} percentage points

First-to-bonus win gap in {latest['season']}:
{latest['first_bonus_win_gap']:.2f} percentage points

Bonus-FTA win gap in {earliest['season']}:
{earliest['bonus_fta_win_gap']:.2f} percentage points

Bonus-FTA win gap in {latest['season']}:
{latest['bonus_fta_win_gap']:.2f} percentage points

IMPORTANT INTERPRETATION
------------------------
These results show an association, not definite causation.
Teams may receive additional late-game free throws because
opponents intentionally foul while trailing. Team quality,
game location, score situation and other factors may also
affect the relationship.
""".strip()

SUMMARY_FILE.write_text(
    findings,
    encoding="utf-8"
)


# --------------------------------------------------
# DISPLAY RESULTS
# --------------------------------------------------
print("\nFINAL HISTORICAL ANALYSIS COMPLETE")
print(f"Seasons analyzed: {data['season'].nunique():,}")
print(f"Games analyzed: {data['gameId'].nunique():,}")

print("\nMAIN RESULTS:")
print(
    "First-to-bonus win-rate difference: "
    f"{first_bonus_effect:.2f} percentage points"
)
print(
    "Bonus-FTA win-rate difference: "
    f"{bonus_fta_effect:.2f} percentage points"
)
print(
    "Combined win-rate difference: "
    f"{combined_effect:.2f} percentage points"
)
print(
    "Bonus-FTA and score-margin correlation: "
    f"{correlation:.3f}"
)

print("\nFILES CREATED:")
print(SUMMARY_FILE)
print(SEASON_RESULTS_FILE)
print(CHART_FOLDER)