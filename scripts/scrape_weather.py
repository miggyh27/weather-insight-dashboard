import argparse
import logging
import os
import sys
from pathlib import Path
import pandas as pd

from weather_capstone.logging_config import configure_logging
from weather_capstone.config import (
    DEFAULT_RAW_CSV_PATH,
)
from weather_capstone import scraper

logger = logging.getLogger("scrape_weather")

def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scrape current weather observations from Weather Around The World using Selenium."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Limit the number of cities scraped (default: 0 for all discovered cities)."
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help=f"Path to export raw CSV output (default: data/raw/weather_raw_YYYYMMDD_HHMMSS.csv)"
    )
    parser.add_argument(
        "--url",
        type=str,
        default=None,
        help=f"Target URL to scrape (default: value in config/environment)"
    )
    return parser.parse_args()

def main() -> None:
    args = parse_arguments()
    configure_logging(level=logging.INFO)

    if args.url:
        scraper.WEATHER_SITE_URL = args.url.strip()
        logger.info("Overriding target URL to: %s", args.url)

    output_path_str = args.output or str(DEFAULT_RAW_CSV_PATH)
    output_path = Path(output_path_str).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Starting scrape run. Target URL: %s", scraper.WEATHER_SITE_URL)
    try:
        records = scraper.scrape_all(limit=args.limit)
        if not records:
            logger.error("Scraper returned no records. Exiting.")
            sys.exit(1)

        df = pd.DataFrame([r.to_dict() for r in records])
        
        initial_len = len(df)
        df = df.drop_duplicates()
        deduped_diff = initial_len - len(df)
        if deduped_diff > 0:
            logger.info("Removed %d duplicate raw records from output.", deduped_diff)

        df.to_csv(output_path, index=False, encoding="utf-8")
        logger.info("Successfully saved %d raw records to: %s", len(df), output_path)

    except Exception as e:
        logger.exception("Scraping pipeline failed: %s", e)
        sys.exit(1)

if __name__ == "__main__":
    main()
