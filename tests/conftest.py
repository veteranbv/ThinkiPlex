"""
Fixtures for tests.
"""

import os
import tempfile
from pathlib import Path

import pytest
import yaml


@pytest.fixture
def temp_config_file():
    """Create a temporary configuration file."""
    with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as f:
        config = {
            "global": {
                "base_dir": "/tmp/thinkiplex",
                "video_quality": "720p",
                "extract_audio": True,
                "audio_quality": 0,
                "audio_format": "mp3",
                "ffmpeg_presentation_merge": True,
            },
            "courses": {
                "test-course": {
                    "course_link": "https://example.thinkific.com/courses/take/test-course",
                    "show_name": "Test Course",
                    "season": "01",
                    "video_quality": "720p",
                    "extract_audio": True,
                    "audio_quality": 0,
                    "audio_format": "mp3",
                    "client_date": "test-date",
                    "cookie_data": "test-cookie",
                    "video_download_quality": "720p",
                }
            },
        }
        yaml.dump(config, f)
        
    yield f.name
    os.unlink(f.name)


@pytest.fixture
def temp_dir():
    """Create a temporary directory."""
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)