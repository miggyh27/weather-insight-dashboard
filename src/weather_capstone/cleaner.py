import logging
import re
from datetime import datetime
from typing import Tuple, Dict, Any
import pandas as pd
from weather_capstone.logging_config import log_execution_time

logger = logging.getLogger(__name__)

def parse_temperature(value: str) -> Tuple[float | None, str | None]:
    if pd.isna(value) or not isinstance(value, str):
        return None, None
        
    value_clean = value.strip()
    match = re.search(r"(-?\d+(?:\.\d+)?)", value_clean)
    if not match:
        return None, None
        
    temp_val = float(match.group(1))

    # prefer the explicit degree forms; fall back to a bare C, else default to F
    if "°C" in value_clean:
        return temp_val, "C"
    if "°F" in value_clean:
        return temp_val, "F"
    if "C" in value_clean and "F" not in value_clean:
        return temp_val, "C"
    return temp_val, "F"

def parse_percentage(value: str) -> float | None:
    if pd.isna(value) or not isinstance(value, str):
        return None
        
    match = re.search(r"(\d+(?:\.\d+)?)", value.strip())
    return float(match.group(1)) if match else None

def parse_speed(value: str) -> Tuple[float | None, str | None]:
    if pd.isna(value) or not isinstance(value, str):
        return None, None
        
    value_clean = value.strip().lower()
    if "calm" in value_clean or "no wind" in value_clean:
        return 0.0, "mph"

    match = re.search(r"(\d+(?:\.\d+)?)", value_clean)
    if not match:
        return None, None
        
    speed_val = float(match.group(1))
    
    unit = None
    if "mph" in value_clean:
        unit = "mph"
    elif "km/h" in value_clean or "kph" in value_clean:
        unit = "kph"
    elif "m/s" in value_clean:
        unit = "m/s"
    elif "knot" in value_clean or "kt" in value_clean:
        unit = "knots"
        
    return speed_val, unit

def parse_pressure(value: str) -> Tuple[float | None, str | None]:
    if pd.isna(value) or not isinstance(value, str):
        return None, None
        
    value_clean = value.strip()
    match = re.search(r"^(\d+(?:\.\d+)?)", value_clean)
    if not match:
        return None, None
        
    pressure_val = float(match.group(1))
    
    if "Hg" in value_clean or '"Hg' in value_clean:
        return pressure_val, "inHg"
    else:
        return pressure_val, "mb"

def normalize_text(value: str) -> str | None:
    if pd.isna(value) or not isinstance(value, str):
        return None
    val_clean = value.strip()
    return val_clean if val_clean != "" else None

def categorize_condition(value: str) -> str:
    if pd.isna(value) or not isinstance(value, str):
        return "Unknown"
        
    val_lower = value.strip().lower()
    
    if any(word in val_lower for word in ["thunderstorm", "storm", "squall", "tornado"]):
        return "Storm"
    elif any(word in val_lower for word in ["snow", "sleet", "hail", "blizzard", "ice"]):
        return "Snow"
    elif any(word in val_lower for word in ["rain", "shower", "drizzle", "wet"]):
        return "Rain"
    elif any(word in val_lower for word in ["fog", "mist", "haze", "smoke", "dust"]):
        return "Fog"
    elif any(word in val_lower for word in ["cloud", "overcast", "grey", "passing"]):
        return "Cloudy"
    elif any(word in val_lower for word in ["sunny", "clear", "fair", "fine"]):
        return "Clear"
    else:
        return "Other"

def extract_country_from_url(url: str) -> str | None:
    if pd.isna(url) or not isinstance(url, str):
        return None
        
    match = re.search(r"/weather/([^/]+)/", url)
    if not match:
        return None
        
    country_slug = match.group(1).replace("-", " ").title()
    
    slug_mappings = {
        "Usa": "USA",
        "Uk": "UK",
        "Uae": "UAE",
    }
    return slug_mappings.get(country_slug, country_slug)

