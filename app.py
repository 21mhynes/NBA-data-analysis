import logging
import math
import os

import pymysql
from dotenv import load_dotenv
from flask import Flask, abort, render_template, request

load_dotenv()
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

TEAM_INFO = {
    "ATL": {"name": "Atlanta Hawks", "logo_id": 1610612737, "source_codes": ["ATL"], "primary_color": "#e13a3e", "secondary_color": "#c4d600"},
    "BOS": {"name": "Boston Celtics", "logo_id": 1610612738, "source_codes": ["BOS"], "primary_color": "#008348", "secondary_color": "#bb9753"},
    "BKN": {"name": "Brooklyn Nets", "logo_id": 1610612751, "source_codes": ["BKN","NJN"], "primary_color": "#061922", "secondary_color": "#ffffff"},
    "CHA": {"name": "Charlotte Hornets", "logo_id": 1610612766, "source_codes": ["CHA","CHH"], "primary_color": "#1d1160", "secondary_color": "#008ca8"},
    "CHI": {"name": "Chicago Bulls", "logo_id": 1610612741, "source_codes": ["CHI"], "primary_color": "#ce1141", "secondary_color": "#061922"},
    "CLE": {"name": "Cleveland Cavaliers", "logo_id": 1610612739, "source_codes": ["CLE"], "primary_color": "#860038", "secondary_color": "#fdbb30"},
    "DAL": {"name": "Dallas Mavericks", "logo_id": 1610612742, "source_codes": ["DAL"], "primary_color": "#007dc5", "secondary_color": "#c4ced3"},
    "DEN": {"name": "Denver Nuggets", "logo_id": 1610612743, "source_codes": ["DEN"], "primary_color": "#4d90cd", "secondary_color": "#fdb927"},
    "DET": {"name": "Detroit Pistons", "logo_id": 1610612765, "source_codes": ["DET"], "primary_color": "#ed174c", "secondary_color": "#006bb6"},
    "GSW": {"name": "Golden State Warriors", "logo_id": 1610612744, "source_codes": ["GSW"], "primary_color": "#fdb927", "secondary_color": "#006bb6"},
    "HOU": {"name": "Houston Rockets", "logo_id": 1610612745, "source_codes": ["HOU"], "primary_color": "#c8102e", "secondary_color": "#ffcd00"},
    "IND": {"name": "Indiana Pacers", "logo_id": 1610612754, "source_codes": ["IND"], "primary_color": "#ffc633", "secondary_color": "#00275d"},
    "LAC": {"name": "LA Clippers", "logo_id": 1610612746, "source_codes": ["LAC"], "primary_color": "#ed174c", "secondary_color": "#006bb6"},
    "LAL": {"name": "Los Angeles Lakers", "logo_id": 1610612747, "source_codes": ["LAL"], "primary_color": "#fdb927", "secondary_color": "#552582"},
    "MEM": {"name": "Memphis Grizzlies", "logo_id": 1610612763, "source_codes": ["MEM","VAN"], "primary_color": "#0f586c", "secondary_color": "#7399c6"},
    "MIA": {"name": "Miami Heat", "logo_id": 1610612748, "source_codes": ["MIA"], "primary_color": "#98002e", "secondary_color": "#f9a01b"},
    "MIL": {"name": "Milwaukee Bucks", "logo_id": 1610612749, "source_codes": ["MIL"], "primary_color": "#00471b", "secondary_color": "#f0ebd2"},
    "MIN": {"name": "Minnesota Timberwolves", "logo_id": 1610612750, "source_codes": ["MIN"], "primary_color": "#005083", "secondary_color": "#00a94f"},
    "NOP": {"name": "New Orleans Pelicans", "logo_id": 1610612740, "source_codes": ["NOP","NOH","NOK"], "primary_color": "#002b5c", "secondary_color": "#e31837"},
    "NYK": {"name": "New York Knicks", "logo_id": 1610612752, "source_codes": ["NYK"], "primary_color": "#006bb6", "secondary_color": "#f58426"},
    "OKC": {"name": "Oklahoma City Thunder", "logo_id": 1610612760, "source_codes": ["OKC","SEA"], "primary_color": "#007dc3", "secondary_color": "#f05133"},
    "ORL": {"name": "Orlando Magic", "logo_id": 1610612753, "source_codes": ["ORL"], "primary_color": "#007dc5", "secondary_color": "#c4ced3"},
    "PHI": {"name": "Philadelphia 76ers", "logo_id": 1610612755, "source_codes": ["PHI"], "primary_color": "#ed174c", "secondary_color": "#006bb6"},
    "PHX": {"name": "Phoenix Suns", "logo_id": 1610612756, "source_codes": ["PHX"], "primary_color": "#e56020", "secondary_color": "#1d1160"},
    "POR": {"name": "Portland Trail Blazers", "logo_id": 1610612757, "source_codes": ["POR"], "primary_color": "#e03a3e", "secondary_color": "#bac3c9"},
    "SAC": {"name": "Sacramento Kings", "logo_id": 1610612758, "source_codes": ["SAC"], "primary_color": "#5b2c81", "secondary_color": "#707272"},
    "SAS": {"name": "San Antonio Spurs", "logo_id": 1610612759, "source_codes": ["SAS"], "primary_color": "#bac3c9", "secondary_color": "#061922"},
    "TOR": {"name": "Toronto Raptors", "logo_id": 1610612761, "source_codes": ["TOR"], "primary_color": "#ce1141", "secondary_color": "#061922"},
    "UTA": {"name": "Utah Jazz", "logo_id": 1610612762, "source_codes": ["UTA"], "primary_color": "#002b5c", "secondary_color": "#f9a01b"},
    "WAS": {"name": "Washington Wizards", "logo_id": 1610612764, "source_codes": ["WAS"], "primary_color": "#002b5c", "secondary_color": "#e31837"},
}
TEAM_NAMES = {code: info["name"] for code, info in TEAM_INFO.items()}
TEAM_DIRECTORY = [
    {"code": code, "name": info["name"], "logo_id": info["logo_id"], "primary_color": info["primary_color"], "secondary_color": info["secondary_color"]}
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


def read_bonus_entry_timing(cursor):
    """Aggregate archived bonus-entry clock times by season, team, and period."""
    cursor.execute(
        """
        SELECT
            JSON_UNQUOTE(JSON_EXTRACT(row_json, '$.season')) AS season,
            JSON_UNQUOTE(JSON_EXTRACT(row_json, '$.team_entering_bonus')) AS team,
            CAST(JSON_UNQUOTE(JSON_EXTRACT(row_json, '$.period')) AS UNSIGNED) AS period,
            AVG(CAST(JSON_UNQUOTE(JSON_EXTRACT(row_json, '$.seconds_remaining')) AS DECIMAL(10,2)))
                AS average_seconds_remaining,
            COUNT(*) AS entries
        FROM analysis_results_archive
        WHERE source_file = %s
          AND JSON_EXTRACT(row_json, '$.season') IS NOT NULL
          AND JSON_EXTRACT(row_json, '$.seconds_remaining') IS NOT NULL
        GROUP BY season, team, period
        ORDER BY season, period, team
        """,
        ("results/historical_bonus_entries.csv",),
    )
    return cursor.fetchall()


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
            league_rows = read_rows(
                cursor,
                "results/team_trends/league_season_trends.csv",
                ["season", "average_bonus_fta", "bonus_ft_percentage"],
            )
    finally:
        connection.close()

    league_by_season = {row["season"]: row for row in league_rows}
    seasons = []
    for row in rows:
        if row["team"] not in team["source_codes"]:
            continue
        league_row = league_by_season.get(row["season"], {})
        seasons.append({
            "season": row["season"],
            "games": int(float(row["games"])),
            "wins": int(float(row["wins"])),
            "attempts": as_float(row["average_bonus_fta"]),
            "total_attempts": int(float(row["total_bonus_fta"])),
            "made": int(float(row["total_bonus_ftm"])),
            "win_pct": as_float(row["win_percentage"]),
            "accuracy": as_float(row["bonus_ft_percentage"]),
            "league_attempts": as_float(league_row.get("average_bonus_fta")),
            "league_accuracy": as_float(league_row.get("bonus_ft_percentage")),
        })
    seasons.sort(key=lambda row: row["season"])
    if not seasons:
        raise RuntimeError(
            "No team-season rows were found in the TiDB analysis archive."
        )

    chart_values = [row["attempts"] for row in seasons]
    chart_values.extend(
        row["league_attempts"] for row in seasons
        if row["league_attempts"] is not None
    )
    min_attempts = min(chart_values)
    max_attempts = max(chart_values)
    spread = max_attempts - min_attempts or 1
    for row in seasons:
        row["bar_height"] = 8 + 84 * (row["attempts"] - min_attempts) / spread
        row["league_bar_height"] = (
            8 + 84 * (row["league_attempts"] - min_attempts) / spread
            if row["league_attempts"] is not None
            else None
        )

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


def load_league_analysis_data():
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            quarters = read_rows(
                cursor,
                "results/quarter_bonus_analysis/first_to_bonus_by_quarter.csv",
                ["period_label", "games", "win_percentage"],
            )
            q4 = read_rows(
                cursor,
                "results/quarter_bonus_analysis/fourth_quarter_sensitivity.csv",
                ["group", "games", "win_percentage"],
            )
            home_first = read_rows(
                cursor,
                "results/home_accuracy_analysis/home_away_first_in_game.csv",
                ["location", "games_first_to_bonus", "share_of_first_entries", "win_percentage"],
            )
            home_overall = read_rows(
                cursor,
                "results/home_accuracy_analysis/home_away_bonus_summary.csv",
                ["location", "win_percentage"],
            )
            season_gaps = read_rows(
                cursor,
                "results/final_historical_season_results.csv",
                ["season", "bonus_fta_win_gap"],
            )
            adjusted_gaps = read_rows(
                cursor,
                "results/historical_without_late_fouls_by_season.csv",
                ["season", "win_percentage_gap"],
            )
            team_change_rows = read_rows(
                cursor,
                "results/team_trends/team_changes_first5_vs_last5.csv",
                ["bonus_fta_change", "bonus_ft_percentage_change", "win_percentage_change"],
            )
            timing_rows = read_bonus_entry_timing(cursor)
    finally:
        connection.close()

    source_to_team = {
        source_code: code
        for code, info in TEAM_INFO.items()
        for source_code in info["source_codes"]
    }
    team_timing = {}
    league_timing = {}
    for row in timing_rows:
        code = source_to_team.get(row.get("team"))
        season = row.get("season")
        period_number = int(float(row.get("period") or 0))
        seconds = as_float(row.get("average_seconds_remaining"))
        entries = int(float(row.get("entries") or 0))
        if not code or not season or seconds is None or entries < 1:
            continue
        period = str(period_number) if period_number <= 4 else "OT"
        team_key = (season, code, period)
        values = team_timing.setdefault(team_key, [0.0, 0])
        values[0] += seconds * entries
        values[1] += entries
        league_key = (season, period)
        totals = league_timing.setdefault(league_key, [0.0, 0])
        totals[0] += seconds * entries
        totals[1] += entries

    timing_rows_data = []
    for (season, code, period), (weighted_seconds, entries) in team_timing.items():
        timing_rows_data.append({
            "season": season,
            "team": code,
            "period": period,
            "average_seconds": weighted_seconds / entries,
            "entries": entries,
        })
    for (season, period), (weighted_seconds, entries) in league_timing.items():
        timing_rows_data.append({
            "season": season,
            "team": "ALL",
            "period": period,
            "average_seconds": weighted_seconds / entries,
            "entries": entries,
        })
    period_order = {"1": 1, "2": 2, "3": 3, "4": 4, "OT": 5}
    timing_rows_data.sort(
        key=lambda row: (
            season_sort_key(row["season"]),
            period_order[row["period"]],
            row["team"],
        )
    )
    timing_seasons = sorted(
        {row["season"] for row in timing_rows_data},
        key=season_sort_key,
    )

    season_gap_data = []
    adjusted_by_season = {row["season"]: as_float(row["win_percentage_gap"]) for row in adjusted_gaps}
    for row in season_gaps:
        season_gap_data.append({
            "season": row["season"],
            "attempt_gap": as_float(row["bonus_fta_win_gap"]),
            "adjusted_gap": adjusted_by_season.get(row["season"]),
        })

    def corr_for_team_change(x_field):
        pairs = [
            (as_float(row.get(x_field)), as_float(row.get("win_percentage_change")))
            for row in team_change_rows
        ]
        pairs = [(x, y) for x, y in pairs if x is not None and y is not None]
        if len(pairs) < 2:
            return None
        xs, ys = zip(*pairs)
        mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
        numerator = sum((x - mx) * (y - my) for x, y in pairs)
        denominator = math.sqrt(
            sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys)
        )
        return numerator / denominator if denominator else None

    return {
        "quarters": [
            {"label": row["period_label"], "games": int(float(row["games"])),
             "win_pct": as_float(row["win_percentage"])}
            for row in quarters
        ],
        "q4": [
            {"label": row["group"], "games": int(float(row["games"])),
             "win_pct": as_float(row["win_percentage"])}
            for row in q4
        ],
        "home_first": [
            {"location": row["location"], "entries": int(float(row["games_first_to_bonus"])),
             "share": as_float(row["share_of_first_entries"]),
             "win_pct": as_float(row["win_percentage"])}
            for row in home_first
        ],
        "home_overall": {row["location"]: as_float(row["win_percentage"]) for row in home_overall},
        "season_gaps": season_gap_data,
        "bonus_timing": {
            "seasons": timing_seasons,
            "rows": timing_rows_data,
        },
        "attempt_change_corr": corr_for_team_change("bonus_fta_change"),
        "accuracy_change_corr": corr_for_team_change("bonus_ft_percentage_change"),
    }


