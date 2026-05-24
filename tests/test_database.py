import sqlite3
import tempfile
from pathlib import Path

import pytest

from weather_capstone.database import (
    create_table,
    insert_record,
    insert_records,
    get_summary,
    get_countries,
    get_extremes,
    get_conditions,
    get_by_country,
    get_connection,
)


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False) as f:
        db_path = Path(f.name)
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    create_table(conn)
    yield conn, db_path
    conn.close()
    db_path.unlink()


def test_create_table(temp_db):
    """Test table creation."""
    conn, _ = temp_db
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    assert "weather_observations" in tables


def test_insert_record(temp_db):
    """Test single record insertion."""
    conn, _ = temp_db
    
    record = {
        "city": "Tokyo",
        "country": "Japan",
        "temperature_celsius": 25.5,
        "condition": "Clear",
        "humidity_percent": 60,
        "wind_speed_kmh": 10.0,
        "pressure_hpa": 1013,
        "local_time": "12:00",
        "scraped_at": "2024-01-01 12:00:00",
        "source_url": "https://example.com"
    }
    
    result = insert_record(conn, record)
    assert result is True
    
    cursor = conn.execute("SELECT COUNT(*) FROM weather_observations")
    count = cursor.fetchone()[0]
    assert count == 1


def test_insert_duplicate(temp_db):
    """Test duplicate record handling."""
    conn, _ = temp_db
    
    record = {
        "city": "Tokyo",
        "country": "Japan",
        "temperature_celsius": 25.5,
        "condition": "Clear",
        "humidity_percent": 60,
        "wind_speed_kmh": 10.0,
        "pressure_hpa": 1013,
        "local_time": "12:00",
        "scraped_at": "2024-01-01 12:00:00",
        "source_url": "https://example.com"
    }
    
    insert_record(conn, record)
    result = insert_record(conn, record)
    assert result is False
    
    cursor = conn.execute("SELECT COUNT(*) FROM weather_observations")
    count = cursor.fetchone()[0]
    assert count == 1


def test_insert_records(temp_db):
    """Test bulk record insertion."""
    conn, _ = temp_db
    
    records = [
        {
            "city": "Tokyo",
            "country": "Japan",
            "temperature_celsius": 25.5,
            "condition": "Clear",
            "humidity_percent": 60,
            "wind_speed_kmh": 10.0,
            "pressure_hpa": 1013,
            "local_time": "12:00",
            "scraped_at": "2024-01-01 12:00:00",
            "source_url": "https://example.com"
        },
        {
            "city": "London",
            "country": "UK",
            "temperature_celsius": 15.0,
            "condition": "Rain",
            "humidity_percent": 80,
            "wind_speed_kmh": 20.0,
            "pressure_hpa": 1000,
            "local_time": "09:00",
            "scraped_at": "2024-01-01 09:00:00",
            "source_url": "https://example.com"
        }
    ]
    
    inserted, duplicates = insert_records(conn, records)
    assert inserted == 2
    assert duplicates == 0


def test_get_summary(temp_db):
    """Test summary statistics."""
    conn, _ = temp_db
    
    records = [
        {
            "city": "Tokyo",
            "country": "Japan",
            "temperature_celsius": 25.5,
            "condition": "Clear",
            "humidity_percent": 60,
            "wind_speed_kmh": 10.0,
            "pressure_hpa": 1013,
            "local_time": "12:00",
            "scraped_at": "2024-01-01 12:00:00",
            "source_url": "https://example.com"
        },
        {
            "city": "London",
            "country": "UK",
            "temperature_celsius": 15.0,
            "condition": "Rain",
            "humidity_percent": 80,
            "wind_speed_kmh": 20.0,
            "pressure_hpa": 1000,
            "local_time": "09:00",
            "scraped_at": "2024-01-01 09:00:00",
            "source_url": "https://example.com"
        }
    ]
    
    insert_records(conn, records)
    summary = get_summary(conn)
    
    assert summary["total_records"] == 2
    assert summary["countries"] == 2
    assert summary["cities"] == 2
    assert summary["avg_temperature_celsius"] == 20.25
    assert summary["unique_conditions"] == 2


