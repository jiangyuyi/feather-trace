import tempfile
import shutil
import os
import logging
from pathlib import Path
from contextlib import contextmanager
from .provider import StorageProvider

class TempFileManager:
    """
    Manages temporary files for operations that require local paths 
    (OpenCV, ExifTool) when working with remote providers.
    """
    
    @staticmethod
    @contextmanager
    def get_local_copy(provider: StorageProvider, remote_path: str):
        """
        Context manager that ensures a file is available locally.
        If the provider supports local paths directly, returns that.
        Otherwise, downloads to a temp file and cleans up after.
        """
        local_path = provider.get_local_path(remote_path)
        
        if local_path:
            # It's already local, just return the path
            yield local_path
        else:
            # Must download
            fd, temp_path = tempfile.mkstemp(suffix=Path(remote_path).suffix)
            os.close(fd)
            try:
                logging.debug(f"Downloading {remote_path} to {temp_path}...")
                data = provider.read_bytes(remote_path)
                with open(temp_path, 'wb') as f:
                    f.write(data)
                
                yield temp_path
                
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
