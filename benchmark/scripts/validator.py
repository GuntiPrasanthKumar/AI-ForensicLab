import os
from pathlib import Path
from typing import Dict, Any
from PIL import Image, UnidentifiedImageError


class ImageValidator:
    """
    Validates image file integrity, detects corrupted or zero-byte files,
    and extracts basic technical metadata (dimensions, color mode, file size).
    """

    @staticmethod
    def validate_and_extract_metadata(file_path: str | Path) -> Dict[str, Any]:
        """
        Validates an image file and extracts metadata.

        Returns a dictionary containing:
          - valid (bool)
          - invalid_reason (str | None)
          - size_bytes (int)
          - width (int | None)
          - height (int | None)
          - mode (str | None)
        """
        path = Path(file_path)

        if not path.exists():
            return {
                "valid": False,
                "invalid_reason": "File not found",
                "size_bytes": 0,
                "width": None,
                "height": None,
                "mode": None
            }

        try:
            size_bytes = path.stat().st_size
        except OSError as e:
            return {
                "valid": False,
                "invalid_reason": f"File access error: {str(e)}",
                "size_bytes": 0,
                "width": None,
                "height": None,
                "mode": None
            }

        if size_bytes == 0:
            return {
                "valid": False,
                "invalid_reason": "Zero-byte file",
                "size_bytes": 0,
                "width": None,
                "height": None,
                "mode": None
            }

        try:
            with Image.open(path) as img:
                # Verify image structural integrity
                img.verify()

            # Re-open after verify() to read dimension & mode attributes safely
            with Image.open(path) as img:
                width, height = img.size
                mode = img.mode

            return {
                "valid": True,
                "invalid_reason": None,
                "size_bytes": size_bytes,
                "width": width,
                "height": height,
                "mode": mode
            }

        except UnidentifiedImageError:
            return {
                "valid": False,
                "invalid_reason": "Corrupted or unrecognized image format",
                "size_bytes": size_bytes,
                "width": None,
                "height": None,
                "mode": None
            }
        except (OSError, SyntaxError, ValueError) as err:
            return {
                "valid": False,
                "invalid_reason": f"Corrupted or unreadable image file ({str(err)})",
                "size_bytes": size_bytes,
                "width": None,
                "height": None,
                "mode": None
            }
        except Exception as err:
            return {
                "valid": False,
                "invalid_reason": f"Unexpected validation error: {str(err)}",
                "size_bytes": size_bytes,
                "width": None,
                "height": None,
                "mode": None
            }
