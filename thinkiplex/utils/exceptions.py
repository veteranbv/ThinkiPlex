"""
Custom exceptions for ThinkiPlex.

This module provides custom exception classes for better error handling and reporting.
"""

class ThinkiPlexError(Exception):
    """Base exception for all ThinkiPlex errors."""
    pass


class ConfigError(ThinkiPlexError):
    """Raised when there's an issue with the configuration."""
    pass


class ValidationError(ConfigError):
    """Raised when configuration validation fails."""
    pass


class DownloaderError(ThinkiPlexError):
    """Raised when there's an issue with the downloader."""
    pass


class PHPError(DownloaderError):
    """Raised when there's an issue with the PHP downloader."""
    pass


class DockerError(DownloaderError):
    """Raised when there's an issue with Docker."""
    pass


class OrganizerError(ThinkiPlexError):
    """Raised when there's an issue with organizing files."""
    pass


class MediaProcessingError(OrganizerError):
    """Raised when there's an issue with media processing."""
    pass


class MetadataError(OrganizerError):
    """Raised when there's an issue with metadata."""
    pass


class FileSystemError(ThinkiPlexError):
    """Raised when there's an issue with file system operations."""
    pass


class NetworkError(ThinkiPlexError):
    """Raised when there's a network-related issue."""
    pass


class AuthenticationError(NetworkError):
    """Raised when there's an authentication issue."""
    pass


class TranscriptionError(ThinkiPlexError):
    """Raised when there's an issue with audio transcription."""
    pass


class AIProcessingError(ThinkiPlexError):
    """Raised when there's an issue with AI processing."""
    pass