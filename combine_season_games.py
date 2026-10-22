from pathlib import Path
import csv
import re

project_dir = Path(__file__).resolve().parent
data_dir = project_dir / "data"

# Match season files like games_1996_97.csv.
# This excludes the separate games_full_ files.
files = sorted(
    path for path in data_dir.glob("games_*.csv")
    if re.fullmatch(r"games_\d{4}_\d{2}\.csv", path.name)
)

if not files:
    raise SystemExit("No season game CSV files were found in the data folder.")

# Build one column list from the headers, matching columns by name.
fieldnames = []
for path in files:
    with path.open("r", newline="", encoding="utf-8-sig") as infile:
        header = next(csv.reader(infile), None)

    if not header:
        raise SystemExit(f"The file {path.name} has no header row.")

    if len(header) != len(set(header)):
        raise SystemExit(f"The file {path.name} has duplicate column names.")

    for name in header:
        if name not in fieldnames:
            fieldnames.append(name)

output_path = data_dir / "games_all.csv"

with output_path.open("w", newline="", encoding="utf-8") as outfile:
    writer = csv.DictWriter(outfile, fieldnames=fieldnames, extrasaction="raise")
    writer.writeheader()

    for path in files:
        with path.open("r", newline="", encoding="utf-8-sig") as infile:
            reader = csv.DictReader(infile)

            for row in reader:
                if None in row:
                    raise SystemExit(f"Unexpected extra values in {path.name}.")
                writer.writerow({key: (r"\N" if value == "?" else value) for key, value in row.items()})

print(f"Combined {len(files)} season files into: {output_path}")
print(f"Columns included: {len(fieldnames)}")