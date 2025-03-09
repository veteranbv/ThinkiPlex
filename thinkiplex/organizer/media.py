"""
Media processing utilities for ThinkiPlex.

This module provides functions for processing video and audio files.
"""

import os
import shutil
import subprocess
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from ..utils.exceptions import FileSystemError, MediaProcessingError
from ..utils.logging import get_logger
from ..utils.parallel import parallel_map

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
            True if copy was successful

        Raises:
            FileSystemError: If the file cannot be copied
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
            raise FileSystemError(f"Failed to copy {source_path} to {target_path}: {e}") from e

    def add_video_metadata(self, video_path: str, metadata: dict) -> bool:
        """Add metadata to a video file.

        Args:
            video_path: Path to the video file
            metadata: Dictionary of metadata to add

        Returns:
            True if metadata was added successfully

        Raises:
            MediaProcessingError: If metadata cannot be added
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
            raise MediaProcessingError(f"Failed to add metadata to {video_path}: {e}") from e

    def extract_audio_from_video(
        self, video_path: str, audio_path: str, metadata: dict
    ) -> bool:
        """Extract audio from a video file.

        Args:
            video_path: Path to the video file
            audio_path: Path to the output audio file
            metadata: Dictionary of metadata to add

        Returns:
            True if extraction was successful

        Raises:
            MediaProcessingError: If audio extraction fails
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
                f"lib{self.audio_format}",
                "-q:a",
                str(self.audio_quality),
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
            raise MediaProcessingError(f"Failed to extract audio from {video_path} to {audio_path}: {e}") from e

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
            True if processing was successful

        Raises:
            FileSystemError: If file operations fail
            MediaProcessingError: If media processing fails
        """
        try:
            # Copy video to Plex directory
            self.copy_to_plex(video_path, plex_path)

            # Add metadata to video
            self.add_video_metadata(plex_path, metadata)

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

                self.extract_audio_from_video(
                    video_path, audio_path, audio_metadata
                )

            return True
        except (FileSystemError, MediaProcessingError) as e:
            logger.error(f"Error processing episode: {e}")
            raise
        
    def process_episodes_parallel(
        self, episodes_data: List[Dict[str, any]], max_workers: int = 4
    ) -> List[bool]:
        """Process multiple episodes in parallel.
        
        Args:
            episodes_data: List of episode data dictionaries containing:
                - video_path: Path to the source video file
                - plex_path: Path to the target Plex video file
                - audio_dir: Directory to store extracted audio
                - metadata: Dictionary of metadata to add
            max_workers: Maximum number of worker processes
            
        Returns:
            List of results (True for success, False for failure)
        """
        # Define worker function
        def process_episode_worker(data: Dict[str, any]) -> bool:
            try:
                return self.process_episode(
                    data["video_path"],
                    data["plex_path"],
                    data["audio_dir"],
                    data["metadata"]
                )
            except Exception as e:
                logger.error(f"Error processing episode: {e}")
                return False
        
        # Use parallel_map utility
        logger.info(f"Processing {len(episodes_data)} episodes in parallel with {max_workers} workers")
        results = parallel_map(
            process_episode_worker,
            episodes_data,
            max_workers=max_workers
        )
        
        logger.info(f"Completed processing {sum(1 for r in results if r)} of {len(results)} episodes")
        return results
        
    def extract_audio_batch(
        self, videos: List[Tuple[str, str, Dict[str, any]]], max_workers: int = 4
    ) -> List[bool]:
        """Extract audio from multiple videos in parallel.
        
        Args:
            videos: List of (video_path, audio_path, metadata) tuples
            max_workers: Maximum number of worker processes
            
        Returns:
            List of results (True for success, False for failure)
        """
        def extract_worker(data: Tuple[str, str, Dict[str, any]]) -> bool:
            video_path, audio_path, metadata = data
            try:
                return self.extract_audio_from_video(video_path, audio_path, metadata)
            except Exception as e:
                logger.error(f"Error extracting audio: {e}")
                return False
        
        logger.info(f"Extracting audio from {len(videos)} videos in parallel with {max_workers} workers")
        results = parallel_map(extract_worker, videos, max_workers=max_workers)
        
        logger.info(f"Completed extracting audio from {sum(1 for r in results if r)} of {len(results)} videos")
        return results
