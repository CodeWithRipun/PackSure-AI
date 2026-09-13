import pytesseract

from app.core.config import settings
from app.services.image_service import preprocess_image


def ocr_image(data: bytes):
    warnings = []

    if settings.TESSERACT_CMD:
        pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD

    try:
        image = preprocess_image(data)
        text = pytesseract.image_to_string(image, config="--psm 6").strip()

        if not text:
            warnings.append(
                "OCR returned no readable text. Manual review is recommended."
            )

        return text, warnings

    except Exception as exc:
        return "", [f"OCR unavailable or failed: {exc}"]
