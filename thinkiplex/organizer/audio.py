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

    # Extract more descriptive titles based on patterns

    # Saturday Live Call pattern
    if "saturday-live-call" in title.lower():
        # Extract the main topic after the date
        parts = title.split("-")
        if len(parts) > 4:  # Has date and topic
            # Join all parts after the date (which is typically parts[3])
            topic = "-".join(parts[4:])
            # Clean up the topic
            topic = topic.replace("-", " ").strip()
            # Capitalize words
            topic = " ".join(word.capitalize() for word in topic.split())
            if topic:
                return f"Understanding {topic}"

        # If we couldn't extract a good topic, use a generic title with the number
        match = re.search(r"saturday-live-call-(\d+)", title.lower())
        if match:
            call_num = match.group(1)
            return f"Saturday Live Call {call_num}"

    # Heart Sync pattern
    if "heart-sync" in title.lower():
        match = re.search(r"heart-sync-(\d+)", title.lower())
        if match:
            sync_num = match.group(1)
            return f"Heart Sync Session {sync_num}"

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
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".mp4") and "playback-lesson" in root:
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

        # Try to determine if this is a Saturday Live Call or Heart Sync session
        if "saturday" in dir_name.lower() or "live call" in dir_name.lower():
            description = (
                f"Saturday Live Call session focusing on {title}. Part of the {show_name} course."
            )
        elif "heart sync" in dir_name.lower():
            heart_sync_num = re.search(r"heart-sync-(\d+)", dir_name.lower())
            if heart_sync_num:
                sync_num = heart_sync_num.group(1)
                description = f"Heart Sync session {sync_num} providing guided practice and experiential learning. Part of the {show_name} course."
            else:
                description = f"Heart Sync session providing guided practice and experiential learning. Part of the {show_name} course."

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
            "date=2025",
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
    try:
        config = Config(str(base_dir / "config" / "thinkiplex.yaml"))
        downloader = PHPDownloader(base_dir, config=config)
        course_data = downloader.get_course_data(course_name)
    except Exception as e:
        logger.warning(f"Failed to get course data: {e}")

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
            existing_video_files = list(video_output_dir.glob("*.mp4")) + list(
                video_output_dir.glob("*.mkv")
            )
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
) -> List[str]:
    """
    Process video files for Plex.

    Args:
        course_dir: Directory containing the course content
        output_dir: Directory to output video files
        show_name: Name of the show
        season: Season number
        chapter_titles: Mapping of chapter IDs to titles

    Returns:
        List of processed files
    """
    logger.info(f"Processing videos from {course_dir} to {output_dir}")

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

    # Check if we already have the expected number of video files
    existing_video_files = list(output_dir.glob("*.mp4")) + list(output_dir.glob("*.mkv"))
    if len(existing_video_files) >= len(video_dirs):
        logger.info(f"All video files already exist in {output_dir}. Skipping video processing.")
        return [str(f) for f in existing_video_files]

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

        logger.info(f"Processing video {title}")

        # Create output filename with the same format as the audio files
        video_ext = os.path.splitext(video_file)[1]
        output_filename = f"{show_name} - s{season}e{ep_num} - {title}{video_ext}"
        output_file = output_dir / output_filename

        # Generate a description based on the title and directory name
        description = f"Episode {ep_num} of the {show_name} course."

        # Try to determine if this is a Saturday Live Call or Heart Sync session
        if "saturday" in dir_name.lower() or "live call" in dir_name.lower():
            description = (
                f"Saturday Live Call session focusing on {title}. Part of the {show_name} course."
            )
        elif "heart sync" in dir_name.lower():
            heart_sync_num = re.search(r"heart-sync-(\d+)", dir_name.lower())
            if heart_sync_num:
                sync_num = heart_sync_num.group(1)
                description = f"Heart Sync session {sync_num} providing guided practice and experiential learning. Part of the {show_name} course."
            else:
                description = f"Heart Sync session providing guided practice and experiential learning. Part of the {show_name} course."

        # Skip if file already exists and has correct size
        if output_file.exists():
            file_size_original = os.path.getsize(video_file)
            file_size_output = os.path.getsize(output_file)

            # Check if file sizes are similar (within 5%)
            size_diff_percent = (
                abs(file_size_original - file_size_output) / file_size_original * 100
            )

            if size_diff_percent < 5:
                logger.info(f"Skipping video {title} (already exists)")
                processed_files.append(str(output_file))
                continue
            else:
                logger.warning(f"File size mismatch for {title}. Re-copying.")

        # First copy the video file to a temporary location
        temp_file = output_file.with_suffix(f".temp{video_ext}")
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

            # Run ffmpeg to add metadata
            subprocess.run(
                ffmpeg_cmd,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            # Remove the temporary file
            os.remove(temp_file)

            logger.info(f"Processed video {title} with metadata")
            processed_files.append(str(output_file))
        except Exception as e:
            logger.error(f"Failed to process video: {e}")
            # Clean up temporary file if it exists
            if temp_file.exists():
                os.remove(temp_file)

    logger.info(f"Video processing complete. {len(processed_files)} files processed.")
    return processed_files
