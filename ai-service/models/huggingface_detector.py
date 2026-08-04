import torch
import numpy as np
from PIL import Image
from typing import Dict, Any
from models.base_model import BaseForensicModel

class HuggingFaceViTDetector(BaseForensicModel):
    """
    HuggingFace Vision Transformer (ViT) DeepFake & AI Image Detector.
    Supports pretrained image classification models from HuggingFace Hub.
    """

    def __init__(self, model_id: str = "dima806/deepfake_vs_real_image_detection", name: str = "HuggingFace ViT Classifier"):
        super().__init__(model_id, name)
        self.processor = None
        self.model = None

    def load(self) -> bool:
        if self.is_loaded:
            return True
        try:
            print(f"[HuggingFaceViTDetector] Loading model weights: {self.model_id}...")
            from transformers import AutoImageProcessor, AutoModelForImageClassification

            self.processor = AutoImageProcessor.from_pretrained(self.model_id)
            self.model = AutoModelForImageClassification.from_pretrained(self.model_id)
            self.model.eval()
            self.is_loaded = True
            print(f"[HuggingFaceViTDetector] Successfully loaded {self.name} ({self.model_id})")
            return True
        except Exception as e:
            print(f"[HuggingFaceViTDetector] Failed to load {self.model_id}: {e}")
            self.is_loaded = False
            return False

    def analyze(self, pil_img: Image.Image, np_img: np.ndarray) -> Dict[str, Any]:
        if not self.is_loaded:
            success = self.load()
            if not success:
                raise RuntimeError(f"Model {self.model_id} failed to initialize.")

        try:
            inputs = self.processor(images=pil_img, return_tensors="pt")
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits
                probs = torch.softmax(logits, dim=-1)[0].numpy()

            id2label = getattr(self.model.config, "id2label", {0: "REAL", 1: "FAKE"})
            
            ai_prob = 0.0
            for idx, label_name in id2label.items():
                clean_label = str(label_name).upper()
                if any(kw in clean_label for kw in ["FAKE", "AI", "SYNTHETIC", "GENERATED"]):
                    ai_prob = float(probs[idx]) * 100.0
                    break
                elif any(kw in clean_label for kw in ["REAL", "HUMAN", "NATURAL"]):
                    ai_prob = (1.0 - float(probs[idx])) * 100.0

            ai_prob = round(float(np.clip(ai_prob, 0.5, 99.5)), 1)

            return {
                "ai_model_probability": ai_prob,
                "model_name": f"{self.name} ({self.model_id.split('/')[-1]})",
                "raw_probs": probs.tolist()
            }
        except Exception as e:
            print(f"[HuggingFaceViTDetector] Inference error: {e}")
            raise e
