import time
import os
from pathlib import Path
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from weather_capstone.scraper import build_driver

def main():
    print("Initializing Chrome WebDriver for screenshots...")
    driver = build_driver()
    try:
        url = "http://localhost:8501"
        print(f"Visiting {url}...")
        driver.get(url)
        
        print("Waiting for dashboard to render...")
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "stApp"))
        )
        time.sleep(5)  # Wait for charts/data to load fully
        
        screenshot_dir = Path("reports/screenshots")
        screenshot_dir.mkdir(parents=True, exist_ok=True)
        
        print("Capturing Tab 1: Overview & Map...")
        driver.save_screenshot(str(screenshot_dir / "dashboard_tab1_overview.png"))
        
        tabs = driver.find_elements(By.CSS_SELECTOR, "button[data-baseweb='tab']")
        print(f"Found {len(tabs)} tabs.")
        tab_names = ["overview", "temperature_analysis", "wind_humidity", "conditions", "data_explorer"]
        for idx, tab in enumerate(tabs):
            if idx == 0:
                continue
            name = tab_names[idx] if idx < len(tab_names) else f"tab{idx+1}"
            print(f"Clicking Tab {idx+1} ({tab.text})...")
            driver.execute_script("arguments[0].click();", tab)
            time.sleep(4)  # Wait for animations and charts to render
            print(f"Capturing Tab {idx+1}...")
            driver.save_screenshot(str(screenshot_dir / f"dashboard_tab{idx+1}_{name}.png"))
            
        print("All screenshots successfully captured and saved in reports/screenshots/")
    except Exception as e:
        print(f"Error capturing screenshots: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
