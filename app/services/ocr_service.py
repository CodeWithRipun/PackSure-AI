import logging
from pathlib import Path
from shutil import which

import pytesseract

from app.core.config import settings
from app.services.image_service import preprocess_image

logger = logging.getLogger(__name__)
DEFAULT_TESSERACT_CMD = pytesseract.pytesseract.tesseract_cmd


def _tesseract_command() -> str:
    """Return a usable configured command, falling back to the PATH default.

    A copied development ``.env`` can contain a Windows-only executable path.
    Treat that as a configuration warning instead of making OCR permanently
    unavailable on another platform.
    """
    configured = settings.TESSERACT_CMD.strip()
    if not configured:
        return DEFAULT_TESSERACT_CMD

    if Path(configured).is_file() or which(configured):
        return configured

    logger.warning(
        "Configured TESSERACT_CMD is unavailable; falling back to the default command."
    )
    return DEFAULT_TESSERACT_CMD


def ocr_image(data: bytes):
    try:
        pytesseract.pytesseract.tesseract_cmd = _tesseract_command()
        image = preprocess_image(data)
        text = pytesseract.image_to_string(image, config="--psm 6").strip()

        if not text:
            return "", ["OCR returned no readable text. Manual review is recommended."]

        return text, []

    except Exception:
        # OCR exceptions can contain executable paths and OS details. Keep that
        # information in the server log, not in an API response or PDF report.
        logger.exception("OCR failed while processing an uploaded image")
        return "", ["OCR could not process this image. Manual review is recommended."]
