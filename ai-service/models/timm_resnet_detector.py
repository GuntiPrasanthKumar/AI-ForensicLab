import torch
import numpy as np
from PIL import Image
from typing import Dict, Any
from models.base_model import BaseForensicModel

class TimmResNetDetector(BaseForensicModel):
    """
    TIMM ResNet / EfficientNet Pretrained Vision Classifier.
    Extracts deep convolutional features using PyTorch timm models.
    """

    def __init__(self, model_id: str = "resnet50", name: str = "TIMM ResNet50 Classifier"):
        super().__init__(model_id, name)
        self.model = None

    def load(self) -> bool:
        if self.is_loaded:
            return True
        try:
            print(f"[TimmResNetDetector] Loading TIMM vision model: {self.model_id}...")
            import timm
            self.model = timm.create_model(self.model_id, pretrained=True)
            self.model.eval()
            self.is_loaded = True
            print(f"[TimmResNetDetector] Successfully loaded {self.name}")
            return True
        except Exception as e:
            print(f"[TimmResNetDetector] Load warning ({self.model_id}): {e}")
            self.is_loaded = False
            return False

    def analyze(self, pil_img: Image.Image, np_img: np.ndarray) -> Dict[str, Any]:
        if not self.is_loaded:
            success = self.load()
            if not success:
                raise RuntimeError(f"TIMM Model {self.model_id} failed to initialize.")

        try:
            # Resize and convert to PyTorch Tensor
            img_resized = pil_img.resize((224, 224))
            arr = np.array(img_resized, dtype=np.float32) / 255.0
            tensor = torch.from_numpy(arr).permute(2, 0, 1).unsqueeze(0)

            # ImageNet mean & std
            mean = torch.tensor([0.485, 0.456, 0.406]).view(1, 3, 1, 1)
            std = torch.tensor([0.229, 0.224, 0.225]).view(1, 3, 1, 1)
            norm_tensor = (tensor - mean) / std

            with torch.no_grad():
                logits = self.model(norm_tensor)
                probs = torch.softmax(logits, dim=-1)[0].numpy()

            # ResNet ImageNet feature entropy ratio for AI probability
            entropy = -np.sum(probs * np.log(probs + 1e-12))
            top_prob = float(np.max(probs))

            # AI images often have highly peaked or over-confident ImageNet activations
            ai_prob = round(float(np.clip(top_prob * 100.0 * 0.75 + (entropy * 5.0), 5.0, 95.0)), 1)

            return {
                "ai_model_probability": ai_prob,
                "model_name": self.name,
                "top_probability": round(top_prob, 4),
                "feature_entropy": round(float(entropy), 4)
            }
        except Exception as e:
            print(f"[TimmResNetDetector] Inference error: {e}")
            raise e
