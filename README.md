# NBA Bonus and Free-Throw Analysis

## Project overview

This project analyzes NBA regular-season play-by-play data to examine how bonus timing and bonus free throws relate to winning. The website presents league-wide, period-level, home-court, and team-season results.

## Research question

How does reaching the bonus first—and then shooting more free throws while in the bonus—affect an NBA team’s chance of winning?

## Dataset

The analysis covers 30 NBA regular seasons, from 1996–97 through 2025–26:

- 35,546 games
- 71,092 team-game observations
- 158,332 recorded bonus entries

## Method

The game-level measure identifies the first team to enter the bonus anywhere in the game. Separate period-level results identify which team enters the bonus first within each period.

The analysis tracks team-foul penalties separately by period and accounts for the NBA’s final-two-minute foul rule. Technical, flagrant, and clear-path free throws are excluded from standard bonus free-throw totals. The adjusted comparison excludes bonus free throws from the final two minutes of the fourth quarter and overtime.

## Key findings

- The team that reached the bonus first anywhere in the game won 53.17% of games.
- Teams with more bonus free-throw attempts won 60.86% of games, compared with 39.14% for teams with fewer attempts.
- Excluding bonus free throws from the final two minutes of the fourth quarter and overtime, the win rates were 52.23% for teams with more adjusted attempts and 47.77% for teams with fewer.
- Bonus free-throw accuracy also related to winning, but less strongly than attempt volume.
- Across the seasons studied, teams attempted fewer bonus free throws but made them more accurately.

These are associations in the data; they do not show that bonus timing or free throws cause teams to win.

## Data pipeline

1. NBA play-by-play data is downloaded and processed with Python analysis scripts.
2. The scripts create prepared results and charts.
3. Prepared results are stored in TiDB’s `NBA_Project.analysis_results_archive` table.
4. The Flask website reads the results from TiDB and displays them in its pages.
5. Vercel hosts the website.

## Technology

- Python and pandas for data processing
- Flask, HTML, and CSS for the website
- TiDB for the prepared-results archive
- Vercel for hosting

## Run locally

1. Create and activate a virtual environment:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate

## Key project files

- `app.py` — Flask routes and read-only TiDB queries
- `bonus_analysis.py` — bonus and free-throw analysis
- `historical_bonus_analysis.py` — historical season analysis
- `quarter_bonus_analysis.py` — quarter-level analysis
- `templates/` — website pages
- `results/` — prepared analysis files and charts
- `requirements.txt` — Python packages needed by the website
- `.env.example` — required TiDB environment-variable names
- `VERCEL_SETUP.md` — deployment notes