import re
from pathlib import Path

import pandas as pd


# -----------------------------
# FILE LOCATIONS
# -----------------------------
PLAY_BY_PLAY_FILE = "data/play_by_play_2025_26.csv"
GAME_FILE = "data/games_2025_26.csv"

OUTPUT_FOLDER = Path("results")
OUTPUT_FOLDER.mkdir(exist_ok=True)

TEAM_GAME_FILE = OUTPUT_FOLDER / "bonus_team_games_2025_26.csv"
ENTRY_FILE = OUTPUT_FOLDER / "bonus_entries_2025_26.csv"
TEAM_SUMMARY_FILE = OUTPUT_FOLDER / "bonus_team_summary_2025_26.csv"
OUTCOME_FILE = OUTPUT_FOLDER / "bonus_outcome_summary_2025_26.csv"


# -----------------------------
# HELPER FUNCTIONS
# -----------------------------
def clock_to_seconds(clock):
    """
    Converts an NBA clock such as PT08M17.00S into seconds remaining.
    """
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
    """
    Extracts the official team-foul number from descriptions
    such as (P2.T4).
    """
    match = re.search(r"\.T(\d+)", str(description))

    if match:
        return int(match.group(1))

    return None


def other_team(teams, team):
    """
    Returns the opponent of the specified team.
    """
    opponents = [value for value in teams if value != team]

    if opponents:
        return opponents[0]

    return None


# -----------------------------
# LOAD DATA
# -----------------------------
print("Loading the full season dataset...")

plays = pd.read_csv(
    PLAY_BY_PLAY_FILE,
    dtype={"gameId": str},
    low_memory=False
)

games = pd.read_csv(
    GAME_FILE,
    dtype={"GAME_ID": str},
    low_memory=False
)

plays["gameId"] = plays["gameId"].str.zfill(10)
games["GAME_ID"] = games["GAME_ID"].str.zfill(10)

plays["actionNumber"] = pd.to_numeric(
    plays["actionNumber"],
    errors="coerce"
)

plays["period"] = pd.to_numeric(
    plays["period"],
    errors="coerce"
)

games["PTS"] = pd.to_numeric(
    games["PTS"],
    errors="coerce"
)

print(f"Play-by-play rows loaded: {len(plays):,}")
print(f"Games found: {plays['gameId'].nunique():,}")


# -----------------------------
# CREATE GAME INFORMATION
# -----------------------------
game_information = {}

for game_id, game_rows in games.groupby("GAME_ID"):
    game_rows = game_rows.drop_duplicates(
        subset=["TEAM_ABBREVIATION"]
    )

    teams = (
        game_rows["TEAM_ABBREVIATION"]
        .dropna()
        .astype(str)
        .tolist()
    )

    if len(teams) != 2:
        continue

    team_details = {}

    for _, row in game_rows.iterrows():
        team = str(row["TEAM_ABBREVIATION"])

        team_details[team] = {
            "win": 1 if str(row["WL"]).upper() == "W" else 0,
            "points": row["PTS"]
        }

    game_information[game_id] = {
        "teams": teams,
        "details": team_details
    }


# These foul types count toward the NBA team-foul total.
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


team_game_results = []
bonus_entry_results = []


# -----------------------------
# ANALYZE EVERY GAME
# -----------------------------
grouped_games = plays.groupby("gameId", sort=False)
total_games = plays["gameId"].nunique()

