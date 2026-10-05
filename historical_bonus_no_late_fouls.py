import re
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

OUTPUT_FILE = Path(
    "results/historical_bonus_without_late_fouls.csv"
)

SEASON_FILE = Path(
    "results/historical_without_late_fouls_by_season.csv"
)

CHART_FOLDER = Path(
    "results/charts/no_late_fouls"
)

CHART_FOLDER.mkdir(
    parents=True,
    exist_ok=True
)


# --------------------------------------------------
# HELPER FUNCTIONS
# --------------------------------------------------
def clock_to_seconds(clock):
    text = str(clock)

    match = re.search(
        r"PT(?:(\d+)M)?([\d.]+)S",
        text
    )

    if not match:
        return None

    minutes = int(match.group(1) or 0)
    seconds = float(match.group(2))

    return minutes * 60 + seconds


def official_team_foul_number(description):
    match = re.search(
        r"\.T(\d+)",
        str(description)
    )

    if match:
        return int(match.group(1))

    return None


def win_rate(frame):
    if len(frame) == 0:
        return np.nan

    return frame["win"].mean() * 100


# Foul types that count toward the team-foul total.
TEAM_FOUL_TYPES = {
    "Shooting",
    "Personal",
    "Loose Ball",
    "Personal Take",
    "Transition Take",
    "Away From Play",
    "Clear Path",
    "Flagrant Type 1",
    "Flagrant Type 2"
}


# --------------------------------------------------
# LOAD EXISTING RESULTS
# --------------------------------------------------
print("Loading the completed historical results...")

team_games = pd.read_csv(
    TEAM_GAME_FILE,
    dtype={"gameId": str},
    low_memory=False
)

team_games["gameId"] = (
    team_games["gameId"]
    .astype(str)
    .str.zfill(10)
)

team_games["win"] = pd.to_numeric(
    team_games["win"],
    errors="coerce"
)

team_games[
    "bonus_fta_before_final_2"
] = 0


# --------------------------------------------------
# PROCESS EACH SEASON
# --------------------------------------------------
seasons = sorted(
    team_games["season"]
    .dropna()
    .astype(str)
    .unique()
)

total_seasons = len(seasons)

