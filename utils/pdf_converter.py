"""
Handles the conversion of downloaded images to a PDF file.
"""

import os
from PIL import Image
from utils.logger import log_success, log_error

def convert_to_pdf(image_paths, pdf_path, delete_images=False):
    """
    Converts a list of images to a single PDF file without quality loss,
    and optionally deletes the original images.
    """
    try:
        images = [Image.open(p).convert("RGB") for p in image_paths]
        if images:
            images[0].save(
                pdf_path,
                save_all=True,
                append_images=images[1:],
                resolution=100.0,
                quality=100,
            )
            log_success(f"Successfully created PDF: {pdf_path}")

            if delete_images:
                for image_path in image_paths:
                    try:
                        os.remove(image_path)
                    except Exception as e:
                        log_error(f"Failed to delete image {image_path}: {e}")
                # Attempt to remove the chapter folder if it's empty
                folder_path = os.path.dirname(image_paths[0])
                if not os.listdir(folder_path):
                    os.rmdir(folder_path)
            return pdf_path
    except Exception as e:
        log_error(f"Failed to create PDF for {pdf_path}: {e}")
        return None