def season_sort_key(season):
    """Sort season labels by their starting calendar year."""
    return int(str(season).split("-", 1)[0])


def load_team_comparison_data():
    """Load team-season rows used by the team pages for the comparison tool."""
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            rows = read_rows(
                cursor,
                "results/team_trends/team_by_season_summary.csv",
                [
                    "season", "team", "games", "wins", "total_bonus_fta",
                    "total_bonus_ftm",
                ],
            )
    finally:
        connection.close()

    source_to_team = {
        source_code: code
        for code, team in TEAM_INFO.items()
        for source_code in team["source_codes"]
    }
    grouped = {}
    for row in rows:
        code = source_to_team.get(row.get("team"))
        season = row.get("season")
        if not code or not season:
            continue
        key = (code, season)
        totals = grouped.setdefault(
            key, {"team": code, "season": season, "games": 0, "wins": 0,
                  "attempts": 0, "made": 0}
        )
        totals["games"] += int(float(row.get("games") or 0))
        totals["wins"] += int(float(row.get("wins") or 0))
        totals["attempts"] += int(float(row.get("total_bonus_fta") or 0))
        totals["made"] += int(float(row.get("total_bonus_ftm") or 0))

    seasons = sorted({season for _, season in grouped}, key=season_sort_key)
    return {
        "seasons": seasons,
        "rows": list(grouped.values()),
    }


