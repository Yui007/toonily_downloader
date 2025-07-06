import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QLineEdit, QPushButton, 
    QTextEdit, QLabel, QHBoxLayout, QTableWidget, QTableWidgetItem, QMessageBox,
    QCheckBox, QScrollArea, QFrame, QProgressBar, QHeaderView, QDialog, QDialogButtonBox
)
from PyQt6.QtCore import Qt, QUrl, QThread, pyqtSignal
from PyQt6.QtGui import QDesktopServices, QPalette, QColor

from scraper.fetcher import fetch_html
from scraper.parser import parse_manga_details, parse_chapter_images, parse_search_results
from scraper.downloader import download_chapter
from utils.logger import log_info, log_error, log_success
from utils.config import SEARCH_URL, DOWNLOAD_THREADS # Import DOWNLOAD_THREADS

# --- Chapter Selection Dialog ---
class ChapterSelectionDialog(QDialog):
    def __init__(self, chapters, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Chapters")
        self.layout = QVBoxLayout(self)
        
        self.chapters_scroll_area = QScrollArea()
        self.chapters_scroll_area.setWidgetResizable(True)
        self.chapters_widget = QWidget()
        self.chapters_layout = QVBoxLayout(self.chapters_widget)
        self.chapters_scroll_area.setWidget(self.chapters_widget)
        self.layout.addWidget(self.chapters_scroll_area)

        self.selected_chapters = []

        for chapter in chapters:
            checkbox = QCheckBox(f"Chapter {chapter['number']}: {chapter['title']}")
            checkbox.setProperty("chapter_data", chapter)
            self.chapters_layout.addWidget(checkbox)

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

    def get_selected_chapters(self):
        selected = []
        for i in range(self.chapters_layout.count()):
            widget = self.chapters_layout.itemAt(i).widget()
            if isinstance(widget, QCheckBox) and widget.isChecked():
                selected.append(widget.property("chapter_data"))
        return selected

# --- Scraper Thread ---
class ScraperThread(QThread):
    # Signals to communicate with the GUI
    manga_details_fetched = pyqtSignal(dict)
    chapter_progress = pyqtSignal(str) # For individual chapter progress
    download_finished = pyqtSignal(str) # When all downloads are done
    error_occurred = pyqtSignal(str)
    overall_progress = pyqtSignal(int) # For overall download progress (percentage)

    def __init__(self, url, chapters_to_download=None, create_pdf=False, delete_images=False):
        super().__init__()
        self.url = url
        self.chapters_to_download = chapters_to_download
        self.create_pdf = create_pdf
        self.delete_images = delete_images

    def run(self):
        try:
            log_info(f"Starting to scrape: {self.url}")
            html = fetch_html(self.url)
            if not html:
                self.error_occurred.emit("Could not retrieve manga page. Exiting.")
                return

            manga_details = parse_manga_details(html)
            if not manga_details:
                self.error_occurred.emit("Could not parse manga details. Exiting.")
                return

            self.manga_details_fetched.emit(manga_details)

            chapters = manga_details["chapters"]
            if not chapters:
                self.error_occurred.emit("No chapters found for this manga.")
                return

            chapters_to_process = self.chapters_to_download if self.chapters_to_download is not None else chapters
            total_chapters = len(chapters_to_process)
            
            from concurrent.futures import ThreadPoolExecutor
            
            completed_chapters = 0
            def download_chapter_wrapper(chapter):
                nonlocal completed_chapters
                chapter_title = chapter["title"]
                chapter_url = chapter["url"]
                
                self.chapter_progress.emit(f"Processing chapter: {chapter_title}")

                chapter_html = fetch_html(chapter_url)
                if not chapter_html:
                    self.chapter_progress.emit(f"Skipping chapter {chapter_title} (could not fetch)")
                    return

                image_urls = parse_chapter_images(chapter_html)
                if not image_urls:
                    self.chapter_progress.emit(f"Skipping chapter {chapter_title} (no images found)")
                    return

                download_chapter(chapter_title, image_urls, manga_details["title"], chapter_url, self.create_pdf, self.delete_images)
                self.chapter_progress.emit(f"Finished downloading chapter: {chapter_title}")
                
                completed_chapters += 1
                progress_percentage = int((completed_chapters / total_chapters) * 100)
                self.overall_progress.emit(progress_percentage)


            with ThreadPoolExecutor(max_workers=DOWNLOAD_THREADS) as executor:
                executor.map(download_chapter_wrapper, chapters_to_process)

            self.download_finished.emit("All selected chapters downloaded!")

        except Exception as e:
            self.error_occurred.emit(f"An unexpected error occurred during scraping: {e}")

# --- Main Window ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Toonily Manga Scraper")
        self.setGeometry(100, 100, 900, 700) # Increased size for more content

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.apply_dark_theme() # Apply theme

        self.create_search_section()
        self.create_results_section()
        self.create_manga_details_section()
        self.create_download_options_section()
        self.create_log_section()

        self.scraper_thread = None
        self.current_manga_details = None
        self.current_manga_url = None # Add this to store the URL
        self.selected_chapters_for_download = []

    def apply_dark_theme(self):
        # Set a dark palette
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Text, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
        palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(0, 0, 0))
        self.setPalette(palette)

        # Apply QSS for more detailed styling
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2C3E50; /* Dark Navy Blue */
            }
            QWidget {
                background-color: #2C3E50;
                color: #ECF0F1; /* Light Gray */
            }
            QLineEdit, QTextEdit, QTableWidget {
                background-color: #34495E; /* Slightly lighter navy */
                color: #ECF0F1;
                border: 1px solid #3498DB; /* Blue border */
                padding: 5px;
                border-radius: 5px;
            }
            QPushButton {
                background-color: #3498DB; /* Blue */
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #2980B9; /* Darker blue on hover */
            }
            QTableWidget::item {
                padding: 5px;
            }
            QTableWidget::item:selected {
                background-color: #2980B9;
                color: white;
            }
            QHeaderView::section {
                background-color: #34495E;
                color: #ECF0F1;
                padding: 5px;
                border: 1px solid #2C3E50;
            }
            QCheckBox {
                color: #ECF0F1;
            }
            QFrame {
                border: 1px solid #3498DB;
                border-radius: 5px;
                padding: 10px;
                background-color: #2C3E50;
            }
            QProgressBar {
                text-align: center;
                color: white;
                background-color: #34495E;
                border: 1px solid #3498DB;
                border-radius: 5px;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3498DB, stop:1 #2ECC71); /* Blue to Green gradient */
                border-radius: 5px;
            }
        """)

    def create_search_section(self):
        search_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter manga title or URL")
        search_layout.addWidget(self.search_input)

        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.perform_search)
        search_layout.addWidget(self.search_button)

        self.layout.addLayout(search_layout)

    def create_results_section(self):
        self.results_label = QLabel("Search Results:")
        self.layout.addWidget(self.results_label)

        # Add separate labels for "Title" and "URL"
        header_labels_layout = QHBoxLayout()
        self.title_header_label = QLabel("Title")
        self.url_header_label = QLabel("URL")
        header_labels_layout.addWidget(self.title_header_label)
        header_labels_layout.addStretch(1)
        header_labels_layout.addWidget(self.url_header_label)
        header_labels_layout.addStretch(1)
        self.layout.addLayout(header_labels_layout)

        self.results_table = QTableWidget()
        self.results_table.setColumnCount(2)
        # Remove horizontal header labels from the table itself
        self.results_table.horizontalHeader().setVisible(False) # Hide the actual header
        self.results_table.verticalHeader().setVisible(False) # Hide row numbers
        self.results_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.results_table.itemSelectionChanged.connect(self.toggle_fetch_chapters_button)
        self.results_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.results_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.layout.addWidget(self.results_table)

        self.fetch_chapters_button = QPushButton("Fetch Chapters for Selected Manga")
        self.fetch_chapters_button.clicked.connect(self.fetch_chapters_from_selection)
        self.fetch_chapters_button.setEnabled(False) # Disabled by default
        self.layout.addWidget(self.fetch_chapters_button)
        self.layout.addSpacing(10) # Add some spacing after the button

    def create_manga_details_section(self):
        self.manga_details_frame = QFrame()
        self.manga_details_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.manga_details_frame.setFrameShadow(QFrame.Shadow.Raised)
        self.manga_details_layout = QVBoxLayout(self.manga_details_frame)
        self.manga_details_frame.setVisible(False) # Hidden by default

        self.manga_title_label = QLabel("Manga Title: ")
        self.manga_details_layout.addWidget(self.manga_title_label)

        self.chapters_label = QLabel("Chapters:")
        self.manga_details_layout.addWidget(self.chapters_label)

        self.select_chapters_button = QPushButton("Select Chapters")
        self.select_chapters_button.clicked.connect(self.open_chapter_selection_dialog)
        self.manga_details_layout.addWidget(self.select_chapters_button)

        self.layout.addWidget(self.manga_details_frame)
        self.layout.addSpacing(10) # Add some spacing after the frame

    def create_download_options_section(self):
        self.download_options_frame = QFrame()
        self.download_options_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.download_options_frame.setFrameShadow(QFrame.Shadow.Raised)
        self.download_options_layout = QVBoxLayout(self.download_options_frame)
        self.download_options_frame.setVisible(False) # Hidden by default

        self.pdf_checkbox = QCheckBox("Convert to PDF")
        self.download_options_layout.addWidget(self.pdf_checkbox)

        self.delete_images_checkbox = QCheckBox("Delete images after PDF conversion")
        self.delete_images_checkbox.setEnabled(False) # Enabled only if PDF is checked
        self.pdf_checkbox.stateChanged.connect(self.delete_images_checkbox.setEnabled)
        self.download_options_layout.addWidget(self.delete_images_checkbox)

        self.download_button = QPushButton("Download Selected Chapters")
        self.download_button.clicked.connect(self.start_download)
        self.download_options_layout.addWidget(self.download_button)

        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setValue(0)
        self.download_options_layout.addWidget(self.progress_bar)
        self.download_options_layout.addStretch(1) # Push content to top

        self.layout.addWidget(self.download_options_frame)
        self.layout.addSpacing(10) # Add some spacing after the frame

    def create_log_section(self):
        self.log_label = QLabel("Logs:")
        self.layout.addWidget(self.log_label)

        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.layout.addWidget(self.log_display)
        self.layout.addStretch(1) # Push content to top

    def append_log(self, message):
        self.log_display.append(message)
        self.log_display.verticalScrollBar().setValue(self.log_display.verticalScrollBar().maximum()) # Auto-scroll to bottom

    def perform_search(self):
        query = self.search_input.text().strip()
        if not query:
            QMessageBox.warning(self, "Input Error", "Please enter a manga title or URL to search.")
            return

        self.results_table.setRowCount(0) # Clear previous results
        self.manga_details_frame.setVisible(False) # Hide details section
        self.download_options_frame.setVisible(False) # Hide download options
        self.log_display.clear() # Clear logs
        self.progress_bar.setValue(0) # Reset progress bar
        self.fetch_chapters_button.setEnabled(False) # Disable button until selection

        if query.startswith("http://") or query.startswith("https://"):
            self.handle_url_input(query)
        else:
            self.handle_search_query(query)

    def handle_url_input(self, url):
        self.append_log(f"URL detected: {url}. Fetching manga details...")
        self.start_manga_details_fetch(url)

    def handle_search_query(self, query):
        self.append_log(f"Searching for: {query}...")
        
        search_url = f"{SEARCH_URL}/{query.replace(' ', '-')}"
        
        html = fetch_html(search_url)
        if not html:
            QMessageBox.critical(self, "Search Error", "Could not retrieve search results.")
            self.results_label.setText("Search Results: (Error)")
            self.append_log("Error: Could not retrieve search results.")
            return

        results = parse_search_results(html)
        if not results:
            QMessageBox.information(self, "Search Results", "No search results found.")
            self.results_label.setText("Search Results: (No results)")
            self.append_log("No search results found.")
            return

        self.search_results_data = results # Store results for later use (e.g., double click)
        self.results_table.setRowCount(len(results))
        for i, result in enumerate(results):
            self.results_table.setItem(i, 0, QTableWidgetItem(result['title']))
            self.results_table.setItem(i, 1, QTableWidgetItem(result['url']))
        
        self.results_label.setText(f"Search Results: {len(results)} found")
        self.append_log(f"Found {len(results)} search results.")

    def toggle_fetch_chapters_button(self):
        # Enable/disable the "Fetch Chapters" button based on row selection
        self.fetch_chapters_button.setEnabled(len(self.results_table.selectedItems()) > 0)

    def fetch_chapters_from_selection(self):
        selected_items = self.results_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select a manga from the search results table.")
            return
        
        row = selected_items[0].row() # Get the row of the first selected item
        selected_manga = self.search_results_data[row]
        self.append_log(f"Selected manga: {selected_manga['title']}. Fetching details...")
        self.start_manga_details_fetch(selected_manga['url'])

    def start_manga_details_fetch(self, url):
        self.current_manga_url = url # Store the URL here
        
        self.manga_details_frame.setVisible(True)
        self.download_options_frame.setVisible(True)
        self.manga_title_label.setText("Manga Title: Fetching...")
        self.chapters_label.setText("Chapters: Fetching...")
        self.select_chapters_button.setEnabled(False)
        self.download_button.setEnabled(False)
        self.progress_bar.setValue(0) # Reset progress bar

        # Use a temporary thread for fetching manga details to keep GUI responsive
        self.details_fetch_thread = QThread()
        self.details_fetch_worker = MangaDetailsFetcher(url)
        self.details_fetch_worker.moveToThread(self.details_fetch_thread)
        self.details_fetch_thread.started.connect(self.details_fetch_worker.run)
        self.details_fetch_worker.manga_details_fetched.connect(self.display_manga_details)
        self.details_fetch_worker.error_occurred.connect(self.append_log)
        self.details_fetch_worker.finished.connect(self.details_fetch_thread.quit)
        self.details_fetch_worker.finished.connect(self.details_fetch_worker.deleteLater)
        self.details_fetch_thread.finished.connect(self.details_fetch_thread.deleteLater)
        self.details_fetch_thread.start()

    def display_manga_details(self, manga_details):
        self.current_manga_details = manga_details
        self.manga_title_label.setText(f"Manga Title: {manga_details['title']}")
        self.chapters_label.setText(f"Chapters: {len(manga_details['chapters'])} found")
        self.select_chapters_button.setEnabled(True)
        self.download_button.setEnabled(True)
        self.append_log(f"Manga details fetched for: {manga_details['title']}")

    def open_chapter_selection_dialog(self):
        if not self.current_manga_details:
            return
        
        dialog = ChapterSelectionDialog(self.current_manga_details['chapters'], self)
        if dialog.exec():
            self.selected_chapters_for_download = dialog.get_selected_chapters()
            self.append_log(f"Selected {len(self.selected_chapters_for_download)} chapters for download.")

    def start_download(self):
        if self.scraper_thread and self.scraper_thread.isRunning():
            QMessageBox.warning(self, "Download in Progress", "A download is already in progress. Please wait.")
            return

        if not self.selected_chapters_for_download:
            QMessageBox.warning(self, "No Chapters Selected", "Please select chapters to download using the 'Select Chapters' button.")
            return

        pdf_conversion = self.pdf_checkbox.isChecked()
        delete_after_pdf = self.delete_images_checkbox.isChecked()

        self.append_log(f"Starting download for {len(self.selected_chapters_for_download)} chapters...")
        self.download_button.setEnabled(False) # Disable button during download
        self.progress_bar.setValue(0) # Reset progress bar

        self.scraper_thread = ScraperThread(
            url=self.current_manga_url, # Use the stored URL
            chapters_to_download=self.selected_chapters_for_download,
            create_pdf=pdf_conversion,
            delete_images=delete_after_pdf
        )
        self.scraper_thread.chapter_progress.connect(self.append_log)
        self.scraper_thread.overall_progress.connect(self.progress_bar.setValue) # Connect progress signal
        self.scraper_thread.download_finished.connect(self.on_download_finished)
        self.scraper_thread.error_occurred.connect(self.on_scraper_error)
        self.scraper_thread.start()

    def on_download_finished(self, message):
        self.append_log(message)
        QMessageBox.information(self, "Download Complete", message)
        self.download_button.setEnabled(True) # Re-enable button
        self.progress_bar.setValue(100) # Set to 100% on completion

    def on_scraper_error(self, message):
        self.append_log(f"ERROR: {message}")
        QMessageBox.critical(self, "Scraper Error", message)
        self.download_button.setEnabled(True) # Re-enable button
        self.progress_bar.setValue(0) # Reset progress bar on error

# --- Helper Thread for initial Manga Details Fetch ---
class MangaDetailsFetcher(QThread):
    manga_details_fetched = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        try:
            html = fetch_html(self.url)
            if not html:
                self.error_occurred.emit("Could not retrieve manga page. Exiting.")
                return

            manga_details = parse_manga_details(html)
            if not manga_details:
                self.error_occurred.emit("Could not parse manga details.")
                return
            self.manga_details_fetched.emit(manga_details)
        except Exception as e:
            self.error_occurred.emit(f"An error occurred while fetching manga details: {e}")
        finally:
            self.finished.emit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
