"""
Metadata utilities for ThinkiPlex.

This module provides functions for extracting and managing metadata for episodes.
"""

import re
from typing import Any, Dict, Optional, Tuple

from ..utils.logging import get_logger

logger = get_logger()


class MetadataExtractor:
    """Extracts metadata from course data and directory names."""

    def __init__(self, course_data: Optional[Dict[str, Any]] = None):
        """Initialize the metadata extractor.

        Args:
            course_data: Course data from the downloader
        """
        self.course_data = course_data or {}

    def extract_episode_number(self, dir_name: str) -> int:
        """Extract episode number from directory name.

        Args:
            dir_name: Directory name to extract episode number from

        Returns:
            Episode number as integer, or 0 if not found
        """
        match = re.match(r"^(\d+)\.", dir_name)
        if match:
            return int(match.group(1))
        return 0

    def extract_from_course_data(
        self, ep_num: int
    ) -> Tuple[Optional[str], Optional[str]]:
        """Extract title and description from course data if available.

        Args:
            ep_num: Episode number

        Returns:
            Tuple of (title, description) or (None, None) if not found
        """
        if not self.course_data:
            return None, None

        # Try to find the content in the course data
        if "contents" in self.course_data:
            for content in self.course_data["contents"]:
                # Check if this content matches the episode number
                content_id = content.get("id", "")
                if str(content_id) == str(ep_num) or content.get("position") == ep_num:
                    title = content.get("name", "")
                    description = content.get("description", "")
                    return title, description

        # Try to find in chapters
        if "chapters" in self.course_data:
            for chapter in self.course_data["chapters"]:
                if chapter.get("position") == ep_num:
                    title = chapter.get("name", "")
                    description = chapter.get("description", "")
                    return title, description

        return None, None

    def get_episode_title(self, ep_num: int, dir_name: str) -> str:
        """Get episode title from course data or extract from directory name.

        Args:
            ep_num: Episode number
            dir_name: Directory name to extract title from if not found in course data

        Returns:
            Episode title
        """
        # Try to get from course data
        title, _ = self.extract_from_course_data(ep_num)
        if title:
            return title

        # Extract from directory name
        title = re.sub(r"^[0-9]+\.\s*", "", dir_name)
        title = re.sub(
            r"-[0-9]+-[0-9]+-[0-9]+$", "", title
        )  # Remove date suffix if present
        title = title.replace(
            "-", " "
        ).title()  # Replace hyphens with spaces and capitalize

        logger.info(f"Using extracted title for episode {ep_num}: {title}")
        return title

    def get_episode_description(self, ep_num: int, dir_name: str) -> str:
        """Get episode description from course data or generate a description.

        Args:
            ep_num: Episode number
            dir_name: Directory name (used for context in generic description)

        Returns:
            Episode description
        """
        # Try to get from course data
        _, description = self.extract_from_course_data(ep_num)
        if description:
            return description

        # Generate a more descriptive generic description based on the directory name
        title = self.get_episode_title(ep_num, dir_name)

        # Check if it's a live call or heart sync session
        if "live" in dir_name.lower() or "call" in dir_name.lower():
            description = f"Live call session {ep_num} focusing on {title.lower()}"
        elif "heart" in dir_name.lower() or "sync" in dir_name.lower():
            description = f"Heart Sync session {ep_num} providing guided practice related to {title.lower()}"
        else:
            description = f"Episode {ep_num}: {title}"

        logger.info(f"Using generated description for episode {ep_num}")
        return description