def test_get_countries(temp_db):
    """Test country listing."""
    conn, _ = temp_db
    
    records = [
        {
            "city": "Tokyo",
            "country": "Japan",
            "temperature_celsius": 25.5,
            "condition": "Clear",
            "humidity_percent": 60,
            "wind_speed_kmh": 10.0,
            "pressure_hpa": 1013,
            "local_time": "12:00",
            "scraped_at": "2024-01-01 12:00:00",
            "source_url": "https://example.com"
        },
        {
            "city": "Osaka",
            "country": "Japan",
            "temperature_celsius": 24.0,
            "condition": "Cloudy",
            "humidity_percent": 65,
            "wind_speed_kmh": 12.0,
            "pressure_hpa": 1012,
            "local_time": "12:30",
            "scraped_at": "2024-01-01 12:30:00",
            "source_url": "https://example.com"
        }
    ]
    
    insert_records(conn, records)
    countries = get_countries(conn)
    
    assert len(countries) == 1
    assert countries[0]["country"] == "Japan"
    assert countries[0]["count"] == 2


def test_get_extremes(temp_db):
    """Test temperature extremes."""
    conn, _ = temp_db
    
    records = [
        {
            "city": "Tokyo",
            "country": "Japan",
            "temperature_celsius": 35.0,
            "condition": "Clear",
            "humidity_percent": 60,
            "wind_speed_kmh": 10.0,
            "pressure_hpa": 1013,
            "local_time": "12:00",
            "scraped_at": "2024-01-01 12:00:00",
            "source_url": "https://example.com"
        },
        {
            "city": "London",
            "country": "UK",
            "temperature_celsius": 5.0,
            "condition": "Rain",
            "humidity_percent": 80,
            "wind_speed_kmh": 20.0,
            "pressure_hpa": 1000,
            "local_time": "09:00",
            "scraped_at": "2024-01-01 09:00:00",
            "source_url": "https://example.com"
        }
    ]
    
    insert_records(conn, records)
    extremes = get_extremes(conn)
    
    assert extremes["hottest"]["city"] == "Tokyo"
    assert extremes["hottest"]["temperature_celsius"] == 35.0
    assert extremes["coldest"]["city"] == "London"
    assert extremes["coldest"]["temperature_celsius"] == 5.0


def test_get_conditions(temp_db):
    """Test condition frequencies."""
    conn, _ = temp_db
    
    records = [
        {
            "city": "Tokyo",
            "country": "Japan",
            "temperature_celsius": 25.5,
            "condition": "Clear",
            "humidity_percent": 60,
            "wind_speed_kmh": 10.0,
            "pressure_hpa": 1013,
            "local_time": "12:00",
            "scraped_at": "2024-01-01 12:00:00",
            "source_url": "https://example.com"
        },
        {
            "city": "London",
            "country": "UK",
            "temperature_celsius": 15.0,
            "condition": "Rain",
            "humidity_percent": 80,
            "wind_speed_kmh": 20.0,
            "pressure_hpa": 1000,
            "local_time": "09:00",
            "scraped_at": "2024-01-01 09:00:00",
            "source_url": "https://example.com"
        },
        {
            "city": "Paris",
            "country": "France",
            "temperature_celsius": 18.0,
            "condition": "Rain",
            "humidity_percent": 75,
            "wind_speed_kmh": 15.0,
            "pressure_hpa": 1005,
            "local_time": "10:00",
            "scraped_at": "2024-01-01 10:00:00",
            "source_url": "https://example.com"
        }
    ]
    
    insert_records(conn, records)
    conditions = get_conditions(conn)
    
    assert len(conditions) == 2
    rain_condition = next(c for c in conditions if c["condition"] == "Rain")
    assert rain_condition["count"] == 2


def test_get_by_country(temp_db):
    """Test country-specific queries."""
    conn, _ = temp_db
    
    records = [
        {
            "city": "Tokyo",
            "country": "Japan",
            "temperature_celsius": 25.5,
            "condition": "Clear",
            "humidity_percent": 60,
            "wind_speed_kmh": 10.0,
            "pressure_hpa": 1013,
            "local_time": "12:00",
            "scraped_at": "2024-01-01 12:00:00",
            "source_url": "https://example.com"
        },
        {
            "city": "London",
            "country": "UK",
            "temperature_celsius": 15.0,
            "condition": "Rain",
            "humidity_percent": 80,
            "wind_speed_kmh": 20.0,
            "pressure_hpa": 1000,
            "local_time": "09:00",
            "scraped_at": "2024-01-01 09:00:00",
            "source_url": "https://example.com"
        }
    ]
    
    insert_records(conn, records)
    japan_data = get_by_country(conn, "Japan")
    
    assert len(japan_data) == 1
    assert japan_data[0]["city"] == "Tokyo"
