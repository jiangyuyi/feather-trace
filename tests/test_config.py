import os
import yaml
import pytest
from src.utils.config_loader import load_config

def test_load_config_base(tmp_path):
    # Create dummy settings
    settings_file = tmp_path / "settings.yaml"
    settings_data = {"key": "value", "recognition": {"api": {"key": "default"}}}
    with open(settings_file, "w") as f:
        yaml.dump(settings_data, f)
        
    config = load_config(str(settings_file), str(tmp_path / "secrets.yaml"))
    assert config["key"] == "value"
    assert config["recognition"]["api"]["key"] == "default"

def test_load_config_with_secrets(tmp_path):
    # Create dummy settings
    settings_file = tmp_path / "settings.yaml"
    settings_data = {"recognition": {"api": {"key": "default", "url": "http://api"}}}
    with open(settings_file, "w") as f:
        yaml.dump(settings_data, f)
        
    # Create dummy secrets
    secrets_file = tmp_path / "secrets.yaml"
    secrets_data = {"recognition": {"api": {"key": "secret_key"}}}
    with open(secrets_file, "w") as f:
        yaml.dump(secrets_data, f)
        
    config = load_config(str(settings_file), str(secrets_file))
    assert config["recognition"]["api"]["key"] == "secret_key"
    assert config["recognition"]["api"]["url"] == "http://api"
