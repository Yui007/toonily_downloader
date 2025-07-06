# Toonily Manga Scraper - GUI Usage Guide

This document outlines how to use the Manga Scraper via the command-line interface (CLI), supporting both interactive prompts and direct argument-based commands.

---

## 🚀 Getting Started

Ensure you have Python 3.10+ installed and all dependencies are met.

```bash
# Navigate to the project root directory
cd /path/to/toonily/
```

---

## 💬 Interactive Mode

To start the interactive mode, run the `main.py` script without any arguments. This mode provides a user-friendly interface for searching and downloading mangas.

```bash
python main.py
```

**Interactive Flow:**

1.  **Choose an Option:**
    You will be prompted to choose between searching for a manga, entering a URL directly, or exiting by entering a number.
    ```
    Please choose an option:
    1. Search for a manga
    2. Enter a manga URL
    3. Exit
    Enter your choice (1-3): 1
    ```

2.  **Search for a Manga:**
    -   If you select "Search for a manga," you will be asked to enter a title.
    -   The CLI will display a table of search results.
    -   Enter the number corresponding to the manga you want to scrape.

3.  **Enter a Manga URL:**
    -   If you select "Enter a manga URL," you will be prompted to provide the full URL of the manga.

4.  **Select Chapters to Download:**
    -   After selecting a manga, the CLI will display a list of its available chapters.
    ```
    Manga: Not a Lady Anymore
    Total Chapters: 5
    Chapters:
    [1] Chapter 1
    [2] Chapter 2
    ...
    [5] Chapter 5
    Enter chapter numbers to download (e.g., 1-5, 10, 15-20) or 'all' for all chapters: 1-3, 5
    ```

5.  **Confirm Download:**
    -   The download process will begin, showing progress in the console.

---

## ⚙️ Argument-Based Mode

You can also provide arguments directly to the `main.py` script for non-interactive operations, useful for scripting or quick downloads.

### Search Manga

Search for a manga and list its details.

```bash
python main.py search "Manga Title"
```

**Example:**

```bash
python main.py search "Not a Lady Anymore"
```

### Scrape and Download Specific Manga Chapters

Download chapters directly by providing the manga URL and desired chapter numbers to the `scrape` command.

```bash
python main.py scrape <manga_url> <chapters_to_download>
```

-   `<manga_url>`: **(Required)** The full URL of the manga series page on Toonily.
-   `<chapters_to_download>`: **(Optional)** A comma-separated list of chapter numbers or ranges. If omitted, the command will enter interactive mode for chapter selection.
    -   Individual chapters: `1,5,10`
    -   Ranges: `1-5` (downloads chapters 1, 2, 3, 4, 5)
    -   Mixed: `1-3, 7, 10.5-12`
    -   All chapters: `all`

**Example (Interactive chapter selection):**

```bash
python main.py scrape https://toonily.com/serie/not-a-lady-anymore/
```

**Example (Download specific chapters directly):**

```bash
python main.py scrape https://toonily.com/serie/not-a-lady-anymore/ "1,2,3.5,5-7"
```

**Example (Download All Chapters directly):**

```bash
python main.py scrape https://toonily.com/serie/solo-leveling/ all
```

### Output Directory

By default, mangas are downloaded to a `downloads` folder in the project root. The current CLI implementation does not support specifying a custom output directory via command-line arguments. This feature can be added in `utils/config.py` if needed.

---

## 📋 Logging

The CLI provides clear logs for progress, success, and errors.

-   `[INFO]`: General information and progress updates.
-   `[SUCCESS]`: Indicates successful operations (e.g., image downloaded).
-   `[ERROR]`: Details any failures during fetching, parsing, or downloading.

---

## 💡 Tips

-   Always use the full Toonily series URL for the `--url` argument, not a specific chapter URL.
-   Chapter numbers can be integers or floats (e.g., `1`, `5.5`, `0`). The scraper will attempt to match these to the chapter titles.
-   For long-running downloads, consider using a terminal multiplexer like `tmux` or `screen` to keep the process running in the background.
