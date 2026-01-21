from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BirdRecognizer(ABC):
    @abstractmethod
    def predict(self, image_path: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Predict the bird species in the image.
        Returns a list of dicts: [{"scientific_name": "...", "confidence": 0.9}, ...]
        """
        pass