for season_number, season in enumerate(
    seasons,
    start=1
):
    season_tag = season.replace("-", "_")

    pbp_file = Path(
        f"data/play_by_play_{season_tag}.csv"
    )

    print(
        f"\nSeason {season_number}/{total_seasons}: "
        f"{season}"
    )

    if not pbp_file.exists():
        print(f"Missing file: {pbp_file}")
        continue

    plays = pd.read_csv(
        pbp_file,
        dtype={"gameId": str},
        low_memory=False
    )

    plays["gameId"] = (
        plays["gameId"]
        .astype(str)
        .str.zfill(10)
    )

    plays["period"] = pd.to_numeric(
        plays["period"],
        errors="coerce"
    )

    plays["actionNumber"] = pd.to_numeric(
        plays["actionNumber"],
        errors="coerce"
    )

    plays = plays.sort_values(
        [
            "gameId",
            "period",
            "actionNumber"
        ]
    )

    season_team_games = team_games[
        team_games["season"].astype(str)
        == season
    ]

    game_teams = (
        season_team_games
        .groupby("gameId")["team"]
        .apply(
            lambda values:
            list(dict.fromkeys(
                values.dropna().astype(str)
            ))
        )
        .to_dict()
    )

    season_counts = {}

    grouped_plays = plays.groupby(
        "gameId",
        sort=False
    )

    total_games = plays["gameId"].nunique()

    for game_number, (
        game_id,
        game_plays
    ) in enumerate(
        grouped_plays,
        start=1
    ):
        if (
            game_number % 200 == 0
            or game_number == 1
        ):
            print(
                f"Processing game "
                f"{game_number}/{total_games}..."
            )

        teams = game_teams.get(
            game_id,
            []
        )

        if len(teams) != 2:
            continue

        bonus_active = {}
        counted_team_fouls = {}
        final_two_minute_fouls = {}

        for team in teams:
            season_counts[
                (game_id, team)
            ] = 0

        for row in game_plays.itertuples(
            index=False
        ):
            period_value = getattr(
                row,
                "period",
                None
            )

            if pd.isna(period_value):
                continue

            period = int(period_value)

            team = str(
                getattr(
                    row,
                    "teamTricode",
                    ""
                )
            )

            action_type = str(
                getattr(
                    row,
                    "actionType",
                    ""
                )
            )

            subtype = str(
                getattr(
                    row,
                    "subType",
                    ""
                )
            )

            description = str(
                getattr(
                    row,
                    "description",
                    ""
                )
            )

            clock = getattr(
                row,
                "clock",
                ""
            )

            seconds_remaining = (
                clock_to_seconds(clock)
            )

            for current_team in teams:
                key = (
                    period,
                    current_team
                )

                if key not in bonus_active:
                    bonus_active[key] = False
                    counted_team_fouls[key] = 0
                    final_two_minute_fouls[key] = 0

            # --------------------------------------
            # PROCESS FOULS AND ACTIVATE THE BONUS
            # --------------------------------------
            if (
                action_type == "Foul"
                and subtype in TEAM_FOUL_TYPES
                and team in teams
            ):
                foul_key = (
                    period,
                    team
                )

                counted_team_fouls[
                    foul_key
                ] += 1

                official_number = (
                    official_team_foul_number(
                        description
                    )
                )

                if official_number is not None:
                    foul_total = official_number
                else:
                    foul_total = (
                        counted_team_fouls[
                            foul_key
                        ]
                    )

                if (
                    seconds_remaining is not None
                    and seconds_remaining <= 120
                ):
                    final_two_minute_fouls[
                        foul_key
                    ] += 1

                late_foul_total = (
                    final_two_minute_fouls[
                        foul_key
                    ]
                )

                if period <= 4:
                    normal_bonus = (
                        foul_total >= 5
                    )
                else:
                    normal_bonus = (
                        foul_total >= 4
                    )

                final_two_bonus = (
                    late_foul_total >= 2
                )

                opponent = (
                    teams[1]
                    if team == teams[0]
                    else teams[0]
                )

                if (
                    normal_bonus
                    or final_two_bonus
                ):
                    bonus_active[
                        (period, opponent)
                    ] = True

            # --------------------------------------
            # COUNT BONUS FREE THROWS
            # EXCLUDE FINAL 2:00 OF 4TH AND OVERTIME
            # --------------------------------------
            if (
                action_type == "Free Throw"
                and team in teams
            ):
                special_free_throw = any(
                    label in subtype
                    for label in [
                        "Technical",
                        "Flagrant",
                        "Clear Path"
                    ]
                )

                if special_free_throw:
                    continue

                currently_in_bonus = (
                    bonus_active.get(
                        (period, team),
                        False
                    )
                )

                late_game_window = (
                    period >= 4
                    and seconds_remaining
                    is not None
                    and seconds_remaining <= 120
                )

                if (
                    currently_in_bonus
                    and not late_game_window
                ):
                    season_counts[
                        (game_id, team)
                    ] += 1

    # Add the new count to the correct team-game row.
    season_mask = (
        team_games["season"].astype(str)
        == season
    )

    team_games.loc[
        season_mask,
        "bonus_fta_before_final_2"
    ] = [
        season_counts.get(
            (game_id, team),
            0
        )
        for game_id, team in zip(
            team_games.loc[
                season_mask,
                "gameId"
            ],
            team_games.loc[
                season_mask,
                "team"
            ].astype(str)
        )
    ]

    print(f"Finished {season}")


# --------------------------------------------------
# CALCULATE OPPONENT VALUES AND DIFFERENCES
# --------------------------------------------------
opponent_lookup = (
    team_games[
        [
            "gameId",
            "team",
            "bonus_fta_before_final_2"
        ]
    ]
    .rename(
        columns={
            "team": "opponent",
            "bonus_fta_before_final_2":
                "opponent_bonus_fta_before_final_2"
        }
    )
)

team_games = team_games.merge(
    opponent_lookup,
    on=[
        "gameId",
        "opponent"
    ],
    how="left"
)

team_games[
    "opponent_bonus_fta_before_final_2"
] = (
    team_games[
        "opponent_bonus_fta_before_final_2"
    ]
    .fillna(0)
)

team_games[
    "bonus_fta_difference_before_final_2"
] = (
    team_games[
        "bonus_fta_before_final_2"
    ]
    - team_games[
        "opponent_bonus_fta_before_final_2"
    ]
)

team_games.to_csv(
    OUTPUT_FILE,
    index=False
)


# --------------------------------------------------
# OVERALL RESULTS
# --------------------------------------------------
more_early = team_games[
    team_games[
        "bonus_fta_difference_before_final_2"
    ] > 0
]

fewer_early = team_games[
    team_games[
        "bonus_fta_difference_before_final_2"
    ] < 0
]

tied_early = team_games[
    team_games[
        "bonus_fta_difference_before_final_2"
    ] == 0
]

early_more_rate = win_rate(more_early)
early_fewer_rate = win_rate(fewer_early)
early_tied_rate = win_rate(tied_early)

early_gap = (
    early_more_rate
    - early_fewer_rate
)

original_more = team_games[
    team_games["bonus_fta_difference"] > 0
]

original_fewer = team_games[
    team_games["bonus_fta_difference"] < 0
]

original_gap = (
    win_rate(original_more)
    - win_rate(original_fewer)
)


