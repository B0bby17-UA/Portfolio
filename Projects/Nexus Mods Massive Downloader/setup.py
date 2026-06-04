"""
Nexus Mods Login Setup

Opens a Chrome window with a separate profile for you to log into Nexus Mods.
Your login session is saved in the chrome_profile/ directory and reused by
download.py on subsequent runs.

Usage:
    1. Run `python setup.py`
    2. Log into your Nexus Mods account in the Chrome window
    3. Close Chrome when done
    4. Run `python download.py` to start downloading
"""

import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from pathlib import Path

CHROME_PROFILE = str(Path(__file__).parent / "chrome_profile")


def main():
    print("=" * 60)
    print("  Nexus Mods Login Setup")
    print("=" * 60)
    print()
    print("  A Chrome window will open with a separate profile.")
    print("  Log into your Nexus Mods account, then close Chrome.")
    print("  Your session will be saved for download.py to use.")
    print()

    options = uc.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument(f"--user-data-dir={CHROME_PROFILE}")

    print("[*] Starting Chrome...")
    driver = uc.Chrome(options=options, headless=False, version_main=148)

    try:
        # Navigate to the Nexus Mods login page
        driver.get("https://users.nexusmods.com/auth/sign_in")
        time.sleep(3)

        # Dismiss cookie banner if present
        try:
            deny_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Deny')]")
            if deny_btn.is_displayed():
                deny_btn.click()
                time.sleep(1)
        except Exception:
            pass

        print()
        print("  >>> LOG INTO NEXUS MODS <<<")
        print("  >>> Close Chrome when done <<<")
        print()

        # Wait for the user to close Chrome
        while True:
            try:
                _ = driver.title  # will throw if browser is closed
                time.sleep(2)
            except Exception:
                break

        print("[+] Login saved successfully!")

    except Exception as e:
        print(f"[!] Error: {e}")
    finally:
        try:
            driver.quit()
        except Exception:
            pass


if __name__ == "__main__":
    main()
