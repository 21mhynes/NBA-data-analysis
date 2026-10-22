#!/usr/bin/env python3
"""Combine season CSVs in ./data and report file sizes.

Run from the NBA project root with: python3 combine_nba_csvs.py
"""
from __future__ import annotations

import csv
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"


def combine(pattern: str, output_name: str) -> None:
    files = sorted(DATA_DIR.glob(pattern))
    if not files:
        print(f"No files matched {pattern!r} in {DATA_DIR}")
        return

    # Confirm all seasons have the same header before writing a combined file.
    expected_header = None
    for path in files:
        with path.open("r", newline="", encoding="utf-8-sig") as source:
            header = next(csv.reader(source), None)
        if not header:
            raise SystemExit(f"{path.name} is empty or has no header row")
        if expected_header is None:
            expected_header = header
        elif header != expected_header:
            raise SystemExit(
                f"Column names differ in {path.name}. No combined file was written."
            )

    output_path = DATA_DIR / output_name
    row_count = 0
    with output_path.open("w", newline="", encoding="utf-8") as destination:
        writer = csv.writer(destination)
        writer.writerow(expected_header)
        for path in files:
            with path.open("r", newline="", encoding="utf-8-sig") as source:
                reader = csv.reader(source)
                next(reader, None)  # Skip this file's header; keep only the first header.
                for row in reader:
                    writer.writerow(row)
                    row_count += 1

    size_mib = output_path.stat().st_size / (1024 * 1024)
    print(f"Created {output_path.name} from {len(files)} files, {row_count:,} rows")
    print(f"Size: {size_mib:.2f} MiB ({output_path.stat().st_size:,} bytes)")


def main() -> None:
    if not DATA_DIR.is_dir():
        raise SystemExit(f"Could not find the data folder: {DATA_DIR}")
    combine("games_????_??.csv", "games_all.csv")
    combine("play_by_play_????_??.csv", "play_by_play_all.csv")


if __name__ == "__main__":
    main()
