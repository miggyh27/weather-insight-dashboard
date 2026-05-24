import pandas as pd
import pytest

from weather_capstone.cleaner import (
    parse_temperature,
    parse_percentage,
    parse_speed,
    parse_pressure,
    normalize_text,
    categorize_condition,
    extract_country_from_url,
    clean_data,
)


def test_parse_temperature_celsius():
    """Test temperature parsing for Celsius."""
    temp, unit = parse_temperature("25°C")
    assert temp == 25.0
    assert unit == "C"


def test_parse_temperature_fahrenheit():
    """Test temperature parsing for Fahrenheit."""
    temp, unit = parse_temperature("77°F")
    assert temp == 77.0
    assert unit == "F"


def test_parse_temperature_no_unit():
    """Test temperature parsing without unit defaults to F."""
    temp, unit = parse_temperature("72")
    assert temp == 72.0
    assert unit == "F"


def test_parse_temperature_invalid():
    """Test temperature parsing with invalid input."""
    temp, unit = parse_temperature("invalid")
    assert temp is None
    assert unit is None


def test_parse_percentage():
    """Test percentage parsing."""
    result = parse_percentage("65%")
    assert result == 65.0


def test_parse_percentage_no_symbol():
    """Test percentage parsing without symbol."""
    result = parse_percentage("65")
    assert result == 65.0


def test_parse_percentage_invalid():
    """Test percentage parsing with invalid input."""
    result = parse_percentage("invalid")
    assert result is None


def test_parse_speed_mph():
    """Test speed parsing for mph."""
    speed, unit = parse_speed("10 mph")
    assert speed == 10.0
    assert unit == "mph"


def test_parse_speed_kph():
    """Test speed parsing for km/h."""
    speed, unit = parse_speed("16 km/h")
    assert speed == 16.0
    assert unit == "kph"


def test_parse_speed_calm():
    """Test speed parsing for calm conditions."""
    speed, unit = parse_speed("Calm")
    assert speed == 0.0
    assert unit == "mph"


def test_parse_speed_invalid():
    """Test speed parsing with invalid input."""
    speed, unit = parse_speed("invalid")
    assert speed is None
    assert unit is None


def test_parse_pressure_inhg():
    """Test pressure parsing for inHg."""
    pressure, unit = parse_pressure("29.92 inHg")
    assert pressure == 29.92
    assert unit == "inHg"


def test_parse_pressure_mb():
    """Test pressure parsing for mb."""
    pressure, unit = parse_pressure("1013 mb")
    assert pressure == 1013.0
    assert unit == "mb"


def test_parse_pressure_invalid():
    """Test pressure parsing with invalid input."""
    pressure, unit = parse_pressure("invalid")
    assert pressure is None
    assert unit is None


def test_normalize_text():
    """Test text normalization."""
    result = normalize_text("  test  ")
    assert result == "test"


def test_normalize_text_empty():
    """Test text normalization with empty string."""
    result = normalize_text("   ")
    assert result is None


def test_normalize_text_none():
    """Test text normalization with None."""
    result = normalize_text(None)
    assert result is None


def test_categorize_condition_rain():
    """Test condition categorization for rain."""
    result = categorize_condition("Light rain")
    assert result == "Rain"


def test_categorize_condition_clear():
    """Test condition categorization for clear."""
    result = categorize_condition("Sunny")
    assert result == "Clear"


def test_categorize_condition_cloudy():
    """Test condition categorization for cloudy."""
    result = categorize_condition("Overcast")
    assert result == "Cloudy"


def test_categorize_condition_storm():
    """Test condition categorization for storm."""
    result = categorize_condition("Thunderstorm")
    assert result == "Storm"


def test_categorize_condition_fog():
    """Test condition categorization for fog."""
    result = categorize_condition("Mist")
    assert result == "Fog"


def test_categorize_condition_snow():
    """Test condition categorization for snow."""
    result = categorize_condition("Heavy snow")
    assert result == "Snow"


def test_categorize_condition_unknown():
    """Test condition categorization for unknown."""
    result = categorize_condition("Unknown condition")
    assert result == "Other"


def test_extract_country_from_url():
    """Test country extraction from URL."""
    result = extract_country_from_url("https://www.timeanddate.com/weather/japan/tokyo")
    assert result == "Japan"


def test_extract_country_from_url_with_dash():
    """Test country extraction from URL with dashes."""
    result = extract_country_from_url("https://www.timeanddate.com/weather/united-kingdom/london")
    assert result == "United Kingdom"


def test_extract_country_from_url_usa():
    """Test country extraction mapping for USA."""
    result = extract_country_from_url("https://www.timeanddate.com/weather/usa/new-york")
    assert result == "USA"


