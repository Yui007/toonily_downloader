"""
💾 Downloads images and saves them by chapter
"""

import os
import mimetypes
import re
from concurrent.futures import ThreadPoolExecutor

from scraper.fetcher import get_download_session
from utils.config import DOWNLOAD_DIR, DOWNLOAD_THREADS
from utils.logger import log_success, log_error, log_info
from utils.pdf_converter import convert_to_pdf


_WINDOWS_INVALID_CHARS = re.compile(r'[<>:"/\\|?*]')
_WINDOWS_RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}


def sanitize_filename(name, fallback="download"):
    """Return a filesystem-safe filename component for Windows and POSIX."""
    sanitized = _WINDOWS_INVALID_CHARS.sub("_", str(name))
    sanitized = "".join("_" if ord(char) < 32 else char for char in sanitized)
    sanitized = sanitized.strip(" .")

    if not sanitized:
        sanitized = fallback

    stem, ext = os.path.splitext(sanitized)
    if stem.upper() in _WINDOWS_RESERVED_NAMES:
        sanitized = f"{stem}_{ext}"

    return sanitized[:120]


def sanitize_pdf_filename(filename):
    """Return a safe filename while preserving the PDF extension."""
    stem, ext = os.path.splitext(filename)
    if ext.lower() != ".pdf":
        ext = ".pdf"
    return f"{sanitize_filename(stem, fallback='chapter')}{ext}"


def download_image(session, url, folder_path, image_index):
    """Downloads a single image using a session with FlareSolverr cookies."""
    try:
        img_res = session.get(url, timeout=30)
        img_res.raise_for_status()

        # Determine file extension from Content-Type header
        content_type = img_res.headers.get("content-type")
        ext = mimetypes.guess_extension(content_type) if content_type else ".jpg"

        if ext == ".jpe":
            ext = ".jpg"

        # Fallback if the content type is not an image
        if not ext or (content_type and "image" not in content_type):
            # Try to get from URL
            url_ext = os.path.splitext(url.split("?")[0])[1]
            if url_ext in [".jpg", ".jpeg", ".png", ".webp", ".gif"]:
                ext = url_ext
            else:
                ext = ".jpg"  # Default to .jpg if all else fails

        image_name = f"{image_index:03d}{ext}"
        os.makedirs(folder_path, exist_ok=True)

        file_path = os.path.join(folder_path, image_name)
        with open(file_path, "wb") as f:
            for chunk in img_res.iter_content(8192):
                f.write(chunk)

        log_success(f"Downloaded: {image_name}")
        return file_path
    except Exception as e:
        log_error(f"Failed to download {url}: {e}")
        return None

def download_chapter(chapter_title, image_urls, manga_title, chapter_url, create_pdf=False, delete_images=False):
    """Downloads all images for a given chapter and optionally converts them to PDF."""
    safe_manga_title = sanitize_filename(manga_title)
    safe_chapter_title = sanitize_filename(chapter_title)

    if safe_manga_title != manga_title:
        log_info(f"Manga folder name sanitized: {manga_title} -> {safe_manga_title}")
    if safe_chapter_title != chapter_title:
        log_info(f"Chapter folder name sanitized: {chapter_title} -> {safe_chapter_title}")

    manga_folder = os.path.join(DOWNLOAD_DIR, safe_manga_title)
    chapter_folder = os.path.join(manga_folder, safe_chapter_title)
    os.makedirs(chapter_folder, exist_ok=True)

    log_info(f"Downloading chapter: {chapter_title}")

    # Create a session with FlareSolverr cookies for this chapter
    session = get_download_session(chapter_url)

    downloaded_image_paths = []
    with ThreadPoolExecutor(max_workers=DOWNLOAD_THREADS) as executor:
        futures = []
        for i, img_url in enumerate(image_urls):
            futures.append(executor.submit(download_image, session, img_url, chapter_folder, i + 1))

        for future in futures:
            result = future.result() # Wait for all downloads to complete
            if result:
                downloaded_image_paths.append(result)

    log_success(f"Finished downloading chapter: {chapter_title}")

    if create_pdf and downloaded_image_paths:
        pdf_path = os.path.join(manga_folder, sanitize_pdf_filename(f"{safe_chapter_title}.pdf"))
        # Sort images by name before converting to PDF
        downloaded_image_paths.sort()
        convert_to_pdf(downloaded_image_paths, pdf_path, delete_images)


if __name__ == "__main__":
    # Example usage for testing
    test_image_urls = [
        "https://via.placeholder.com/800x1200.png?text=Image+1",
        "https://via.placeholder.com/800x1200.png?text=Image+2",
        "https://via.placeholder.com/800x1200.png?text=Image+3"
    ]
    download_chapter("Chapter 1", test_image_urls, "Test Manga", "https://example.com", create_pdf=True, delete_images=True)
