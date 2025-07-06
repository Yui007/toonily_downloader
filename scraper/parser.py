"""
🧠 Parses HTML and extracts manga, chapters, and images
"""

from bs4 import BeautifulSoup
from utils.logger import log_error, log_success

def parse_search_results(html):
    """Parses search results from HTML content."""
    try:
        soup = BeautifulSoup(html, "html.parser")
        results = []
        for item in soup.find_all("div", class_="page-item-detail manga"):
            title_tag = item.find("h3", class_="h5").find("a")
            if title_tag:
                title = title_tag.text.strip()
                url = title_tag["href"]
                results.append({"title": title, "url": url})
        log_success(f"Parsed {len(results)} search results.")
        return results
    except Exception as e:
        log_error(f"Failed to parse search results: {e}")
        return []

import re

def parse_manga_details(html):
    """Parses manga details from HTML content."""
    try:
        soup = BeautifulSoup(html, "html.parser")
        title_element = soup.find("div", class_="post-title").find("h1")
        
        # Clones the title element and removes any span elements within it
        # This is to avoid including "HOT" or "NEW" badges in the title
        title_clone = title_element
        for span in title_clone.find_all("span"):
            span.decompose()
        
        title = title_clone.get_text(strip=True)
        
        chapters = []
        for chapter_item in soup.find_all("li", class_="wp-manga-chapter"):
            chapter_title = chapter_item.find("a").text.strip()
            chapter_url = chapter_item.find("a")["href"]
            
            chapter_number = 0.0 # Default if no number is found
            is_side_story = False
            side_story_original_num = 0 # To store the number from "Side Story X"
            import re

            # Try to match "Chapter X" (e.g., Chapter 1, Chapter 0, Chapter 1.5)
            match_chapter = re.search(r'Chapter\s*(\d+(\.\d+)?)', chapter_title, re.IGNORECASE)
            if match_chapter:
                try:
                    chapter_number = float(match_chapter.group(1))
                except ValueError:
                    pass
            # If not a main chapter, try to match "Side Story X"
            else:
                match_side_story = re.search(r'Side Story\s*(\d+)', chapter_title, re.IGNORECASE)
                if match_side_story:
                    is_side_story = True
                    try:
                        side_story_original_num = int(match_side_story.group(1))
                    except ValueError:
                        pass
                # Handle other cases where no number is found, assign a very low number
                else:
                    chapter_number = -1.0 # Assign a negative value for truly unnumbered chapters

            chapters.append({
                "title": chapter_title,
                "url": chapter_url,
                "number": chapter_number,
                "is_side_story": is_side_story,
                "side_story_original_num": side_story_original_num # Store original side story number
            })
        
        main_chapters = []
        side_stories = []
        for chapter in chapters:
            if chapter["is_side_story"]:
                side_stories.append(chapter)
            else:
                main_chapters.append(chapter)

        # Sort main chapters
        main_chapters.sort(key=lambda x: x["number"])

        # Sort side stories by their original number
        side_stories.sort(key=lambda x: x["side_story_original_num"])

        # Find the maximum main chapter number
        max_main_chapter_number = 0.0
        if main_chapters:
            max_main_chapter_number = main_chapters[-1]["number"] # Last chapter in sorted main_chapters

        # Re-assign numbers for side stories
        import math
        start_side_story_number = math.ceil(max_main_chapter_number)
        if start_side_story_number <= max_main_chapter_number:
            start_side_story_number += 1.0

        for i, chapter in enumerate(side_stories):
            chapter["number"] = start_side_story_number + i
            # Remove the temporary key
            del chapter["side_story_original_num"]

        # Combine and sort all chapters
        all_chapters = main_chapters + side_stories
        all_chapters.sort(key=lambda x: x["number"])

        log_success(f"Parsed {len(all_chapters)} chapters for manga: {title}")
        return {"title": title, "chapters": all_chapters}
    except Exception as e:
        log_error(f"Failed to parse manga details: {e}")
        return None

def parse_chapter_images(html):
    """Parses chapter images from HTML content."""
    try:
        soup = BeautifulSoup(html, "html.parser")
        images = []
        reading_content = soup.find("div", class_="reading-content")
        if reading_content:
            for img_tag in reading_content.find_all("img", class_="wp-manga-chapter-img"):
                if 'data-src' in img_tag.attrs:
                    images.append(img_tag["data-src"].strip())
        log_success(f"Parsed {len(images)} images")
        return images
    except Exception as e:
        log_error(f"Failed to parse chapter images: {e}")
        return None

if __name__ == "__main__":
    # Example usage for testing
    from scraper.fetcher import fetch_html
    # Test with a sample manga URL
    test_manga_url = "https://toonily.com/webtoon/solo-leveling-0005/"
    html_content = fetch_html(test_manga_url)
    if html_content:
        manga_details = parse_manga_details(html_content)
        if manga_details and manga_details["chapters"]:
            # Test parsing images from the first chapter
            first_chapter_url = manga_details["chapters"][0]["url"]
            chapter_html = fetch_html(first_chapter_url)
            if chapter_html:
                images = parse_chapter_images(chapter_html)
                print(f"Images in first chapter: {images}")
