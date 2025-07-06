"""
💾 Downloads images and saves them by chapter
"""

import os
import mimetypes
import cloudscraper
from concurrent.futures import ThreadPoolExecutor

from utils.config import DOWNLOAD_DIR, DOWNLOAD_THREADS
from utils.logger import log_success, log_error, log_info
from utils.pdf_converter import convert_to_pdf

def download_image(url, folder_path, image_index, referer_url, user_agent):
    """Downloads a single image and saves it using cloudscraper with custom headers."""
    scraper = cloudscraper.create_scraper()
    custom_headers = {
        "Referer": referer_url,
        "User-Agent": user_agent
    }
    try:
        img_res = scraper.get(url, headers=custom_headers, stream=True)
        img_res.raise_for_status()

        # Determine file extension from Content-Type header
        content_type = img_res.headers.get("content-type")
        ext = mimetypes.guess_extension(content_type) if content_type else ".jpg"

        if ext == ".jpe":
            ext = ".jpg"

        # Fallback if the content type is not an image
        if not ext or "image" not in content_type:
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
    manga_folder = os.path.join(DOWNLOAD_DIR, manga_title)
    chapter_folder = os.path.join(manga_folder, chapter_title)

    log_info(f"Downloading chapter: {chapter_title}")

    # Get a user agent from a new scraper instance for consistency
    temp_scraper = cloudscraper.create_scraper()
    user_agent = temp_scraper.headers.get("User-Agent")

    downloaded_image_paths = []
    with ThreadPoolExecutor(max_workers=DOWNLOAD_THREADS) as executor:
        futures = []
        for i, img_url in enumerate(image_urls):
            futures.append(executor.submit(download_image, img_url, chapter_folder, i + 1, chapter_url, user_agent))

        for future in futures:
            result = future.result() # Wait for all downloads to complete
            if result:
                downloaded_image_paths.append(result)

    log_success(f"Finished downloading chapter: {chapter_title}")

    if create_pdf and downloaded_image_paths:
        pdf_path = os.path.join(manga_folder, f"{chapter_title}.pdf")
        # Sort images by name before converting to PDF
        downloaded_image_paths.sort()
        convert_to_pdf(downloaded_image_paths, pdf_path, delete_images)


if __name__ == "__main__":
    # Example usage for testing
    # This requires a list of image URLs from the parser
    # For demonstration, we'll use placeholder URLs
    test_image_urls = [
        "https://via.placeholder.com/800x1200.png?text=Image+1",
        "https://via.placeholder.com/800x1200.png?text=Image+2",
        "https://via.placeholder.com/800x1200.png?text=Image+3"
    ]
    download_chapter("Chapter 1", test_image_urls, "Test Manga", "https://example.com", create_pdf=True, delete_images=True)
