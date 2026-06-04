"""
Nexus Mods Collection Downloader

Downloads all mods from a Nexus Mods collection using the internal API.
Bypasses Cloudflare by executing API calls within an authenticated browser session
via undetected-chromedriver, then downloads files directly through Python requests.

Usage:
    1. Run `python setup.py` to create a Chrome profile and log in.
    2. Run `python download.py` to start downloading.
    3. Re-run `python download.py` anytime to resume — already downloaded mods are skipped.

Tested on Stardew Valley collection pr6e5b (574 mods).
Should work with any Nexus Mods collection by changing the COLLECTION_SLUG constant.
"""

import os
import sys
import time
import json
import requests
import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options
from pathlib import Path

# =============================================================================
# CONFIGURATION
# =============================================================================

# Collection to download — change the slug to use a different collection
COLLECTION_SLUG = "pr6e5b"

# Game ID (1303 = Stardew Valley). Find yours at nexusmods.com/{game}/collections
GAME_ID = 1303

# Where to save downloaded mods
DEST_DIR = Path(r"D:\Stardew Mods")

# Chrome profile directory (created by setup.py)
PROFILE_DIR = Path(__file__).parent / "chrome_profile"

# Download history — tracks which mods were already downloaded
HISTORY_FILE = Path(__file__).parent / ".download_history.json"

# Nexus Mods API endpoints
GRAPHQL_URL = "https://api.nexusmods.com/v2/graphql"
DOWNLOAD_API = "https://www.nexusmods.com/Core/Libs/Common/Managers/Downloads?GenerateDownloadUrl"

# Rate limiting — Nexus Mods will temporarily ban you if you download too fast
# These defaults are conservative; increase if you have a premium account
MAX_DOWNLOADS_PER_SESSION = 200   # pause after this many downloads
PAUSE_DURATION = 300              # seconds to pause (5 minutes)
DOWNLOAD_DELAY = 3                # seconds between each download


# =============================================================================
# DOWNLOAD HISTORY
# =============================================================================
# The history file lets us resume downloads without re-downloading mods.
# Each entry maps a file ID to its metadata.

def load_history():
    """Load the download history from disk."""
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_history(history):
    """Persist the download history to disk."""
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)


# =============================================================================
# BROWSER SETUP
# =============================================================================
# We use undetected-chromedriver to bypass Cloudflare bot detection.
# The browser is launched with a persistent Chrome profile so that your
# Nexus Mods login session is preserved across runs.

def create_driver():
    """
    Create and return an undetected Chrome WebDriver instance.

    Uses the existing Chrome profile so the user stays logged in.
    """
    print("[*] Starting browser...")
    options = Options()
    options.add_argument("--profile-directory=Default")
    options.add_argument(f"--user-data-dir={PROFILE_DIR}")
    options.add_argument("--disable-blink-features=AutomationControlled")

    # Update version_main to match your installed Chrome version
    driver = uc.Chrome(options=options, version_main=148)

    # Tell Chrome where to save downloads (used as a fallback)
    driver.execute_cdp_cmd("Page.setDownloadBehavior", {
        "behavior": "allow",
        "downloadPath": str(DEST_DIR)
    })

    return driver


# =============================================================================
# GRAPHQL API
# =============================================================================
# Nexus Mods uses a GraphQL API to expose collection data.
# We execute the query from within the browser context so that all cookies
# and Cloudflare tokens are automatically included.

COLLECTION_MODS_QUERY = """
query CollectionRevisionMods($slug: String!, $revision: Int, $viewAdultContent: Boolean) {
  collectionRevision(slug: $slug, revision: $revision, viewAdultContent: $viewAdultContent) {
    modFiles {
      fileId
      optional
      file {
        fileId
        name
        size
        sizeInBytes
        version
        mod {
          modId
          name
          game {
            domainName
            id
          }
        }
      }
    }
  }
}
"""


