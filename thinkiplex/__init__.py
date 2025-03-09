"""
ThinkiPlex - A comprehensive tool for downloading and organizing Thinkific courses for Plex.

This package provides tools to download Thinkific courses and organize them for Plex media server.
"""

__version__ = "0.1.0"

from .cli import main
from .downloader import PHPDownloader
from .organizer import CourseOrganizer, MediaProcessor, MetadataExtractor
from .utils import Config, get_logger, setup_logging

__all__ = [
    "main",
    "PHPDownloader",
    "CourseOrganizer",
    "MetadataExtractor",
    "MediaProcessor",
    "Config",
    "setup_logging",
    "get_logger",
]
