"""Configuration management for RPA framework."""

import os
import re
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


class Config:
    """Load and manage configuration from YAML files with environment variable support."""

    def __init__(self, config_path: Optional[str] = None):
        self._config: Dict[str, Any] = {}
        self._config_path = config_path

        if config_path and Path(config_path).exists():
            self.load(config_path)

    def load(self, config_path: str) -> None:
        """Load configuration from a YAML file."""
        with open(config_path, "r") as f:
            raw_config = yaml.safe_load(f) or {}

        self._config = self._resolve_env_vars(raw_config)
        self._config_path = config_path

    def _resolve_env_vars(self, obj: Any) -> Any:
        """Recursively resolve ${VAR} environment variable references."""
        if isinstance(obj, str):
            pattern = r"\$\{([^}]+)\}"
            matches = re.findall(pattern, obj)
            for var_name in matches:
                env_value = os.environ.get(var_name, "")
                obj = obj.replace(f"${{{var_name}}}", env_value)
            return obj
        elif isinstance(obj, dict):
            return {k: self._resolve_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._resolve_env_vars(item) for item in obj]
        return obj

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value using dot notation (e.g., 'email.smtp_server')."""
        keys = key.split(".")
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value using dot notation."""
        keys = key.split(".")
        config = self._config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    def __getitem__(self, key: str) -> Any:
        return self.get(key)

    def __setitem__(self, key: str, value: Any) -> None:
        self.set(key, value)

    def __contains__(self, key: str) -> bool:
        return self.get(key) is not None

    @property
    def all(self) -> Dict[str, Any]:
        """Return all configuration as a dictionary."""
        return self._config.copy()
