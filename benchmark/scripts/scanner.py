"""
Dataset Scanner Module
Discovers image files within directory trees.
"""
import os
from pathlib import Path
from typing import List, Dict, Any, Set

SUPPORTED_IMAGE_EXTENSIONS: Set[str] = {
    ".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".tif"
}

KNOWN_LABELS: Set[str] = {"human", "ai", "mixed"}


class DatasetScanner:
    """
    Recursively scans dataset directories to find supported image files
    and infers ground-truth labels and source categories from directory structures.
    """

    def __init__(self, dataset_dir: str | Path, supported_extensions: Set[str] = None):
        self.dataset_dir = Path(dataset_dir).resolve()
        self.supported_extensions = {
            ext.lower() for ext in (supported_extensions or SUPPORTED_IMAGE_EXTENSIONS)
        }

    def is_supported_file(self, file_path: Path) -> bool:
        """Returns True if the file has a supported image extension."""
        return file_path.suffix.lower() in self.supported_extensions

    def derive_label_and_source(self, relative_path: Path) -> tuple[str, str]:
        """
        Derives ground-truth label and source category from relative path parts.

        Examples:
          human/phone_camera/img.jpg  -> ("human", "phone_camera")
          ai/midjourney/render.png   -> ("ai", "midjourney")
          mixed/batch1/test.jpg      -> ("mixed", "batch1")
          mixed/test.webp            -> ("mixed", "mixed")
          unknown_folder/img.jpg     -> ("unknown", "unknown_folder")
        """
        parts = relative_path.parts[:-1]  # Exclude filename

        if not parts:
            return ("unknown", "unknown")

        first_part = parts[0].lower()

        if first_part in KNOWN_LABELS:
            label = first_part
            if len(parts) >= 2:
                source = parts[1]
            else:
                source = label
        else:
            label = "unknown"
            source = parts[0]

        return (label, source)

    def scan(self) -> List[Dict[str, Any]]:
        """
        Scans the dataset directory recursively and returns a list of basic file records.
        """
        records: List[Dict[str, Any]] = []

        if not self.dataset_dir.exists() or not self.dataset_dir.is_dir():
            return records

        for root, _, files in os.walk(self.dataset_dir):
            for file_name in sorted(files):
                if file_name.startswith("."):
                    continue

                full_path = Path(root) / file_name

                if not self.is_supported_file(full_path):
                    continue

                try:
                    rel_path = full_path.relative_to(self.dataset_dir)
                except ValueError:
                    rel_path = full_path

                label, source = self.derive_label_and_source(rel_path)
                ext = full_path.suffix.lstrip(".").lower()

                # Portable relative path (e.g. datasets/human/phone_camera/photo.jpg)
                portable_rel_path = f"datasets/{rel_path.as_posix()}"

                records.append({
                    "full_path": str(full_path),
                    "relative_path": portable_rel_path,
                    "filename": file_name,
                    "extension": ext,
                    "label": label,
                    "source": source
                })

        return records
