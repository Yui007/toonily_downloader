"""
⚙️ Settings, paths, and user preferences
"""

# Scraper Settings
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36"
REQUEST_TIMEOUT = 10  # seconds
RETRY_COUNT = 3
RETRY_DELAY = 2  # seconds

# Download Settings
DOWNLOAD_DIR = "downloads"
DOWNLOAD_THREADS = 10

# Toonily Settings
BASE_URL = "https://toonily.com"
SEARCH_URL = f"{BASE_URL}/search"