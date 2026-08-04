from typing import Dict, Any
from PIL import Image
import numpy as np

from models.model_manager import model_manager

def run_cv_model_inference(pil_img: Image.Image, np_img: np.ndarray) -> Dict[str, Any]:
    """
    Delegates inference execution to the ForensicModelManager.
    Executes the configured primary model with automatic fallback logic.
    """
    return model_manager.analyze(pil_img, np_img)