def get_collection_mods(driver):
    """
    Fetch the list of all mod files in the collection via the GraphQL API.

    Returns a list of mod file objects, each containing:
      - fileId: unique identifier for this file version
      - file.name: display name of the file
      - file.mod.modId: the mod's ID
      - file.mod.name: the mod's display name
    """
    print("[*] Fetching collection mods...")

    result = driver.execute_script("""
    const query = arguments[0];
    const response = await fetch("https://api.nexusmods.com/v2/graphql", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Requested-With": "XMLHttpRequest" },
        body: JSON.stringify({
            query: query,
            operationName: "CollectionRevisionMods",
            variables: { slug: arguments[1], revision: null, viewAdultContent: true }
        })
    });
    return await response.json();
    """, COLLECTION_MODS_QUERY, COLLECTION_SLUG)

    if result and "data" in result and result["data"]["collectionRevision"]:
        mod_files = result["data"]["collectionRevision"]["modFiles"]
        print(f"[+] Found {len(mod_files)} mod files in collection")
        return mod_files

    print("[!] Failed to fetch collection mods. Check your collection slug.")
    if result and "errors" in result:
        print(f"    API error: {result['errors'][0].get('message', 'unknown')}")
    return []


# =============================================================================
# DOWNLOAD URL GENERATION
# =============================================================================
# Nexus Mods has a GenerateDownloadUrl endpoint that converts a file ID
# into a direct CDN download link. This is the same endpoint used by the
# official Vortex mod manager and the popular Tampermonkey script.

def get_download_url(driver, file_id, retry=False):
    """
    Generate a direct download URL for the given file ID.

    Executes a fetch() call from the browser to include session cookies,
    then returns the CDN URL string or None on failure.
    """
    try:
        result = driver.execute_script("""
        try {
            const response = await fetch(
                "https://www.nexusmods.com/Core/Libs/Common/Managers/Downloads?GenerateDownloadUrl",
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/x-www-form-urlencoded",
                        "X-Requested-With": "XMLHttpRequest"
                    },
                    body: "fid=" + arguments[0] + "&game_id=" + arguments[1] + "&nmm=0"
                }
            );
            const text = await response.text();
            try { return JSON.parse(text); }
            catch(e) { return { error: text.substring(0, 200) }; }
        } catch(e) {
            return { error: e.toString() };
        }
        """, file_id, GAME_ID)

        # If we got an error (likely Cloudflare block), refresh and retry once
        if result and "error" in result:
            if not retry:
                print("    [!] Cloudflare block — refreshing session...")
                driver.get("https://www.nexusmods.com/")
                time.sleep(5)
                return get_download_url(driver, file_id, retry=True)
            return None

        # Extract the URL from the response
        if result and "url" in result:
            return result["url"]
        elif result and "data" in result and "url" in result["data"]:
            return result["data"]["url"]

    except Exception as e:
        # JavaScript execution failed — likely a Cloudflare challenge page
        if not retry:
            print(f"    [!] JS error: {str(e)[:80]}")
            driver.get("https://www.nexusmods.com/")
            time.sleep(5)
            return get_download_url(driver, file_id, retry=True)

    return None


# =============================================================================
# FILE DOWNLOAD
# =============================================================================
# Downloads are performed via Python requests against the CDN URL.
# The CDN typically does not have Cloudflare protection, so direct HTTP
# works fine for the actual file transfer.

def sanitize_filename(name):
    """Remove characters that are invalid in Windows file paths."""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        name = name.replace(char, "_")
    return name.strip()


def get_extension_from_url(url):
    """
    Extract the file extension from a download URL.

    Examples:
        https://files.nexus-cdn.com/1303/34356/mod-name-12345.zip  -> .zip
        https://files.nexus-cdn.com/1303/34356/mod-name-12345.7z   -> .7z
    """
    path = url.split("?")[0]
    filename = path.split("/")[-1]
    if "." in filename:
        ext = "." + filename.split(".")[-1]
        if ext.lower() in (".zip", ".7z", ".rar", ".tar", ".gz"):
            return ext
    return ".zip"  # default fallback


