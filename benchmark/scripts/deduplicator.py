"""
Dataset Deduplicator Module
Deduplicates images using content SHA-256 hashing.
"""
import hashlib
from pathlib import Path
from typing import Dict, Any, List


class ImageDeduplicator:
    """
    Detects duplicate image files across dataset folders using content hashing (SHA-256).
    Does not rely on filenames or file paths.
    """

    def __init__(self):
        self.seen_hashes: Dict[str, str] = {}  # sha256 -> record_id

    def compute_content_hash(self, file_path: str | Path, chunk_size: int = 65536) -> str:
        """
        Computes a SHA-256 hash of the file content.
        Returns empty string if file is unreadable.
        """
        path = Path(file_path)
        if not path.exists() or path.stat().st_size == 0:
            return ""

        hasher = hashlib.sha256()
        try:
            with open(path, "rb") as f:
                while chunk := f.read(chunk_size):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except OSError:
            return ""

    def process_records(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Processes a list of image records, assigns SHA-256 content hashes,
        and flags duplicates.
        """
        for record in records:
            full_path = record.get("full_path")
            rec_id = record.get("id", "")

            content_hash = self.compute_content_hash(full_path)
            record["hash"] = content_hash

            if not content_hash or not record.get("valid", True):
                record["duplicate"] = False
                continue

            if content_hash in self.seen_hashes:
                record["duplicate"] = True
                record["duplicate_of"] = self.seen_hashes[content_hash]
            else:
                record["duplicate"] = False
                self.seen_hashes[content_hash] = rec_id

        return records
