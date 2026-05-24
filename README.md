# Weather Around The World Insight Dashboard

A clean Python project that scrapes global weather observations using Selenium, structures and cleans the data using Pandas, and saves the outputs for analysis.

## Setup Instructions

1. **Create and activate a virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # macOS/Linux
   # .venv\Scripts\activate    # Windows
   ```

2. **Install the dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up configurations:**
   ```bash
   cp .env.example .env
   ```

---

## How to Run

Set your Python path so the scripts can find the modules:
```bash
export PYTHONPATH=src
```

### 1. Run the Scraper
Collect weather records from TimeAndDate. This saves raw data to `data/raw/`:
```bash
python scripts/scrape_weather.py --limit 5
```

### 2. Run the Cleaner
Process the raw data into a clean format and save it to `data/processed/`:
```bash
python scripts/clean_weather.py --input data/raw/weather_raw_<filename>.csv
```
*(Replace `<filename>` with the actual generated filename).*