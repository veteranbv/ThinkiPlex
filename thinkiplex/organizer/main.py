"""
Course Organizer Module
---------------------
This module provides functionality to organize course content for Plex.
"""

import logging
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def organize_course(
    source_dir: Path,
    plex_dir: Path,
    course_data: Dict[str, Any],
    show_name: str,
    season: str = "01",
    extract_audio: bool = True,
    audio_quality: int = 0,
    audio_format: str = "mp3",
) -> int:
    """
    Organize a course for Plex.

    Args:
        source_dir: Source directory containing the course content
        plex_dir: Plex directory to organize the course into
        course_data: Course data
        show_name: Name of the show
        season: Season number
        extract_audio: Whether to extract audio from videos
        audio_quality: Audio quality (0-9, where 0 is best)
        audio_format: Audio format (mp3, aac, flac, ogg)

    Returns:
        Number of episodes processed
    """
    logger.info(f"Organizing course: {show_name}")

    # Create the Plex directory if it doesn't exist
    os.makedirs(plex_dir, exist_ok=True)

    # Create the season directory
    season_dir = plex_dir / "home-video" / show_name / f"Season {season}"
    os.makedirs(season_dir, exist_ok=True)

    # Audio directory is now handled by the extract_course_audio function
    # We'll just set it to None here
    audio_dir = None

    # Process each chapter/lesson
    episodes_processed = 0

    # Check if course_data has chapters
    if "chapters" not in course_data:
        logger.error("No chapters found in course data")
        return 0

    # Process each chapter
    for chapter_idx, chapter in enumerate(course_data["chapters"], 1):
        chapter_title = chapter.get("title", f"Chapter {chapter_idx}")
        logger.info(f"Processing chapter: {chapter_title}")

        # Process each lesson in the chapter
        if "lessons" not in chapter:
            logger.warning(f"No lessons found in chapter: {chapter_title}")
            continue

        for lesson_idx, lesson in enumerate(chapter["lessons"], 1):
            lesson_title = lesson.get("title", f"Lesson {lesson_idx}")
            lesson_type = lesson.get("type", "unknown")

            # Calculate episode number
            episode_num = episodes_processed + 1
            episode_num_str = f"{episode_num:02d}"

            logger.info(
                f"Processing lesson: {lesson_title} (Episode {episode_num_str})"
            )

            # Handle different lesson types
            if lesson_type == "video":
                process_video_lesson(
                    source_dir=source_dir,
                    season_dir=season_dir,
                    audio_dir=audio_dir if extract_audio else None,
                    lesson=lesson,
                    show_name=show_name,
                    season=season,
                    episode_num=episode_num_str,
                    audio_quality=audio_quality,
                    audio_format=audio_format,
                )
                episodes_processed += 1
            elif lesson_type == "pdf" or lesson_type == "document":
                process_document_lesson(
                    source_dir=source_dir,
                    season_dir=season_dir,
                    lesson=lesson,
                    show_name=show_name,
                    season=season,
                    episode_num=episode_num_str,
                )
                episodes_processed += 1
            elif lesson_type == "presentation":
                process_presentation_lesson(
                    source_dir=source_dir,
                    season_dir=season_dir,
                    audio_dir=audio_dir if extract_audio else None,
                    lesson=lesson,
                    show_name=show_name,
                    season=season,
                    episode_num=episode_num_str,
                    audio_quality=audio_quality,
                    audio_format=audio_format,
                )
                episodes_processed += 1
            else:
                logger.warning(f"Unsupported lesson type: {lesson_type}")

    logger.info(f"Organized {episodes_processed} episodes")
    return episodes_processed


def process_video_lesson(
    source_dir: Path,
    season_dir: Path,
    audio_dir: Optional[Path],
    lesson: Dict[str, Any],
    show_name: str,
    season: str,
    episode_num: str,
    audio_quality: int = 0,
    audio_format: str = "mp3",
) -> None:
    """Process a video lesson."""
    lesson_title = lesson.get("title", f"Episode {episode_num}")
    lesson_id = lesson.get("id", "")

    # Find the video file
    video_file = find_video_file(source_dir, lesson_id)
    if not video_file:
        logger.warning(f"Video file not found for lesson: {lesson_title}")
        return

    # Create the Plex-formatted filename
    plex_filename = f"{show_name} - s{season}e{episode_num} - {lesson_title}.mp4"
    plex_file = season_dir / plex_filename

    # Copy the video file to the Plex directory
    logger.info(f"Copying video file to: {plex_file}")
    shutil.copy2(video_file, plex_file)

    # Add metadata to the video file
    add_video_metadata(
        video_file=plex_file,
        title=lesson_title,
        show_name=show_name,
        season=season,
        episode=episode_num,
        description=lesson.get("description", ""),
    )

    # Extract audio if requested
    if audio_dir:
        extract_audio_from_video(
            video_file=plex_file,
            audio_dir=audio_dir,
            title=lesson_title,
            artist=show_name,
            album=f"{show_name} - Season {season}",
            track=episode_num,
            description=lesson.get("description", ""),
            audio_quality=audio_quality,
            audio_format=audio_format,
        )


