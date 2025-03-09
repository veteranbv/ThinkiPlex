"""
Service for transcribing audio using AssemblyAI.
"""

import os
from datetime import timedelta
from pathlib import Path

import assemblyai as aai

from ...utils.exceptions import TranscriptionError
from ...utils.logging import get_logger

logger = get_logger()


class AssemblyAIService:
    """Service for interacting with the AssemblyAI API for audio transcription."""

    def __init__(self) -> None:
        """
        Initialize the AssemblyAI service.

        Raises:
            TranscriptionError: If the AssemblyAI API key is not set.
        """
        self.api_key = os.getenv("ASSEMBLYAI_API_KEY")

        if not self.api_key:
            raise TranscriptionError(
                "AssemblyAI API key is not set in environment variables. Please set ASSEMBLYAI_API_KEY."
            )

        aai.settings.api_key = self.api_key
        self.transcriber = aai.Transcriber()
        logger.info("AssemblyAI service initialized")

    def transcribe_audio(self, audio_path: Path, diarization: bool = True) -> aai.Transcript:
        """
        Transcribe an audio file using AssemblyAI.

        Args:
            audio_path: Path to the audio file
            diarization: Whether to use speaker diarization

        Returns:
            The transcription result

        Raises:
            FileNotFoundError: If the audio file is not found
            TranscriptionError: If there's an error during transcription
        """
        try:
            logger.info(f"Transcribing file: {audio_path}")

            config = aai.TranscriptionConfig(
                speaker_labels=diarization,
                punctuate=True,
                format_text=True,
                disfluencies=False,
            )

            transcript = self.transcriber.transcribe(str(audio_path), config)
            logger.info(f"Transcription completed for {audio_path}")

            return transcript

        except aai.APIError as e:
            logger.error(f"AssemblyAI API error: {str(e)}")
            raise TranscriptionError(f"AssemblyAI API error: {str(e)}")

        except FileNotFoundError:
            logger.error(f"Audio file not found: {audio_path}")
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        except Exception as e:
            logger.exception(f"Unexpected error transcribing audio: {str(e)}")
            raise TranscriptionError(f"Unexpected error transcribing audio: {str(e)}")

    def format_transcript(self, transcript: aai.Transcript) -> str:
        """
        Format the transcript into a readable string with speaker labels and timestamps.

        Args:
            transcript: The transcript object from AssemblyAI

        Returns:
            The formatted transcript text

        Raises:
            TranscriptionError: If there's an error during formatting
        """
        try:
            formatted_text = ""

            for utterance in transcript.utterances:
                start_time = str(timedelta(milliseconds=utterance.start))[:-3]
                end_time = str(timedelta(milliseconds=utterance.end))[:-3]
                formatted_text += (
                    f"Speaker {utterance.speaker} {start_time} - {end_time}: {utterance.text}\n\n"
                )

            return formatted_text

        except AttributeError as e:
            logger.error(f"Error formatting transcript: {str(e)}")
            raise TranscriptionError("Invalid transcript format")

        except Exception as e:
            logger.exception(f"Unexpected error formatting transcript: {str(e)}")
            raise TranscriptionError(f"Unexpected error formatting transcript: {str(e)}")

    def delete_transcript(self, transcript_id: str) -> None:
        """
        Delete a transcript from AssemblyAI servers.

        Args:
            transcript_id: The ID of the transcript to delete

        Raises:
            TranscriptionError: If there's an error during deletion
        """
        try:
            logger.info(f"Deleting transcript with ID: {transcript_id}")
            self.transcriber.delete_transcript(transcript_id)
            logger.info(f"Transcript {transcript_id} deleted from AssemblyAI servers")

        except aai.APIError as e:
            logger.error(f"AssemblyAI API error deleting transcript: {str(e)}")
            raise TranscriptionError(f"AssemblyAI API error deleting transcript: {str(e)}")

        except Exception as e:
            logger.exception(f"Unexpected error deleting transcript: {str(e)}")
            raise TranscriptionError(f"Unexpected error deleting transcript: {str(e)}")
