"""
Configuration utilities for ThinkiPlex.

This module provides functions for loading, validating, and managing configuration.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


class Config:
    """Configuration manager for ThinkiPlex."""

    def __init__(self, config_file: str = "config/thinkiplex.yaml"):
        """Initialize the configuration manager.

        Args:
            config_file: Path to the configuration file
        """
        self.config_file = config_file
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file or create default if not exists.

        Returns:
            Dictionary with loaded configuration
        """
        if not os.path.exists(self.config_file):
            self._create_default_config()

        with open(self.config_file, "r") as f:
            return yaml.safe_load(f)

    def _create_default_config(self) -> None:
        """Create a default configuration file."""
        # Ensure the config directory exists
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)

        default_config = {
            "global": {
                "base_dir": os.getcwd(),
                "video_quality": "720p",
                "extract_audio": True,
                "audio_quality": 0,
                "audio_format": "mp3",
            },
            "courses": {
                "example-course": {
                    "course_link": "https://example.thinkific.com/courses/take/example-course",
                    "show_name": "Example Course",
                    "season": "01",
                    "video_quality": "720p",
                    "extract_audio": True,
                    "audio_quality": 0,
                    "audio_format": "mp3",
                }
            },
        }

        with open(self.config_file, "w") as f:
            yaml.dump(default_config, f, default_flow_style=False)

        print(
            f"Default configuration created at {self.config_file}. Please edit it with your course details."
        )

    def get(self, path: str, fallback: Any = None) -> Any:
        """Get a configuration value using dot notation.

        Args:
            path: Configuration path (e.g., "global.video_quality")
            fallback: Fallback value if path is not found

        Returns:
            Configuration value or fallback
        """
        parts = path.split(".")
        value = self.config

        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return fallback

        return value

    def get_course_config(self, course_name: str) -> Dict[str, Any]:
        """Get the configuration for a specific course.

        Args:
            course_name: Name of the course

        Returns:
            Dictionary with course configuration or empty dict if not found
        """
        if "courses" not in self.config or course_name not in self.config["courses"]:
            return {}

        # Start with a copy of the global settings
        course_config = self.config["global"].copy()

        # Override with course-specific settings
        course_config.update(self.config["courses"][course_name])

        return course_config

    def get_courses(self) -> Dict[str, Dict[str, Any]]:
        """Get all configured courses.

        Returns:
            Dictionary of course configurations
        """
        return self.config.get("courses", {})

    def set(self, path: str, value: Any) -> None:
        """Set a configuration value using dot notation.

        Args:
            path: Configuration path (e.g., "global.video_quality")
            value: Value to set
        """
        parts = path.split(".")
        config = self.config

        # Navigate to the parent of the target key
        for part in parts[:-1]:
            if part not in config:
                config[part] = {}
            config = config[part]

        # Set the value
        config[parts[-1]] = value

    def save(self) -> None:
        """Save the configuration to file."""
        with open(self.config_file, "w") as f:
            yaml.dump(self.config, f, default_flow_style=False)

    def get_path(self, path: str, fallback: Optional[str] = None) -> Path:
        """Get a path configuration value.

        Args:
            path: Configuration path (e.g., "global.base_dir")
            fallback: Fallback value if path is not found

        Returns:
            Path object
        """
        path_str = self.get(path, fallback=fallback)
        if path_str:
            return Path(path_str)

        if fallback:
            return Path(fallback)

        return Path()
