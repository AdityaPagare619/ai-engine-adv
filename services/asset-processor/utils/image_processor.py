from PIL import Image
import io

def convert_to_webp(image_bytes: bytes, quality: int = 85) -> bytes:
    with Image.open(io.BytesIO(image_bytes)) as img:
        output = io.BytesIO()
        img.save(output, format="WEBP", quality=quality)
        return output.getvalue()

def get_image_dimensions(image_bytes: bytes) -> dict:
    with Image.open(io.BytesIO(image_bytes)) as img:
        return {"width": img.width, "height": img.height}

def crop_image(image_bytes: bytes, box: tuple) -> bytes:
    with Image.open(io.BytesIO(image_bytes)) as img:
        cropped = img.crop(box)
        output = io.BytesIO()
        cropped.save(output, format=img.format)
        return output.getvalue()
