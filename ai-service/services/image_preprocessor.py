import io
import hashlib
from typing import Tuple, Dict, Any
from PIL import Image, ImageOps
import numpy as np

SUPPORTED_FORMATS = {"JPEG", "JPG", "PNG", "WEBP", "BMP", "TIFF"}

def preprocess_image(image_bytes: bytes) -> Dict[str, Any]:
    """
    Validates, loads, and normalizes raw uploaded image bytes.
    - Validates file integrity & corruption
    - Converts color space to RGB & strips Alpha channel if present
    - Generates SHA-256 digest for caching
    - Outputs PIL Image, NumPy array, and image dimensions
    """
    if not image_bytes or len(image_bytes) < 16:
        raise ValueError("Uploaded image file is empty or corrupted.")

    # 1. Compute SHA-256 Hash
    sha256_hash = hashlib.sha256(image_bytes).hexdigest()

    # 2. Open PIL Image & Validate Integrity
    try:
        raw_img = Image.open(io.BytesIO(image_bytes))
        image_format = (raw_img.format or "JPEG").upper()
    except Exception as e:
        raise ValueError(f"Corrupted or unreadable image file: {str(e)}")

    if image_format not in SUPPORTED_FORMATS and raw_img.format not in SUPPORTED_FORMATS:
        # Allow fallback if PIL recognized image despite format extension
        if not raw_img.format:
            raise ValueError(f"Unsupported image format: {image_format}")

    # Auto-orient based on EXIF orientation if present
    try:
        raw_img = ImageOps.exif_transpose(raw_img)
    except Exception:
        pass

    width, height = raw_img.size

    # 3. Convert Color Space to RGB (Remove Alpha / CMYK / Palette)
    if raw_img.mode in ("RGBA", "LA", "P"):
        # Create solid black background for alpha blending
        rgb_img = Image.new("RGB", raw_img.size, (0, 0, 0))
        if raw_img.mode == "P":
            raw_img = raw_img.convert("RGBA")
        rgb_img.paste(raw_img, mask=raw_img.split()[-1])
    else:
        rgb_img = raw_img.convert("RGB")

    # Convert to NumPy uint8 array
    np_img = np.array(rgb_img)

    return {
        "pil_image": rgb_img,
        "np_image": np_img,
        "width": width,
        "height": height,
        "format": image_format,
        "mode": rgb_img.mode,
        "file_size": len(image_bytes),
        "hash": sha256_hash,
        "raw_img_ref": raw_img
    }
