import logging
import os

import pymysql
from dotenv import load_dotenv
from flask import Flask, render_template

load_dotenv()
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

COMPARISONS = (
    {
        "label": "All bonus free throws",
        "source_file": "results/historical_bonus_team_games.csv",
        "difference_field": "bonus_fta_difference",
    },
    {
        "label": "Final 2:00 excluded",
        "source_file": "results/historical_bonus_without_late_fouls.csv",
        "difference_field": "bonus_fta_difference_before_final_2",
    },
)


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


def fetch_comparison(source_file, difference_field, label):
    # difference_field is selected only from the fixed COMPARISONS above.
    query = f"""
        SELECT
            ROUND(AVG(CASE WHEN bonus_diff > 0 THEN win_value END) * 100, 2)
                AS more_fta_win_pct,
            ROUND(AVG(CASE WHEN bonus_diff < 0 THEN win_value END) * 100, 2)
                AS fewer_fta_win_pct
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
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (source_file,))
            row = cursor.fetchone()
    finally:
        connection.close()

    more_pct = row["more_fta_win_pct"]
    fewer_pct = row["fewer_fta_win_pct"]
    if more_pct is None or fewer_pct is None:
        raise RuntimeError(f"No usable rows found for {source_file}")

    more_pct = float(more_pct)
    fewer_pct = float(fewer_pct)
    return {
        "label": label,
        "more_pct": more_pct,
        "fewer_pct": fewer_pct,
        "gap": round(more_pct - fewer_pct, 2),
    }


def load_findings():
    return [
        fetch_comparison(
            item["source_file"], item["difference_field"], item["label"]
        )
        for item in COMPARISONS
    ]


@app.route("/")
def home():
    error = None
    findings = []
    try:
        findings = load_findings()
    except Exception:
        logging.exception("Could not load the NBA findings from TiDB")
        error = (
            "The page could not reach TiDB. Check the database settings in your "
            "local .env file, then refresh."
        )

    return render_template(
        "index.html",
        findings=findings,
        error=error,
        seasons="1996–97 through 2025–26",
        games="35,546",
        team_games="71,092",
    )


if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG") == "1")
