# NBA Bonus Analysis — Project Status

## Project owner

Michael Hynes

## Project location

`~/Documents/GitHub/NBA-data-analysis`

## Main research question

How does reaching the bonus first—and then shooting more free throws while in the bonus—affect an NBA team’s chance of winning?

The project also examines how these relationships have changed over time.

---

## Dataset

The project contains NBA regular-season play-by-play data covering:

- First season: 1996-97
- Most recent season: 2025-26
- Seasons analyzed: 30
- Games analyzed: 35,546
- Team-game rows: 71,092
- Recorded bonus entries: 158,332

The canceled Celtics–Pacers game from April 16, 2013 (`0021201214`) was excluded because it was never played and has no play-by-play data.

---

## Definition of the bonus

The analysis tracks the NBA team-foul penalty separately during every period.

A team enters the bonus when its opponent reaches the applicable team-foul limit. The analysis also accounts for the NBA’s special final-two-minute foul rule.

Technical, flagrant, and clear-path free throws are excluded from standard bonus free-throw totals.

---

## Important definition of “reaching the bonus first”

The initial game-level analysis measures whether a team reached the bonus first in more periods than its opponent.

For example:

- Team A enters the bonus first in three quarters.
- Team B enters first in one quarter.
- Team A receives the first-to-bonus advantage for that game.

This does not necessarily mean Team A was the first team to enter the bonus anywhere in the game.

A future analysis will separately examine the first team to reach the bonus in each quarter and anywhere in the game.

---

## Accuracy validation

The original current-season analysis tested 5,339 detected bonus entries.

Results:

- 100% matched actual foul events
- 100% assigned to valid teams
- All recorded clocks were valid
- No duplicate entries were detected

---

## Questions answered

### 1. Does reaching the bonus first affect winning?

Yes, based on the initial definition.

Teams reaching the bonus first in more periods had a win-rate advantage of 9.71 percentage points compared with teams reaching it first in fewer periods.

This is an association and does not prove causation.

### 2. Does shooting more free throws while in the bonus affect winning?

The original analysis found a 21.72-percentage-point win-rate gap between teams with more bonus free throws and teams with fewer.

However, this figure was heavily influenced by late-game fouling.

### 3. Which matters more: reaching the bonus first or shooting more bonus free throws?

Shooting more bonus free throws was the stronger predictor of winning.

The original combined categories produced these win rates:

- First more often and more bonus free throws: 59.7%
- First more often without more bonus free throws: 36.1%
- More bonus free throws without the first-bonus advantage: 63.1%
- Neither advantage: 41.3%

This suggests that reaching the bonus first only becomes especially useful when it produces additional free-throw attempts.

### 4. Has the bonus advantage changed over time?

Yes. Every measured bonus advantage weakened over the 30 seasons.

Approximate changes:

- Bonus-FTA win gap: about 30 points to about 13 points
- Combined bonus advantage: about 28 points to about 12 points
- First-to-bonus advantage: about 16 points to about 7 points

The relationships remained positive, but became smaller over time.

### 5. How much of the bonus-FTA relationship comes from late-game fouling?

A second analysis excluded bonus free throws during the final two minutes of the fourth quarter and overtime.

Results:

- Original bonus-FTA win-rate gap: 21.72 percentage points
- Adjusted gap: 4.46 percentage points
- Win rate with more adjusted bonus FTs: 52.23%
- Win rate with fewer adjusted bonus FTs: 47.77%

Approximately 79.5% of the original win-rate gap disappeared after excluding the final two minutes.

### 6. Do bonus free throws still matter without late intentional fouling?

Yes, but the association is modest.

Teams with more adjusted bonus free throws won 52.23% of games, compared with 47.77% for teams with fewer adjusted attempts.

---

## Current main conclusion

Across 35,546 NBA regular-season games from 1996-97 through 2025-26, teams that reached the bonus first more frequently and attempted more bonus free throws generally won at higher rates.

