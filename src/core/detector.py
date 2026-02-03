import yaml
from ultralytics import YOLO
import logging
from pathlib import Path
import torch
import os

class BirdDetector:
    def __init__(self, model_path: str, confidence: float = 0.5, device: str = "auto"):
        """
        Initialize the YOLOv8 bird detector.
        """
        self.confidence = confidence
        self.bird_class_id = 14  # COCO class for 'bird'
        self.model_path = model_path  # Store for reloading
        self.reload_count = 0  # Track reloads to avoid infinite loop

        # Auto-detect device
        if device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        # Check CUDA availability and fallback if needed
        if self.device == "cuda" and not torch.cuda.is_available():
            logging.warning("CUDA requested but not available. Falling back to CPU.")
            self.device = "cpu"

        # Load model
        self._load_model()

    def _load_model(self):
        """Load or reload the YOLO model."""
        if not os.path.exists(self.model_path):
            logging.warning(f"YOLO model not found at {self.model_path}, downloading yolov8n.pt...")
            self.model = YOLO("yolov8n.pt")
        else:
            self.model = YOLO(self.model_path)
        logging.info(f"YOLO detector initialized on {self.device}")

    def detect(self, image_path: str):
        """
        Detect birds in the image.
        """
        try:
            results = self.model.predict(
                source=image_path,
                conf=self.confidence,
                verbose=False,
                device=self.device
            )
        except Exception as e:
            error_str = str(e)
            # Handle model compatibility errors - reload model once
            if "Conv" in error_str and "bn" in error_str:
                if self.reload_count < 2:  # Limit reload attempts
                    self.reload_count += 1
                    self._load_model()
                    results = self.model.predict(
                        source=image_path,
                        conf=self.confidence,
                        verbose=False,
                        device=self.device
                    )
                else:
                    return []
            elif "CUDA" in error_str and self.device != "cpu":
                self.device = "cpu"
                results = self.model.predict(
                    source=image_path,
                    conf=self.confidence,
                    verbose=False,
                    device="cpu"
                )
            else:
                return []

        bird_boxes = []
        for result in results:
            for box in result.boxes:
                if int(box.cls) == self.bird_class_id:
                    # Convert to list of floats [x1, y1, x2, y2]
                    coords = box.xyxy[0].tolist()
                    score = float(box.conf[0])
                    bird_boxes.append((coords, score))

        return bird_boxes

if __name__ == "__main__":
    # Quick test if run directly
    detector = BirdDetector("yolov8n.pt")
    print("Detector initialized.")
