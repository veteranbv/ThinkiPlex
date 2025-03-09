"""
Schema definitions for configuration validation.

This module provides Pydantic models for validating configuration.
"""

from typing import Dict, List, Optional, Union
from pydantic import BaseModel, Field, validator, HttpUrl


class CourseConfig(BaseModel):
    """Schema for a course configuration."""
    
    course_link: str = Field(..., description="URL to the Thinkific course")
    show_name: str = Field(..., description="Name to use in Plex")
    season: str = Field("01", description="Season number for Plex")
    video_quality: str = Field("720p", description="Video quality for download")
    extract_audio: bool = Field(True, description="Whether to extract audio from videos")
    audio_quality: int = Field(0, description="Audio quality (0-9, 0 is best)")
    audio_format: str = Field("mp3", description="Audio format")
    client_date: Optional[str] = Field(None, description="Date header from network request")
    cookie_data: Optional[str] = Field(None, description="Cookie data from network request")
    video_download_quality: str = Field("720p", description="Quality for video downloads")
    
    @validator("video_quality", "video_download_quality")
    def validate_quality(cls, v):
        valid_qualities = ["Original File", "1080p", "720p", "540p", "360p", "224p"]
        if v not in valid_qualities:
            raise ValueError(f"Quality must be one of {valid_qualities}")
        return v
    
    @validator("audio_format")
    def validate_audio_format(cls, v):
        valid_formats = ["mp3", "aac", "flac", "ogg"]
        if v not in valid_formats:
            raise ValueError(f"Audio format must be one of {valid_formats}")
        return v


class GlobalConfig(BaseModel):
    """Schema for global configuration."""
    
    base_dir: str = Field(..., description="Base directory for ThinkiPlex")
    video_quality: str = Field("720p", description="Default video quality")
    extract_audio: bool = Field(True, description="Whether to extract audio by default")
    audio_quality: int = Field(0, description="Default audio quality")
    audio_format: str = Field("mp3", description="Default audio format")
    ffmpeg_presentation_merge: bool = Field(True, description="Whether to merge presentation files")
    
    @validator("video_quality")
    def validate_quality(cls, v):
        valid_qualities = ["Original File", "1080p", "720p", "540p", "360p", "224p"]
        if v not in valid_qualities:
            raise ValueError(f"Quality must be one of {valid_qualities}")
        return v
    
    @validator("audio_format")
    def validate_audio_format(cls, v):
        valid_formats = ["mp3", "aac", "flac", "ogg"]
        if v not in valid_formats:
            raise ValueError(f"Audio format must be one of {valid_formats}")
        return v


class ThinkiPlexConfig(BaseModel):
    """Schema for the complete ThinkiPlex configuration."""
    
    global_config: GlobalConfig = Field(..., alias="global")
    courses: Dict[str, CourseConfig] = Field(default_factory=dict)