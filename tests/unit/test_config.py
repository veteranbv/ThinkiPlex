"""
Tests for the configuration utilities.
"""

import os
import tempfile

import pytest
import yaml

from thinkiplex.utils.config import Config
from thinkiplex.utils.exceptions import ConfigError, ValidationError


@pytest.fixture
def config(temp_config_file):
    """Create a test configuration object."""
    return Config(config_file=temp_config_file)


def test_load_config(config):
    """Test loading a valid configuration file."""
    assert config.config is not None
    assert "global" in config.config
    assert "courses" in config.config


def test_get_course_config(config):
    """Test getting a course configuration."""
    course_config = config.get_course_config("test-course")
    assert course_config is not None
    assert course_config["show_name"] == "Test Course"
    assert course_config["course_link"] == "https://example.thinkific.com/courses/take/test-course"


def test_get_nonexistent_course(config):
    """Test getting a course that doesn't exist."""
    course_config = config.get_course_config("nonexistent-course")
    assert course_config == {}


def test_get_configuration_value(config):
    """Test getting a configuration value with dot notation."""
    value = config.get("global.video_quality")
    assert value == "720p"


def test_get_nonexistent_value(config):
    """Test getting a configuration value that doesn't exist."""
    value = config.get("global.nonexistent", fallback="default")
    assert value == "default"


def test_set_configuration_value(config, temp_config_file):
    """Test setting a configuration value."""
    config.set("global.video_quality", "1080p")
    assert config.get("global.video_quality") == "1080p"
    
    # Save and reload to check persistence
    config.save()
    config2 = Config(config_file=temp_config_file)
    assert config2.get("global.video_quality") == "1080p"


def test_validation_error():
    """Test validation error for invalid configuration."""
    with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as f:
        config = {
            "global": {
                "base_dir": "/tmp/thinkiplex",
                "video_quality": "invalid-quality",  # Invalid value
                "extract_audio": True,
                "audio_quality": 0,
                "audio_format": "mp3",
                "ffmpeg_presentation_merge": True,
            },
            "courses": {},
        }
        yaml.dump(config, f)
    
    try:
        with pytest.raises(ValidationError):
            Config(config_file=f.name)
    finally:
        os.unlink(f.name)