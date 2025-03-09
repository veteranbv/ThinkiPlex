"""
Transcription and AI summary processor for ThinkiPlex.

This module provides functionality for transcribing audio files and generating AI summaries.
"""

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ..utils.config import Config
from ..utils.exceptions import TranscriptionError
from ..utils.logging import get_logger
from .services.assemblyai_service import AssemblyAIService
from .services.claude_service import ClaudeService

logger = get_logger()


class TranscriptionProcessor:
    """Processor for audio transcription and AI summary generation."""

    def __init__(self, config_file: Optional[str] = None):
        """Initialize the transcription processor.

        Args:
            config_file: Path to the configuration file
        """
        self.config = Config(config_file or "config/thinkiplex.yaml")
        self.assemblyai_service = AssemblyAIService()
        self.claude_service = ClaudeService()
        logger.info("TranscriptionProcessor initialized")

    def set_claude_model(self, model: str) -> None:
        """
        Set the Claude model to be used for text processing.

        Args:
            model (str): The name of the Claude model to use.
        """
        self.claude_service.set_model(model)

    def get_available_claude_models(self) -> List[str]:
        """
        Get a list of available Claude models.

        Returns:
            List[str]: A list of available model names.
        """
        return self.claude_service.get_available_models()

    def get_claude_model_info(self, model: str) -> Dict[str, Any]:
        """
        Get detailed information about a Claude model.

        Args:
            model: The name of the model

        Returns:
            Dict with model information
        """
        return self.claude_service.get_model_info(model)

    def get_available_prompt_types(self) -> List[str]:
        """
        Get a list of available prompt types.

        Returns:
            List[str]: A list of available prompt type names
        """
        # Get the prompt types from the configuration
        prompts_config = self.claude_service.prompts_config
        if prompts_config:
            if prompts_config.get("use_source") == "default":
                return list(prompts_config.get("defaults", {}).keys())
            else:
                return list(prompts_config.get("files", {}).keys())
        return ["summarize", "transcribe", "analyze", "comprehensive", "course_notes"]

    def get_default_prompt_type(self) -> str:
        """
        Get the default prompt type from configuration.

        Returns:
            str: The default prompt type
        """
        return self.claude_service.default_prompt_type

    def process_course_materials(
        self,
        course_name: str,
        prompt_type: str,
        base_dir: Optional[Path] = None,
        diarization: bool = False,
    ) -> Dict[str, Any]:
        """Process all materials for a course.

        Args:
            course_name: Name of the course
            prompt_type: Type of prompt to use for AI summary
            base_dir: Base directory for the course
            diarization: Whether to use speaker diarization

        Returns:
            Dictionary with results
        """
        logger.info(f"Processing course: {course_name}")
        logger.info(f"Using prompt type: {prompt_type}")

        # Define paths
        if base_dir is None:
            base_dir = Path("data/courses")
        course_dir = base_dir / course_name
        plex_dir = course_dir / "plex"

        # Check if plex directory exists
        if not plex_dir.exists():
            raise FileNotFoundError(f"Plex directory not found: {plex_dir}")

        # Get course configuration
        course_config = self._get_course_config(course_name)
        show_name = course_config.get("show_name", course_name.replace("-", " ").title())

        # Check if home video directory exists
        home_video_dir = plex_dir / "home-video" / show_name
        if not home_video_dir.exists():
            raise FileNotFoundError(f"Home video directory not found: {home_video_dir}")

        # Process downloads directory directly
        downloads_dir = course_dir / "downloads"
        if not downloads_dir.exists():
            raise FileNotFoundError(f"Downloads directory not found: {downloads_dir}")

        # Process each download directory
        results = {}
        errors = []

        # Get all download directories sorted by their episode number
        download_dirs = []
        for dir_path in downloads_dir.glob("*"):
            if dir_path.is_dir():
                # Extract episode number from directory name
                match = re.match(r"^(\d+)\.", dir_path.name)
                if match:
                    episode_number = int(match.group(1))
                    download_dirs.append((episode_number, dir_path))

        # Sort by episode number
        download_dirs.sort(key=lambda x: x[0])

        for episode_number, dir_path in download_dirs:
            try:
                logger.info(f"Processing download directory: {dir_path.name}")
                result = self.process_download_directory(dir_path, prompt_type, diarization)
                if result:
                    results[dir_path.name] = result
            except Exception as e:
                logger.error(f"Error processing directory {dir_path.name}: {str(e)}")
                errors.append({"directory": dir_path.name, "error": str(e)})

        return {"results": results, "errors": errors}

    def process_download_directory(
        self, download_dir: Path, prompt_type: str, diarization: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Process a single download directory.

        Args:
            download_dir: Path to the download directory
            prompt_type: Type of prompt to use for AI summary
            diarization: Whether to use speaker diarization

        Returns:
            Dictionary with results or None if processing failed
        """
        logger.info(f"Processing download directory: {download_dir}")

        # Find audio file in the download directory
        audio_dir = download_dir / "audio"
        if not audio_dir.exists() or not audio_dir.is_dir():
            logger.warning(f"No audio directory found in {download_dir}")
            return None

        # Find the first audio file
        audio_file = None
        for ext in [".mp3", ".m4a", ".wav", ".aac", ".flac"]:
            audio_files = list(audio_dir.glob(f"*{ext}"))
            if audio_files:
                audio_file = audio_files[0]
                break

        if not audio_file:
            logger.warning(f"No audio file found in {audio_dir}")
            return None

        # Create class name from directory name
        class_name = (
            download_dir.name.split(". ", 1)[1] if ". " in download_dir.name else download_dir.name
        )
        class_name = class_name.replace(" ", "-").lower()

        # Create output directories
        transcripts_dir = download_dir / "transcripts"
        summaries_dir = download_dir / "summaries"
        os.makedirs(transcripts_dir, exist_ok=True)
        os.makedirs(summaries_dir, exist_ok=True)

        transcript_file = transcripts_dir / f"{class_name}_transcript.txt"
        summary_file = summaries_dir / f"{class_name}_summary.md"

        # Check if transcript already exists
        if transcript_file.exists():
            logger.info(f"Transcript already exists for {class_name}, using existing file")
            with open(transcript_file, "r", encoding="utf-8") as f:
                transcript_text = f.read()
        else:
            # Transcribe the audio file
            logger.info(f"Transcribing audio file: {audio_file}")
            transcript_text = self.transcribe_audio(audio_file, diarization)

            # Save the transcript
            with open(transcript_file, "w", encoding="utf-8") as f:
                f.write(transcript_text)

            logger.info(f"Saved transcript to {transcript_file}")

        # Check if summary already exists
        if summary_file.exists():
            logger.info(f"Summary already exists for {class_name}, using existing file")
            with open(summary_file, "r", encoding="utf-8") as f:
                summary_text = f.read()
            return {
                "class_name": class_name,
                "transcript_file": str(transcript_file),
                "summary_file": str(summary_file),
                "transcript_length": len(transcript_text),
                "summary_length": len(summary_text),
            }

        # Gather additional course materials
        notes_dir = download_dir / "notes"
        notes_text = ""
        if notes_dir.exists() and notes_dir.is_dir():
            for note_file in notes_dir.glob("*.txt"):
                with open(note_file, "r", encoding="utf-8") as f:
                    notes_text += f"\n\n--- Notes from {note_file.name} ---\n\n"
                    notes_text += f.read()

        # Prepare context for AI summary
        context = f"Class Name: {class_name}\n\n"
        if notes_text:
            context += f"Additional Notes:\n{notes_text}\n\n"

        # Generate AI summary
        logger.info(f"Generating AI summary for {class_name}")
        summary_text = self.claude_service.chunk_and_summarize(context, prompt_type)

        # Save the summary
        with open(summary_file, "w", encoding="utf-8") as f:
            f.write(summary_text)

        logger.info(f"Saved summary to {summary_file}")

        return {
            "class_name": class_name,
            "transcript_file": str(transcript_file),
            "summary_file": str(summary_file),
            "transcript_length": len(transcript_text),
            "summary_length": len(summary_text),
        }

    def _find_audio_file(self, video_file: Path) -> Optional[Path]:
        """
        Find the corresponding audio file for a video file.

        Args:
            video_file: Path to the video file

        Returns:
            Path to the audio file or None if not found
        """
        # First look for audio file in the season directory
        audio_dir = video_file.parent / "audio"
        if audio_dir.exists():
            for ext in [".mp3", ".aac", ".flac", ".ogg"]:
                audio_file = audio_dir / f"{video_file.stem}{ext}"
                if audio_file.exists():
                    return audio_file

        # Look for audio file in the audiobooks directory
        show_name = video_file.parents[1].name
        if "Season" in video_file.parent.name:
            season_name = video_file.parent.name

            # Construct path to audiobooks directory
            audiobooks_dir = video_file.parents[3] / "audiobooks" / show_name / season_name

            if audiobooks_dir.exists():
                for ext in [".mp3", ".aac", ".flac", ".ogg"]:
                    audio_file = audiobooks_dir / f"{video_file.stem}{ext}"
                    if audio_file.exists():
                        return audio_file

        return None

    def _collect_course_materials(self, video_file: Path, class_dir: Path) -> List[Dict[str, str]]:
        """Collect additional course materials for context.

        Args:
            video_file: Path to the video file
            class_dir: Path to the class directory

        Returns:
            List of dictionaries with material type and content
        """
        materials: List[Dict[str, str]] = []

        # Look for notes in the class directory
        notes_dir = class_dir / "notes"
        if notes_dir.exists() and notes_dir.is_dir():
            for note_file in notes_dir.glob("*.txt"):
                with open(note_file, "r", encoding="utf-8") as f:
                    materials.append({"type": "notes", "name": note_file.name, "content": f.read()})

        return materials

    def _prepare_context(self, transcript: str, materials: List[Dict[str, str]]) -> str:
        """
        Prepare context for AI summary by combining transcript and course materials.

        Args:
            transcript: The transcription text
            materials: List of course materials

        Returns:
            Combined context string
        """
        context = f"TRANSCRIPT:\n\n{transcript}\n\n"

        if materials:
            context += "COURSE MATERIALS:\n\n"

            for idx, material in enumerate(materials, 1):
                material_type = material["type"].upper()
                material_path = material["path"]
                content = material["content"]

                context += f"--- MATERIAL {idx} ({material_type}) ---\n"
                context += f"Source: {material_path}\n\n"
                context += f"{content}\n\n"

        return context

    def _get_course_config(self, course_name: str) -> Dict[str, Any]:
        """Get the configuration for a course.

        Args:
            course_name: Name of the course

        Returns:
            Course configuration dictionary
        """
        return self.config.get_course_config(course_name)

    def transcribe_audio(self, audio_path: Union[str, Path], diarization: bool = False) -> str:
        """Transcribe an audio file.

        Args:
            audio_path: Path to the audio file
            diarization: Whether to use speaker diarization

        Returns:
            Transcribed text
        """
        try:
            # Convert to Path if it's a string
            if isinstance(audio_path, str):
                audio_path = Path(audio_path)

            transcript = self.assemblyai_service.transcribe_audio(
                audio_path, diarization=diarization
            )
            return self.assemblyai_service.format_transcript(transcript)
        except Exception as e:
            raise TranscriptionError(f"Failed to transcribe audio: {str(e)}")

    def generate_ai_summary(self, transcript_text: str, context: str, prompt_type: str) -> str:
        """Generate an AI summary of the transcript.

        Args:
            transcript_text: Transcribed text
            context: Additional context for the summary
            prompt_type: Type of prompt to use

        Returns:
            Generated summary
        """
        try:
            return self.claude_service.chunk_and_summarize(
                transcript_text + "\n\n" + context, prompt_type
            )
        except Exception as e:
            raise AIProcessingError(f"Failed to generate AI summary: {str(e)}")
