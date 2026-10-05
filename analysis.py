from nba_api.stats.endpoints import leaguegamefinder
from nba_api.stats.endpoints import playbyplayv3

# Find games from the 2025–26 NBA regular season
games = leaguegamefinder.LeagueGameFinder(
    season_nullable="2025-26",
    season_type_nullable="Regular Season",
    timeout=30
).get_data_frames()[0]

# Select one real game
game_id = games.iloc[0]["GAME_ID"]
print("Game ID:", game_id)

# Download that game's play-by-play data
play_by_play = playbyplayv3.PlayByPlayV3(
    game_id=game_id,
    timeout=30
).get_data_frames()[0]

print(play_by_play.head())

# Keep only foul events
fouls = play_by_play[
    play_by_play["actionType"].str.contains("foul", case=False, na=False)
]

print("\nFOULS:")
print(
    fouls[
        ["period", "clock", "teamTricode", "playerName", "description"]
    ].to_string(index=False)
)