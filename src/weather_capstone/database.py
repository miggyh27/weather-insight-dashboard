import sqlite3
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from contextlib import contextmanager

from weather_capstone.config import DEFAULT_SQLITE_PATH

logger = logging.getLogger(__name__)

TABLE_NAME = "weather_observations"


@contextmanager
def get_connection(db_path: Optional[Path] = None):
    """Context manager for database connections."""
    db_path = db_path or DEFAULT_SQLITE_PATH
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def create_table(conn: sqlite3.Connection) -> None:
    """Create the weather_observations table if it doesn't exist."""
    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            city TEXT NOT NULL,
            country TEXT NOT NULL,
            temperature_celsius REAL,
            condition TEXT,
            humidity_percent REAL,
            wind_speed_kmh REAL,
            pressure_hpa REAL,
            local_time TEXT,
            scraped_at TEXT NOT NULL,
            source_url TEXT NOT NULL,
            UNIQUE(city, country, scraped_at)
        )
    """)
    conn.commit()
    logger.info(f"Table {TABLE_NAME} created or already exists")


def insert_record(conn: sqlite3.Connection, record: Dict[str, Any]) -> bool:
    """Insert a single weather record, handling duplicates."""
    try:
        conn.execute(f"""
            INSERT INTO {TABLE_NAME} (
                city, country, temperature_celsius, condition, humidity_percent,
                wind_speed_kmh, pressure_hpa, local_time, scraped_at, source_url
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            record.get("city"),
            record.get("country"),
            record.get("temperature_celsius"),
            record.get("condition"),
            record.get("humidity_percent"),
            record.get("wind_speed_kmh"),
            record.get("pressure_hpa"),
            record.get("local_time"),
            record.get("scraped_at"),
            record.get("source_url")
        ))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        logger.debug(f"Duplicate record skipped: {record.get('city')}, {record.get('country')}, {record.get('scraped_at')}")
        return False


def insert_records(conn: sqlite3.Connection, records: List[Dict[str, Any]]) -> Tuple[int, int]:
    """Insert multiple records, returning (inserted_count, duplicate_count)."""
    inserted = 0
    duplicates = 0
    
    for record in records:
        if insert_record(conn, record):
            inserted += 1
        else:
            duplicates += 1
    
    logger.info(f"Inserted {inserted} records, skipped {duplicates} duplicates")
    return inserted, duplicates


def get_summary(conn: sqlite3.Connection) -> Dict[str, Any]:
    """Get summary statistics from the database."""
    total = conn.execute(f"SELECT COUNT(*) FROM {TABLE_NAME}").fetchone()[0]
    
    countries = conn.execute(f"SELECT COUNT(DISTINCT country) FROM {TABLE_NAME}").fetchone()[0]
    
    cities = conn.execute(f"SELECT COUNT(DISTINCT city) FROM {TABLE_NAME}").fetchone()[0]
    
    avg_temp = conn.execute(f"SELECT AVG(temperature_celsius) FROM {TABLE_NAME} WHERE temperature_celsius IS NOT NULL").fetchone()[0]
    
    conditions = conn.execute(f"SELECT COUNT(DISTINCT condition) FROM {TABLE_NAME} WHERE condition IS NOT NULL").fetchone()[0]
    
    return {
        "total_records": total,
        "countries": countries,
        "cities": cities,
        "avg_temperature_celsius": round(avg_temp, 2) if avg_temp else None,
        "unique_conditions": conditions
    }


def get_countries(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    """Get list of countries with record counts."""
    rows = conn.execute(f"""
        SELECT country, COUNT(*) as count, AVG(temperature_celsius) as avg_temp
        FROM {TABLE_NAME}
        GROUP BY country
        ORDER BY count DESC
    """).fetchall()
    
    return [{"country": row["country"], "count": row["count"], "avg_temp": round(row["avg_temp"], 2) if row["avg_temp"] else None} for row in rows]


def get_extremes(conn: sqlite3.Connection) -> Dict[str, Any]:
    """Get temperature extremes."""
    hottest = conn.execute(f"""
        SELECT city, country, temperature_celsius, scraped_at
        FROM {TABLE_NAME}
        WHERE temperature_celsius IS NOT NULL
        ORDER BY temperature_celsius DESC
        LIMIT 1
    """).fetchone()
    
    coldest = conn.execute(f"""
        SELECT city, country, temperature_celsius, scraped_at
        FROM {TABLE_NAME}
        WHERE temperature_celsius IS NOT NULL
        ORDER BY temperature_celsius ASC
        LIMIT 1
    """).fetchone()
    
    return {
        "hottest": {
            "city": hottest["city"] if hottest else None,
            "country": hottest["country"] if hottest else None,
            "temperature_celsius": hottest["temperature_celsius"] if hottest else None,
            "scraped_at": hottest["scraped_at"] if hottest else None
        },
        "coldest": {
            "city": coldest["city"] if coldest else None,
            "country": coldest["country"] if coldest else None,
            "temperature_celsius": coldest["temperature_celsius"] if coldest else None,
            "scraped_at": coldest["scraped_at"] if coldest else None
        }
    }


def get_conditions(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    """Get weather condition frequencies."""
    rows = conn.execute(f"""
        SELECT condition, COUNT(*) as count
        FROM {TABLE_NAME}
        WHERE condition IS NOT NULL
        GROUP BY condition
        ORDER BY count DESC
    """).fetchall()
    
    return [{"condition": row["condition"], "count": row["count"]} for row in rows]


def get_by_country(conn: sqlite3.Connection, country: str) -> List[Dict[str, Any]]:
    """Get all records for a specific country."""
    rows = conn.execute(f"""
        SELECT city, temperature_celsius, condition, humidity_percent, wind_speed_kmh, local_time
        FROM {TABLE_NAME}
        WHERE country = ?
        ORDER BY city
    """, (country,)).fetchall()
    
    return [{
        "city": row["city"],
        "temperature_celsius": row["temperature_celsius"],
        "condition": row["condition"],
        "humidity_percent": row["humidity_percent"],
        "wind_speed_kmh": row["wind_speed_kmh"],
        "local_time": row["local_time"]
    } for row in rows]


def initialize_database(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """Initialize database and create table."""
    with get_connection(db_path) as conn:
        create_table(conn)
        return conn
