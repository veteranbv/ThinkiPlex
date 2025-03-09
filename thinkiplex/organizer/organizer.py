"""
Main organizer module for ThinkiPlex.

This module provides the main functionality for organizing course content for Plex.
"""

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from ..utils.logging import get_logger
from .media import MediaProcessor
from .metadata import MetadataExtractor

logger = get_logger()


class CourseOrganizer:
    """Organizes course content for Plex."""

    def __init__(
        self,
        source_dir: Path,
        plex_base_dir: Path,
        show_name: str,
        season: str,
        course_data: Optional[Dict[str, Any]] = None,
        ffmpeg_config: Optional[Dict[str, Any]] = None,
    ):
        """Initialize the course organizer.

        Args:
            source_dir: Directory containing the downloaded course content
            plex_base_dir: Directory where Plex-formatted content will be stored
            show_name: Name of the show in Plex
            season: Season number
            course_data: Course data from the downloader
            ffmpeg_config: FFmpeg configuration
        """
        self.source_dir = source_dir
        self.plex_base_dir = plex_base_dir
        self.show_name = show_name
        self.season = season

        # Create metadata extractor
        self.metadata_extractor = MetadataExtractor(course_data)

        # Create media processor
        self.media_processor = MediaProcessor(ffmpeg_config or {})

        # Track processed episodes to avoid duplicates
        self.processed_episodes: Set[int] = set()

        # Create necessary directories
        self._create_directories()

    def _create_directories(self) -> None:
        """Create necessary directory structure."""
        # Create Plex directory structure
        self.plex_show_dir = self.plex_base_dir / self.show_name
        self.plex_season_dir = self.plex_show_dir / f"Season {self.season}"

        os.makedirs(self.plex_show_dir, exist_ok=True)
        os.makedirs(self.plex_season_dir, exist_ok=True)

        logger.info("Created Plex directory structure:")
        logger.info(f"- {self.plex_show_dir}")
        logger.info(f"- {self.plex_season_dir}")

    def process_directory(self, directory: str) -> bool:
        """Process a course directory to extract episode information.

        Args:
            directory: Directory to process

        Returns:
            True if processing was successful, False otherwise
        """
        dir_name = os.path.basename(directory)

        # Skip if not a directory
        if not os.path.isdir(directory):
            return False

        # Extract episode number
        ep_num = self.metadata_extractor.extract_episode_number(dir_name)
        if ep_num == 0:
            logger.warning(
                f"Could not extract episode number from directory: {dir_name}"
            )
            return False

        # Skip if already processed
        if ep_num in self.processed_episodes:
            logger.info(f"Episode {ep_num} already processed. Skipping.")
            return True

        # Find the video file
        video_file = self.media_processor.find_video_file(directory)
        if not video_file:
            logger.warning(f"No video file found in directory: {directory}")
            return False

        # Get episode title and description
        title = self.metadata_extractor.get_episode_title(ep_num, dir_name)
        description = self.metadata_extractor.get_episode_description(ep_num, dir_name)

        # Format episode number with leading zero if needed
        ep_num_padded = f"{ep_num:02d}"

        # Define target filename in Plex directory
        plex_filename = (
            f"{self.show_name} - s{self.season}e{ep_num_padded} - {title}.mp4"
        )
        plex_filepath = os.path.join(self.plex_season_dir, plex_filename)

        logger.info(f"Processing Episode {ep_num}: {title}")

        # Create metadata dictionary
        metadata = {
            "title": title,
            "episode_id": str(ep_num),
            "season_number": self.season,
            "episode_sort": str(ep_num),
            "show": self.show_name,
            "description": description,
        }

        # Create audio directory
        audio_dir = os.path.join(os.path.dirname(video_file), "audio")

        # Process the episode
        success = self.media_processor.process_episode(
            video_file, plex_filepath, audio_dir, metadata
        )

        if success:
            # Mark as processed
            self.processed_episodes.add(ep_num)
            logger.info(f"Episode {ep_num} processed successfully!")

        return success

    def organize_course(self) -> int:
        """Organize the course content for Plex.

        Returns:
            Number of episodes processed successfully
        """
        logger.info(f"Scanning for episodes in {self.source_dir}...")

        # Get all directories that start with a number
        dirs = [
            d
            for d in os.listdir(self.source_dir)
            if os.path.isdir(os.path.join(self.source_dir, d))
            and re.match(r"^[0-9]", d)
        ]

        # Sort directories by episode number
        dirs.sort(key=lambda x: self.metadata_extractor.extract_episode_number(x))

        # Process each directory
        successful_episodes = 0
        for dir_name in dirs:
            dir_path = os.path.join(self.source_dir, dir_name)
            if self.process_directory(dir_path):
                successful_episodes += 1

        logger.info(
            f"Processing complete! {successful_episodes} episodes processed successfully."
        )

        # Generate verification commands
        self._generate_verification_commands(dirs)

        return successful_episodes

    def _generate_verification_commands(self, dirs: List[str]) -> None:
        """Generate verification commands for checking metadata.

        Args:
            dirs: List of directory names
        """
        if not self.processed_episodes:
            return

        first_ep = min(self.processed_episodes)
        first_dir = next(
            (
                d
                for d in dirs
                if self.metadata_extractor.extract_episode_number(d) == first_ep
            ),
            dirs[0],
        )
        first_title = self.metadata_extractor.get_episode_title(first_ep, first_dir)
        ep_num_padded = f"{first_ep:02d}"

        logger.info("")
        logger.info("To verify metadata in a video file, run:")
        logger.info(
            f"ffprobe -v quiet -print_format json -show_format "
            f'"{os.path.join(self.plex_season_dir, self.show_name)} - '
            f's{self.season}e{ep_num_padded} - {first_title}.mp4"'
        )

        # If audio extraction is enabled
        if self.media_processor.extract_audio:
            audio_format = self.media_processor.audio_format
            logger.info("")
            logger.info("To verify metadata in an audio file, run:")
            logger.info(
                f"ffprobe -v quiet -print_format json -show_format "
                f'"{os.path.join(self.source_dir, first_dir, "audio", self.show_name)} - '
                f's{self.season}e{ep_num_padded} - {first_title}.{audio_format}"'
            )
