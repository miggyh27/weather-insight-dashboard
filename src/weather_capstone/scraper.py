import logging
import re
import time
from datetime import datetime
from typing import List, Dict, Any, Tuple
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

from weather_capstone.config import (
    WEATHER_SITE_URL,
    USER_AGENT,
    SCRAPE_DELAY_SECONDS,
    PAGE_LOAD_TIMEOUT_SECONDS,
    MAX_RETRIES,
)
from weather_capstone.models import WeatherRecord

logger = logging.getLogger(__name__)

def build_driver() -> webdriver.Chrome:
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(f"user-agent={USER_AGENT}")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT_SECONDS)
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"}
    )
    return driver

def wait_for_page_ready(driver: webdriver.Chrome, timeout: int = 15) -> bool:
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        return True
    except TimeoutException:
        logger.warning("Page ready state timeout.")
        return False

def safe_text(parent: Any, selector: Tuple[By, str]) -> str | None:
    try:
        element = parent.find_element(*selector)
        return element.text.strip()
    except NoSuchElementException:
        return None

def parse_weather_card(element: Any, source_url: str) -> WeatherRecord | None:
    return None

def discover_pages(driver: webdriver.Chrome) -> List[Tuple[str, str]]:
    logger.info("Accessing main weather index: %s", WEATHER_SITE_URL)
    retries = 0
    while retries < MAX_RETRIES:
        try:
            driver.get(WEATHER_SITE_URL)
            wait_for_page_ready(driver)
            break
        except WebDriverException as e:
            retries += 1
            logger.warning("Failed to load index page (attempt %d/%d): %s", retries, MAX_RETRIES, e)
            if retries >= MAX_RETRIES:
                logger.error("Max retries exceeded for main weather index load.")
                raise e
            time.sleep(SCRAPE_DELAY_SECONDS * 2)

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "tb-theme"))
        )
    except TimeoutException:
        logger.error("Main weather table was not loaded in time.")
        return []

    table = driver.find_element(By.CLASS_NAME, "tb-theme")
    rows = table.find_elements(By.TAG_NAME, "tr")
    
    discovered: List[Tuple[str, str]] = []
    url_pattern = re.compile(r"https://www\.timeanddate\.com/weather/([^/]+)/([^/]+)/?$")
    
    for row in rows:
        cells = row.find_elements(By.XPATH, "./td | ./th")
        if len(cells) != 12:
            continue
            
        for idx in range(3):
            city_cell = cells[idx * 4]
            links = city_cell.find_elements(By.TAG_NAME, "a")
            if not links:
                continue
                
            city_name = city_cell.text.strip().rstrip("*").strip()
            href = links[0].get_attribute("href")
            if href and url_pattern.match(href):
                discovered.append((city_name, href))
                
    seen = set()
    deduped = []
    for city, url in discovered:
        if url not in seen:
            seen.add(url)
            deduped.append((city, url))
            
    logger.info("Discovered %d unique city detail page links.", len(deduped))
    return deduped

def scrape_page(driver: webdriver.Chrome, url: str, fallback_city: str = "") -> WeatherRecord | None:
    logger.info("Scraping city details from: %s", url)
    retries = 0
    while retries < MAX_RETRIES:
        try:
            driver.get(url)
            wait_for_page_ready(driver)
            break
        except WebDriverException as e:
            retries += 1
            logger.warning("Attempt %d/%d failed for: %s", retries, MAX_RETRIES, url)
            if retries >= MAX_RETRIES:
                logger.warning("Skipping page after %d failed attempts: %s", MAX_RETRIES, url)
                return None
            time.sleep(SCRAPE_DELAY_SECONDS * 2)

    scraped_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    h1_text = safe_text(driver, (By.TAG_NAME, "h1"))
    city = fallback_city
    country = None

    if h1_text and "Weather in " in h1_text:
        parts = [p.strip() for p in h1_text.replace("Weather in ", "").split(",")]
        if len(parts) >= 2:
            city, country = parts[0], parts[1]
        elif len(parts) == 1:
            city = parts[0]

    if not country or not city:
        match = re.search(r"/weather/([^/]+)/([^/]+)/?$", url)
        if match:
            url_country = match.group(1).replace("-", " ").title()
            url_city = match.group(2).replace("-", " ").title()
            if not country:
                country = url_country
            if not city:
                city = url_city

    temperature_raw = None
    condition = None
    wind_raw = None
    humidity_raw = None
    pressure_raw = None
    visibility_raw = None
    local_time_raw = None

    try:
        qlook = driver.find_element(By.CLASS_NAME, "bk-focus__qlook")
        temperature_raw = safe_text(qlook, (By.CLASS_NAME, "h2"))
        
        condition_img = qlook.find_elements(By.ID, "cur-weather")
        if condition_img:
            condition = condition_img[0].get_attribute("title")
        else:
            condition = safe_text(qlook, (By.TAG_NAME, "p"))
            
        paragraphs = qlook.find_elements(By.TAG_NAME, "p")
        for p in paragraphs:
            text = p.text
            if "wind" in text.lower():
                for line in text.split("\n"):
                    if "wind" in line.lower():
                        wind_raw = re.sub(r"(?i)^wind:\s*", "", line).strip()
    except NoSuchElementException:
        logger.warning("Focus look section not found on details page: %s", url)

    try:
        table = driver.find_element(By.CLASS_NAME, "table--inner-borders-rows")
        rows = table.find_elements(By.TAG_NAME, "tr")
        for row in rows:
            th_text = safe_text(row, (By.TAG_NAME, "th"))
            td_text = safe_text(row, (By.TAG_NAME, "td"))
            if th_text and td_text:
                th_clean = th_text.replace(":", "").strip().lower()
                if "humidity" in th_clean:
                    humidity_raw = td_text
                elif "pressure" in th_clean:
                    pressure_raw = td_text
                elif "visibility" in th_clean:
                    visibility_raw = td_text
                elif "current time" in th_clean:
                    local_time_raw = td_text
    except NoSuchElementException:
        logger.warning("Facts table not found on details page: %s", url)

    if not local_time_raw:
        local_time_raw = safe_text(driver, (By.ID, "wtct"))

    return WeatherRecord(
        city=city,
        country=country,
        temperature_raw=temperature_raw,
        condition=condition,
        humidity_raw=humidity_raw,
        wind_raw=wind_raw,
        pressure_raw=pressure_raw,
        local_time_raw=local_time_raw,
        scraped_at=scraped_at,
        source_url=url
    )

def scrape_all(limit: int = 0) -> List[WeatherRecord]:
    driver = build_driver()
    records: List[WeatherRecord] = []
    try:
        cities = discover_pages(driver)
        if not cities:
            logger.error("No cities discovered. Scrape operation aborted.")
            return []

        if limit > 0:
            cities = cities[:limit]
            logger.info("Limit parameter set. Scraping restricted to %d cities.", limit)

        for idx, (city_name, url) in enumerate(cities):
            try:
                record = scrape_page(driver, url, fallback_city=city_name)
                if record:
                    records.append(record)
                    logger.info("Successfully scraped (%d/%d): %s, %s", idx + 1, len(cities), record.city, record.country)
                else:
                    logger.warning("Failed to parse city (%d/%d): %s", idx + 1, len(cities), city_name)
            except Exception as ex:
                logger.error("Unexpected error scraping city %s: %s", city_name, ex)
            
            time.sleep(SCRAPE_DELAY_SECONDS)

    finally:
        driver.quit()

    logger.info("Scrape cycle complete. Total records collected: %d", len(records))
    return records
