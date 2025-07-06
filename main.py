"""
🔁 Entry point for CLI/GUI
"""

import sys
import typer
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt
from PyQt6.QtWidgets import QApplication # Import QApplication

from scraper.fetcher import fetch_html
from scraper.parser import parse_manga_details, parse_chapter_images, parse_search_results
from scraper.downloader import download_chapter
from utils.logger import log_info, log_error, log_success
from utils.config import SEARCH_URL

app = typer.Typer()
console = Console()

def _search_manga(query: str):
    """Helper function to search for a manga and return results."""
    log_info(f"Searching for: {query}")
    search_url = f"{SEARCH_URL}/{query.replace(' ', '-')}"
    
    html = fetch_html(search_url)
    if not html:
        log_error("Could not retrieve search results.")
        return None

    results = parse_search_results(html)
    if not results:
        log_error("No search results found.")
        return None

    table = Table(title="Search Results")
    table.add_column("No.", style="yellow")
    table.add_column("Title", style="cyan")
    table.add_column("URL", style="magenta")

    for i, result in enumerate(results, 1):
        table.add_row(str(i), result['title'], result['url'])

    console.print(table)
    return results

def _scrape_manga(url: str, chapters_to_process: str = None, create_pdf: bool = False, delete_images: bool = False):
    """Helper function to scrape and download a manga."""
    log_info(f"Starting to scrape: {url}")

    html = fetch_html(url)
    if not html:
        log_error("Could not retrieve manga page. Exiting.")
        return

    manga_details = parse_manga_details(html)
    if not manga_details:
        log_error("Could not parse manga details. Exiting.")
        return

    manga_title = manga_details["title"]
    log_success(f"Found manga: {manga_title}")

    chapters = manga_details["chapters"]
    if not chapters:
        log_error("No chapters found for this manga.")
        return

    table = Table(title=f"Chapters for {manga_title}")
    table.add_column("Chapter No.", style="cyan")
    table.add_column("Title", style="magenta")
    table.add_column("URL", style="green")

    for chapter in chapters:
        table.add_row(str(chapter["number"]), chapter["title"], chapter["url"])

    console.print(table)

    chapters_to_download = []

    if chapters_to_process is None:
        while True:
            selection = typer.prompt("Enter chapter numbers to download (e.g., 1,5-7,all) or 'q' to quit")
            if selection.lower() == 'q':
                break
            
            if selection.lower() == 'all':
                chapters_to_download = chapters
                break
            else:
                try:
                    parts = selection.split(',')
                    temp_chapters = []
                    valid_selection = True
                    for part in parts:
                        if '-' in part:
                            start_str, end_str = part.split('-')
                            start = float(start_str)
                            end = float(end_str)
                            selected_range = [c for c in chapters if start <= c["number"] <= end]
                            temp_chapters.extend(selected_range)
                        else:
                            target_chapter_num = float(part)
                            found_chapter = next((c for c in chapters if c["number"] == target_chapter_num), None)
                            if found_chapter:
                                temp_chapters.append(found_chapter)
                            else:
                                log_error(f"Chapter {part} not found. Please enter a valid chapter number or range.")
                                valid_selection = False
                                break
                    if valid_selection:
                        chapters_to_download = temp_chapters
                        break
                except ValueError:
                    log_error("Invalid selection format. Please use numbers and ranges (e.g., 1, 5-7, 10.5).")
                    continue
    else:
        if chapters_to_process.lower() == 'all':
            chapters_to_download = chapters
        else:
            try:
                parts = chapters_to_process.split(',')
                for part in parts:
                    if '-' in part:
                        start_str, end_str = part.split('-')
                        start = float(start_str)
                        end = float(end_str)
                        selected_range = [c for c in chapters if start <= c["number"] <= end]
                        chapters_to_download.extend(selected_range)
                    else:
                        target_chapter_num = float(part)
                        found_chapter = next((c for c in chapters if c["number"] == target_chapter_num), None)
                        if found_chapter:
                            chapters_to_download.append(found_chapter)
                        else:
                            log_error(f"Chapter {part} not found. Exiting.")
                            return
            except ValueError:
                log_error("Invalid chapter selection format provided. Exiting.")
                return

    if not chapters_to_download:
        log_info("No chapters selected for download. Exiting.")
        return

    from concurrent.futures import ThreadPoolExecutor
    from utils.config import DOWNLOAD_THREADS

    def download_chapter_wrapper(chapter):
        chapter_title = chapter["title"]
        chapter_url = chapter["url"]
        
        log_info(f"Processing chapter: {chapter_title}")

        chapter_html = fetch_html(chapter_url)
        if not chapter_html:
            log_error(f"Skipping chapter {chapter_title} (could not fetch)")
            return

        image_urls = parse_chapter_images(chapter_html)
        if not image_urls:
            log_error(f"Skipping chapter {chapter_title} (no images found)")
            return

        download_chapter(chapter_title, image_urls, manga_title, chapter_url, create_pdf, delete_images)
        log_success(f"Finished downloading chapter: {chapter_title}")

    with ThreadPoolExecutor(max_workers=DOWNLOAD_THREADS) as executor:
        executor.map(download_chapter_wrapper, chapters_to_download)

    log_success("All selected chapters downloaded!")