def test_extract_country_from_url_invalid():
    """Test country extraction with invalid URL."""
    result = extract_country_from_url("invalid-url")
    assert result is None


def test_clean_data_basic():
    """Test basic data cleaning."""
    df = pd.DataFrame({
        "city": ["  Tokyo  ", "London"],
        "country": ["Japan", "UK"],
        "temperature_raw": ["25°C", "15°C"],
        "condition": ["Clear", "Rain"],
        "humidity_raw": ["60%", "80%"],
        "wind_raw": ["10 km/h", "20 km/h"],
        "pressure_raw": ["1013 mb", "1000 mb"],
        "local_time_raw": ["12:00", "09:00"],
        "scraped_at": ["2024-01-01 12:00:00", "2024-01-01 09:00:00"],
        "source_url": [
            "https://www.timeanddate.com/weather/japan/tokyo",
            "https://www.timeanddate.com/weather/uk/london"
        ]
    })
    
    cleaned_df, stats = clean_data(df)
    
    assert stats["raw_rows"] == 2
    assert stats["cleaned_rows"] == 2
    assert stats["removed_duplicates"] == 0
    assert cleaned_df["city"].iloc[0] == "Tokyo"
    assert cleaned_df["temperature_c"].iloc[0] == 25.0
    assert cleaned_df["humidity_pct"].iloc[0] == 60.0


def test_clean_data_duplicate_removal():
    """Test duplicate row removal."""
    df = pd.DataFrame({
        "city": ["Tokyo", "Tokyo"],
        "country": ["Japan", "Japan"],
        "temperature_raw": ["25°C", "25°C"],
        "condition": ["Clear", "Clear"],
        "humidity_raw": ["60%", "60%"],
        "wind_raw": ["10 km/h", "10 km/h"],
        "pressure_raw": ["1013 mb", "1013 mb"],
        "local_time_raw": ["12:00", "12:00"],
        "scraped_at": ["2024-01-01 12:00:00", "2024-01-01 12:00:00"],
        "source_url": [
            "https://www.timeanddate.com/weather/japan/tokyo",
            "https://www.timeanddate.com/weather/japan/tokyo"
        ]
    })
    
    cleaned_df, stats = clean_data(df)
    
    assert stats["raw_rows"] == 2
    assert stats["removed_duplicates"] == 1
    assert stats["cleaned_rows"] == 1


def test_clean_data_malformed_removal():
    """Test removal of malformed rows (missing city or temperature)."""
    df = pd.DataFrame({
        "city": ["Tokyo", None, "London"],
        "country": ["Japan", "UK", "UK"],
        "temperature_raw": ["25°C", "15°C", None],
        "condition": ["Clear", "Rain", "Cloudy"],
        "humidity_raw": ["60%", "80%", "75%"],
        "wind_raw": ["10 km/h", "20 km/h", "15 km/h"],
        "pressure_raw": ["1013 mb", "1000 mb", "1005 mb"],
        "local_time_raw": ["12:00", "09:00", "10:00"],
        "scraped_at": ["2024-01-01 12:00:00", "2024-01-01 09:00:00", "2024-01-01 10:00:00"],
        "source_url": [
            "https://www.timeanddate.com/weather/japan/tokyo",
            "https://www.timeanddate.com/weather/uk/london",
            "https://www.timeanddate.com/weather/france/paris"
        ]
    })
    
    cleaned_df, stats = clean_data(df)
    
    assert stats["raw_rows"] == 3
    assert stats["removed_malformed"] == 2
    assert stats["cleaned_rows"] == 1


def test_clean_data_fahrenheit_conversion():
    """Test Fahrenheit to Celsius conversion."""
    df = pd.DataFrame({
        "city": ["New York"],
        "country": ["USA"],
        "temperature_raw": ["77°F"],
        "condition": ["Clear"],
        "humidity_raw": ["60%"],
        "wind_raw": ["10 mph"],
        "pressure_raw": ["29.92 inHg"],
        "local_time_raw": ["12:00"],
        "scraped_at": ["2024-01-01 12:00:00"],
        "source_url": ["https://www.timeanddate.com/weather/usa/new-york"]
    })
    
    cleaned_df, stats = clean_data(df)
    
    assert cleaned_df["temperature_c"].iloc[0] == 25.0
    assert cleaned_df["temperature_f"].iloc[0] == 77.0
    assert cleaned_df["wind_speed_kph"].iloc[0] == 16.1
    assert cleaned_df["pressure_mb"].iloc[0] == 1013.2