def process_document_lesson(
    source_dir: Path,
    season_dir: Path,
    lesson: Dict[str, Any],
    show_name: str,
    season: str,
    episode_num: str,
) -> None:
    """Process a document lesson."""
    lesson_title = lesson.get("title", f"Episode {episode_num}")
    lesson_id = lesson.get("id", "")

    # Find the document file
    document_file = find_document_file(source_dir, lesson_id)
    if not document_file:
        logger.warning(f"Document file not found for lesson: {lesson_title}")
        return

    # Create the Plex-formatted filename
    plex_filename = (
        f"{show_name} - s{season}e{episode_num} - {lesson_title}{document_file.suffix}"
    )
    plex_file = season_dir / plex_filename

    # Copy the document file to the Plex directory
    logger.info(f"Copying document file to: {plex_file}")
    shutil.copy2(document_file, plex_file)


def process_presentation_lesson(
    source_dir: Path,
    season_dir: Path,
    audio_dir: Optional[Path],
    lesson: Dict[str, Any],
    show_name: str,
    season: str,
    episode_num: str,
    audio_quality: int = 0,
    audio_format: str = "mp3",
) -> None:
    """Process a presentation lesson."""
    lesson_title = lesson.get("title", f"Episode {episode_num}")
    lesson_id = lesson.get("id", "")

    # Find the presentation file
    presentation_file = find_presentation_file(source_dir, lesson_id)
    if not presentation_file:
        logger.warning(f"Presentation file not found for lesson: {lesson_title}")
        return

    # Create the Plex-formatted filename
    plex_filename = f"{show_name} - s{season}e{episode_num} - {lesson_title}{presentation_file.suffix}"
    plex_file = season_dir / plex_filename

    # Copy the presentation file to the Plex directory
    logger.info(f"Copying presentation file to: {plex_file}")
    shutil.copy2(presentation_file, plex_file)

    # Find the audio file if available
    audio_file = find_audio_file(source_dir, lesson_id)
    if audio_file and audio_dir:
        # Create the audio filename
        audio_filename = (
            f"{show_name} - s{season}e{episode_num} - {lesson_title}.{audio_format}"
        )
        output_audio_file = audio_dir / audio_filename

        # Convert the audio file
        convert_audio_file(
            input_file=audio_file,
            output_file=output_audio_file,
            title=lesson_title,
            artist=show_name,
            album=f"{show_name} - Season {season}",
            track=episode_num,
            description=lesson.get("description", ""),
            audio_quality=audio_quality,
            audio_format=audio_format,
        )


def find_video_file(source_dir: Path, lesson_id: str) -> Optional[Path]:
    """Find the video file for a lesson."""
    # Look for video files in the lesson directory
    lesson_dir = source_dir / lesson_id
    if not lesson_dir.exists():
        return None

    # Look for MP4 files
    video_files = list(lesson_dir.glob("*.mp4"))
    if video_files:
        return video_files[0]

    return None


def find_document_file(source_dir: Path, lesson_id: str) -> Optional[Path]:
    """Find the document file for a lesson."""
    # Look for document files in the lesson directory
    lesson_dir = source_dir / lesson_id
    if not lesson_dir.exists():
        return None

    # Look for PDF files
    pdf_files = list(lesson_dir.glob("*.pdf"))
    if pdf_files:
        return pdf_files[0]

    # Look for other document types
    doc_files = list(lesson_dir.glob("*.doc*"))
    if doc_files:
        return doc_files[0]

    return None


def find_presentation_file(source_dir: Path, lesson_id: str) -> Optional[Path]:
    """Find the presentation file for a lesson."""
    # Look for presentation files in the lesson directory
    lesson_dir = source_dir / lesson_id
    if not lesson_dir.exists():
        return None

    # Look for PPT files
    ppt_files = list(lesson_dir.glob("*.ppt*"))
    if ppt_files:
        return ppt_files[0]

    # Look for PDF files (presentations are often saved as PDFs)
    pdf_files = list(lesson_dir.glob("*.pdf"))
    if pdf_files:
        return pdf_files[0]

    return None


