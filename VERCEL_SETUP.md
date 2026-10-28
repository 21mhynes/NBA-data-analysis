# NBA Bonus Findings Website

This Flask site reads the original and late-game-adjusted win-rate comparisons from
`NBA_Project.analysis_results_archive` in TiDB. It uses read-only SQL queries.

## Run locally in VS Code

1. Open the repository folder in VS Code.
2. In the Terminal, activate your existing virtual environment if you have one.
3. Install the website dependencies:

   ```bash
   python3 -m pip install -r requirements.txt
   ```

4. Add the variables listed in `.env.example` to your existing local `.env` file.
   Use the TiDB connection details from the TiDB Cloud Connect dialog. Keep the
   real password in `.env`; never commit it.
5. Start the site:

   ```bash
   python3 app.py
   ```

6. Open `http://127.0.0.1:5000` in your browser.

The page reports a connection message if it cannot reach TiDB. The app reads the
following analysis fields from the archived result rows:
- `results/historical_bonus_team_games.csv`: `bonus_fta_difference` and `win`
- `results/historical_bonus_without_late_fouls.csv`:
  `bonus_fta_difference_before_final_2` and `win`

## Deploy to Vercel after the local page works

1. Import this GitHub repository in Vercel.
2. In the Vercel project settings, add `TIDB_HOST`, `TIDB_PORT`, `TIDB_USER`,
   `TIDB_PASSWORD`, and `TIDB_DATABASE` as environment variables.
3. Deploy the project. Vercel detects the Flask app in `app.py`.

The database password belongs only in local environment settings or Vercel's
environment-variable settings, never in HTML, Python source, or a Git commit.
