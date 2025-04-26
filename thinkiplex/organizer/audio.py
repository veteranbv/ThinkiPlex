"""
Audio Extraction Module
---------------------
This module provides functionality for extracting audio from video files.
"""

import logging
import os
import re
import shutil
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from thinkiplex.downloader.php_wrapper import PHPDownloader
from thinkiplex.utils import Config

logger = logging.getLogger(__name__)


def extract_episode_number(directory_name: str) -> str:
    """
    Extract the episode number from a directory name.

    Args:
        directory_name: Directory name

    Returns:
        Episode number as a string
    """
    # Extract the first number from the directory name
    match = re.search(r"^(\d+)", directory_name)
    if match:
        # Ensure the episode number is two digits
        ep_num = match.group(1)
        # Ensure the episode number is two digits
        if len(ep_num) == 1:
            ep_num = f"0{ep_num}"
        return ep_num
    return "01"  # Default to episode 1 if no number found


def extract_title(directory_name: str) -> str:
    """
    Extract the title from a directory name.

    Args:
        directory_name: Name of the directory

    Returns:
        Title as a string
    """
    # Remove leading episode number and dot
    title = re.sub(r"^\d+\.\s*", "", directory_name)

    # Remove trailing date if present
    title = re.sub(r"-\d+-\d+-\d+$", "", title)

    # Replace hyphens with spaces and capitalize words
    title = title.replace("-", " ").strip()
    title = " ".join(word.capitalize() for word in title.split())

    return title


def find_video_file(directory: Path) -> Optional[Path]:
    """
    Find a video file in a directory.

    Args:
        directory: Directory to search

    Returns:
        Path to the video file or None if not found
    """
    # Define common video extensions
    video_extensions = [".mp4", ".mkv", ".avi", ".mov", ".webm", ".m4v"]

    # First try to find in paths that might contain lesson videos
    priority_patterns = ["playback-lesson", "watch", "video", "playback"]

    # Look in priority directories first
    for root, _, files in os.walk(directory):
        # Check if this directory matches any priority patterns
        if any(pattern in root.lower() for pattern in priority_patterns):
            for file in files:
                file_ext = os.path.splitext(file)[1].lower()
                if file_ext in video_extensions:
                    return Path(root) / file

    # If not found in priority directories, search the entire directory
    for root, _, files in os.walk(directory):
        for file in files:
            file_ext = os.path.splitext(file)[1].lower()
            if file_ext in video_extensions:
                return Path(root) / file

    return None


def extract_audio_to_original_directory(
    video_file: Path,
    audio_quality: int = 0,
    audio_format: str = "mp3",
) -> Optional[Path]:
    """
    Extract audio from a video file and save it with the same name in an 'audio' directory
    next to the video file.

    Args:
        video_file: Path to the video file
        audio_quality: Audio quality (0-9, where 0 is best)
        audio_format: Audio format (mp3, aac, flac, ogg)

    Returns:
        Path to the extracted audio file, or None if extraction failed
    """
    if not video_file.exists():
        logger.warning(f"Video file does not exist: {video_file}")
        return None

    # Create audio directory next to the video file
    audio_dir = video_file.parent.parent / "audio"
    os.makedirs(audio_dir, exist_ok=True)

    # Create output filename with the same name as the video file
    output_filename = f"{video_file.stem}.{audio_format}"
    output_file = audio_dir / output_filename

    # Skip if the audio file already exists
    if output_file.exists():
        logger.info(f"Audio file already exists: {output_file}")
        return output_file

    # Build ffmpeg command
    ffmpeg_cmd = [
        "ffmpeg",
        "-i",
        str(video_file),
        "-vn",  # No video
        "-q:a",
        str(audio_quality),  # Audio quality
        "-y",  # Overwrite output file
        str(output_file),
    ]

    # Run ffmpeg
    try:
        logger.info(f"Extracting audio from {video_file} to {output_file}")
        subprocess.run(ffmpeg_cmd, check=True, capture_output=True)
        logger.info(f"Audio extraction complete: {output_file}")
        return output_file
    except subprocess.CalledProcessError as e:
        logger.error(f"Error extracting audio: {e}")
        logger.error(f"ffmpeg stderr: {e.stderr.decode()}")
        return None


