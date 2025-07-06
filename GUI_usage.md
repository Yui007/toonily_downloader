# Toonily Manga Scraper - GUI Usage Guide

This guide provides instructions on how to use the graphical user interface (GUI) of the Toonily Manga Scraper.

## Launching the GUI

To launch the GUI, run the following command in your terminal:

```bash
python main.py
```

Then, select option `2` for GUI Mode.

## Searching for Manga

You can search for a manga in two ways:

1.  **By Title**: Enter the title of the manga in the search bar and click the "Search" button. The search results will be displayed in a table.
2.  **By URL**: Paste the full URL of a Toonily manga into the search bar and click the "Search" button. The application will directly fetch the details for that manga.

## Selecting a Manga

Once the search results are displayed, you can select a manga by clicking on its row in the table. This will enable the "Fetch Chapters for Selected Manga" button.

## Selecting Chapters

After fetching the chapters for a selected manga, click the "Select Chapters" button to open a new dialog. In this dialog, you can select the chapters you want to download by checking the corresponding boxes. You can also use the "Select All Chapters" checkbox to select or deselect all chapters at once.

Click "OK" to confirm your selection or "Cancel" to close the dialog without making any changes.

## Downloading

Once you have selected the chapters you want to download, click the "Download Selected Chapters" button to start the download process. The progress of the download will be displayed in the progress bar.

## Download Options

Before starting the download, you can choose from the following options:

*   **Convert to PDF**: If checked, the downloaded chapters will be converted into PDF files.
*   **Delete images after PDF conversion**: If checked, the original image files will be deleted after the PDF conversion is complete. This option is only available if "Convert to PDF" is checked.

## Logging

The "Logs" section at the bottom of the window displays real-time information about the scraping and downloading process, including progress, success messages, and any errors that may occur.
