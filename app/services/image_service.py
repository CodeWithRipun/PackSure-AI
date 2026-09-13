from io import BytesIO
import warnings
from PIL import Image, ImageEnhance, ImageOps, UnidentifiedImageError

SUPPORTED_FORMATS = {
    "JPEG": ".jpg",
    "PNG": ".png",
    "WEBP": ".webp",
}

def image_extension(data: bytes) -> str:
    """Validate upload bytes and return a safe extension for their real format."""
    if not data:
        raise ValueError("The uploaded image is empty.")
        
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(data)) as image:
                image.verify()
                image_format = image.format
    except (
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
        UnidentifiedImageError,
        OSError,
    ) as exc:
        raise ValueError("The upload is not a valid image file.") from exc
        
    if image_format not in SUPPORTED_FORMATS:
        raise ValueError("Only JPEG, PNG and WEBP images are supported.")
        
    return SUPPORTED_FORMATS[image_format]

def preprocess_image(data: bytes) -> Image.Image:
    with Image.open(BytesIO(data)) as source:
        image = ImageOps.exif_transpose(source).convert("RGB")
        image.thumbnail((2400, 2400))
        gray = ImageOps.grayscale(image)
        gray = ImageEnhance.Contrast(gray).enhance(1.6)
        gray = ImageEnhance.Sharpness(gray).enhance(1.4)
        return gray