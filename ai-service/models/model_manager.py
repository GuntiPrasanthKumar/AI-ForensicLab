import os
from typing import Dict, Any, List
from PIL import Image
import numpy as np

from models.base_model import BaseForensicModel
from models.huggingface_detector import HuggingFaceViTDetector
from models.pytorch_spectral_detector import PyTorchSpectralDetector
from models.timm_resnet_detector import TimmResNetDetector

class ForensicModelManager:
    """
    Model Registry & Orchestrator for Multi-Model AI Image Detection.
    - Manages model registration and common interface execution
    - Respects PRIMARY_IMAGE_MODEL environment variable
    - Automates failover to secondary models when errors occur
    - Extensible: New models can be added without modifying existing code
    """

    def __init__(self):
        self.registry: Dict[str, BaseForensicModel] = {}
        self._register_default_models()

    def register_model(self, model_key: str, model_instance: BaseForensicModel):
        """Registers a new model instance into the global registry."""
        if not isinstance(model_instance, BaseForensicModel):
            raise TypeError("Model must inherit from BaseForensicModel")
        self.registry[model_key] = model_instance
        print(f"[ModelManager] Registered forensic model: '{model_key}' ({model_instance.name})")

    def _register_default_models(self):
        """Registers default suite of forensic vision models."""
        self.register_model("hf_vit_deepfake", HuggingFaceViTDetector("dima806/deepfake_vs_real_image_detection", "PyTorch ViT DeepFake Classifier"))
        self.register_model("hf_deepfake_v2", HuggingFaceViTDetector("prithivMLmods/Deep-Fake-Detector-v2", "HuggingFace DeepFake Detector v2"))
        self.register_model("pytorch_spectral", PyTorchSpectralDetector("pytorch_spectral_v1", "PyTorch Deep Spatial-Spectral Feature Engine"))
        self.register_model("timm_resnet", TimmResNetDetector("resnet50", "TIMM ResNet50 Classifier"))

    def analyze(self, pil_img: Image.Image, np_img: np.ndarray) -> Dict[str, Any]:
        """
        Executes inference using the configured primary model with automatic fallback.
        """
        primary_key = os.getenv("PRIMARY_IMAGE_MODEL", "hf_vit_deepfake")

        # Construct fallback queue (Primary -> Registered Fallbacks)
        fallback_order = [primary_key, "hf_deepfake_v2", "pytorch_spectral", "timm_resnet"]
        
        ordered_keys: List[str] = []
        for k in fallback_order:
            if k not in ordered_keys and k in self.registry:
                ordered_keys.append(k)
        for k in self.registry:
            if k not in ordered_keys:
                ordered_keys.append(k)

        last_error = None

        for key in ordered_keys:
            model = self.registry[key]
            try:
                # Ensure model is loaded into memory
                if not model.is_loaded:
                    success = model.load()
                    if not success:
                        print(f"[ModelManager] Skipping model '{key}' (Failed to load weights)")
                        continue

                print(f"[ModelManager] Executing forensic inference via: '{key}' ({model.name})")
                result = model.analyze(pil_img, np_img)
                
                result["model_key_used"] = key
                result["model_name"] = result.get("model_name", model.name)
                return result

            except Exception as e:
                print(f"[ModelManager] Inference warning on model '{key}': {e}. Triggering fallback...")
                last_error = e

        raise RuntimeError(f"All registered forensic models failed to execute. Last error: {last_error}")

# Global Model Manager Instance
model_manager = ForensicModelManager()
