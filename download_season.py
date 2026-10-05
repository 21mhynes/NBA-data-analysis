from pathlib import Path
import time

import pandas as pd
from nba_api.stats.endpoints import leaguegamefinder, playbyplayv3


# -----------------------------
# SETTINGS
# -----------------------------
SEASON = "2025-26"
WAIT_BETWEEN_GAMES = 1.5

DATA_FOLDER = Path("data")
GAME_FOLDER = DATA_FOLDER / "play_by_play_2025_26"

DATA_FOLDER.mkdir(exist_ok=True)
GAME_FOLDER.mkdir(exist_ok=True)

GAME_LIST_FILE = DATA_FOLDER / "games_2025_26.csv"
COMBINED_FILE = DATA_FOLDER / "play_by_play_2025_26.csv"
FAILED_FILE = DATA_FOLDER / "failed_games_2025_26.csv"


# -----------------------------
# GET THE REGULAR-SEASON GAMES
# -----------------------------
print(f"Finding all NBA games from the {SEASON} regular season...")

game_finder = leaguegamefinder.LeagueGameFinder(
    league_id_nullable="00",
    season_nullable=SEASON,
    season_type_nullable="Regular Season",
    timeout=60
)

team_game_rows = game_finder.get_data_frames()[0]
team_game_rows.to_csv(GAME_LIST_FILE, index=False)

# Every game appears twice—once for each team—so remove duplicates.
game_ids = (
    team_game_rows["GAME_ID"]
    .astype(str)
    .str.zfill(10)
    .drop_duplicates()
    .sort_values()
    .tolist()
)

print(f"Found {len(game_ids)} games.")
print(f"Game list saved to {GAME_LIST_FILE}")


# -----------------------------
# DOWNLOAD EACH GAME
# -----------------------------
failed_games = []

for number, game_id in enumerate(game_ids, start=1):
    game_file = GAME_FOLDER / f"{game_id}.csv"

    # Skip games that were already successfully downloaded.
    if game_file.exists() and game_file.stat().st_size > 0:
        print(f"[{number}/{len(game_ids)}] Already saved: {game_id}")
        continue

    print(f"[{number}/{len(game_ids)}] Downloading {game_id}...")

    success = False

    for attempt in range(1, 4):
        try:
            response = playbyplayv3.PlayByPlayV3(
                game_id=game_id,
                timeout=60
            )

            play_by_play = response.get_data_frames()[0]

            # These use assignment so existing columns are safely replaced.
            play_by_play["gameId"] = game_id
            play_by_play["season"] = SEASON

            play_by_play.to_csv(game_file, index=False)

            print(f"    Saved {len(play_by_play)} plays.")
            success = True
            break

        except Exception as error:
            print(f"    Attempt {attempt} failed: {error}")

            if attempt < 3:
                print("    Waiting 10 seconds before trying again...")
                time.sleep(10)

    if not success:
        failed_games.append(game_id)
        print(f"    Could not download game {game_id}.")

    time.sleep(WAIT_BETWEEN_GAMES)


# -----------------------------
# SAVE A LIST OF FAILED GAMES
# -----------------------------
pd.DataFrame({"gameId": failed_games}).to_csv(
    FAILED_FILE,
    index=False
)


# -----------------------------
# COMBINE ALL DOWNLOADED GAMES
# -----------------------------
print("\nCombining downloaded games into one dataset...")

game_files = sorted(GAME_FOLDER.glob("*.csv"))
dataframes = []

for game_file in game_files:
    try:
        game_data = pd.read_csv(
            game_file,
            dtype={"gameId": str}
        )
        dataframes.append(game_data)

    except Exception as error:
        print(f"Could not read {game_file.name}: {error}")

if dataframes:
    complete_play_by_play = pd.concat(
        dataframes,
        ignore_index=True
    )

    complete_play_by_play.to_csv(
        COMBINED_FILE,
        index=False
    )

    print("\nDOWNLOAD COMPLETE")
    print(f"Games downloaded: {len(game_files)}")
    print(f"Play-by-play rows: {len(complete_play_by_play):,}")
    print(f"Combined dataset: {COMBINED_FILE}")
    print(f"Failed games: {len(failed_games)}")

else:
    print("No game data was downloaded.")