import yaml
import logging
from pathlib import Path

# 全局配置缓存
_config_cache = None

def get_config() -> dict:
    """
    Get the application configuration (cached).

    This is a convenience function that calls load_config() and caches the result.
    """
    global _config_cache
    if _config_cache is None:
        _config_cache = load_config()
    return _config_cache

def load_config(settings_path: str = "config/settings.yaml", secrets_path: str = "config/secrets.yaml") -> dict:
    """
    Load settings.yaml and merge with secrets.yaml if it exists.
    """
    # 1. Load Base Settings
    config = {}
    base_path = Path(settings_path)
    if base_path.exists():
        with open(base_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
    else:
        logging.warning(f"Settings file not found at {base_path}")

    # 2. Load Secrets
    secret_path = Path(secrets_path)
    if secret_path.exists():
        logging.info(f"Loading secrets from {secret_path}")
        with open(secret_path, 'r', encoding='utf-8') as f:
            secrets = yaml.safe_load(f) or {}
            
        # 3. Merge (Simple recursive merge for 'recognition' section)
        if 'recognition' in secrets and 'recognition' in config:
            rec_sec = secrets['recognition']
            target_rec = config['recognition']
            
            for key in ['api', 'dongniao']:
                if key in rec_sec and key in target_rec:
                    # Update keys inside the sub-dict
                    target_rec[key].update(rec_sec[key])
    
    return config
