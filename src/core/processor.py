from PIL import Image
import logging
from pathlib import Path
from typing import List, Tuple

class ImageProcessor:
    @staticmethod
    def crop_and_resize(
        image_path: str, 
        box: List[float], 
        output_path: str, 
        target_size: int = 640, 
        padding: int = 10
    ) -> bool:
        """
        Crop the image based on the bounding box and resize it to target_size.
        Box format: [x1, y1, x2, y2]
        """
        try:
            with Image.open(image_path) as img:
                width, height = img.size
                x1, y1, x2, y2 = box
                
                # Apply padding
                x1 = max(0, x1 - padding)
                y1 = max(0, y1 - padding)
                x2 = min(width, x2 + padding)
                y2 = min(height, y2 + padding)
                
                # Crop
                cropped = img.crop((x1, y1, x2, y2))
                
                # Resize (maintain aspect ratio and pad if necessary, or just resize to square?)
                # Documentation says "缩放到目标尺寸（默认 640px）以供归档"
                # We'll use thumbnail/resize while maintaining aspect ratio or force square
                # BioCLIP usually expects 224x224, but YOLO/archiving might want larger.
                # Let's resize so the long edge is target_size.
                
                cropped.thumbnail((target_size, target_size), Image.Resampling.LANCZOS)
                
                # Create directory if it doesn't exist
                Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                
                cropped.save(output_path, quality=95)
                return True
        except Exception as e:
            logging.error(f"Failed to process image {image_path}: {e}")
            return False
