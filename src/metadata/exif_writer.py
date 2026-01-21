import exiftool
import logging
from typing import List, Dict, Any

class ExifWriter:
    def __init__(self, exiftool_path: str = "exiftool"):
        """
        exiftool_path: Path to the exiftool executable. 
        Ensure it is in PATH or provide absolute path.
        """
        self.exiftool_path = exiftool_path

    def write_metadata(self, image_path: str, tags: Dict[str, Any]):
        """
        Write tags to the image.
        """
        import shutil
        if not shutil.which(self.exiftool_path):
            logging.warning(f"ExifTool not found at '{self.exiftool_path}'. Skipping metadata writing.")
            return False

        try:
            with exiftool.ExifTool(self.exiftool_path) as et:
                # Prepare arguments
                # format: -Tag=Value
                args = []
                for tag, value in tags.items():
                    if isinstance(value, list):
                        # For multi-value tags like Keywords
                        for v in value:
                            args.append(f"-{tag}={v}")
                    else:
                        args.append(f"-{tag}={value}")
                
                # Execute
                et.execute(*args, image_path)
                logging.info(f"Metadata written to {image_path}")
                return True
        except Exception as e:
            logging.error(f"Failed to write metadata: {e}")
            return False

    def rename_photo(self, current_path: str, new_name: str) -> str:
        """
        Rename/move the photo to a new filename in the same directory.
        Returns the new absolute path.
        """
        from pathlib import Path
        p = Path(current_path)
        new_path = p.parent / new_name
        p.rename(new_path)
        return str(new_path.absolute())
