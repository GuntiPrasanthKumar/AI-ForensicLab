from typing import List, Dict, Any


class DatasetStatisticsCalculator:
    """
    Calculates aggregated statistics and metrics over processed dataset image records.
    """

    @staticmethod
    def compute_summary(records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Computes summary statistics for a dataset index.
        """
        total = len(records)
        valid_count = sum(1 for r in records if r.get("valid", False))
        invalid_count = total - valid_count
        duplicate_count = sum(1 for r in records if r.get("duplicate", False))

        human_count = sum(1 for r in records if r.get("label") == "human")
        ai_count = sum(1 for r in records if r.get("label") == "ai")
        mixed_count = sum(1 for r in records if r.get("label") == "mixed")

        sources: Dict[str, int] = {}
        categories: Dict[str, int] = {}
        extensions: Dict[str, int] = {}
        invalid_reasons: Dict[str, int] = {}

        for r in records:
            src = r.get("source", "unknown")
            sources[src] = sources.get(src, 0) + 1

            lbl = r.get("label", "unknown")
            categories[lbl] = categories.get(lbl, 0) + 1

            ext = r.get("extension", "unknown").lower()
            extensions[ext] = extensions.get(ext, 0) + 1

            if not r.get("valid", False):
                reason = r.get("invalid_reason", "Unknown error")
                invalid_reasons[reason] = invalid_reasons.get(reason, 0) + 1

        return {
            "total_images": total,
            "valid_images": valid_count,
            "invalid_images": invalid_count,
            "human_images": human_count,
            "ai_images": ai_count,
            "mixed_images": mixed_count,
            "duplicate_images": duplicate_count,
            "images_per_source": sources,
            "images_per_category": categories,
            "images_per_extension": extensions,
            "invalid_reasons": invalid_reasons
        }