# --------------------------------------------------
# SEASON-BY-SEASON RESULTS
# --------------------------------------------------
season_rows = []

for season, rows in team_games.groupby(
    "season"
):
    more = rows[
        rows[
            "bonus_fta_difference_before_final_2"
        ] > 0
    ]

    fewer = rows[
        rows[
            "bonus_fta_difference_before_final_2"
        ] < 0
    ]

    tied = rows[
        rows[
            "bonus_fta_difference_before_final_2"
        ] == 0
    ]

    season_rows.append({
        "season": season,
        "more_bonus_fta_before_final_2_win_percentage":
            win_rate(more),
        "fewer_bonus_fta_before_final_2_win_percentage":
            win_rate(fewer),
        "tied_bonus_fta_before_final_2_win_percentage":
            win_rate(tied),
        "win_percentage_gap":
            win_rate(more) - win_rate(fewer)
    })

season_results = pd.DataFrame(
    season_rows
)

season_results["start_year"] = (
    season_results["season"]
    .astype(str)
    .str[:4]
    .astype(int)
)

season_results = season_results.sort_values(
    "start_year"
)

season_results.to_csv(
    SEASON_FILE,
    index=False
)


# --------------------------------------------------
# CHART 1: OVERALL RESULTS WITHOUT LATE FOULS
# --------------------------------------------------
labels = [
    "More bonus FTs",
    "Tied",
    "Fewer bonus FTs"
]

values = [
    early_more_rate,
    early_tied_rate,
    early_fewer_rate
]

colors = [
    "#1D428A",
    "#B0B7BC",
    "#C8102E"
]

plt.figure(figsize=(10, 6))

bars = plt.bar(
    labels,
    values,
    color=colors
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
        height + 0.6,
        f"{height:.1f}%",
        ha="center",
        fontweight="bold"
    )

plt.ylabel("Win percentage")
plt.title(
    "Bonus Free Throws and Winning\n"
    "Excluding the Final Two Minutes"
)

plt.ylim(
    0,
    max(values) + 10
)

plt.tight_layout()

plt.savefig(
    CHART_FOLDER
    / "01_without_late_fouls.png",
    dpi=300
)

plt.close()


# --------------------------------------------------
# CHART 2: ORIGINAL VS ADJUSTED RESULT
# --------------------------------------------------
plt.figure(figsize=(9, 6))

comparison_labels = [
    "Original analysis",
    "Final 2:00 excluded"
]

comparison_values = [
    original_gap,
    early_gap
]

bars = plt.bar(
    comparison_labels,
    comparison_values,
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
        f"{height:.1f} points",
        ha="center",
        fontweight="bold"
    )

plt.ylabel(
    "Win-percentage-point advantage"
)

plt.title(
    "Bonus-FTA Winning Advantage\n"
    "Before and After Removing Late Fouls"
)

plt.ylim(
    0,
    max(comparison_values) + 5
)

plt.tight_layout()

plt.savefig(
    CHART_FOLDER
    / "02_original_vs_adjusted.png",
    dpi=300
)

plt.close()


# --------------------------------------------------
# CHART 3: ADJUSTED TREND OVER TIME
# --------------------------------------------------
x = np.arange(
    len(season_results)
)

plt.figure(figsize=(15, 7))

plt.plot(
    x,
    season_results[
        "win_percentage_gap"
    ],
    marker="o",
    linewidth=2.5,
    color="#1D428A"
)

plt.axhline(
    0,
    color="black",
    linestyle="--"
)

plt.xticks(
    x,
    season_results["season"],
    rotation=65
)

plt.ylabel(
    "Win-percentage-point advantage"
)

plt.xlabel("Season")

plt.title(
    "Bonus-FTA Winning Advantage by Season\n"
    "Excluding the Final Two Minutes"
)

plt.grid(
    axis="y",
    alpha=0.25
)

plt.tight_layout()

plt.savefig(
    CHART_FOLDER
    / "03_adjusted_trend.png",
    dpi=300
)

plt.close()


# --------------------------------------------------
# DISPLAY RESULTS
# --------------------------------------------------
print("\nNO-LATE-FOUL ANALYSIS COMPLETE")

print(
    "\nOriginal bonus-FTA win-rate gap: "
    f"{original_gap:.2f} percentage points"
)

print(
    "Adjusted gap after excluding "
    "the final two minutes: "
    f"{early_gap:.2f} percentage points"
)

print(
    "\nWin rate with more adjusted bonus FTs: "
    f"{early_more_rate:.2f}%"
)

print(
    "Win rate with fewer adjusted bonus FTs: "
    f"{early_fewer_rate:.2f}%"
)

print("\nFiles created:")
print(OUTPUT_FILE)
print(SEASON_FILE)
print(CHART_FOLDER)