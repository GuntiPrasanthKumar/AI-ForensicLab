import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATASETS_DIR = os.path.join(BASE_DIR, "datasets")

HUMAN_CATEGORIES = ["phone_camera", "dslr", "screenshots", "edited", "social_media"]
AI_CATEGORIES = ["chatgpt", "gemini", "dall_e", "midjourney", "flux", "stable_diffusion", "sdxl", "ideogram", "leonardo"]

def populate_all_datasets(samples_per_category=3):
    """Populates sub-category taxonomy directories with representative test image samples."""
    print("[Dataset Generator] Initializing taxonomy folders and sample images...")
    
    # 1. Populate Human Categories
    for cat in HUMAN_CATEGORIES:
        cat_dir = os.path.join(DATASETS_DIR, "human", cat)
        os.makedirs(cat_dir, exist_ok=True)
        for i in range(1, samples_per_category + 1):
            filepath = os.path.join(cat_dir, f"{cat}_sample_{i}.jpg")
            if not os.path.exists(filepath):
                # Simulate high-pass noise camera sensor photo
                arr = np.random.randint(0, 256, (384, 384, 3), dtype=np.uint8)
                img = Image.fromarray(arr, "RGB")
                draw = ImageDraw.Draw(img)
                draw.rectangle((50, 50, 300, 300), outline=(255, 200, 100), width=4)
                
                exif = img.getexif()
                exif[271] = "Apple" if cat == "phone_camera" else ("Canon" if cat == "dslr" else "Sony")
                exif[272] = f"Sensor Model {cat}"
                exif[306] = "2026:08:04 12:00:00"
                img.save(filepath, format="JPEG", quality=92, exif=exif)

    # 2. Populate AI Categories
    for cat in AI_CATEGORIES:
        cat_dir = os.path.join(DATASETS_DIR, "ai", cat)
        os.makedirs(cat_dir, exist_ok=True)
        for i in range(1, samples_per_category + 1):
            filepath = os.path.join(cat_dir, f"{cat}_sample_{i}.png")
            if not os.path.exists(filepath):
                # Simulate smooth synthetic AI image with subtle frequency patterns
                img = Image.new("RGB", (384, 384), color=(100, 120, 200))
                draw = ImageDraw.Draw(img)
                for y in range(384):
                    draw.line([(0, y), (384, y)], fill=((y * 3) % 255, (y * 2) % 255, (y * 5) % 255))
                img = img.filter(ImageFilter.GaussianBlur(5))
                img.save(filepath, format="PNG")

    # 3. Populate Mixed Directory
    mixed_dir = os.path.join(DATASETS_DIR, "mixed")
    os.makedirs(mixed_dir, exist_ok=True)

    print("[Dataset Generator] All 14 taxonomy dataset categories populated successfully!")

if __name__ == "__main__":
    populate_all_datasets(3)
