"""
Tests for the media processing utilities.
"""

import os
import shutil
from unittest.mock import patch, MagicMock

import pytest

from thinkiplex.organizer.media import MediaProcessor
from thinkiplex.utils.exceptions import FileSystemError, MediaProcessingError


@pytest.fixture
def media_processor():
    """Create a test media processor."""
    return MediaProcessor({
        "extract_audio": True,
        "audio_quality": 0,
        "audio_format": "mp3",
    })


@pytest.fixture
def setup_test_file(temp_dir):
    """Create a test file."""
    test_file = temp_dir / "test.txt"
    with open(test_file, "w") as f:
        f.write("test content")
    return test_file


def test_copy_to_plex_success(media_processor, temp_dir, setup_test_file):
    """Test successful file copy to Plex."""
    source_path = setup_test_file
    target_dir = temp_dir / "plex"
    target_path = target_dir / "test.txt"
    
    # Copy should succeed
    result = media_processor.copy_to_plex(str(source_path), str(target_path))
    
    assert result is True
    assert os.path.exists(target_path)
    assert open(target_path, "r").read() == "test content"


def test_copy_to_plex_failure(media_processor, temp_dir):
    """Test file copy failure."""
    source_path = temp_dir / "nonexistent.txt"
    target_path = temp_dir / "plex" / "nonexistent.txt"
    
    # Copy should fail with FileSystemError
    with pytest.raises(FileSystemError):
        media_processor.copy_to_plex(str(source_path), str(target_path))


@patch("subprocess.run")
def test_add_video_metadata_success(mock_run, media_processor, temp_dir, setup_test_file):
    """Test successful metadata addition."""
    video_path = setup_test_file
    metadata = {"title": "Test Video", "show": "Test Show"}
    
    # Mock shutil.move to avoid actually moving files
    with patch("shutil.move") as mock_move:
        result = media_processor.add_video_metadata(str(video_path), metadata)
    
    assert result is True
    mock_run.assert_called_once()
    # Check that ffmpeg was called with correct arguments
    call_args = mock_run.call_args[0][0]
    assert "-metadata" in call_args
    assert f"title={metadata['title']}" in call_args[call_args.index("-metadata") + 1]


@patch("subprocess.run", side_effect=Exception("ffmpeg error"))
def test_add_video_metadata_failure(mock_run, media_processor, temp_dir, setup_test_file):
    """Test metadata addition failure."""
    video_path = setup_test_file
    metadata = {"title": "Test Video", "show": "Test Show"}
    
    # Should raise MediaProcessingError
    with pytest.raises(MediaProcessingError):
        media_processor.add_video_metadata(str(video_path), metadata)


@patch("subprocess.run")
def test_extract_audio_success(mock_run, media_processor, temp_dir, setup_test_file):
    """Test successful audio extraction."""
    video_path = str(setup_test_file)
    audio_path = str(temp_dir / "audio" / "test.mp3")
    metadata = {"title": "Test Audio", "show": "Test Show"}
    
    result = media_processor.extract_audio_from_video(video_path, audio_path, metadata)
    
    assert result is True
    mock_run.assert_called_once()
    # Check that ffmpeg was called with correct arguments
    call_args = mock_run.call_args[0][0]
    assert "-vn" in call_args  # Video removal flag
    assert "-metadata" in call_args
    assert audio_path in call_args  # Output path is last argument


@patch("subprocess.run", side_effect=Exception("ffmpeg error"))
def test_extract_audio_failure(mock_run, media_processor, temp_dir, setup_test_file):
    """Test audio extraction failure."""
    video_path = str(setup_test_file)
    audio_path = str(temp_dir / "audio" / "test.mp3")
    metadata = {"title": "Test Audio", "show": "Test Show"}
    
    # Should raise MediaProcessingError
    with pytest.raises(MediaProcessingError):
        media_processor.extract_audio_from_video(video_path, audio_path, metadata)