@log_execution_time("weather_capstone.cleaner")
def clean_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    stats = {}
    stats["raw_rows"] = len(df)
    
    if hasattr(df, "map"):
        df = df.map(lambda x: x.strip() if isinstance(x, str) else x)
    else:
        df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)

    df = df.replace(r"^\s*$", None, regex=True)
    
    stats["missing_before"] = df.isna().sum().to_dict()

    initial_len = len(df)
    df = df.drop_duplicates()
    stats["removed_duplicates"] = initial_len - len(df)

    if "source_url" in df.columns:
        df["country"] = df.apply(
            lambda row: extract_country_from_url(row["source_url"]) or row["country"],
            axis=1
        )

    df["city"] = df["city"].apply(normalize_text)
    df["country"] = df["country"].apply(normalize_text)
    df["condition"] = df["condition"].apply(normalize_text)

    temp_parsed = df["temperature_raw"].apply(parse_temperature)
    df["temperature_val"] = temp_parsed.apply(lambda x: x[0])
    df["temperature_unit"] = temp_parsed.apply(lambda x: x[1])

    def get_temp_c(row: pd.Series) -> float | None:
        val, unit = row["temperature_val"], row["temperature_unit"]
        return None if pd.isna(val) else ((val - 32) * 5 / 9 if unit == "F" else val)

    def get_temp_f(row: pd.Series) -> float | None:
        val, unit = row["temperature_val"], row["temperature_unit"]
        return None if pd.isna(val) else (val * 9 / 5 + 32 if unit == "C" else val)

    df["temperature_c"] = df.apply(get_temp_c, axis=1).round(1)
    df["temperature_f"] = df.apply(get_temp_f, axis=1).round(1)

    df["humidity_pct"] = df["humidity_raw"].apply(parse_percentage)

    wind_parsed = df["wind_raw"].apply(parse_speed)
    def convert_wind_speed(row: Tuple[float | None, str | None]) -> float | None:
        val, unit = row
        if pd.isna(val):
            return None
        if unit == "mph":
            return val * 1.60934
        elif unit == "m/s":
            return val * 3.6
        elif unit == "knots":
            return val * 1.852
        return val

    df["wind_speed_kph"] = wind_parsed.apply(convert_wind_speed).round(1)

    pressure_parsed = df["pressure_raw"].apply(parse_pressure)
    def convert_pressure(row: Tuple[float | None, str | None]) -> float | None:
        val, unit = row
        if pd.isna(val):
            return None
        return val * 33.8639 if unit == "inHg" else val

    df["pressure_mb"] = pressure_parsed.apply(convert_pressure).round(1)

    df["local_time_raw"] = df["local_time_raw"].apply(normalize_text)

    df["condition_category"] = df["condition"].apply(categorize_condition)
    df["city_country"] = df.apply(
        lambda r: f"{r['city']}, {r['country']}" if r['city'] and r['country'] else r['city'] or r['country'],
        axis=1
    )
    
    df["scraped_date"] = df["scraped_at"].apply(
        lambda x: x.split(" ")[0] if isinstance(x, str) and " " in x else x
    )

    df["is_extreme_heat"] = df["temperature_c"].apply(lambda x: True if x is not None and x > 35 else False)
    df["is_cold"] = df["temperature_c"].apply(lambda x: True if x is not None and x < 5 else False)

    def get_comfort_band(tc: float | None) -> str:
        if pd.isna(tc):
            return "Unknown"
        if tc >= 32:
            return "Very Hot"
        if tc >= 24:
            return "Warm"
        if tc >= 18:
            return "Comfortable"
        if tc >= 10:
            return "Cool"
        return "Cold"

    df["comfort_band"] = df["temperature_c"].apply(get_comfort_band)

    df = df.drop(columns=["temperature_val", "temperature_unit"], errors="ignore")

    initial_len = len(df)
    df = df.dropna(subset=["city", "temperature_c"])
    stats["removed_malformed"] = initial_len - len(df)

    stats["cleaned_rows"] = len(df)
    stats["missing_after"] = df.isna().sum().to_dict()

    return df, stats
