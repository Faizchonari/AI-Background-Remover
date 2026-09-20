"""Application Configuration Manager for AI Background Remover."""

import json
from pathlib import Path
import sys
from typing import Any


class ConfigManager:
    """Manages application paths, user preferences, and configuration persistence."""

    def __init__(self, config_dir: Path | str | None = None):
        if config_dir is None:
            if getattr(sys, "frozen", False):
                self.base_dir = Path(sys.executable).resolve().parent
            else:
                self.base_dir = Path(__file__).resolve().parent.parent.parent
            self.config_dir = self.base_dir / "config"
        else:
            self.config_dir = Path(config_dir)
            self.base_dir = self.config_dir.parent

        self.config_path = self.config_dir / "default_config.json"
        self._data: dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        """Load settings from JSON configuration file."""
        if self.config_path.is_file():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
                return
            except Exception:
                pass

        # Defaults
        self._data = {
            "app_name": "AI Background Remover",
            "version": "1.1.0",
            "default_model": "birefnet-portrait",
            "input_dir": str(self.base_dir / "input"),
            "output_dir": str(self.base_dir / "output"),
            "model_storage_dir": str(self.base_dir / "model_storage"),
            "theme": "dark",
            "auto_detect_hardware": True,
            "max_cpu_threads": 6,
            "developer": {
                "name": "Faiz",
                "role": "Developer / Creator",
                "description": "Creator of AI Background Remover. Passionate about building fast, local-first, privacy-focused desktop AI applications.",
                "github_username": "Faizchonari",
                "github_profile_url": "https://github.com/Faizchonari",
                "project_repo_url": "https://github.com/Faizchonari/AI-Background-Remover",
                "avatar_path": "assets/developer_avatar.png"
            },
            # GENERAL
            "auto_open_output": False,
            "remember_selected_model": True,
            "auto_start_on_drop": False,
            # PROCESSING
            "execution_device": "CPU",
            "processing_quality": "High (Optimal)",
            "max_parallel_jobs": 1,
            "memory_safeguard": True,
            "memory_safeguard_threshold_gb": 1.5,
        }


    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value

    def save(self) -> None:
        """Save settings to config file."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2)
