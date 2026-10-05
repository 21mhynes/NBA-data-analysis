from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


TEAM_GAMES_FILE = "results/bonus_team_games_2025_26.csv"
TEAM_SUMMARY_FILE = "results/bonus_team_summary_2025_26.csv"
OUTCOME_FILE = "results/bonus_outcome_summary_2025_26.csv"

CHART_FOLDER = Path("results/charts")
CHART_FOLDER.mkdir(parents=True, exist_ok=True)


print("Loading analysis results...")

team_games = pd.read_csv(TEAM_GAMES_FILE)
team_summary = pd.read_csv(TEAM_SUMMARY_FILE)
outcomes = pd.read_csv(OUTCOME_FILE)


# -----------------------------
# CHART 1: WIN RATE
# -----------------------------
order = ["Fewer", "Tied", "More"]

outcomes["first_bonus_result"] = pd.Categorical(
    outcomes["first_bonus_result"],
    categories=order,
    ordered=True
)

outcomes = outcomes.sort_values("first_bonus_result")
outcomes["win_percentage_display"] = (
    outcomes["win_percentage"] * 100
)

plt.figure(figsize=(8, 5))

bars = plt.bar(
    outcomes["first_bonus_result"],
    outcomes["win_percentage_display"],
    color=["#d9534f", "#8c8c8c", "#2e86de"]
)

plt.axhline(
    50,
    color="black",
    linestyle="--",
    linewidth=1,
    label="50% win rate"
)

plt.ylim(40, 60)
plt.xlabel("Quarters reaching the bonus first")
plt.ylabel("Win percentage")
plt.title("Win Rate Based on Reaching the Bonus First")

for bar, value in zip(
    bars,
    outcomes["win_percentage_display"]
):
    plt.text(
        bar.get_x() + bar.get_width() / 2,
        value + 0.4,
        f"{value:.1f}%",
        ha="center"
    )

plt.legend()
plt.tight_layout()
plt.savefig(
    CHART_FOLDER / "win_rate_by_bonus.png",
    dpi=300
)
plt.close()


# -----------------------------
# CHART 2: BONUS FTA BY TEAM
# -----------------------------
team_summary = team_summary.sort_values(
    "average_bonus_fta"
)

plt.figure(figsize=(10, 10))

plt.barh(
    team_summary["team"],
    team_summary["average_bonus_fta"],
    color="#2e86de"
)

plt.xlabel("Average free-throw attempts while in the bonus")
plt.ylabel("Team")
plt.title("Average Bonus-Period Free Throws by Team")
plt.tight_layout()

plt.savefig(
    CHART_FOLDER / "team_bonus_free_throws.png",
    dpi=300
)
plt.close()


# -----------------------------
# CHART 3: FTA DIFFERENCE VS MARGIN
# -----------------------------
plt.figure(figsize=(9, 6))

plt.scatter(
    team_games["bonus_fta_difference"],
    team_games["point_difference"],
    alpha=0.25,
    color="#6c5ce7",
    edgecolors="none"
)

plt.axhline(
    0,
    color="black",
    linewidth=1
)

plt.axvline(
    0,
    color="black",
    linewidth=1
)

plt.xlabel("Bonus free-throw attempt difference")
plt.ylabel("Final point difference")
plt.title(
    "Bonus Free-Throw Advantage and Game Outcome"
)

plt.tight_layout()

plt.savefig(
    CHART_FOLDER / "bonus_fta_vs_point_margin.png",
    dpi=300
)
plt.close()


print("\nCHARTS COMPLETE")
print("Created:")
print("results/charts/win_rate_by_bonus.png")
print("results/charts/team_bonus_free_throws.png")
print("results/charts/bonus_fta_vs_point_margin.png")