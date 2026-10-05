from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# ---------------------------------------------------------
# FILE LOCATIONS
# ---------------------------------------------------------

INPUT_FILE = Path(
    "results/team_trends/team_changes_first5_vs_last5.csv"
)

OUTPUT_FOLDER = Path(
    "results/charts/final_relationships"
)

OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------

if not INPUT_FILE.exists():
    raise SystemExit(
        "Could not find the team-change results file."
    )

data = pd.read_csv(INPUT_FILE)

team_column = data.columns[0]

print("Creating final relationship charts...")


# ---------------------------------------------------------
# CHART FUNCTION
# ---------------------------------------------------------

def create_scatterplot(
    x_column,
    x_label,
    title,
    filename,
    color,
):
    chart_data = data[
        [team_column, x_column, "win_percentage_change"]
    ].dropna()

    x = chart_data[x_column]
    y = chart_data["win_percentage_change"]

    correlation = x.corr(y)

    plt.figure(figsize=(12, 8))

    plt.scatter(
        x,
        y,
        color=color,
        edgecolor="black",
        s=90,
        alpha=0.8,
    )

    if len(chart_data) >= 2:
        slope, intercept = np.polyfit(x, y, 1)

        line_x = np.linspace(x.min(), x.max(), 100)
        line_y = slope * line_x + intercept

        plt.plot(
            line_x,
            line_y,
            color="black",
            linestyle="--",
            linewidth=2,
            label=f"Trend line (correlation = {correlation:.3f})",
        )

    for _, row in chart_data.iterrows():
        plt.annotate(
            str(row[team_column]),
            (
                row[x_column],
                row["win_percentage_change"],
            ),
            xytext=(5, 5),
            textcoords="offset points",
            fontsize=8,
        )

    plt.axhline(
        0,
        color="gray",
        linewidth=1,
        alpha=0.7,
    )

    plt.axvline(
        0,
        color="gray",
        linewidth=1,
        alpha=0.7,
    )

    plt.title(title)
    plt.xlabel(x_label)
    plt.ylabel(
        "Change in winning percentage\n"
        "(percentage points)"
    )

    plt.grid(alpha=0.25)
    plt.legend()
    plt.tight_layout()

    plt.savefig(
        OUTPUT_FOLDER / filename,
        dpi=200,
    )

    plt.close()

    return correlation


# ---------------------------------------------------------
# CREATE ATTEMPT RELATIONSHIP CHART
# ---------------------------------------------------------

attempt_correlation = create_scatterplot(
    x_column="bonus_fta_change",
    x_label=(
        "Change in average bonus free-throw attempts "
        "per team-game"
    ),
    title=(
        "Change in Bonus Attempts vs. "
        "Change in Winning Percentage"
    ),
    filename="bonus_attempt_change_vs_winning.png",
    color="royalblue",
)


# ---------------------------------------------------------
# CREATE ACCURACY RELATIONSHIP CHART
# ---------------------------------------------------------

accuracy_correlation = create_scatterplot(
    x_column="bonus_ft_percentage_change",
    x_label=(
        "Change in bonus free-throw accuracy "
        "(percentage points)"
    ),
    title=(
        "Change in Bonus Accuracy vs. "
        "Change in Winning Percentage"
    ),
    filename="bonus_accuracy_change_vs_winning.png",
    color="darkorange",
)


# ---------------------------------------------------------
# PRINT RESULTS
# ---------------------------------------------------------

print()
print("=" * 65)
print("FINAL RELATIONSHIP CHARTS CREATED")
print("=" * 65)

print(
    f"Bonus-attempt correlation: "
    f"{attempt_correlation:.3f}"
)

print(
    f"Bonus-accuracy correlation: "
    f"{accuracy_correlation:.3f}"
)

print()
print("Charts saved in:")
print("results/charts/final_relationships/")