def extract_audio(
    course_dir: Path,
    output_dir: Path,
    show_name: str,
    season: str = "01",
    audio_quality: int = 0,
    audio_format: str = "mp3",
    metadata: Optional[Dict[str, str]] = None,
    chapter_titles: Optional[Dict[str, str]] = None,
    session_types: Optional[Dict[str, Dict[str, str]]] = None,
) -> List[str]:
    """
    Extract audio from video files in a course directory.

    Args:
        course_dir: Directory containing the course content
        output_dir: Directory to output audio files
        show_name: Name of the show
        season: Season number
        audio_quality: Audio quality (0-9, where 0 is best)
        audio_format: Audio format (mp3, aac, flac, ogg)
        metadata: Additional metadata to add to the audio files
        chapter_titles: Mapping of chapter IDs to titles
        session_types: Dictionary of session type patterns and their description templates

    Returns:
        List of processed files
    """
    logger.info(f"Extracting audio from {course_dir} to {output_dir}")

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    processed_files = []

    # Get all numbered directories and sort them
    numbered_dirs = []
    for item in os.listdir(course_dir):
        if not item[0].isdigit():
            continue

        dir_num_match = re.search(r"^(\d+)", item)
        if dir_num_match:
            dir_num = int(dir_num_match.group(1))
            numbered_dirs.append((dir_num, item))

    # Sort directories by number
    numbered_dirs.sort()

    # Filter to only include directories with video files
    video_dirs = []
    for dir_num, dir_name in numbered_dirs:
        dir_path = course_dir / dir_name
        if not dir_path.is_dir():
            continue

        video_file = find_video_file(dir_path)
        if video_file:
            video_dirs.append((dir_num, dir_name))
            # Also extract audio to the original directory with the same name
            extract_audio_to_original_directory(
                video_file=video_file,
                audio_quality=audio_quality,
                audio_format=audio_format,
            )

    # Default session type patterns if none provided
    if session_types is None:
        session_types = {}

    # Process each directory with video files, assigning sequential episode numbers starting from 01
    for i, (dir_num, dir_name) in enumerate(video_dirs):
        # Assign sequential episode number starting from 1
        ep_num = f"{i + 1:02d}"  # Format as two digits with leading zero

        dir_path = course_dir / dir_name
        video_file = find_video_file(dir_path)

        if not video_file:
            logger.warning(f"No video file found in {dir_path}")
            continue

        # Extract title from directory name
        title = extract_title(dir_name)

        # If we have chapter titles, try to find a better title
        if chapter_titles and ep_num in chapter_titles:
            title = chapter_titles[ep_num]

        logger.info(f"Processing {title}")

        # Create output filename with the same format as the video files
        output_filename = f"{show_name} - s{season}e{ep_num} - {title}.{audio_format}"
        output_file = output_dir / output_filename

        # Skip if file already exists
        if output_file.exists():
            logger.info(f"Skipping {title} (already exists)")
            processed_files.append(str(output_file))
            continue

        # Generate a description based on the title and directory name
        description = f"Episode {ep_num} of the {show_name} course."

        # Apply session type detection based on configured patterns
        dir_name_lower = dir_name.lower()

        # Try to match session type patterns
        for session_key, session_info in session_types.items():
            if session_key in dir_name_lower:
                # Try to extract session number if pattern provided
                if "pattern" in session_info:
                    match = re.search(session_info["pattern"], dir_name_lower)
                    if match and "template" in session_info:
                        # If found a number, format it into the template
                        try:
                            # Try positional formatting first
                            description = session_info["template"].format(
                                match.group(1), title=title, show_name=show_name, ep_num=ep_num
                            )
                        except (IndexError, KeyError):
                            # Fall back to keyword formatting
                            description = session_info["template"].format(
                                title=title,
                                show_name=show_name,
                                session_num=match.group(1),
                                ep_num=ep_num,
                            )
                    else:
                        # Use default template if no match found
                        description = session_info.get(
                            "default_template",
                            f"{session_key.replace('-', ' ').title()} focusing on {title}. Part of the {show_name} course.",
                        )
                else:
                    # No pattern defined, use simple template
                    description = session_info.get(
                        "template",
                        f"{session_key.replace('-', ' ').title()} focusing on {title}. Part of the {show_name} course.",
                    )
                break

        # Build metadata arguments
        metadata_args = [
            "-metadata",
            f"title={title}",
            "-metadata",
            f"artist={show_name}",
            "-metadata",
            f"album={show_name}",
            "-metadata",
            f"track={ep_num}",
            "-metadata",
            f"date={datetime.now().year}",
            "-metadata",
            "genre=Educational",
            "-metadata",
            f"description={description}",
            "-metadata",
            f"comment=Part of the {show_name} course",
        ]

        # Add custom metadata if provided
        if metadata:
            for key, value in metadata.items():
                metadata_args.extend(["-metadata", f"{key}={value}"])

        # Build ffmpeg command
        ffmpeg_cmd = [
            "ffmpeg",
            "-i",
            str(video_file),
            "-vn",  # Disable video
            "-q:a",
            str(audio_quality),  # Audio quality (0-9, where 0 is best)
            *metadata_args,
            str(output_file),
        ]

        # Run ffmpeg
        try:
            subprocess.run(
                ffmpeg_cmd,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            logger.info(f"Processed {title}")
            processed_files.append(str(output_file))
        except subprocess.CalledProcessError as e:
            logger.error(f"Error processing {title}: {e}")
            logger.error(f"ffmpeg stderr: {e.stderr.decode()}")

    return processed_files


def extract_course_audio(
    course_name: str,
    base_dir: Path,
    show_name: Optional[str] = None,
    season: str = "01",
    audio_quality: int = 0,
    audio_format: str = "mp3",
) -> bool:
    """
    Extract audio from a course.

    Args:
        course_name: Name of the course
        base_dir: Base directory for the course
        show_name: Name of the show (defaults to course_name)
        season: Season number
        audio_quality: Audio quality (0-9, where 0 is best)
        audio_format: Audio format (mp3, aac, flac, ogg)

    Returns:
        True if successful, False otherwise
    """
    # Get course data to extract chapter titles
    course_data = {}
    config = None
    try:
        config = Config(str(base_dir / "config" / "thinkiplex.yaml"))
        downloader = PHPDownloader(base_dir, config=config)
        course_data = downloader.get_course_data(course_name)
    except Exception as e:
        logger.warning(f"Failed to get course data: {e}")

    # Read session types from config if available
    session_types = None
    if config:
        # Try to get global session types first
        session_types = config.get("session_types", {})

        # Check for course-specific session types that would override globals
        course_configs = config.get("courses", {})
        if course_name in course_configs:
            course_config = course_configs.get(course_name, {})
            if "session_types" in course_config:
                # Course-specific settings override global settings
                session_types = course_config.get("session_types")

    if not session_types:
        # Default empty session types if not defined in config
        session_types = {}
        logger.info("No session types found in configuration")

    # Extract chapter titles from course data
    chapter_titles = {}
    if course_data and "chapters" in course_data:
        for chapter in course_data.get("chapters", []):
            chapter_id = chapter.get("id", "")
            chapter_title = chapter.get("title", "")
            if chapter_id and chapter_title:
                chapter_titles[chapter_id] = chapter_title

    # If we have episodes in the course data, create a mapping of episode numbers to titles
    episode_titles = {}
    if course_data and "chapters" in course_data:
        episode_index = 1
        for chapter in course_data.get("chapters", []):
            for episode in chapter.get("episodes", []):
                if episode.get("type") == "video":
                    episode_id = episode.get("id", "")
                    episode_title = episode.get("title", "")
                    if episode_id and episode_title:
                        episode_titles[f"{episode_index:02d}"] = episode_title
                        episode_index += 1

    if show_name is None:
        show_name = course_name

    # Format the show name for directory naming
    # Check if show_name already contains the year to avoid duplication
    if "-" in course_name and not re.search(r"\(\d{4}\)", show_name):
        year = course_name.split("-")[-1]
        if year.isdigit() and len(year) == 4:
            formatted_show_name = f"{show_name} ({year})"
        else:
            formatted_show_name = show_name
    else:
        formatted_show_name = show_name

    # Create paths
    course_dir = base_dir / "data" / "courses" / course_name / "downloads"

    # Use the Plex directory structure
    output_dir = (
        base_dir
        / "data"
        / "courses"
        / course_name
        / "plex"
        / "audiobooks"
        / formatted_show_name
        / f"Season {season}"
    )

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Check if audio files already exist in the output directory
    existing_audio_files = list(output_dir.glob(f"*.{audio_format}"))
    if existing_audio_files:
        # Count how many audio files we expect based on video directories
        video_dir_count = 0
        for item in os.listdir(course_dir):
            if not item[0].isdigit():
                continue
            dir_path = course_dir / item
            if not dir_path.is_dir():
                continue
            video_file = find_video_file(dir_path)
            if video_file:
                video_dir_count += 1

        # If we have the same number of audio files as video directories, we can skip
        if len(existing_audio_files) >= video_dir_count:
            logger.info(f"Audio files already exist in {output_dir}. Skipping audio extraction.")

            # Still process videos to ensure they're in the right place
            video_output_dir = (
                base_dir
                / "data"
                / "courses"
                / course_name
                / "plex"
                / "home-video"
                / formatted_show_name
                / f"Season {season}"
            )

            os.makedirs(video_output_dir, exist_ok=True)

            # Check if video files already exist
            existing_video_files = []
            video_extensions = [".mp4", ".mkv", ".avi", ".mov", ".webm", ".m4v"]
            for ext in video_extensions:
                existing_video_files.extend(list(video_output_dir.glob(f"*{ext}")))

            if len(existing_video_files) >= video_dir_count:
                logger.info(
                    f"Video files already exist in {video_output_dir}. Skipping video processing."
                )
                return True

            # Process videos for Plex
            process_videos_for_plex(
                course_dir=course_dir,
                output_dir=video_output_dir,
                show_name=formatted_show_name,
                season=season,
                chapter_titles=episode_titles,
                session_types=session_types,
            )

            return True

    # Extract audio
    try:
        extract_audio(
            course_dir=course_dir,
            output_dir=output_dir,
            show_name=formatted_show_name,
            season=season,
            audio_quality=audio_quality,
            audio_format=audio_format,
            chapter_titles=episode_titles,  # Pass episode titles instead of chapter titles
            session_types=session_types,
        )

        # Also process videos for Plex
        video_output_dir = (
            base_dir
            / "data"
            / "courses"
            / course_name
            / "plex"
            / "home-video"
            / formatted_show_name
            / f"Season {season}"
        )

        os.makedirs(video_output_dir, exist_ok=True)

        # Copy video files to the Plex directory
        process_videos_for_plex(
            course_dir=course_dir,
            output_dir=video_output_dir,
            show_name=formatted_show_name,
            season=season,
            chapter_titles=episode_titles,
            session_types=session_types,
        )

        return True
    except Exception as e:
        logger.error(f"Failed to extract audio: {e}")
        return False


def process_videos_for_plex(
    course_dir: Path,
    output_dir: Path,
    show_name: str,
    season: str = "01",
    chapter_titles: Optional[Dict[str, str]] = None,
    session_types: Optional[Dict[str, Dict[str, str]]] = None,
) -> List[str]:
    """
    Process video files for Plex.

    Args:
        course_dir: Directory containing the course content
        output_dir: Directory to output video files
        show_name: Name of the show
        season: Season number
        chapter_titles: Mapping of chapter IDs to titles
        session_types: Dictionary of session type patterns and their description templates
                      e.g. {"workshop": {"pattern": "workshop-(\\d+)",
                                           "template": "Workshop session {0} providing hands-on practice"}}

    Returns:
        List of processed files
    """
    logger.info(f"Processing videos from {course_dir} to {output_dir}")

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Default session type patterns if none provided
    if session_types is None:
        session_types = {}

    processed_files = []

    # Get all numbered directories and sort them
    numbered_dirs = []
    for item in os.listdir(course_dir):
        if not item[0].isdigit():
            continue

        dir_num_match = re.search(r"^(\d+)", item)
        if dir_num_match:
            dir_num = int(dir_num_match.group(1))
            numbered_dirs.append((dir_num, item))

    # Sort directories by number
    numbered_dirs.sort()

    # Filter to only include directories with video files
    video_dirs = []
    for dir_num, dir_name in numbered_dirs:
        dir_path = course_dir / dir_name
        if not dir_path.is_dir():
            continue

        video_file = find_video_file(dir_path)
        if video_file:
            video_dirs.append((dir_num, dir_name, video_file))

    # Define common video extensions for existing file check
    video_extensions = [".mp4", ".mkv", ".avi", ".mov", ".webm", ".m4v"]

    # Check if we already have the expected number of video files
    existing_video_files = []
    for ext in video_extensions:
        existing_video_files.extend(list(output_dir.glob(f"*{ext}")))

    if len(existing_video_files) >= len(video_dirs):
        logger.info(f"All video files already exist in {output_dir}. Skipping video processing.")
        return [str(f) for f in existing_video_files]

    # Process each directory with video files, assigning sequential episode numbers starting from 01
    for i, (dir_num, dir_name, video_file) in enumerate(video_dirs):
        # Assign sequential episode number starting from 1
        ep_num = f"{i + 1:02d}"  # Format as two digits with leading zero

        # Extract title from directory name
        title = extract_title(dir_name)

        # If we have chapter titles, try to find a better title
        if chapter_titles and ep_num in chapter_titles:
            title = chapter_titles[ep_num]

        logger.info(f"Processing video {title}")

        # Get original file extension and use it for the output
        video_ext = os.path.splitext(video_file)[1]
        output_filename = f"{show_name} - s{season}e{ep_num} - {title}{video_ext}"
        output_file = output_dir / output_filename

        # Generate a description based on the title and directory name
        description = f"Episode {ep_num} of the {show_name} course."

        # Apply session type detection based on configured patterns
        dir_name_lower = dir_name.lower()
        session_type_detected = False

        # Try to match session type patterns
        for session_key, session_info in session_types.items():
            if session_key in dir_name_lower:
                # Try to extract session number if pattern provided
                if "pattern" in session_info:
                    match = re.search(session_info["pattern"], dir_name_lower)
                    if match and "template" in session_info:
                        # If found a number, format it into the template
                        try:
                            # Try positional formatting first
                            description = session_info["template"].format(
                                match.group(1), title=title, show_name=show_name, ep_num=ep_num
                            )
                        except (IndexError, KeyError):
                            # Fall back to keyword formatting
                            description = session_info["template"].format(
                                title=title,
                                show_name=show_name,
                                session_num=match.group(1),
                                ep_num=ep_num,
                            )
                    else:
                        # Use default template if no match found
                        description = session_info.get(
                            "default_template",
                            f"{session_key.replace('-', ' ').title()} focusing on {title}. Part of the {show_name} course.",
                        )
                else:
                    # No pattern defined, use simple template
                    description = session_info.get(
                        "template",
                        f"{session_key.replace('-', ' ').title()} focusing on {title}. Part of the {show_name} course.",
                    )

                session_type_detected = True
                break

        # Check if file already exists
        skip_processing = False
        if output_file.exists():
            # Compare file modification times instead of sizes
            source_mtime = os.path.getmtime(video_file)
            target_mtime = os.path.getmtime(output_file)
            source_size = os.path.getsize(video_file)
            target_size = os.path.getsize(output_file)

            # If target file is newer than source and sizes are close, skip
            if (
                target_mtime > source_mtime
                and abs(target_size - source_size) / max(source_size, 1) < 0.10
            ):
                logger.info(f"Skipping video {title} (already exists and is up to date)")
                processed_files.append(str(output_file))
                skip_processing = True
            else:
                logger.info(f"Re-processing {title} (file changed or size mismatch)")

        if skip_processing:
            continue

        # Use a unique temporary filename to avoid conflicts
        temp_file = output_file.with_suffix(f".temp_{int(time.time())}{video_ext}")
        try:
            logger.info(f"Copying {video_file} to temporary file")
            shutil.copy2(video_file, temp_file)

            # Now add metadata using ffmpeg
            logger.info(f"Adding metadata to {title}")

            # Build ffmpeg command for adding metadata
            ffmpeg_cmd = [
                "ffmpeg",
                "-i",
                str(temp_file),
                "-metadata",
                f"title={title}",
                "-metadata",
                f"episode_id={ep_num}",
                "-metadata",
                f"season_number={season}",
                "-metadata",
                f"episode_sort={ep_num}",
                "-metadata",
                f"show={show_name}",
                "-metadata",
                f"description={description}",
                "-codec",
                "copy",  # Copy without re-encoding
                str(output_file),
            ]

            # Run ffmpeg
            subprocess.run(
                ffmpeg_cmd,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            # Remove the temporary file
            if os.path.exists(temp_file):
                os.remove(temp_file)

            logger.info(f"Processed video {title} with metadata")
            processed_files.append(str(output_file))
        except Exception as e:
            logger.error(f"Failed to process video: {e}")
            # Clean up temporary file if it exists
            if os.path.exists(temp_file):
                os.remove(temp_file)

    logger.info(f"Video processing complete. {len(processed_files)} files processed.")
    return processed_files
