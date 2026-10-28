import logging
import math
import os

import pymysql
from dotenv import load_dotenv
from flask import Flask, render_template

load_dotenv()
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)


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
    # fields and source_file are constants in this application, not user input.
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
            home_rows = read_rows(
                cursor,
                "results/home_accuracy_analysis/home_away_first_in_game.csv",
                ["location", "share_of_first_entries", "win_percentage"],
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
                "Final two minutes excluded",
            )
    finally:
        connection.close()

    if not first_bonus_rows or not season_rows:
        raise RuntimeError("The required summary rows were not found in TiDB.")

    first_bonus_pct = as_float(first_bonus_rows[0]["win_percentage"])
    first_bonus_games = int(float(first_bonus_rows[0]["games"]))
    quarter_data = [
        {
            "label": row["period_label"],
            "games": int(float(row["games"])),
            "win_pct": as_float(row["win_percentage"]),
        }
        for row in quarter_rows
    ]
    home_data = [
        {
            "label": row["location"],
            "share_pct": as_float(row["share_of_first_entries"]),
            "win_pct": as_float(row["win_percentage"]),
        }
        for row in home_rows
    ]
    attempts = {row["attempt_result"]: as_float(row["win_percentage"]) for row in attempt_rows}
    accuracy = {row["accuracy_result"]: as_float(row["win_percentage"]) for row in accuracy_rows}

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

    comparable_teams = [
        {
            **row,
            "attempt_change": as_float(row["bonus_fta_change"]),
            "accuracy_change": as_float(row["bonus_ft_percentage_change"]),
            "win_change": as_float(row["win_percentage_change"]),
        }
        for row in team_rows
        if as_float(row["bonus_fta_change"]) is not None
    ]
    attempt_change_sorted = sorted(comparable_teams, key=lambda row: row["attempt_change"])
    accuracy_change_sorted = sorted(
        [row for row in comparable_teams if row["accuracy_change"] is not None],
        key=lambda row: row["accuracy_change"],
        reverse=True,
    )
    adjusted_pct_of_gap_removed = (
        (original["gap"] - adjusted["gap"]) / original["gap"] * 100
        if original["gap"]
        else 0
    )

    return {
        "first_bonus_pct": first_bonus_pct,
        "first_bonus_games": first_bonus_games,
        "quarters": quarter_data,
        "home": home_data,
        "attempts": attempts,
        "accuracy": accuracy,
        "seasons": seasons,
        "first_season": seasons[0],
        "last_season": seasons[-1],
        "team_count": len(comparable_teams),
        "attempt_corr": pearson(team_rows, "bonus_fta_change", "win_percentage_change"),
        "accuracy_corr": pearson(team_rows, "bonus_ft_percentage_change", "win_percentage_change"),
        "least_attempt_declines": list(reversed(attempt_change_sorted[-3:])),
        "largest_attempt_declines": attempt_change_sorted[:3],
        "largest_accuracy_improvements": accuracy_change_sorted[:3],
        "original": original,
        "adjusted": adjusted,
        "gap_removed_pct": adjusted_pct_of_gap_removed,
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

    return render_template(
        "index.html",
        data=data,
        error=error,
        seasons="1996–97 through 2025–26",
        games="35,546",
        team_games="71,092",
        bonus_entries="158,332",
    )


if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG") == "1")
