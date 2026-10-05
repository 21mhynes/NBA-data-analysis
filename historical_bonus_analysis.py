from pathlib import Path
import time

import pandas as pd
from nba_api.stats.endpoints import leaguegamelog


DATA_FOLDER = Path("data")
HISTORY_FOLDER = Path("results/history")
HISTORY_FOLDER.mkdir(parents=True, exist_ok=True)

BASE_ANALYSIS_FILE = Path("bonus_analysis.py")

SEASONS = [
    f"{year}-{str(year + 1)[-2:]}"
    for year in range(1996, 2026)
]


def season_tag(season):
    return season.replace("-", "_")


def game_file_is_complete(file_path):
    if not file_path.exists():
        return False

    try:
        games = pd.read_csv(
            file_path,
            dtype={"GAME_ID": str},
            low_memory=False,
        )
    except Exception:
        return False

    required = {
        "GAME_ID",
        "TEAM_ABBREVIATION",
        "WL",
        "PTS",
    }

    if not required.issubset(games.columns):
        return False

    games["GAME_ID"] = games["GAME_ID"].astype(str).str.zfill(10)

    team_counts = (
        games.groupby("GAME_ID")["TEAM_ABBREVIATION"]
        .nunique()
    )

    return len(team_counts) > 0 and team_counts.ge(2).all()


def get_complete_game_file(season):
    tag = season_tag(season)

    original_file = DATA_FOLDER / f"games_{tag}.csv"
    repaired_file = DATA_FOLDER / f"games_full_{tag}.csv"

    if game_file_is_complete(original_file):
        print(f"{season}: existing game results are complete")
        return original_file

    if game_file_is_complete(repaired_file):
        print(f"{season}: repaired game results already saved")
        return repaired_file

    print(f"{season}: downloading the complete two-team game table...")

    last_error = None

    for attempt in range(1, 6):
        try:
            game_log = leaguegamelog.LeagueGameLog(
                season=season,
                season_type_all_star="Regular Season",
                timeout=60,
            ).get_data_frames()[0]

            if game_log.empty:
                raise ValueError("The NBA returned an empty game table.")

            game_log["GAME_ID"] = (
                game_log["GAME_ID"]
                .astype(str)
                .str.replace(".0", "", regex=False)
                .str.zfill(10)
            )

            game_log.to_csv(repaired_file, index=False)

            if not game_file_is_complete(repaired_file):
                raise ValueError(
                    "The downloaded table does not contain "
                    "two teams for every game."
                )

            print(
                f"{season}: saved complete game results to "
                f"{repaired_file}"
            )

            time.sleep(1)
            return repaired_file

        except Exception as error:
            last_error = error
            print(
                f"{season}: attempt {attempt}/5 failed: {error}"
            )

            if attempt < 5:
                time.sleep(attempt * 5)

    raise RuntimeError(
        f"Could not retrieve complete game results for "
        f"{season}: {last_error}"
    )


def run_season_analysis(season, game_file):
    tag = season_tag(season)

    play_file = DATA_FOLDER / f"play_by_play_{tag}.csv"
    season_output = HISTORY_FOLDER / tag
    season_output.mkdir(parents=True, exist_ok=True)

    team_game_file = (
        season_output / f"bonus_team_games_{tag}.csv"
    )

    if team_game_file.exists() and team_game_file.stat().st_size > 100:
        print(f"{season}: analysis already complete — skipping")
        return

    if not play_file.exists():
        raise FileNotFoundError(
            f"Missing play-by-play file: {play_file}"
        )

    print("\n" + "=" * 65)
    print(f"ANALYZING {season}")
    print("=" * 65)

    source = BASE_ANALYSIS_FILE.read_text(encoding="utf-8")

    source = source.replace(
        'PLAY_BY_PLAY_FILE = "data/play_by_play_2025_26.csv"',
        f'PLAY_BY_PLAY_FILE = "{play_file}"',
    )

    source = source.replace(
        'GAME_FILE = "data/games_2025_26.csv"',
        f'GAME_FILE = "{game_file}"',
    )

    source = source.replace(
        'OUTPUT_FOLDER = Path("results")',
        f'OUTPUT_FOLDER = Path("{season_output}")',
    )

    source = source.replace(
        "_2025_26.csv",
        f"_{tag}.csv",
    )

    source = source.replace(
        '"season": "2025-26"',
        f'"season": "{season}"',
    )

    analysis_globals = {
        "__name__": "__main__",
        "__file__": str(BASE_ANALYSIS_FILE),
    }

    exec(
        compile(
            source,
            f"bonus_analysis_{tag}.py",
            "exec",
        ),
        analysis_globals,
    )