def find_audio_file(source_dir: Path, lesson_id: str) -> Optional[Path]:
    """Find the audio file for a lesson."""
    # Look for audio files in the lesson directory
    lesson_dir = source_dir / lesson_id
    if not lesson_dir.exists():
        return None

    # Look for MP3 files
    mp3_files = list(lesson_dir.glob("*.mp3"))
    if mp3_files:
        return mp3_files[0]

    # Look for other audio types
    audio_files = (
        list(lesson_dir.glob("*.m4a"))
        + list(lesson_dir.glob("*.aac"))
        + list(lesson_dir.glob("*.wav"))
    )
    if audio_files:
        return audio_files[0]

    return None


def add_video_metadata(
    video_file: Path,
    title: str,
    show_name: str,
    season: str,
    episode: str,
    description: str = "",
) -> None:
    """Add metadata to a video file using FFmpeg."""
    logger.info(f"Adding metadata to video file: {video_file}")

    # Create a temporary file
    temp_file = video_file.parent / f"temp_{video_file.name}"

    # Build the FFmpeg command
    cmd = [
        "ffmpeg",
        "-i",
        str(video_file),
        "-metadata",
        f"title={title}",
        "-metadata",
        f"show={show_name}",
        "-metadata",
        f"season_number={season}",
        "-metadata",
        f"episode_id={episode}",
        "-metadata",
        f"episode_sort={episode}",
    ]

    if description:
        cmd.extend(["-metadata", f"description={description}"])

    cmd.extend(["-codec", "copy", str(temp_file)])

    try:
        # Run the FFmpeg command
        subprocess.run(cmd, check=True, capture_output=True)

        # Replace the original file with the temporary file
        os.replace(temp_file, video_file)

        logger.info("Metadata added successfully")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error adding metadata: {e}")
        if temp_file.exists():
            os.remove(temp_file)


def extract_audio_from_video(
    video_file: Path,
    audio_dir: Path,
    title: str,
    artist: str,
    album: str,
    track: str,
    description: str = "",
    audio_quality: int = 0,
    audio_format: str = "mp3",
) -> None:
    """Extract audio from a video file using FFmpeg."""
    logger.info(f"Extracting audio from video file: {video_file}")

    # Create the output audio file
    output_file = audio_dir / f"{video_file.stem}.{audio_format}"

    # Build the FFmpeg command
    cmd = [
        "ffmpeg",
        "-i",
        str(video_file),
        "-vn",
    ]

    # Add codec-specific options
    if audio_format == "mp3":
        cmd.extend(["-c:a", "libmp3lame", "-q:a", str(audio_quality)])
    elif audio_format == "aac":
        cmd.extend(["-c:a", "aac", "-b:a", "192k"])
    elif audio_format == "flac":
        cmd.extend(["-c:a", "flac"])
    else:
        cmd.extend(["-c:a", "copy"])

    # Add metadata
    cmd.extend(
        [
            "-metadata",
            f"title={title}",
            "-metadata",
            f"artist={artist}",
            "-metadata",
            f"album={album}",
            "-metadata",
            f"track={track}",
        ]
    )

    if description:
        cmd.extend(["-metadata", f"comment={description}"])

    cmd.append(str(output_file))

    try:
        # Run the FFmpeg command
        subprocess.run(cmd, check=True, capture_output=True)
        logger.info(f"Audio extracted to: {output_file}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error extracting audio: {e}")


def convert_audio_file(
    input_file: Path,
    output_file: Path,
    title: str,
    artist: str,
    album: str,
    track: str,
    description: str = "",
    audio_quality: int = 0,
    audio_format: str = "mp3",
) -> None:
    """Convert an audio file using FFmpeg."""
    logger.info(f"Converting audio file: {input_file}")

    # Build the FFmpeg command
    cmd = [
        "ffmpeg",
        "-i",
        str(input_file),
    ]

    # Add codec-specific options
    if audio_format == "mp3":
        cmd.extend(["-c:a", "libmp3lame", "-q:a", str(audio_quality)])
    elif audio_format == "aac":
        cmd.extend(["-c:a", "aac", "-b:a", "192k"])
    elif audio_format == "flac":
        cmd.extend(["-c:a", "flac"])
    else:
        cmd.extend(["-c:a", "copy"])

    # Add metadata
    cmd.extend(
        [
            "-metadata",
            f"title={title}",
            "-metadata",
            f"artist={artist}",
            "-metadata",
            f"album={album}",
            "-metadata",
            f"track={track}",
        ]
    )

    if description:
        cmd.extend(["-metadata", f"comment={description}"])

    cmd.append(str(output_file))

    try:
        # Run the FFmpeg command
        subprocess.run(cmd, check=True, capture_output=True)
        logger.info(f"Audio converted to: {output_file}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error converting audio: {e}")
