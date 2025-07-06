"""
🌐 Handles HTTP requests (headers, retries, proxies)
"""

import cloudscraper

from utils.config import USER_AGENT, REQUEST_TIMEOUT
from utils.logger import log_error, log_info

def fetch_html(url, headers=None):
    """Fetches HTML content from a given URL using cloudscraper."""
    scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})
    try:
        log_info(f"Fetching HTML from: {url}")
        # Merge default scraper headers with custom headers
        effective_headers = scraper.headers.copy()
        if headers:
            effective_headers.update(headers)

        response = scraper.get(url, headers=effective_headers, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.text
    except Exception as e:
        log_error(f"Failed to fetch HTML from {url}: {e}")
        return None

if __name__ == "__main__":
    # Example usage for testing
    import sys
    if len(sys.argv) > 1:
        test_url = sys.argv[1]
        html = fetch_html(test_url)
        if html:
            print(html[:500]) # Print first 500 characters
    else:
        print("Usage: python -m scraper.fetcher <url>")
