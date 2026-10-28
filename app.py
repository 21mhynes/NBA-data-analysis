import logging
import math
import os

import pymysql
from dotenv import load_dotenv
from flask import Flask, abort, render_template

load_dotenv()
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

TEAM_INFO = {
    "ATL": {"name": "Atlanta Hawks", "logo_id": 1610612737, "source_codes": ["ATL"]},
    "BOS": {"name": "Boston Celtics", "logo_id": 1610612738, "source_codes": ["BOS"]},
    "BKN": {"name": "Brooklyn Nets", "logo_id": 1610612751, "source_codes": ["BKN","NJN"]},
    "CHA": {"name": "Charlotte Hornets", "logo_id": 1610612766, "source_codes": ["CHA","CHH"]},
    "CHI": {"name": "Chicago Bulls", "logo_id": 1610612741, "source_codes": ["CHI"]},
    "CLE": {"name": "Cleveland Cavaliers", "logo_id": 1610612739, "source_codes": ["CLE"]},
    "DAL": {"name": "Dallas Mavericks", "logo_id": 1610612742, "source_codes": ["DAL"]},
    "DEN": {"name": "Denver Nuggets", "logo_id": 1610612743, "source_codes": ["DEN"]},
    "DET": {"name": "Detroit Pistons", "logo_id": 1610612765, "source_codes": ["DET"]},
    "GSW": {"name": "Golden State Warriors", "logo_id": 1610612744, "source_codes": ["GSW"]},
    "HOU": {"name": "Houston Rockets", "logo_id": 1610612745, "source_codes": ["HOU"]},
    "IND": {"name": "Indiana Pacers", "logo_id": 1610612754, "source_codes": ["IND"]},
    "LAC": {"name": "LA Clippers", "logo_id": 1610612746, "source_codes": ["LAC"]},
    "LAL": {"name": "Los Angeles Lakers", "logo_id": 1610612747, "source_codes": ["LAL"]},
    "MEM": {"name": "Memphis Grizzlies", "logo_id": 1610612763, "source_codes": ["MEM","VAN"]},
    "MIA": {"name": "Miami Heat", "logo_id": 1610612748, "source_codes": ["MIA"]},
    "MIL": {"name": "Milwaukee Bucks", "logo_id": 1610612749, "source_codes": ["MIL"]},
    "MIN": {"name": "Minnesota Timberwolves", "logo_id": 1610612750, "source_codes": ["MIN"]},
    "NOP": {"name": "New Orleans Pelicans", "logo_id": 1610612740, "source_codes": ["NOP","NOH","NOK"]},
    "NYK": {"name": "New York Knicks", "logo_id": 1610612752, "source_codes": ["NYK"]},
    "OKC": {"name": "Oklahoma City Thunder", "logo_id": 1610612760, "source_codes": ["OKC","SEA"]},
    "ORL": {"name": "Orlando Magic", "logo_id": 1610612753, "source_codes": ["ORL"]},
    "PHI": {"name": "Philadelphia 76ers", "logo_id": 1610612755, "source_codes": ["PHI"]},
    "PHX": {"name": "Phoenix Suns", "logo_id": 1610612756, "source_codes": ["PHX"]},
    "POR": {"name": "Portland Trail Blazers", "logo_id": 1610612757, "source_codes": ["POR"]},
    "SAC": {"name": "Sacramento Kings", "logo_id": 1610612758, "source_codes": ["SAC"]},
    "SAS": {"name": "San Antonio Spurs", "logo_id": 1610612759, "source_codes": ["SAS"]},
    "TOR": {"name": "Toronto Raptors", "logo_id": 1610612761, "source_codes": ["TOR"]},
    "UTA": {"name": "Utah Jazz", "logo_id": 1610612762, "source_codes": ["UTA"]},
    "WAS": {"name": "Washington Wizards", "logo_id": 1610612764, "source_codes": ["WAS"]},
}
TEAM_NAMES = {code: info["name"] for code, info in TEAM_INFO.items()}
TEAM_DIRECTORY = [
    {"code": code, "name": info["name"], "logo_id": info["logo_id"]}
    for code, info in TEAM_INFO.items()
]


def get_connection():
    """Open a short-lived, TLS-verified connection to TiDB."""
    required = ("TIDB_HOST", "TIDB_USER", "TIDB_PASSWORD")
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        raise RuntimeError("Missing environment variables: " + ", ".join(missing))

    return pymysql.connect(
        host=os.environ["TIDB_HOST"],
        port=int(os.getenv("TIDB_PORT", "4000")),
        user=os.environ["TIDB_USER"],
        password=os.environ["TIDB_PASSWORD"],
        database=os.getenv("TIDB_DATABASE", "NBA_Project"),
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        connect_timeout=10,
        read_timeout=20,
        write_timeout=10,
        ssl_verify_cert=True,
        ssl_verify_identity=True,
    )


