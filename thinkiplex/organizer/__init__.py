"""
Organizer Package
---------------
This package provides functionality to organize course content for Plex.
"""

from thinkiplex.organizer.audio import extract_course_audio
from thinkiplex.organizer.main import organize_course

from .media import MediaProcessor
from .metadata import MetadataExtractor
from .organizer import CourseOrganizer

__all__ = [
    "CourseOrganizer",
    "MetadataExtractor",
    "MediaProcessor",
    "organize_course",
    "extract_course_audio",
]
