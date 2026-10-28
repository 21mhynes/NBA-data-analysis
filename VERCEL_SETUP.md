# NBA Bonus and Free-Throw Analysis Website

This Flask site reads the project's prepared analysis results from
`NBA_Project.analysis_results_archive` in TiDB. It presents the research
question, dataset coverage, all nine findings, the overall conclusion,
limitations, and project output paths. It uses read-only SQL queries.

## Run locally in VS Code

1. Open the repository folder in VS Code.
2. Activate your existing virtual environment if you have one.
3. Install the website dependencies:

   ```bash
   python3 -m pip install -r requirements.txt
   ```

4. Add the variables listed in `.env.example` to your existing local `.env`
   file, using the connection values from the TiDB Cloud Connect dialog. Keep
   the actual password in `.env`; never commit it.
5. Start the site:

   ```bash
   python3 app.py
   ```

6. Open `http://127.0.0.1:5000` in your browser.

The page reads the prepared result files by `source_file` from the
`analysis_results_archive` table. The route only runs SELECT queries. It does
not modify or import database data.

## Deploy to Vercel after the local page works

1. Import this GitHub repository in Vercel.
2. In the Vercel project settings, add `TIDB_HOST`, `TIDB_PORT`, `TIDB_USER`,
   `TIDB_PASSWORD`, and `TIDB_DATABASE` as environment variables.
3. Deploy the project. Vercel detects the Flask app in `app.py`.

The database password belongs only in local environment settings or Vercel's
environment-variable settings, never in HTML, Python source, or a Git commit.