def read_rows(cursor, source_file, fields):
    """Read selected fields from one archived result CSV in TiDB."""
    # fields and source_file are constants in this app, never URL/form input.
    selected = ", ".join(
        f"JSON_UNQUOTE(JSON_EXTRACT(row_json, '$.{field}')) AS `{field}`"
        for field in fields
    )
    query = f"""
        SELECT {selected}
        FROM analysis_results_archive
        WHERE source_file = %s
        ORDER BY CAST(source_row AS UNSIGNED)
    """
    cursor.execute(query, (source_file,))
    return cursor.fetchall()


def archive_count(cursor, source_file):
    """Count rows for one prepared result file stored in the TiDB archive."""
    cursor.execute(
        "SELECT COUNT(*) AS row_count FROM analysis_results_archive WHERE source_file = %s",
        (source_file,),
    )
    return int(cursor.fetchone()["row_count"])


def as_float(value):
    if value is None or value == "":
        return None
    return float(value)


def comparison(cursor, source_file, difference_field, label):
    query = f"""
        SELECT
            ROUND(AVG(CASE WHEN bonus_diff > 0 THEN win_value END) * 100, 2)
                AS more_win_pct,
            ROUND(AVG(CASE WHEN bonus_diff < 0 THEN win_value END) * 100, 2)
                AS fewer_win_pct
        FROM (
            SELECT
                CAST(JSON_UNQUOTE(JSON_EXTRACT(row_json, '$.{difference_field}'))
                    AS DECIMAL(10,4)) AS bonus_diff,
                CAST(JSON_UNQUOTE(JSON_EXTRACT(row_json, '$.win'))
                    AS DECIMAL(10,4)) AS win_value
            FROM analysis_results_archive
            WHERE source_file = %s
        ) AS comparison_data
    """
    cursor.execute(query, (source_file,))
    row = cursor.fetchone()
    more = as_float(row["more_win_pct"])
    fewer = as_float(row["fewer_win_pct"])
    if more is None or fewer is None:
        raise RuntimeError(f"No usable rows found for {source_file}")
    return {
        "label": label,
        "more_pct": more,
        "fewer_pct": fewer,
        "gap": round(more - fewer, 2),
    }


def pearson(rows, x_field, y_field):
    pairs = [
        (as_float(row.get(x_field)), as_float(row.get(y_field)))
        for row in rows
    ]
    pairs = [(x, y) for x, y in pairs if x is not None and y is not None]
    if len(pairs) < 2:
        return None
    xs, ys = zip(*pairs)
    mean_x = sum(xs) / len(xs)
    mean_y = sum(ys) / len(ys)
    numerator = sum((x - mean_x) * (y - mean_y) for x, y in pairs)
    denominator = math.sqrt(
        sum((x - mean_x) ** 2 for x in xs)
        * sum((y - mean_y) ** 2 for y in ys)
    )
    return numerator / denominator if denominator else None


def team_name(code):
    return TEAM_NAMES.get(code, code)