for game_number, (game_id, game_plays) in enumerate(
    grouped_games,
    start=1
):
    if game_number % 100 == 0 or game_number == 1:
        print(f"Analyzing game {game_number}/{total_games}...")

    if game_id not in game_information:
        print(f"Missing game information for {game_id}")
        continue

    info = game_information[game_id]
    teams = info["teams"]

    game_plays = game_plays.sort_values(
        ["period", "actionNumber"]
    )

    # Statistics for each team during this game.
    team_stats = {}

    for team in teams:
        team_stats[team] = {
            "periods_reached_bonus": 0,
            "periods_first_to_bonus": 0,
            "bonus_fta": 0,
            "bonus_ftm": 0,
            "total_standard_fta": 0,
            "total_standard_ftm": 0
        }

    # Tracks the bonus separately for each period.
    bonus_active = {}
    first_bonus_team = {}

    # Counts team fouls and fouls during the final two minutes.
    counted_team_fouls = {}
    final_two_minute_fouls = {}

    for _, play in game_plays.iterrows():
        period_value = play["period"]

        if pd.isna(period_value):
            continue

        period = int(period_value)
        action_type = str(play.get("actionType", ""))
        subtype = str(play.get("subType", ""))
        team = str(play.get("teamTricode", ""))
        description = str(play.get("description", ""))
        seconds_remaining = clock_to_seconds(
            play.get("clock", "")
        )

        # Set up tracking when a period is first encountered.
        if period not in first_bonus_team:
            first_bonus_team[period] = None

            for current_team in teams:
                bonus_active[(period, current_team)] = False
                counted_team_fouls[(period, current_team)] = 0
                final_two_minute_fouls[(period, current_team)] = 0

        # -------------------------
        # PROCESS FOULS
        # -------------------------
        if (
            action_type == "Foul"
            and subtype in TEAM_FOUL_TYPES
            and team in teams
        ):
            counted_team_fouls[(period, team)] += 1

            official_number = official_team_foul_number(
                description
            )

            if official_number is not None:
                foul_total = official_number
            else:
                foul_total = counted_team_fouls[
                    (period, team)
                ]

            # Special NBA final-two-minute rule.
            if (
                seconds_remaining is not None
                and seconds_remaining <= 120
            ):
                final_two_minute_fouls[
                    (period, team)
                ] += 1

            late_foul_total = final_two_minute_fouls[
                (period, team)
            ]

            # Regulation quarters: penalty after four team fouls.
            # Overtime: penalty after three team fouls.
            if period <= 4:
                normal_bonus_reached = foul_total >= 5
            else:
                normal_bonus_reached = foul_total >= 4

            final_two_bonus_reached = late_foul_total >= 2

            opponent = other_team(teams, team)

            if opponent is None:
                continue

            if (
                normal_bonus_reached
                or final_two_bonus_reached
            ):
                key = (period, opponent)

                if not bonus_active[key]:
                    bonus_active[key] = True

                    team_stats[opponent][
                        "periods_reached_bonus"
                    ] += 1

                    was_first = (
                        first_bonus_team[period] is None
                    )

                    if was_first:
                        first_bonus_team[period] = opponent

                        team_stats[opponent][
                            "periods_first_to_bonus"
                        ] += 1

                    bonus_entry_results.append({
                        "gameId": game_id,
                        "period": period,
                        "team_entering_bonus": opponent,
                        "opponent_committing_fouls": team,
                        "clock": play.get("clock", ""),
                        "seconds_remaining": seconds_remaining,
                        "official_team_foul_number": foul_total,
                        "late_fouls": late_foul_total,
                        "first_to_bonus_in_period": int(
                            was_first
                        )
                    })

        # -------------------------
        # PROCESS FREE THROWS
        # -------------------------
        if action_type == "Free Throw" and team in teams:
            # Exclude technical, flagrant and clear-path attempts.
            special_free_throw = any(
                label in subtype
                for label in [
                    "Technical",
                    "Flagrant",
                    "Clear Path"
                ]
            )

            if not special_free_throw:
                team_stats[team][
                    "total_standard_fta"
                ] += 1

                made = "MISS" not in str(play.get("description", "")).upper()

                if made:
                    team_stats[team][
                        "total_standard_ftm"
                    ] += 1

                if bonus_active.get(
                    (period, team),
                    False
                ):
                    team_stats[team][
                        "bonus_fta"
                    ] += 1

                    if made:
                        team_stats[team][
                            "bonus_ftm"
                        ] += 1

    # -----------------------------
    # SAVE TWO TEAM ROWS PER GAME
    # -----------------------------
    for team in teams:
        opponent = other_team(teams, team)

        if opponent is None:
            continue

        details = info["details"].get(team, {})
        opponent_details = info["details"].get(
            opponent,
            {}
        )

        team_points = details.get("points")
        opponent_points = opponent_details.get("points")

        if pd.notna(team_points) and pd.notna(opponent_points):
            point_difference = team_points - opponent_points
        else:
            point_difference = None

        stats = team_stats[team]
        opponent_stats = team_stats[opponent]

        bonus_fta_difference = (
            stats["bonus_fta"]
            - opponent_stats["bonus_fta"]
        )

        first_bonus_difference = (
            stats["periods_first_to_bonus"]
            - opponent_stats["periods_first_to_bonus"]
        )

        if first_bonus_difference > 0:
            first_bonus_result = "More"
        elif first_bonus_difference < 0:
            first_bonus_result = "Fewer"
        else:
            first_bonus_result = "Tied"

        bonus_percentage = (
            stats["bonus_ftm"] / stats["bonus_fta"]
            if stats["bonus_fta"] > 0
            else None
        )

        team_game_results.append({
            "gameId": game_id,
            "season": "2025-26",
            "team": team,
            "opponent": opponent,
            "win": details.get("win"),
            "team_points": team_points,
            "opponent_points": opponent_points,
            "point_difference": point_difference,
            "periods_reached_bonus":
                stats["periods_reached_bonus"],
            "periods_first_to_bonus":
                stats["periods_first_to_bonus"],
            "opponent_periods_first_to_bonus":
                opponent_stats["periods_first_to_bonus"],
            "first_bonus_difference":
                first_bonus_difference,
            "first_bonus_result":
                first_bonus_result,
            "bonus_fta": stats["bonus_fta"],
            "bonus_ftm": stats["bonus_ftm"],
            "bonus_ft_percentage": bonus_percentage,
            "opponent_bonus_fta":
                opponent_stats["bonus_fta"],
            "bonus_fta_difference":
                bonus_fta_difference,
            "total_standard_fta":
                stats["total_standard_fta"],
            "total_standard_ftm":
                stats["total_standard_ftm"]
        })