@app.command()
def search(query: list[str]):
    """Searches for a manga on Toonily."""
    query_str = " ".join(query)
    _search_manga(query_str)

@app.command()
def scrape(
    url: str,
    chapters_to_process: str = typer.Argument(None, help="Chapter numbers to download (e.g., '1,5-7,all')"),
    pdf: bool = typer.Option(False, "--pdf", help="Convert downloaded chapters to PDF."),
    delete: bool = typer.Option(False, "--delete", help="Delete images after PDF conversion."),
    threads: int = typer.Option(5, "--threads", "-t", help="Number of download threads.")
):
    """Scrapes and downloads a manga from a Toonily URL."""
    from utils import config
    config.DOWNLOAD_THREADS = threads
    _scrape_manga(url, chapters_to_process, pdf, delete)

def interactive_mode():
    """Starts the interactive mode for the scraper."""
    console.print("\n[bold green]Welcome to the Toonily Scraper Interactive Mode![/bold green]")
    
    while True:
        console.print("\n[bold]Please choose an option:[/bold]")
        console.print("1. Search for a manga")
        console.print("2. Enter a manga URL")
        console.print("3. Exit")
        
        choice = Prompt.ask("[bold cyan]Enter your choice (1-3)[/bold cyan]", choices=["1", "2", "3"], default="1")

        if choice == "1":
            query = Prompt.ask("[bold cyan]Enter the manga title to search for[/bold cyan]")
            results = _search_manga(query)
            if results:
                while True:
                    selection = Prompt.ask("\n[bold cyan]Enter the number of the manga to scrape (or 'q' to quit)[/bold cyan]")
                    if selection.lower() == 'q':
                        break
                    try:
                        selection_index = int(selection) - 1
                        if 0 <= selection_index < len(results):
                            selected_manga = results[selection_index]
                            pdf_choice = Prompt.ask("[bold cyan]Convert to PDF? (y/n)[/bold cyan]", choices=["y", "n"], default="n")
                            delete_choice = "n"
                            if pdf_choice.lower() == 'y':
                                delete_choice = Prompt.ask("[bold cyan]Delete images after PDF conversion? (y/n)[/bold cyan]", choices=["y", "n"], default="n")
                            _scrape_manga(selected_manga['url'], create_pdf=(pdf_choice.lower() == 'y'), delete_images=(delete_choice.lower() == 'y'))
                            break
                        else:
                            log_error("Invalid number. Please select a number from the table.")
                    except ValueError:
                        log_error("Invalid input. Please enter a number.")
        
        elif choice == "2":
            url = Prompt.ask("[bold cyan]Please enter the manga URL[/bold cyan]")
            pdf_choice = Prompt.ask("[bold cyan]Convert to PDF? (y/n)[/bold cyan]", choices=["y", "n"], default="n")
            delete_choice = "n"
            if pdf_choice.lower() == 'y':
                delete_choice = Prompt.ask("[bold cyan]Delete images after PDF conversion? (y/n)[/bold cyan]", choices=["y", "n"], default="n")
            _scrape_manga(url, create_pdf=(pdf_choice.lower() == 'y'), delete_images=(delete_choice.lower() == 'y'))

        elif choice == "3":
            log_info("Exiting interactive mode. Goodbye!")
            break # Add break here to exit the while loop
    
@app.command()
def gui():
    """Launches the graphical user interface."""
    log_info("Launching GUI...")
    from gui.window import MainWindow
    q_app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(q_app.exec())

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Check if the first argument is 'gui'
        if sys.argv[1].lower() == 'gui':
            # If 'gui' is the argument, call the gui command directly
            # This bypasses typer's default argument parsing for the 'gui' command
            # and allows QApplication to be initialized correctly.
            from gui.window import MainWindow
            q_app = QApplication(sys.argv)
            window = MainWindow()
            window.show()
            sys.exit(q_app.exec())
        else:
            # For other CLI commands, let typer handle it
            app()
    else:
        # If no arguments, offer interactive or GUI mode
        console.print("\n[bold green]Welcome to the Toonily Scraper![/bold green]")
        console.print("\n[bold]Please choose a mode:[/bold]")
        console.print("1. CLI Interactive Mode")
        console.print("2. GUI Mode")
        
        mode_choice = Prompt.ask("[bold cyan]Enter your choice (1-2)[/bold cyan]", choices=["1", "2"], default="1")

        if mode_choice == "1":
            interactive_mode()
        elif mode_choice == "2":
            log_info("Launching GUI...")
            from gui.window import MainWindow
            q_app = QApplication(sys.argv)
            window = MainWindow()
            window.show()
            sys.exit(q_app.exec())
