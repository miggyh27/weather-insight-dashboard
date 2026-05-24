import argparse
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
import pandas as pd

from weather_capstone.logging_config import configure_logging
from weather_capstone.config import DEFAULT_CLEAN_CSV_PATH
from weather_capstone import cleaner

logger = logging.getLogger("clean_weather")

def get_latest_raw_file() -> Path:
    """Find the most recent raw CSV file in data/raw/."""
    raw_dir = Path("data/raw")
    if not raw_dir.exists():
        raise FileNotFoundError("data/raw/ directory does not exist. Run scrape_weather.py first.")
    
    files = list(raw_dir.glob("weather_raw_*.csv"))
    if not files:
        raise FileNotFoundError("No raw CSV files found in data/raw/. Run scrape_weather.py first.")
    
    return max(files, key=lambda f: f.stat().st_mtime)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Clean raw scraped weather data and export to clean CSV with a markdown summary."
    )
    parser.add_argument(
        "--input",
        type=str,
        default=None,
        help="Path to the raw input weather CSV file (default: most recent file in data/raw/)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help=f"Path to write cleaned CSV (default: data/processed/weather_clean_YYYYMMDD_HHMMSS.csv)"
    )
    return parser.parse_args()

def generate_markdown_report(
    raw_df: pd.DataFrame,
    clean_df: pd.DataFrame,
    stats: dict,
    input_file: str,
    output_file: str
) -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    sample_raw = raw_df.head(3).to_markdown(index=False)
    sample_clean = clean_df.head(3).to_markdown(index=False)

    missing_before_str = "\n".join([f"- **{col}**: {count}" for col, count in stats["missing_before"].items()])
    missing_after_str = "\n".join([f"- **{col}**: {count}" for col, count in stats["missing_after"].items()])

    report = f"""# Weather Data Cleaning Summary Report

Generated on: {timestamp}

## Metadata
- **Source Raw File**: `{input_file}`
- **Output Cleaned File**: `{output_file}`
- **Cleaning Started At**: {timestamp}

## Row Count Metrics
| Metric | Count |
| :--- | :--- |
| **Raw Row Count** | {stats["raw_rows"]} |
| **Cleaned Row Count** | {stats["cleaned_rows"]} |
| **Duplicate Rows Removed** | {stats["removed_duplicates"]} |
| **Malformed Rows Removed (missing City/Temp)** | {stats["removed_malformed"]} |

## Missing Values
### Before Cleaning
{missing_before_str}

### After Cleaning
{missing_after_str}

## Cleaning Decisions and Rationale
1. **Standardized Column Names**: All attributes are normalized to snake_case.
2. **Text Normalization**: Stripped trailing spaces and replaced empty spaces with nulls.
3. **True Country Resolution**: Extracted actual sovereign country names from detail URLs (e.g. mapping `Alberta` or `New York State` back to `Canada` or `USA` respectively).
4. **Numeric Parsing**: Derived numeric temperatures (both `temperature_c` and `temperature_f`), `humidity_pct`, `wind_speed_kph` (converted from mph), and `pressure_mb` (converted from inHg).
5. **Data Categorization**: Mapped weather description elements into standardized condition categories (e.g. Rain, Cloudy, Storm).
6. **Comfort Metrics**: Added comfort band classifications based on Celsius boundaries, alongside hot/cold flags.

## Sample Data Comparison

### Before Cleaning (Raw Sample)
{sample_raw}

### After Cleaning (Processed Sample)
{sample_clean}
"""
    return report

def main() -> None:
    args = parse_arguments()
    configure_logging(level=logging.INFO)

    if args.input:
        input_path = Path(args.input).resolve()
    else:
        try:
            input_path = get_latest_raw_file()
            logger.info("Auto-detected latest raw file: %s", input_path)
        except FileNotFoundError as e:
            logger.error(str(e))
            sys.exit(1)
    
    if not input_path.exists():
        logger.error("Input file not found: %s", input_path)
        sys.exit(1)

    output_path_str = args.output or str(DEFAULT_CLEAN_CSV_PATH)
    output_path = Path(output_path_str).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Reading raw data from: %s", input_path)
    try:
        raw_df = pd.read_csv(input_path)
        if raw_df.empty:
            logger.error("Source CSV file is empty.")
            sys.exit(1)
            
        logger.info("Processing data pipeline...")
        cleaned_df, stats = cleaner.clean_data(raw_df)

        cleaned_df.to_csv(output_path, index=False, encoding="utf-8")
        logger.info("Saved cleaned data to: %s", output_path)

        report_content = generate_markdown_report(
            raw_df=raw_df,
            clean_df=cleaned_df,
            stats=stats,
            input_file=str(input_path),
            output_file=str(output_path)
        )
        
        from weather_capstone.paths import CLEANING_SUMMARY_PATH
        CLEANING_SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
        CLEANING_SUMMARY_PATH.write_text(report_content, encoding="utf-8")
        logger.info("Saved cleaning summary report to: %s", CLEANING_SUMMARY_PATH)

    except Exception as e:
        logger.exception("Data cleaning pipeline failed: %s", e)
        sys.exit(1)

if __name__ == "__main__":
    main()
