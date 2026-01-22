from typing import Dict, Optional
from urllib.parse import urlparse
from .provider import StorageProvider
from .local import LocalProvider

class FileSystemManager:
    _instance = None
    
    def __init__(self, config: dict):
        self.config = config
        self.providers: Dict[str, StorageProvider] = {}
        
        # Initialize Local Provider with security limits
        allowed = config.get('allowed_roots', [])
        self.local_provider = LocalProvider(allowed_roots=allowed)

    @classmethod
    def get_instance(cls, config: dict = None):
        if cls._instance is None:
            if config is None:
                raise ValueError("FileSystemManager not initialized")
            cls._instance = cls(config)
        return cls._instance

    def get_provider(self, path_or_uri: str) -> StorageProvider:
        """
        Determines the correct provider for a given path/URI.
        Currently defaults to LocalProvider for all non-URI paths.
        Future: Parse smb:// or webdav:// prefixes.
        """
        # TODO: Add logic for 'smb://' or 'http://'
        return self.local_provider

    def resolve_path(self, path_or_uri: str):
        """
        Helper to get provider and relative path
        """
        provider = self.get_provider(path_or_uri)
        return provider, path_or_uri
