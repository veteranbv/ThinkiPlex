"""
Downloader package for ThinkiPlex.

This package provides functionality for downloading Thinkific courses.
"""

from .php_wrapper import PHPDownloader

__all__ = ["PHPDownloader"]
