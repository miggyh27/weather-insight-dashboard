#!/usr/bin/env python3
import argparse
import logging
import sys
from pathlib import Path

from weather_capstone.database import (
    get_connection,
    get_summary,
    get_countries,
    get_extremes,
    get_conditions,
    get_by_country,
)
from weather_capstone.config import DEFAULT_SQLITE_PATH
from weather_capstone.logging_config import configure_logging

logger = logging.getLogger(__name__)


def print_summary(db_path: Path) -> None:
    """Print summary statistics."""
    with get_connection(db_path) as conn:
        summary = get_summary(conn)
    
    print("\n=== Weather Database Summary ===")
    print(f"Total records: {summary['total_records']}")
    print(f"Countries: {summary['countries']}")
    print(f"Cities: {summary['cities']}")
    print(f"Average temperature: {summary['avg_temperature_celsius']}°C" if summary['avg_temperature_celsius'] is not None else "Average temperature: N/A")
    print(f"Unique conditions: {summary['unique_conditions']}")
    print()


def print_countries(db_path: Path) -> None:
    """Print countries with record counts."""
    with get_connection(db_path) as conn:
        countries = get_countries(conn)
    
    print("\n=== Countries ===")
    print(f"{'Country':<30} {'Records':<10} {'Avg Temp (°C)':<15}")
    print("-" * 55)
    for c in countries:
        temp_str = f"{c['avg_temp']:.1f}" if c['avg_temp'] is not None else "N/A"
        print(f"{c['country']:<30} {c['count']:<10} {temp_str:<15}")
    print()


def print_extremes(db_path: Path) -> None:
    """Print temperature extremes."""
    with get_connection(db_path) as conn:
        extremes = get_extremes(conn)
    
    print("\n=== Temperature Extremes ===")
    
    hottest = extremes['hottest']
    if hottest['city']:
        print(f"Hottest: {hottest['city']}, {hottest['country']} - {hottest['temperature_celsius']}°C")
        print(f"  Recorded at: {hottest['scraped_at']}")
    else:
        print("Hottest: No data")
    
    coldest = extremes['coldest']
    if coldest['city']:
        print(f"Coldest: {coldest['city']}, {coldest['country']} - {coldest['temperature_celsius']}°C")
        print(f"  Recorded at: {coldest['scraped_at']}")
    else:
        print("Coldest: No data")
    print()


def print_conditions(db_path: Path) -> None:
    """Print weather condition frequencies."""
    with get_connection(db_path) as conn:
        conditions = get_conditions(conn)
    
    print("\n=== Weather Conditions ===")
    print(f"{'Condition':<30} {'Count':<10}")
    print("-" * 40)
    for c in conditions:
        print(f"{c['condition']:<30} {c['count']:<10}")
    print()


def print_country_data(db_path: Path, country: str) -> None:
    """Print data for a specific country."""
    with get_connection(db_path) as conn:
        data = get_by_country(conn, country)
    
    if not data:
        print(f"\nNo records found for country: {country}\n")
        return
    
    print(f"\n=== Weather Data for {country} ===")
    print(f"{'City':<25} {'Temp (°C)':<12} {'Condition':<20} {'Humidity (%)':<12} {'Wind (km/h)':<12}")
    print("-" * 81)
    for row in data:
        temp_str = f"{row['temperature_celsius']:.1f}" if row['temperature_celsius'] is not None else "N/A"
        humidity_str = f"{row['humidity_percent']:.0f}" if row['humidity_percent'] is not None else "N/A"
        wind_str = f"{row['wind_speed_kmh']:.1f}" if row['wind_speed_kmh'] is not None else "N/A"
        print(f"{row['city']:<25} {temp_str:<12} {row['condition']:<20} {humidity_str:<12} {wind_str:<12}")
    print()


def main():
    parser = argparse.ArgumentParser(description="Query weather database from command line")
    parser.add_argument("--db", type=Path, default=DEFAULT_SQLITE_PATH, help="Path to SQLite database file")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    subparsers.add_parser("summary", help="Show database summary")
    subparsers.add_parser("countries", help="List countries with record counts")
    subparsers.add_parser("extremes", help="Show temperature extremes")
    subparsers.add_parser("conditions", help="Show weather condition frequencies")
    
    country_parser = subparsers.add_parser("country", help="Show data for a specific country")
    country_parser.add_argument("name", help="Country name")
    
    args = parser.parse_args()
    
    configure_logging(level=logging.INFO)
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    if not args.db.exists():
        logger.error(f"Database not found: {args.db}")
        print(f"Error: Database not found at {args.db}")
        print("Run load_database.py first to load data.")
        sys.exit(1)
    
    if args.command == "summary":
        print_summary(args.db)
    elif args.command == "countries":
        print_countries(args.db)
    elif args.command == "extremes":
        print_extremes(args.db)
    elif args.command == "conditions":
        print_conditions(args.db)
    elif args.command == "country":
        print_country_data(args.db, args.name)


if __name__ == "__main__":
    main()
