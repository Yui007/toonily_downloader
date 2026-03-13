"""
🌐 Handles HTTP requests using FlareSolverr to bypass Cloudflare
"""

import requests as req

from utils.config import FLARESOLVERR_URL
from utils.logger import log_error, log_info

# ── Cached cookies from FlareSolverr ──────────────────────────────
_cached_cookies = None


def _solve_flaresolverr(url):
    """Send a URL through FlareSolverr. Returns (html, cookies_list)."""
    global _cached_cookies
    payload = {
        "cmd": "request.get",
        "url": url,
        "maxTimeout": 60000,
    }
    try:
        log_info("Solving Cloudflare challenge via FlareSolverr...")
        resp = req.post(FLARESOLVERR_URL, json=payload, timeout=90)
        resp.raise_for_status()
        data = resp.json()

        if data.get("status") != "ok":
            log_error(f"FlareSolverr returned status: {data.get('status')}")
            return None, None

        solution = data["solution"]
        html = solution.get("response", "")
        cookies = solution.get("cookies", [])

        # Cache the cookies for image downloads
        _cached_cookies = cookies
        log_info(f"Cloudflare solved — got {len(cookies)} cookies")
        return html, cookies
    except Exception as e:
        log_error(f"FlareSolverr request failed: {e}")
        return None, None


def fetch_html(url, headers=None):
    """Fetches HTML content from a given URL via FlareSolverr."""
    try:
        log_info(f"Fetching HTML from: {url}")
        html, _ = _solve_flaresolverr(url)
        if not html:
            log_error("FlareSolverr returned empty HTML. Is it running?")
            return None
        return html
    except Exception as e:
        log_error(f"Failed to fetch HTML from {url}: {e}")
        return None


def get_download_session(referer_url):
    """
    Returns a requests.Session loaded with FlareSolverr cookies
    and correct headers for downloading images.
    """
    session = req.Session()

    if _cached_cookies:
        for c in _cached_cookies:
            session.cookies.set(c["name"], c["value"])

    session.headers.update({
        "User-Agent": "Mozilla/5.0",
        "Referer": referer_url,
    })

    return session


if __name__ == "__main__":
    # Example usage for testing
    import sys
    if len(sys.argv) > 1:
        test_url = sys.argv[1]
        html = fetch_html(test_url)
        if html:
            print(html[:500])  # Print first 500 characters
    else:
        print("Usage: python -m scraper.fetcher <url>")