def download_file(url, dest_path):
    """
    Download a file from the given URL to dest_path.

    Displays a progress bar and validates that the downloaded file is not
    an HTML error page. Returns True on success, False on failure.
    """
    try:
        resp = requests.get(url, stream=True, timeout=300, allow_redirects=True)
        resp.raise_for_status()

        total_size = int(resp.headers.get("content-length", 0) or 0)
        downloaded = 0

        with open(dest_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)

                    # Print progress every MB
                    if total_size > 0 and downloaded % (1024 * 1024) == 0:
                        pct = (downloaded / total_size) * 100
                        mb_down = downloaded / (1024 * 1024)
                        mb_total = total_size / (1024 * 1024)
                        print(f"\r    {pct:.1f}% ({mb_down:.1f}/{mb_total:.1f} MB)",
                              end="", flush=True)

        if total_size > 0:
            mb_total = total_size / (1024 * 1024)
            print(f"\r    100.0% ({mb_total:.1f}/{mb_total:.1f} MB)")

        # Validate: check if the file is actually an HTML error page
        if os.path.exists(dest_path) and os.path.getsize(dest_path) > 0:
            with open(dest_path, "rb") as f:
                header = f.read(4)
                if header in (b"<!DO", b"<htm"):
                    print("    [!] Got HTML error page instead of mod file")
                    os.remove(dest_path)
                    return False
            return True

        return False

    except Exception as e:
        print(f"\n    [!] Download failed: {e}")
        if os.path.exists(dest_path):
            os.remove(dest_path)
        return False


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 60)
    print("  Nexus Mods Collection Downloader")
    print("=" * 60)
    print(f"  Collection:   {COLLECTION_SLUG}")
    print(f"  Destination:  {DEST_DIR}")
    print("=" * 60)
    print()

    # Ensure destination directory exists
    DEST_DIR.mkdir(parents=True, exist_ok=True)

    # Launch browser and log in
    driver = create_driver()

    try:
        print("[*] Loading Nexus Mods...")
        driver.get("https://www.nexusmods.com/")
        time.sleep(3)

        # Check if we're logged in by looking for sign-in links
        page_source = driver.page_source
        if "Sign In" in page_source and "Sign Up" in page_source:
            print("[!] Not logged in!")
            print("    Please run setup.py first to create a Chrome profile.")
            return
        print("[+] Logged in successfully!")

        # Fetch the full list of mods from the collection
        mod_files = get_collection_mods(driver)
        if not mod_files:
            return

        # Load download history and calculate stats
        history = load_history()
        total = len(mod_files)
        already_downloaded = sum(
            1 for mf in mod_files
            if str(mf.get("file", mf).get("fileId", mf.get("fileId"))) in history
        )
        remaining = total - already_downloaded

        print(f"\n[*] {total} total | {already_downloaded} downloaded | {remaining} remaining")
        print("[*] Press Ctrl+C to pause, then Ctrl+C again to stop\n")

        downloaded = 0
        failed = 0
        session_count = 0

        for idx, mod_file in enumerate(mod_files):
            # Pause every N downloads to avoid rate limiting
            if session_count >= MAX_DOWNLOADS_PER_SESSION:
                print(f"\n[!] Rate limit reached ({MAX_DOWNLOADS_PER_SESSION} downloads)")
                print(f"    Pausing for {PAUSE_DURATION // 60} minutes...")
                time.sleep(PAUSE_DURATION)
                session_count = 0
                print("[+] Resuming downloads...")

            # Extract file and mod metadata
            file_info = mod_file.get("file", mod_file)
            file_id = file_info.get("fileId", mod_file.get("fileId"))
            mod_info = file_info.get("mod", {})
            mod_id = mod_info.get("modId", "unknown")
            mod_name = mod_info.get("name", f"mod_{mod_id}")
            file_name = file_info.get("name", f"file_{file_id}.zip")

            # Skip mods we've already downloaded
            if str(file_id) in history:
                continue

            print(f"[{idx + 1}/{total}] {mod_name}")

            # Generate the download URL
            url = get_download_url(driver, file_id)
            if not url:
                print("    [!] Could not generate download URL")
                failed += 1
                continue

            # Determine the correct file extension
            ext = get_extension_from_url(url)
            safe_name = sanitize_filename(file_name)
            if not safe_name.endswith(ext):
                safe_name += ext
            dest_path = DEST_DIR / safe_name

            # Download the file
            if download_file(url, dest_path):
                downloaded += 1
                session_count += 1

                # Record in history
                history[str(file_id)] = {
                    "mod_id": mod_id,
                    "mod_name": mod_name,
                    "file_name": file_name,
                    "timestamp": time.time()
                }
                save_history(history)
            else:
                failed += 1

            time.sleep(DOWNLOAD_DELAY)

    except KeyboardInterrupt:
        print("\n\n[!] Paused by user. Re-run the script to resume.")

    finally:
        print("\n[*] Closing browser...")
        driver.quit()

    # Final summary
    print()
    print("=" * 60)
    print("  DOWNLOAD COMPLETE")
    print(f"  Downloaded:  {downloaded}")
    print(f"  Skipped:     {already_downloaded}")
    print(f"  Failed:      {failed}")
    print(f"  Destination: {DEST_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