However, after excluding the final two minutes to reduce the influence of intentional fouling, the bonus free-throw win-rate advantage fell from 21.72 to 4.46 percentage points.

Therefore, bonus free throws retain a modest positive association with winning, but late-game fouling explains most of the original relationship.

---

## Interpretation warning

The analysis establishes association, not definite causation.

Possible influences include:

- Intentional fouling of teams that are already winning
- Team quality
- Score situation
- Home-court advantage
- Playing style
- Opponent defensive style
- Quarter and game timing
- Differences across NBA eras

Do not claim that bonus free throws alone cause teams to win.

---

## Main Python files

### Downloading data

- `download_season.py`
- `download_history.py`

### Main analysis

- `bonus_analysis.py`
- `historical_bonus_analysis.py`
- `historical_bonus_no_late_fouls.py`

### Charts

- `make_charts.py`
- `historical_charts.py`

### Validation

- `validate_bonus.py`
- `check_bonus_accuracy.py`
- `inspect_fouls.py`

---

## Main result files

Located inside `results/`:

- `historical_bonus_team_games.csv`
- `historical_bonus_entries.csv`
- `historical_team_season_summary.csv`
- `historical_season_outcome_summary.csv`
- `historical_season_summary.csv`
- `final_historical_findings.txt`
- `final_historical_season_results.csv`
- `historical_bonus_without_late_fouls.csv`
- `historical_without_late_fouls_by_season.csv`

Do not delete these files.

---

## Main chart folders

### Historical charts

`results/charts/historical/`

Important charts:

- `01_first_bonus_win_percentage.png`
- `02_bonus_fta_win_percentage.png`
- `03_combined_bonus_effect.png`
- `04_bonus_advantage_over_time.png`
- `05_bonus_win_gap_over_time.png`
- `06_bonus_fta_and_score_margin.png`

### Late-foul adjustment

`results/charts/no_late_fouls/`

Important charts:

- `01_without_late_fouls.png`
- `02_original_vs_adjusted.png`
- `03_adjusted_trend.png`

The most important methodological chart is:

`results/charts/no_late_fouls/02_original_vs_adjusted.png`

---

## Potential next research questions

### Bonus timing

1. Does entering the bonus earlier lead to more bonus free throws?
2. Does entering earlier increase win probability?
3. How often does a team enter the bonus but receive no bonus free throws?
4. Does entering with 8–12, 4–8, 2–4, or fewer than 2 minutes remaining change the result?

### Quarter-level results

5. What happens to the first team reaching the bonus in each quarter?
6. Which quarter’s bonus advantage matters most?
7. Does the first team reaching the bonus anywhere in the game win more often?
8. Does reaching the bonus first lead to more attempts during that same quarter?

### Game situation

9. Does the result differ in close games and blowouts?
10. What is the score when each team enters the bonus?
11. Does the advantage remain after controlling for the score at bonus entry?
12. How has intentional late-game fouling changed over time?

### Teams and seasons

13. Which teams enter the bonus first most often?
14. Which teams generate the most adjusted bonus attempts?
15. Which teams commit the most fouls?
16. Which teams put opponents into the bonus earliest?
17. Which franchises changed the most over 30 seasons?
18. Do home teams enter the bonus earlier or receive more attempts?

### Free-throw performance

19. Are bonus attempts or bonus accuracy more closely associated with winning?
20. Which players draw or shoot the most bonus free throws?

---

## Recommended next steps

Complete the questions in this order:

1. Does entering the bonus earlier create more bonus attempts?
2. Which quarter’s bonus advantage matters most?
3. Does the result remain after controlling for the score at bonus entry?
4. Compare close games with blowouts.
5. Produce team-level rankings.
6. Analyze home-versus-away differences.
7. Create a final report or presentation.

---

## Commands used to reproduce completed analyses

Run the full historical analysis:

```bash
python3 historical_bonus_analysis.py