def load_dashboard_data():
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            first_bonus_rows = read_rows(
                cursor,
                "results/quarter_bonus_analysis/first_in_game_summary.csv",
                ["games", "win_percentage"],
            )
            quarter_rows = read_rows(
                cursor,
                "results/quarter_bonus_analysis/first_to_bonus_by_quarter.csv",
                ["period_label", "games", "win_percentage"],
            )
            fourth_quarter_rows = read_rows(
                cursor,
                "results/quarter_bonus_analysis/fourth_quarter_sensitivity.csv",
                ["group", "games", "win_percentage"],
            )
            home_first_rows = read_rows(
                cursor,
                "results/home_accuracy_analysis/home_away_first_in_game.csv",
                ["location", "share_of_first_entries", "win_percentage"],
            )
            home_overall_rows = read_rows(
                cursor,
                "results/home_accuracy_analysis/home_away_bonus_summary.csv",
                ["location", "win_percentage"],
            )
            attempt_rows = read_rows(
                cursor,
                "results/home_accuracy_analysis/bonus_attempt_results.csv",
                ["attempt_result", "win_percentage"],
            )
            accuracy_rows = read_rows(
                cursor,
                "results/home_accuracy_analysis/bonus_accuracy_results.csv",
                ["accuracy_result", "win_percentage"],
            )
            season_rows = read_rows(
                cursor,
                "results/team_trends/league_season_trends.csv",
                ["season", "average_bonus_fta", "bonus_ft_percentage"],
            )
            team_rows = read_rows(
                cursor,
                "results/team_trends/team_changes_first5_vs_last5.csv",
                [
                    "team",
                    "bonus_fta_change",
                    "bonus_ft_percentage_change",
                    "win_percentage_change",
                ],
            )
            coverage_team_games = archive_count(
                cursor, "results/historical_bonus_team_games.csv"
            )
            coverage = {
                "seasons": len(season_rows),
                "games": coverage_team_games // 2,
                "team_games": coverage_team_games,
                "bonus_entries": archive_count(
                    cursor, "results/historical_bonus_entries.csv"
                ),
            }
            original = comparison(
                cursor,
                "results/historical_bonus_team_games.csv",
                "bonus_fta_difference",
                "All bonus attempts",
            )
            adjusted = comparison(
                cursor,
                "results/historical_bonus_without_late_fouls.csv",
                "bonus_fta_difference_before_final_2",
                "After excluding final 2:00 of Q4 and overtime",
            )
    finally:
        connection.close()

    if not first_bonus_rows or not season_rows:
        raise RuntimeError("The required summary rows were not found in TiDB.")

    first_bonus_pct = as_float(first_bonus_rows[0]["win_percentage"])
    first_bonus_games = int(float(first_bonus_rows[0]["games"]))
    quarters = [
        {
            "label": row["period_label"],
            "games": int(float(row["games"])),
            "win_pct": as_float(row["win_percentage"]),
        }
        for row in quarter_rows
    ]
    q4_timing = {
        row["group"]: {
            "games": int(float(row["games"])),
            "win_pct": as_float(row["win_percentage"]),
        }
        for row in fourth_quarter_rows
    }
    home_first = {
        row["location"]: {
            "share_pct": as_float(row["share_of_first_entries"]),
            "win_pct": as_float(row["win_percentage"]),
        }
        for row in home_first_rows
    }
    home_overall = {
        row["location"]: as_float(row["win_percentage"])
        for row in home_overall_rows
    }
    attempts = {
        row["attempt_result"]: as_float(row["win_percentage"])
        for row in attempt_rows
    }
    accuracy = {
        row["accuracy_result"]: as_float(row["win_percentage"])
        for row in accuracy_rows
    }

    seasons = [
        {
            "season": row["season"],
            "attempts": as_float(row["average_bonus_fta"]),
            "accuracy": as_float(row["bonus_ft_percentage"]),
        }
        for row in season_rows
    ]
    min_attempts = min(row["attempts"] for row in seasons)
    max_attempts = max(row["attempts"] for row in seasons)
    span = max_attempts - min_attempts or 1
    for row in seasons:
        row["bar_height"] = 18 + 82 * (row["attempts"] - min_attempts) / span

    teams = []
    for row in team_rows:
        attempt_change = as_float(row["bonus_fta_change"])
        accuracy_change = as_float(row["bonus_ft_percentage_change"])
        win_change = as_float(row["win_percentage_change"])
        if attempt_change is None:
            continue
        teams.append({
            "code": row["team"],
            "name": team_name(row["team"]),
            "attempt_change": attempt_change,
            "accuracy_change": accuracy_change,
            "win_change": win_change,
        })

    attempt_change_sorted = sorted(teams, key=lambda row: row["attempt_change"])
    accuracy_comparable = [row for row in teams if row["accuracy_change"] is not None]
    largest_accuracy_improvements = sorted(
        [row for row in accuracy_comparable if row["accuracy_change"] > 0],
        key=lambda row: row["accuracy_change"],
        reverse=True,
    )[:5]
    accuracy_declines = sorted(
        [row for row in accuracy_comparable if row["accuracy_change"] < 0],
        key=lambda row: row["accuracy_change"],
    )
    original_gap = original["gap"]
    gap_removed_pct = (
        (original_gap - adjusted["gap"]) / original_gap * 100
        if original_gap
        else 0
    )
    first_season, last_season = seasons[0], seasons[-1]
    season_span = f"{first_season['season']} through {last_season['season']}"
    attempts_change = last_season["attempts"] - first_season["attempts"]
    accuracy_change = last_season["accuracy"] - first_season["accuracy"]

    return {
        "coverage": coverage,
        "season_span": season_span,
        "first_bonus_pct": first_bonus_pct,
        "first_bonus_games": first_bonus_games,
        "quarters": quarters,
        "q4_timing": q4_timing,
        "home_first": home_first,
        "home_overall": home_overall,
        "attempts": attempts,
        "accuracy": accuracy,
        "seasons": seasons,
        "first_season": first_season,
        "last_season": last_season,
        "attempts_change": attempts_change,
        "attempts_decline_pct": abs(attempts_change / first_season["attempts"] * 100),
        "accuracy_change": accuracy_change,
        "team_count": len(teams),
        "least_attempt_declines": [
            {"name": row["name"], "change": row["attempt_change"]}
            for row in reversed(attempt_change_sorted[-3:])
        ],
        "largest_attempt_declines": [
            {"name": row["name"], "change": row["attempt_change"]}
            for row in attempt_change_sorted[:3]
        ],
        "largest_accuracy_improvements": [
            {"name": row["name"], "change": row["accuracy_change"]}
            for row in largest_accuracy_improvements
        ],
        "accuracy_declines": [
            {"name": row["name"], "change": row["accuracy_change"]}
            for row in accuracy_declines
        ],
        "attempt_corr": pearson(team_rows, "bonus_fta_change", "win_percentage_change"),
        "accuracy_corr": pearson(team_rows, "bonus_ft_percentage_change", "win_percentage_change"),
        "original": original,
        "adjusted": adjusted,
        "gap_removed_pct": gap_removed_pct,
    }


