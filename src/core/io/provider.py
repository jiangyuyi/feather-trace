from abc import ABC, abstractmethod
from typing import List, Generator, Optional, IO
from pathlib import Path
import os

class FileEntry:
    """Represents a file or directory in the VFS"""
    def __init__(self, path: str, is_dir: bool, size: int = 0, name: str = ""):
        self.path = path # Full path or URI
        self.name = name or os.path.basename(path)
        self.is_dir = is_dir
        self.size = size

class StorageProvider(ABC):
    """Abstract base class for storage backends (Local, SMB, WebDAV)"""
    
    @abstractmethod
    def list_dir(self, path: str, recursive: bool = False) -> Generator[FileEntry, None, None]:
        """List contents of a directory"""
        pass

    @abstractmethod
    def exists(self, path: str) -> bool:
        """Check if path exists"""
        pass
        
    @abstractmethod
    def read_bytes(self, path: str) -> bytes:
        """Read file content as bytes"""
        pass

    @abstractmethod
    def write_bytes(self, path: str, data: bytes):
        """Write bytes to file"""
        pass
    
    @abstractmethod
    def delete(self, path: str):
        """Delete file"""
        pass
        
    @abstractmethod
    def move(self, src_path: str, dest_path: str):
        """Move/Rename file within the same provider"""
        pass

    @abstractmethod
    def get_local_path(self, path: str) -> Optional[str]:
        """
        If the file is already local, return its absolute path.
        If it's remote, return None (caller should use download_to_temp).
        This is for optimizing ExifTool/OpenCV usage.
        """
        pass