@app.route("/compare-teams")
def compare_teams():
    data = None
    error = None
    try:
        data = load_team_comparison_data()
        if not data["seasons"]:
            raise RuntimeError("No team-season rows were found in the TiDB analysis archive.")
    except Exception:
        logging.exception("Could not load team comparison data from TiDB")
        error = (
            "Team comparison data could not be loaded from TiDB. "
            "Check the database connection settings, then refresh."
        )
    return render_template(
        "compare_teams.html",
        data=data,
        error=error,
        team_directory=TEAM_DIRECTORY,
    )


@app.route("/league-analysis")
def league_analysis():
    data = None
    error = None
    try:
        data = load_league_analysis_data()
    except Exception:
        logging.exception("Could not load detailed league analysis from TiDB")
        error = "Detailed league results could not be loaded from TiDB. Check that the listed analysis files are in the archive."
    return render_template(
        "league_analysis.html",
        data=data,
        error=error,
        team_directory=TEAM_DIRECTORY,
    )


@app.route("/season-leaderboard")
def season_leaderboard():
    """Show team rankings for one season using the archived team-season totals."""
    error = None
    data = None
    try:
        comparison_data = load_team_comparison_data()
        if not comparison_data["seasons"]:
            raise RuntimeError("No team-season rows were found in the TiDB analysis archive.")

        metric = request.args.get("metric", "win_rate")
        if metric not in {"attempts", "accuracy", "win_rate"}:
            metric = "win_rate"
        data = {
            "seasons": comparison_data["seasons"],
            "rows": comparison_data["rows"],
            "teams": TEAM_DIRECTORY,
            "selected_season": comparison_data["seasons"][-1],
            "selected_metric": metric,
        }
        requested_season = request.args.get("season")
        if requested_season in comparison_data["seasons"]:
            data["selected_season"] = requested_season
    except Exception:
        logging.exception("Could not load season leaderboard data from TiDB")
        error = (
            "The season leaderboard could not load its team results from TiDB. "
            "Check the database connection settings, then refresh."
        )
    return render_template("season_leaderboard.html", data=data, error=error)


if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG") == "1")
