# NBA Bonus and Free-Throw Analysis

## Research Question

How does reaching the bonus first—and then shooting more free throws while in the bonus—affect an NBA team’s chance of winning?

This project also examines whether the relationship changes by quarter, home-court status, free-throw accuracy, team, and season.

## Dataset

The analysis covers 30 NBA regular seasons, from 1996–97 through 2025–26.

- Seasons analyzed: 30
- Games analyzed: 35,546
- Team-game observations: 71,092
- Recorded bonus entries: 158,332

The analysis uses play-by-play data to identify when each team entered the bonus, how many bonus free throws it attempted and made, and whether it won the game.

## Main Findings

### 1. Reaching the bonus first

The team that reached the bonus first at any point in the game won 53.17% of games.

This represents a small advantage, suggesting that reaching the bonus first is associated with winning but is not a strong predictor by itself.

### 2. Reaching the bonus first by quarter

The win percentages for the team reaching the bonus first were:

- First quarter: 54.15%
- Second quarter: 51.33%
- Third quarter: 52.42%
- Fourth quarter: 52.09%
- Overtime: 76.42%

The overtime result should be interpreted cautiously because overtime periods occur much less frequently and therefore have a smaller sample size.

### 3. Fourth-quarter timing

The team reaching the bonus first during the fourth quarter won:

- 48.60% when it happened before the final two minutes
- 60.50% when it happened during the final two minutes

This large difference suggests that intentional fouling and late-game strategy strongly influence bonus free-throw statistics.

### 4. Bonus free-throw attempts and winning

Using all bonus attempts, teams that attempted more bonus free throws than their opponents won 60.86% of games.

Teams with fewer bonus attempts won 39.14% of games, creating a raw win-rate gap of 21.72 percentage points.

However, after excluding free throws during the final two minutes of the fourth quarter and overtime:

- Teams with more adjusted bonus attempts won 52.23%
- Teams with fewer adjusted bonus attempts won 47.77%
- The adjusted gap was 4.46 percentage points

Approximately 79.5% of the original win-rate gap disappeared after removing late-game free throws.

This indicates that much of the raw relationship between bonus attempts and winning is produced by intentional fouling against teams that are already leading.

### 5. Bonus attempts compared with bonus accuracy

Teams with more bonus attempts won 60.86% of games, compared with 39.14% for teams with fewer attempts.

Teams with higher bonus free-throw accuracy won 53.67% of games, compared with 46.33% for teams with lower accuracy.

The win-rate gaps were:

- Bonus-attempt advantage: 21.72 percentage points
- Bonus-accuracy advantage: 7.34 percentage points

Bonus-attempt advantages had a stronger raw relationship with winning than bonus accuracy. However, the attempt result is heavily affected by intentional late-game fouling.

### 6. Home-court advantage

Home teams reached the bonus first in 52.62% of first bonus entries.

When the home team reached the bonus first, it won 61.19% of games. When the away team reached it first, the away team won 44.27%.

The overall home-team winning percentage was 58.64%, so part of this result reflects the NBA’s general home-court advantage rather than the bonus alone.

### 7. Changes across 30 seasons

League-wide bonus free-throw attempts declined over the 30-season period.

- Average in 1996–97: 11.41 bonus attempts per team-game
- Average in 2025–26: 8.48 bonus attempts per team-game
- Overall change: −2.93 attempts
- Percentage decline: approximately 25.7%

At the same time, bonus free-throw accuracy improved.

- Accuracy in 1996–97: 74.43%
- Accuracy in 2025–26: 78.19%
- Overall improvement: 3.76 percentage points

The league now produces fewer bonus free-throw attempts, but teams make those attempts more accurately.

### 8. Team changes

Every comparable team recorded fewer bonus attempts when its first five seasons were compared with its most recent five seasons.

The smallest declines included:

- Dallas: −0.29 attempts per team-game
- Minnesota: −1.72
- Houston: −2.05

The largest declines included:

- Los Angeles Lakers: −6.29 attempts per team-game
- Utah: −6.07
- Philadelphia: −5.21

The largest improvements in bonus accuracy included:

- Philadelphia: +8.48 percentage points
- Los Angeles Clippers: +8.17
- Los Angeles Lakers: +7.26
- Charlotte: +6.86
- Boston: +6.56

Only four comparable teams experienced a decline in bonus accuracy:

- Houston: −1.65 percentage points
- Milwaukee: −0.49
- New York: −0.19
- Indiana: −0.15

### 9. Team changes and winning

The correlation between changes in bonus attempts and changes in team winning percentage was 0.391, representing a moderate positive relationship.

The correlation between changes in bonus accuracy and changes in team winning percentage was 0.171, representing a weak positive relationship.

Teams that maintained more of their bonus-attempt volume generally experienced better changes in winning percentage than teams that only improved their accuracy.

## Overall Conclusion

Reaching the bonus first gives an NBA team a small advantage, but it is not enough to determine the outcome of a game.

Teams that shoot more free throws while in the bonus appear to have a large winning advantage in the raw data. However, most of that advantage disappears after removing the final two minutes, demonstrating that intentional fouling against teams already leading creates much of the relationship.

Bonus accuracy also matters, but its relationship with winning is weaker than the relationship involving attempts.

Across the last 30 seasons, NBA teams have taken substantially fewer free throws while in the bonus while becoming more accurate at making them.

The strongest overall conclusion is that bonus statistics are connected to winning, but game situation and late-game strategy must be considered before interpreting that relationship as causal.

## Limitations

- The analysis identifies relationships but does not prove that reaching the bonus or receiving more attempts directly causes a team to win.
- Intentional late-game fouling can give leading teams additional free throws.
- Home teams already win more often, making it difficult to isolate the bonus from home-court advantage.
- Overtime findings use a much smaller sample than regulation-quarter findings.
- Team comparisons cover different players, coaches, strategies, and league environments across 30 seasons.
- Rule changes and changes in style of play may influence historical comparisons.
- Comparing the first five seasons with the last five summarizes long-term change but does not capture every season-to-season variation.

## Project Outputs

Important results are stored in:

- `results/historical_bonus_team_games.csv`
- `results/historical_bonus_entries.csv`
- `results/team_trends/team_by_season_summary.csv`
- `results/team_trends/league_season_trends.csv`
- `results/team_trends/team_changes_first5_vs_last5.csv`
- `results/charts/team_trends/`
- `results/charts/final_relationships/`