# -----------------------------
# CREATE RESULT TABLES
# -----------------------------
team_game_data = pd.DataFrame(team_game_results)
bonus_entry_data = pd.DataFrame(bonus_entry_results)

team_game_data.to_csv(
    TEAM_GAME_FILE,
    index=False
)

bonus_entry_data.to_csv(
    ENTRY_FILE,
    index=False
)


# Team-level season summary.
team_summary = (
    team_game_data
    .groupby("team")
    .agg(
        games=("gameId", "count"),
        wins=("win", "sum"),
        average_first_bonus_periods=(
            "periods_first_to_bonus",
            "mean"
        ),
        average_bonus_fta=("bonus_fta", "mean"),
        average_bonus_fta_difference=(
            "bonus_fta_difference",
            "mean"
        ),
        average_point_difference=(
            "point_difference",
            "mean"
        )
    )
    .reset_index()
)

team_summary["win_percentage"] = (
    team_summary["wins"] / team_summary["games"]
)

team_summary = team_summary.sort_values(
    "average_bonus_fta",
    ascending=False
)

team_summary.to_csv(
    TEAM_SUMMARY_FILE,
    index=False
)


# Compare winning based on reaching the bonus first.
outcome_summary = (
    team_game_data
    .groupby("first_bonus_result")
    .agg(
        team_game_rows=("gameId", "count"),
        wins=("win", "sum"),
        average_point_difference=(
            "point_difference",
            "mean"
        ),
        average_bonus_fta_difference=(
            "bonus_fta_difference",
            "mean"
        )
    )
    .reset_index()
)

outcome_summary["win_percentage"] = (
    outcome_summary["wins"]
    / outcome_summary["team_game_rows"]
)

outcome_summary.to_csv(
    OUTCOME_FILE,
    index=False
)


# Correlation between bonus free-throw advantage and score margin.
correlation = team_game_data[
    [
        "bonus_fta_difference",
        "point_difference"
    ]
].corr().iloc[0, 1]


# -----------------------------
# DISPLAY RESULTS
# -----------------------------
print("\nANALYSIS COMPLETE")
print(f"Team-game rows: {len(team_game_data):,}")
print(f"Bonus entries recorded: {len(bonus_entry_data):,}")

print("\nWINNING AND REACHING THE BONUS FIRST:")
print(
    outcome_summary.to_string(
        index=False
    )
)

print(
    "\nCorrelation between bonus-FTA difference "
    f"and point difference: {correlation:.3f}"
)

print("\nFiles created:")
print(TEAM_GAME_FILE)
print(ENTRY_FILE)
print(TEAM_SUMMARY_FILE)
print(OUTCOME_FILE)