@app.route("/")
def home():
    data = None
    error = None
    try:
        data = load_dashboard_data()
    except Exception:
        logging.exception("Could not load the NBA findings from TiDB")
        error = (
            "The page could not load its findings from TiDB. Check the connection "
            "settings in your local .env file, then refresh."
        )

    coverage = data["coverage"] if data else {}
    return render_template(
        "index.html",
        data=data,
        error=error,
        seasons=data["season_span"] if data else "—",
        games=f"{coverage.get('games', '—'):,}" if data else "—",
        team_games=f"{coverage.get('team_games', '—'):,}" if data else "—",
        bonus_entries=f"{coverage.get('bonus_entries', '—'):,}" if data else "—",
        season_count=coverage.get("seasons", "—") if data else "—",
        team_directory=TEAM_DIRECTORY,
    )


def load_team_page_data(team_code):
    """Load one franchise's season summaries from the TiDB analysis archive."""
    team = TEAM_INFO[team_code]
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            rows = read_rows(
                cursor,
                "results/team_trends/team_by_season_summary.csv",
                [
                    "season", "team", "games", "wins", "average_bonus_fta",
                    "total_bonus_fta", "total_bonus_ftm", "win_percentage",
                    "bonus_ft_percentage",
                ],
            )
    finally:
        connection.close()

    seasons = []
    for row in rows:
        if row["team"] not in team["source_codes"]:
            continue
        seasons.append({
            "season": row["season"],
            "games": int(float(row["games"])),
            "wins": int(float(row["wins"])),
            "attempts": as_float(row["average_bonus_fta"]),
            "total_attempts": int(float(row["total_bonus_fta"])),
            "made": int(float(row["total_bonus_ftm"])),
            "win_pct": as_float(row["win_percentage"]),
            "accuracy": as_float(row["bonus_ft_percentage"]),
        })
    seasons.sort(key=lambda row: row["season"])
    if not seasons:
        raise RuntimeError(
            "No team-season rows were found in the TiDB analysis archive."
        )

    min_attempts = min(row["attempts"] for row in seasons)
    max_attempts = max(row["attempts"] for row in seasons)
    spread = max_attempts - min_attempts or 1
    for row in seasons:
        row["bar_height"] = 18 + 82 * (row["attempts"] - min_attempts) / spread

    first_five, last_five = seasons[:5], seasons[-5:]
    def mean(rows, field):
        return sum(row[field] for row in rows) / len(rows)

    first5 = {
        "attempts": mean(first_five, "attempts"),
        "accuracy": mean(first_five, "accuracy"),
        "win_pct": mean(first_five, "win_pct"),
    }
    last5 = {
        "attempts": mean(last_five, "attempts"),
        "accuracy": mean(last_five, "accuracy"),
        "win_pct": mean(last_five, "win_pct"),
    }
    return team, {
        "seasons": seasons,
        "latest": seasons[-1],
        "first_season": seasons[0]["season"],
        "last_season": seasons[-1]["season"],
        "season_count": len(seasons),
        "game_count": sum(row["games"] for row in seasons),
        "first5": first5,
        "last5": last5,
        "five_year_changes": {
            field: last5[field] - first5[field]
            for field in ("attempts", "accuracy", "win_pct")
        },
    }


@app.route("/team/<team_code>")
def team_page(team_code):
    team_code = team_code.upper()
    if team_code not in TEAM_INFO:
        abort(404)
    error = None
    team = TEAM_INFO[team_code]
    data = None
    try:
        team, data = load_team_page_data(team_code)
    except Exception:
        logging.exception("Could not load team findings from TiDB")
        error = (
            "This team page could not load its season results from TiDB. "
            "Check the database connection settings, then refresh."
        )
    return render_template(
        "team.html",
        team={**team, "code": team_code},
        data=data,
        error=error,
        team_directory=TEAM_DIRECTORY,
    )


if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG") == "1")