def combine_results():
    print("\n" + "=" * 65)
    print("COMBINING ALL HISTORICAL RESULTS")
    print("=" * 65)

    team_game_frames = []
    entry_frames = []

    missing_seasons = []

    for season in SEASONS:
        tag = season_tag(season)
        season_folder = HISTORY_FOLDER / tag

        team_file = (
            season_folder / f"bonus_team_games_{tag}.csv"
        )

        entry_file = (
            season_folder / f"bonus_entries_{tag}.csv"
        )

        if not team_file.exists() or not entry_file.exists():
            missing_seasons.append(season)
            continue

        team_data = pd.read_csv(
            team_file,
            dtype={"gameId": str},
            low_memory=False,
        )

        entry_data = pd.read_csv(
            entry_file,
            dtype={"gameId": str},
            low_memory=False,
        )

        if "season" not in entry_data.columns:
            entry_data.insert(1, "season", season)

        team_game_frames.append(team_data)
        entry_frames.append(entry_data)

    if missing_seasons:
        raise RuntimeError(
            "These seasons have not been analyzed: "
            + ", ".join(missing_seasons)
        )

    historical_team_games = pd.concat(
        team_game_frames,
        ignore_index=True,
    )

    historical_entries = pd.concat(
        entry_frames,
        ignore_index=True,
    )

    historical_team_games.to_csv(
        "results/historical_bonus_team_games.csv",
        index=False,
    )

    historical_entries.to_csv(
        "results/historical_bonus_entries.csv",
        index=False,
    )

    # One row per team and season
    team_season_summary = (
        historical_team_games
        .groupby(["season", "team"])
        .agg(
            games=("gameId", "count"),
            wins=("win", "sum"),
            average_first_bonus_periods=(
                "periods_first_to_bonus",
                "mean",
            ),
            average_bonus_fta=("bonus_fta", "mean"),
            average_bonus_fta_difference=(
                "bonus_fta_difference",
                "mean",
            ),
            average_point_difference=(
                "point_difference",
                "mean",
            ),
        )
        .reset_index()
    )

    team_season_summary["win_percentage"] = (
        team_season_summary["wins"]
        / team_season_summary["games"]
    )

    team_season_summary.to_csv(
        "results/historical_team_season_summary.csv",
        index=False,
    )

    # Win rates for More, Fewer, and Tied in each season
    season_outcome_summary = (
        historical_team_games
        .groupby(["season", "first_bonus_result"])
        .agg(
            team_game_rows=("gameId", "count"),
            wins=("win", "sum"),
            average_point_difference=(
                "point_difference",
                "mean",
            ),
            average_bonus_fta_difference=(
                "bonus_fta_difference",
                "mean",
            ),
        )
        .reset_index()
    )

    season_outcome_summary["win_percentage"] = (
        season_outcome_summary["wins"]
        / season_outcome_summary["team_game_rows"]
    )

    season_outcome_summary.to_csv(
        "results/historical_season_outcome_summary.csv",
        index=False,
    )

    # A compact table showing change over time
    win_rate_table = season_outcome_summary.pivot(
        index="season",
        columns="first_bonus_result",
        values="win_percentage",
    ).reset_index()

    for column in ["More", "Fewer", "Tied"]:
        if column not in win_rate_table.columns:
            win_rate_table[column] = pd.NA

    win_rate_table["first_bonus_win_advantage"] = (
        win_rate_table["More"] - win_rate_table["Fewer"]
    )

    season_basic = (
        historical_team_games
        .groupby("season")
        .agg(
            games=("gameId", "nunique"),
            average_bonus_fta=("bonus_fta", "mean"),
            average_bonus_fta_difference=(
                "bonus_fta_difference",
                "mean",
            ),
        )
        .reset_index()
    )

    correlations = (
        historical_team_games
        .groupby("season")
        .apply(
            lambda frame: frame[
                [
                    "bonus_fta_difference",
                    "point_difference",
                ]
            ].corr().iloc[0, 1],
            include_groups=False,
        )
        .reset_index(
            name="bonus_fta_point_margin_correlation"
        )
    )

    historical_season_summary = (
        season_basic
        .merge(win_rate_table, on="season", how="left")
        .merge(correlations, on="season", how="left")
        .rename(
            columns={
                "More": "win_rate_more_first_bonus_periods",
                "Fewer": "win_rate_fewer_first_bonus_periods",
                "Tied": "win_rate_tied_first_bonus_periods",
            }
        )
    )

    historical_season_summary.to_csv(
        "results/historical_season_summary.csv",
        index=False,
    )

    print("\nHISTORICAL ANALYSIS COMPLETE")
    print(
        f"Seasons analyzed: "
        f"{historical_team_games['season'].nunique()}"
    )
    print(
        f"Games analyzed: "
        f"{historical_team_games['gameId'].nunique():,}"
    )
    print(
        f"Team-game rows: "
        f"{len(historical_team_games):,}"
    )
    print(
        f"Bonus entries: "
        f"{len(historical_entries):,}"
    )

    print("\nMain files created:")
    print("results/historical_bonus_team_games.csv")
    print("results/historical_bonus_entries.csv")
    print("results/historical_team_season_summary.csv")
    print("results/historical_season_outcome_summary.csv")
    print("results/historical_season_summary.csv")


def main():
    if not BASE_ANALYSIS_FILE.exists():
        raise FileNotFoundError(
            "bonus_analysis.py must be in the main project folder."
        )

    print("NBA 30-SEASON BONUS ANALYSIS")
    print("Seasons: 1996-97 through 2025-26")
    print(
        "This uses the same bonus rules as "
        "bonus_analysis.py.\n"
    )

    for season in SEASONS:
        game_file = get_complete_game_file(season)
        run_season_analysis(season, game_file)

    combine_results()


if __name__ == "__main__":
    main()