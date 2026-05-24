# Weather Around The World Insight Dashboard

This project collects weather data from around the world, cleans it up, and lets you explore it through a database and command-line tools.

## Quick Start (3 commands to get started)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

That's it! You're ready to run the project.

---

## What This Project Does

1. **Scrapes** weather data from TimeAndDate.com using a web browser
2. **Cleans** the data (fixes temperatures, standardizes units, removes duplicates)
3. **Saves** it to a database for easy querying
4. **Lets you explore** the data with simple commands

---

## Setup Instructions (Detailed)

### Step 1: Create a Virtual Environment
This creates a separate space for this project's dependencies so they don't conflict with other Python projects on your computer.

**On macOS/Linux:**
```bash
python -m venv .venv
source .venv/bin/activate
```

**On Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

You'll know it worked if you see `(.venv)` at the start of your command prompt.

### Step 2: Install the Project
This installs all the needed libraries and makes the commands available.

```bash
pip install -e .
```

### Step 3: (Optional) Configure Settings
Copy the example configuration file if you want to customize settings like scrape delays or timeouts.

```bash
cp .env.example .env
```

Most users can skip this step - the defaults work fine.

---

## Running the Project

### 1. Scrape Weather Data
This downloads weather data from the website. The `--limit 5` means it will only scrape 5 cities (good for testing). Remove `--limit 5` to scrape all available cities.

```bash
python scripts/scrape_weather.py --limit 5
```

This saves a file to `data/raw/` with a name like `weather_raw_20240101_120000.csv`.

### 2. Clean the Data
This processes the raw data: fixes temperature units, standardizes country names, removes duplicates, and calculates useful fields.

**Automatic (recommended):**
```bash
python scripts/clean_weather.py
```

**Manual (specify a specific file):**
```bash
python scripts/clean_weather.py --input data/raw/weather_raw_20240101_120000.csv
```

The script automatically finds the most recent raw file if you don't specify one.

This saves a cleaned file to `data/processed/` and creates a report at `reports/cleaning_summary.md`.

### 3. Load into Database
This loads the cleaned data into a SQLite database for fast querying.

**Automatic (recommended):**
```bash
python scripts/load_database.py
```

**Manual (specify a specific file):**
```bash
python scripts/load_database.py --input data/processed/weather_clean_20240101_120000.csv
```

The script automatically finds the most recent clean file if you don't specify one.

### 4. Query the Data
Now you can ask questions about your weather data:

```bash
# See overall statistics
python query_weather.py summary

# List all countries with their record counts
python query_weather.py countries

# See the hottest and coldest cities
python query_weather.py extremes

# See weather condition frequencies (rain, clear, cloudy, etc.)
python query_weather.py conditions

# See all cities in a specific country
python query_weather.py country "Japan"
```

---

## Troubleshooting

**"Command not found: python"**
- Try `python3` instead of `python`

**"ModuleNotFoundError: No module named 'weather_capstone'"**
- Make sure you ran `pip install -e .` after activating the virtual environment
- Make sure your virtual environment is activated (you should see `(.venv)` in your prompt)

**"selenium.common.exceptions.WebDriverException"**
- Make sure you have Chrome browser installed
- The scraper uses headless Chrome, so you don't need to see the browser window

**Tests are failing**
- Run `pip install -e .` to ensure the package is properly installed
- Run `pytest` to run the test suite

---

## Project Structure

```
weather-insight-dashboard/
├── data/
│   ├── raw/           # Raw scraped data goes here
│   ├── processed/     # Cleaned data goes here
│   └── database/      # SQLite database goes here
├── scripts/           # Command-line tools
│   ├── scrape_weather.py
│   ├── clean_weather.py
│   └── load_database.py
├── src/
│   └── weather_capstone/  # Core Python modules
├── tests/              # Test suite
├── query_weather.py    # CLI query tool
└── reports/            # Generated reports
```