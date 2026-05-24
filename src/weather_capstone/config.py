import os
from datetime import datetime
from dotenv import load_dotenv
from weather_capstone.paths import RAW_DATA_DIR, PROCESSED_DATA_DIR, DATABASE_DIR

load_dotenv()

WEATHER_SITE_URL = os.getenv("WEATHER_SITE_URL", "https://www.timeanddate.com/weather/").strip()

_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
DEFAULT_RAW_CSV_PATH = RAW_DATA_DIR / f"weather_raw_{_timestamp}.csv"
DEFAULT_CLEAN_CSV_PATH = PROCESSED_DATA_DIR / f"weather_clean_{_timestamp}.csv"
DEFAULT_SQLITE_PATH = DATABASE_DIR / "weather.sqlite"

def _get_env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except ValueError:
        return default

def _get_env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default

SCRAPE_DELAY_SECONDS = _get_env_float("SCRAPE_DELAY_SECONDS", 1.0)
PAGE_LOAD_TIMEOUT_SECONDS = _get_env_int("PAGE_LOAD_TIMEOUT_SECONDS", 30)
MAX_RETRIES = _get_env_int("MAX_RETRIES", 3)

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
