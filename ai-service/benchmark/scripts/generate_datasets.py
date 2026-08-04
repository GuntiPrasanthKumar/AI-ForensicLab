import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
HUMAN_DIR = os.path.join(BASE_DIR, "datasets", "human")
AI_DIR = os.path.join(BASE_DIR, "datasets", "ai")

os.makedirs(HUMAN_DIR, exist_ok=True)
os.makedirs(AI_DIR, exist_ok=True)

def generate_human_photos(count=5):
    """Generates synthetic 'Human Camera' photos with noise & simulated EXIF tags."""
    print(f"Generating {count} human test photos...")
    for i in range(1, count + 1):
        # Create image with natural texture + high noise (simulating camera ISO noise)
        arr = np.random.randint(0, 256, (384, 384, 3), dtype=np.uint8)
        img = Image.fromarray(arr, "RGB")
        
        # Add draw elements
        draw = ImageDraw.Draw(img)
        draw.ellipse((50, 50, 300, 300), outline=(255, 255, 255), width=3)
        
        # Add basic EXIF info to PIL Image
        exif = img.getexif()
        exif[271] = "Apple"  # Make
        exif[272] = "iPhone 14 Pro"  # Model
        exif[306] = "2026:08:04 12:00:00"  # DateTime
        
        filepath = os.path.join(HUMAN_DIR, f"camera_photo_{i}.jpg")
        img.save(filepath, format="JPEG", quality=92, exif=exif)

def generate_ai_images(count=5):
    """Generates synthetic 'AI Generated' images with smooth gradients & missing EXIF."""
    print(f"Generating {count} AI test images...")
    for i in range(1, count + 1):
        # Create ultra-smooth gradient (simulating AI skin smoothing)
        img = Image.new("RGB", (384, 384), color=(120, 100, 220))
        draw = ImageDraw.Draw(img)
        for y in range(384):
            draw.line([(0, y), (384, y)], fill=(y % 255, (y * 2) % 255, (y * 3) % 255))
        
        img = img.filter(ImageFilter.GaussianBlur(8))
        filepath = os.path.join(AI_DIR, f"ai_generated_{i}.png")
        img.save(filepath, format="PNG")

if __name__ == "__main__":
    generate_human_photos(5)
    generate_ai_images(5)
    print("Dataset generation complete!")
