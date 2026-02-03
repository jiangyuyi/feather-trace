from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BirdRecognizer(ABC):
    """旧版同步识别器接口（保留兼容）"""
    @abstractmethod
    def predict(self, image_path: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Predict the bird species in the image.
        Returns a list of dicts: [{"scientific_name": "...", "confidence": 0.9}, ...]
        """
        pass

    @abstractmethod
    def predict_batch(self, image_paths: List[str], candidate_labels: List[str], top_k: int = 5) -> List[List[Dict[str, Any]]]:
        """
        Batch predict.
        Returns a list of result lists (one result list per image).
        """
        pass
