import yaml
from ultralytics import YOLO
import logging
from pathlib import Path

class BirdDetector:
    def __init__(self, model_path: str, confidence: float = 0.5, device: str = "cpu"):
        """
        Initialize the YOLOv8 bird detector.
        """
        self.device = device
        self.model = YOLO(model_path)
        self.confidence = confidence
        self.bird_class_id = 14  # COCO class for 'bird'
        
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
        except RuntimeError as e:
            if "CUDA" in str(e) and self.device != "cpu":
                logging.warning(f"CUDA error detected: {e}. Falling back to CPU.")
                self.device = "cpu"
                results = self.model.predict(
                    source=image_path, 
                    conf=self.confidence, 
                    verbose=False, 
                    device="cpu"
                )
            else:
                raise e
        
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
