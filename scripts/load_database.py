#!/usr/bin/env python3
import argparse
import logging
import sys
from pathlib import Path

import pandas as pd

from weather_capstone.database import create_table, insert_records, get_connection
from weather_capstone.config import DEFAULT_SQLITE_PATH
from weather_capstone.logging_config import configure_logging

logger = logging.getLogger(__name__)


def get_latest_clean_file() -> Path:
    """Find the most recent clean CSV file in data/processed/."""
    processed_dir = Path("data/processed")
    if not processed_dir.exists():
        raise FileNotFoundError("data/processed/ directory does not exist. Run clean_weather.py first.")
    
    files = list(processed_dir.glob("weather_clean_*.csv"))
    if not files:
        raise FileNotFoundError("No clean CSV files found in data/processed/. Run clean_weather.py first.")
    
    return max(files, key=lambda f: f.stat().st_mtime)


def load_csv_to_database(csv_path: Path, db_path: Path) -> None:
    """Load cleaned CSV data into SQLite database."""
    if not csv_path.exists():
        logger.error(f"CSV file not found: {csv_path}")
        sys.exit(1)
    
    logger.info(f"Loading data from {csv_path}")
    
    df = pd.read_csv(csv_path)
    logger.info(f"Loaded {len(df)} rows from CSV")
    
    records = df.to_dict(orient="records")
    
    with get_connection(db_path) as conn:
        create_table(conn)
        inserted, duplicates = insert_records(conn, records)
    
    logger.info(f"Database load complete: {inserted} inserted, {duplicates} duplicates skipped")


def main():
    parser = argparse.ArgumentParser(description="Load cleaned weather data into SQLite database")
    parser.add_argument("--input", type=Path, default=None, help="Path to cleaned CSV file (default: most recent file in data/processed/)")
    parser.add_argument("--db", type=Path, default=DEFAULT_SQLITE_PATH, help="Path to SQLite database file")
    
    args = parser.parse_args()
    
    configure_logging(level=logging.INFO)
    
    if args.input:
        csv_path = args.input
    else:
        try:
            csv_path = get_latest_clean_file()
            logger.info("Auto-detected latest clean file: %s", csv_path)
        except FileNotFoundError as e:
            logger.error(str(e))
            sys.exit(1)
    
    load_csv_to_database(csv_path, args.db)


if __name__ == "__main__":
    main()
