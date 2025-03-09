"""
Media processing utilities for ThinkiPlex.

This module provides functions for processing video and audio files.
"""

import os
import shutil
import subprocess
from datetime import datetime
from typing import Optional

from ..utils.logging import get_logger

logger = get_logger()


class MediaProcessor:
    """Processes video and audio files for Plex."""

    def __init__(self, ffmpeg_config: dict):
        """Initialize the media processor.

        Args:
            ffmpeg_config: FFmpeg configuration
        """
        self.extract_audio = ffmpeg_config.get("extract_audio", True)
        self.audio_quality = ffmpeg_config.get("audio_quality", "0")
        self.audio_format = ffmpeg_config.get("audio_format", "mp3")

    def find_video_file(self, directory: str) -> Optional[str]:
        """Find the main video file in a directory.

        Args:
            directory: Directory to search for video files

        Returns:
            Path to the video file, or None if not found
        """
        # First, try to find video files in subdirectories that match specific patterns
        video_dirs = []
        for root, dirs, _ in os.walk(directory):
            for d in dirs:
                if any(
                    pattern in d.lower() for pattern in ["watch", "video", "playback"]
                ):
                    video_dirs.append(os.path.join(root, d))

        # Search in video directories first
        for video_dir in video_dirs:
            for root, _, files in os.walk(video_dir):
                for file in files:
                    if file.endswith(".mp4"):
                        return os.path.join(root, file)

        # If not found, search the entire directory
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(".mp4"):
                    return os.path.join(root, file)

        return None

    def copy_to_plex(self, source_path: str, target_path: str) -> bool:
        """Copy a file to the Plex directory.

        Args:
            source_path: Path to the source file
            target_path: Path to the target file

        Returns:
            True if copy was successful, False otherwise
        """
        try:
            # Ensure target directory exists
            os.makedirs(os.path.dirname(target_path), exist_ok=True)

            # Copy the file
            shutil.copy2(source_path, target_path)
            logger.info(f"Copied {source_path} to {target_path}")

            return True
        except Exception as e:
            logger.error(f"Failed to copy file: {e}")
            return False

    def add_video_metadata(self, video_path: str, metadata: dict) -> bool:
        """Add metadata to a video file.

        Args:
            video_path: Path to the video file
            metadata: Dictionary of metadata to add

        Returns:
            True if metadata was added successfully, False otherwise
        """
        temp_path = f"{video_path}.temp"

        try:
            # Build ffmpeg command
            cmd = ["ffmpeg", "-v", "quiet", "-i", video_path]

            # Add metadata arguments
            for key, value in metadata.items():
                cmd.extend(["-metadata", f"{key}={value}"])

            # Add output arguments
            cmd.extend(["-codec", "copy", temp_path])

            # Run ffmpeg
            subprocess.run(cmd, check=True)

            # Replace original file with temp file
            shutil.move(temp_path, video_path)

            logger.info(f"Added metadata to {video_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to add metadata to video: {e}")
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return False

    def extract_audio_from_video(
        self, video_path: str, audio_path: str, metadata: dict
    ) -> bool:
        """Extract audio from a video file.

        Args:
            video_path: Path to the video file
            audio_path: Path to the output audio file
            metadata: Dictionary of metadata to add

        Returns:
            True if extraction was successful, False otherwise
        """
        if not self.extract_audio:
            return True

        try:
            # Ensure audio directory exists
            os.makedirs(os.path.dirname(audio_path), exist_ok=True)

            # Build ffmpeg command
            cmd = [
                "ffmpeg",
                "-v",
                "quiet",
                "-i",
                video_path,
                "-vn",
                "-c:a",
                f"lib{self.audio_format}lame",
                "-q:a",
                self.audio_quality,
            ]

            # Add metadata arguments
            for key, value in metadata.items():
                cmd.extend(["-metadata", f"{key}={value}"])

            # Add output path
            cmd.append(audio_path)

            # Run ffmpeg
            subprocess.run(cmd, check=True)

            logger.info(f"Extracted audio to {audio_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to extract audio: {e}")
            return False

    def process_episode(
        self, video_path: str, plex_path: str, audio_dir: str, metadata: dict
    ) -> bool:
        """Process a single episode: copy to Plex, add metadata, extract audio.

        Args:
            video_path: Path to the source video file
            plex_path: Path to the target Plex video file
            audio_dir: Directory to store extracted audio
            metadata: Dictionary of metadata to add

        Returns:
            True if processing was successful, False otherwise
        """
        # Copy video to Plex directory
        if not self.copy_to_plex(video_path, plex_path):
            return False

        # Add metadata to video
        if not self.add_video_metadata(plex_path, metadata):
            return False

        # Extract audio if configured
        if self.extract_audio:
            # Create audio metadata
            audio_metadata = metadata.copy()

            # Add audio-specific metadata
            if "title" in audio_metadata:
                audio_metadata["artist"] = metadata.get("show", "Unknown")
                audio_metadata["album"] = (
                    f"{metadata.get('show', 'Unknown')} ({datetime.now().year})"
                )
                audio_metadata["date"] = str(datetime.now().year)
                audio_metadata["genre"] = "Educational"

            # Extract audio
            audio_path = os.path.join(
                audio_dir,
                f"{os.path.splitext(os.path.basename(plex_path))[0]}.{self.audio_format}",
            )

            if not self.extract_audio_from_video(
                video_path, audio_path, audio_metadata
            ):
                return False

        return True
