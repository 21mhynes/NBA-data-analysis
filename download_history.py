from pathlib import Path
import random
import time

import pandas as pd
from nba_api.stats.endpoints import leaguegamelog, playbyplayv3


DATA_FOLDER = Path("data")
DATA_FOLDER.mkdir(exist_ok=True)

# Thirty seasons: 1996-97 through 2025-26
SEASONS = [f"{year}-{str(year + 1)[-2:]}" for year in range(1996, 2026)]

MAX_RETRIES = 5
WAIT_BETWEEN_GAMES = 0.75


def season_tag(season):
    return season.replace("-", "_")


def download_game(game_id, season):
    """Download one game, retrying temporary failures."""

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            frames = playbyplayv3.PlayByPlayV3(
                game_id=game_id,
                timeout=60,
            ).get_data_frames()

            if not frames or frames[0].empty:
                raise ValueError("No play-by-play rows returned")

            game_data = frames[0].copy()
            game_data["season"] = season

            return game_data

        except Exception as error:
            print(
                f"Attempt {attempt}/{MAX_RETRIES} failed "
                f"for game {game_id}: {error}"
            )

            if attempt < MAX_RETRIES:
                wait_time = 5 * attempt + random.uniform(1, 3)
                print(f"Waiting {wait_time:.1f} seconds...")
                time.sleep(wait_time)

    return None


def download_season(season):
    tag = season_tag(season)

    season_folder = DATA_FOLDER / f"play_by_play_{tag}"
    season_folder.mkdir(exist_ok=True)

    combined_file = DATA_FOLDER / f"play_by_play_{tag}.csv"
    games_file = DATA_FOLDER / f"games_{tag}.csv"
    failures_file = DATA_FOLDER / f"failures_{tag}.csv"

    # Do not redownload a completed season
    if combined_file.exists():
        print(f"\n{season} is already complete. Skipping it.")
        return

    print("\n" + "=" * 60)
    print(f"STARTING SEASON {season}")
    print("=" * 60)

    # Get every regular-season game
    try:
        game_log = leaguegamelog.LeagueGameLog(
            season=season,
            season_type_all_star="Regular Season",
            timeout=60,
        ).get_data_frames()[0]

    except Exception as error:
        print(f"Could not get the {season} game list: {error}")
        print("Run the program again later to retry this season.")
        return

    if game_log.empty:
        print(f"No regular-season games were found for {season}.")
        return

    game_log["GAME_ID"] = (
        game_log["GAME_ID"]
        .astype(str)
        .str.replace(".0", "", regex=False)
        .str.zfill(10)
    )

    unique_games = (
        game_log
        .drop_duplicates(subset=["GAME_ID"])
        .copy()
    )

    unique_games.to_csv(games_file, index=False)

    game_ids = unique_games["GAME_ID"].tolist()
        # Exclude the canceled 2013 Celtics-Pacers game
    game_ids = [
        game_id
        for game_id in game_ids
        if game_id != "0021201214"
    ]
    total_games = len(game_ids)

    print(f"Games found: {total_games:,}")

    failures = []

    for number, game_id in enumerate(game_ids, start=1):
        game_file = season_folder / f"{game_id}.csv"

        # Skip games successfully downloaded during an earlier run
        if game_file.exists() and game_file.stat().st_size > 100:
            print(
                f"[{number}/{total_games}] "
                f"{game_id} already downloaded"
            )
            continue

        print(f"[{number}/{total_games}] Downloading {game_id}...")

        game_data = download_game(game_id, season)

        if game_data is None:
            failures.append(
                {
                    "season": season,
                    "gameId": game_id,
                    "reason": "Failed after all retries",
                }
            )
            print(f"FAILED: {game_id}")
        else:
            temporary_file = season_folder / f"{game_id}.temporary.csv"
            game_data.to_csv(temporary_file, index=False)
            temporary_file.replace(game_file)

            print(f"Saved {len(game_data):,} rows")

        time.sleep(WAIT_BETWEEN_GAMES)

    if failures:
        pd.DataFrame(failures).to_csv(failures_file, index=False)

        print(f"\n{season} still has {len(failures)} failed games.")
        print("Run the program again later. It will retry only those games.")
        return

    # Confirm every game exists before creating the combined season file
    downloaded_files = [
        season_folder / f"{game_id}.csv"
        for game_id in game_ids
        if (season_folder / f"{game_id}.csv").exists()
    ]

    if len(downloaded_files) != total_games:
        missing_count = total_games - len(downloaded_files)

        print(f"\n{season} is missing {missing_count} games.")
        print("Run the program again to continue.")
        return

    print(f"\nCombining all {season} games...")

    season_frames = []

    for game_file in downloaded_files:
        season_frames.append(
            pd.read_csv(game_file, low_memory=False)
        )

    combined_data = pd.concat(season_frames, ignore_index=True)
    combined_data.to_csv(combined_file, index=False)

    if failures_file.exists():
        failures_file.unlink()

    print(f"\nSEASON {season} COMPLETE")
    print(f"Games: {total_games:,}")
    print(f"Play-by-play rows: {len(combined_data):,}")
    print(f"Saved here: {combined_file}")


print("HISTORICAL NBA DOWNLOAD")
print("Seasons: 1996-97 through 2025-26")
print("Completed seasons and games will be skipped automatically.")
print("You can stop and restart this program without losing progress.")

for season in SEASONS:
    download_season(season)

print("\n" + "=" * 60)
print("HISTORICAL DOWNLOAD FINISHED")
print("=" * 60)