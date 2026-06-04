# Nexus Mods Collection Downloader

Download all mods from a [Nexus Mods](https://www.nexusmods.com) collection in one click. No Vortex or mod manager required — files are saved directly to a folder of your choice.

## How It Works

This tool uses the same internal API that the popular [Nexus Download Collection](https://greasyfork.org/en/scripts/483337-nexus-download-collection) Tampermonkey script uses:

1. **GraphQL API** fetches the full list of mod files from the collection
2. **GenerateDownloadUrl API** converts each file ID into a direct CDN download link
3. **Python requests** downloads the files straight to your disk

All API calls are executed inside a real browser session (via [undetected-chromedriver](https://github.com/ultrafunkamsterdam/undetected-chromedriver)) to bypass Cloudflare protection. The actual file downloads go through Python's `requests` library for speed.

## Requirements

- Python 3.8+
- Google Chrome installed

## Installation

```bash
pip install undetected-chromedriver requests
```

Or use the provided requirements file:

```bash
pip install -r requirements.txt
```

## Usage

### Step 1: Log into Nexus Mods

```bash
python setup.py
```

A Chrome window will open. Log into your Nexus Mods account, then close Chrome. Your session is saved in `chrome_profile/`.

### Step 2: Download the Collection

```bash
python download.py
```

The script will:
- Fetch all mods from the configured collection
- Skip any mods you've already downloaded (tracked in `.download_history.json`)
- Pause for 5 minutes every 200 downloads to avoid rate limiting
- Display progress for each file download

### Resume Downloads

Simply re-run `python download.py` at any time. It picks up exactly where it left off.

## Configuration

Edit the constants at the top of `download.py`:

```python
COLLECTION_SLUG = "pr6e5b"       # Collection slug from the URL
GAME_ID = 1303                    # Game ID (1303 = Stardew Valley)
DEST_DIR = Path(r"D:\Stardew Mods")  # Where to save files

# Rate limiting
MAX_DOWNLOADS_PER_SESSION = 200
PAUSE_DURATION = 300              # 5 minutes
DOWNLOAD_DELAY = 3                # seconds between downloads
```

### How to Find Your Collection Slug

The **slug** is the short ID in the collection URL. Just copy it from your browser's address bar:

```
https://www.nexusmods.com/games/stardewvalley/collections/pr6e5b/mods
                                               ^^^^^^^
                                               This is the slug
```

Then paste it into `download.py`:

```python
COLLECTION_SLUG = "pr6e5b"
```

### How to Find Your Game ID

The game ID is a number that identifies the game on Nexus Mods. You can find it by:

1. Opening the collection page in your browser
2. Pressing F12 to open DevTools
3. Going to the **Network** tab
4. Filtering by `graphql`
5. Clicking any request and looking for `"gameId"` or `"id"` in the response

Or just use one of the common IDs below:

| Game | ID |
|------|----|
| Stardew Valley | 1303 |
| Skyrim Special Edition | 1704 |
| Fallout 4 | 3333 |
| Oblivion Remastered | 6924 |
| Baldur's Gate 3 | 3474 |
| Cyberpunk 2077 | 3333 |
| Palworld | 5977 |
| Lethal Company | 6264 |

> **Note:** For most Stardew Valley collections, the default settings (`pr6e5b` and `1303`) are already correct. You only need to change them for other games or collections.

## Privacy & Security

### Does this leak my personal data?

**No.** Everything stays on your local machine:

| File | What it contains | Shared? |
|------|------------------|---------|
| `chrome_profile/` | Nexus Mods login cookies | No (in `.gitignore`) |
| `.download_history.json` | Mod names and IDs | No (in `.gitignore`) |
| `download.py` | No personal data | Safe to share |

The only external connections are:
- **Nexus Mods API** — to get the mod list and download URLs
- **Nexus Mods CDN** — to download the actual mod files

No data is sent to third parties. The browser is only used for API calls; downloads go through Python directly.

## Project Structure

```
nexus-collection-downloader/
├── download.py              # Main download script
├── setup.py                 # Chrome profile setup / login
├── requirements.txt         # Python dependencies
├── README.md                # This file
├── .gitignore               # Excludes sensitive files from git
└── chrome_profile/          # Chrome profile with your login (auto-created)
```

## FAQ

### Do I need a Nexus Mods account?

Yes. You need a free account to download mods. If you want to use the collection feature, you need a free Nexus Mods account (not premium required).

### Does this work with premium/NX files?

The script uses the `nmm=0` parameter (browser download), not `nmm=1` (Vortex/NX). This means it downloads from the same CDN as the browser — no premium required. If you have premium and want faster downloads, you could modify the `nmm` parameter in the API call.

### Can I download only specific mods?

Currently the script downloads all mods in the collection. If you want to skip certain mods, you can add their file IDs to the `.download_history.json` file and they'll be skipped.

### How do I change the download folder?

Edit the `DEST_DIR` constant in `download.py`:

```python
# Windows
DEST_DIR = Path(r"D:\My Mods\Stardew Valley")

# macOS / Linux
DEST_DIR = Path.home() / "Downloads" / "stardew-mods"
```

### The script stopped mid-download. What do I do?

Just re-run `python download.py`. It will skip all mods you already downloaded and continue from where it left off.

### I got a "Not logged in!" error

Run `python setup.py` again. Make sure you:
1. See the Nexus Mods website in the Chrome window
2. Actually log in with your credentials
3. Close Chrome normally (don't kill the process)

### I'm getting Cloudflare errors

The script handles Cloudflare automatically by refreshing the session. If it keeps happening:
1. Close all Chrome windows
2. Run `python setup.py` to re-login
3. Run `python download.py` again

### How do I update the Chrome version?

If Chrome updates and the script breaks, update the `version_main` parameter in both `download.py` and `setup.py`:

```python
driver = uc.Chrome(options=options, version_main=148)  # change to your version
```

Check your Chrome version at `chrome://settings/help`.

### Can I use this on Linux/macOS?

Yes. The code is cross-platform. Just make sure:
1. Chrome is installed
2. Python 3.8+ is installed
3. You adjust `DEST_DIR` to use a valid path for your OS

### The downloaded files have no extension

This is a known issue. The script extracts the extension (`.zip`, `.rar`, `.7z`) from the download URL and adds it automatically. If a file still has no extension, it's likely an error page — check the file size.

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Not logged in!" | Run `python setup.py` again |
| Cloudflare errors | Close Chrome, run `setup.py` again |
| HTTP 429 (rate limit) | Wait 5 minutes, script resumes automatically |
| Files have no extension | Script adds them automatically; re-run to fix |
| Script crashes | Re-run `python download.py`, it skips completed mods |
| Wrong game | Change `GAME_ID` in `download.py` |

## Credits

- [Nexus Download Collection](https://greasyfork.org/en/scripts/483337-nexus-download-collection) by Drigtime — the Tampermonkey script that inspired the API approach
- [undetected-chromedriver](https://github.com/ultrafunkamsterdam/undetected-chromedriver) — bypasses Cloudflare bot detection

## License

MIT
