from abc import ABC, abstractmethod
from typing import Dict, Any
from PIL import Image
import numpy as np

class BaseForensicModel(ABC):
    """
    Abstract Base Class for all Image AI Detection Models.
    Enforces a common interface across all computer vision models:
    - load(): Loads model weights into memory
    - analyze(pil_img, np_img): Runs inference on image inputs
    """

    def __init__(self, model_id: str, name: str):
        self.model_id = model_id
        self.name = name
        self.is_loaded = False

    @abstractmethod
    def load(self) -> bool:
        """
        Loads the underlying model weights / processor.
        Returns True if successfully loaded, False otherwise.
        """
        pass

    @abstractmethod
    def analyze(self, pil_img: Image.Image, np_img: np.ndarray) -> Dict[str, Any]:
        """
        Performs model inference on the uploaded image.
        MUST return a dictionary containing:
        - 'ai_model_probability': float (0.0 to 100.0)
        - 'model_name': str
        - 'features': dict (optional feature metrics)
        """
        pass
