from io import BytesIO
import pytest
from PIL import Image
from app.services.image_service import image_extension

def image_bytes(image_format: str) -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (2, 2), "white").save(buffer, format=image_format)
    return buffer.getvalue()

def test_accepts_supported_image_using_its_actual_format():
    assert image_extension(image_bytes("PNG")) == ".png"
    assert image_extension(image_bytes("JPEG")) == ".jpg"

@pytest.mark.parametrize("data", [b"", b"not an image", image_bytes("GIF")])
def test_rejects_empty_invalid_and_unsupported_images(data):
    with pytest.raises(ValueError):
        image_extension(data)