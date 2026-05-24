import argparse
import subprocess
import sys
import logging
import re
from weather_capstone.logging_config import configure_logging

logger = logging.getLogger("run_pipeline")

def main():
    parser = argparse.ArgumentParser(description="Run the complete weather insight pipeline.")
    parser.add_argument("--limit", type=int, default=0, help="Limit the number of cities scraped.")
    args = parser.parse_args()

    configure_logging(level=logging.INFO)
    logger.info("Starting pipeline execution")

    scrape_cmd = [sys.executable, "scripts/scrape_weather.py"]
    if args.limit > 0:
        scrape_cmd.extend(["--limit", str(args.limit)])
    logger.info("Running scraper: %s", " ".join(scrape_cmd))
    scrape_res = subprocess.run(scrape_cmd, capture_output=True, text=True)
    if scrape_res.returncode != 0:
        logger.error("Scraping failed: %s", scrape_res.stderr)
        sys.exit(scrape_res.returncode)
    print(scrape_res.stdout)

    raw_path_match = re.search(r"Successfully saved \d+ raw records to: (.*)", scrape_res.stdout)
    if not raw_path_match:
        logger.error("Could not determine raw output path from scraper output")
        sys.exit(1)
    raw_path = raw_path_match.group(1).strip()

    clean_cmd = [sys.executable, "scripts/clean_weather.py", "--input", raw_path]
    logger.info("Running cleaner: %s", " ".join(clean_cmd))
    clean_res = subprocess.run(clean_cmd, capture_output=True, text=True)
    if clean_res.returncode != 0:
        logger.error("Cleaning failed: %s", clean_res.stderr)
        sys.exit(clean_res.returncode)
    print(clean_res.stdout)

    clean_path_match = re.search(r"Saved cleaned data to: (.*)", clean_res.stdout)
    if not clean_path_match:
        logger.error("Could not determine clean output path from cleaner output")
        sys.exit(1)
    clean_path = clean_path_match.group(1).strip()

    load_cmd = [sys.executable, "scripts/load_database.py", "--input", clean_path]
    logger.info("Running database loader: %s", " ".join(load_cmd))
    load_res = subprocess.run(load_cmd, capture_output=True, text=True)
    if load_res.returncode != 0:
        logger.error("Loading database failed: %s", load_res.stderr)
        sys.exit(load_res.returncode)
    print(load_res.stdout)

    logger.info("Pipeline executed successfully")

if __name__ == "__main__":
    main()
