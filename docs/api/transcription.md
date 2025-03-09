# Transcription API

The Transcription API provides functionality for transcribing audio files and generating AI summaries from transcriptions.

## Processor

The `Processor` class is the main entry point for transcription and AI summary generation.

```python
from thinkiplex.transcribe.processor import Processor

processor = Processor(
    course_name="course-name",
    diarize=True,
    claude_model="claude-3-7-sonnet-latest",
    prompt_type="comprehensive"
)
```

### Methods

#### `process_course_materials`

```python
def process_course_materials(self) -> Dict[str, Any]:
    """
    Process all course materials for transcription and AI summaries.

    Returns:
        Dict[str, Any]: Dictionary containing results of processing.
    """
```

Processes all course materials for the specified course, including:

- Finding video files in the Plex directory
- Extracting audio if needed
- Transcribing audio files
- Generating AI summaries from transcriptions

#### `process_class`

```python
def process_class(self, video_file: str, season_dir: str) -> Dict[str, Any]:
    """
    Process a single class (video file) for transcription and AI summary.

    Args:
        video_file (str): Path to the video file.
        season_dir (str): Path to the season directory.

    Returns:
        Dict[str, Any]: Dictionary containing results of processing.
    """
```

Processes a single class (video file), including:

- Finding the corresponding downloads directory
- Extracting audio if needed
- Transcribing the audio file
- Generating an AI summary from the transcription

## Transcriber

The `Transcriber` class handles the transcription of audio files using AssemblyAI.

```python
from thinkiplex.transcribe.transcriber import Transcriber

transcriber = Transcriber(diarize=True)
```

### Methods

#### `transcribe_audio`

```python
def transcribe_audio(self, audio_file: str) -> str:
    """
    Transcribe an audio file using AssemblyAI.

    Args:
        audio_file (str): Path to the audio file.

    Returns:
        str: Transcription text.
    """
```

Transcribes an audio file using AssemblyAI, with optional speaker diarization.

## Summarizer

The `Summarizer` class generates AI summaries from transcriptions using Claude AI.

```python
from thinkiplex.transcribe.summarizer import Summarizer

summarizer = Summarizer(
    model="claude-3-7-sonnet-latest",
    prompt_type="comprehensive"
)
```

### Methods

#### `generate_summary`

```python
def generate_summary(self, transcript: str, context: Dict[str, Any] = None) -> str:
    """
    Generate an AI summary from a transcript.

    Args:
        transcript (str): Transcript text.
        context (Dict[str, Any], optional): Additional context for the summary.

    Returns:
        str: Generated summary.
    """
```

Generates an AI summary from a transcript using Claude AI, with optional additional context.

## Command Line Interface

The transcription functionality is accessible through the ThinkiPlex CLI:

```bash
python -m thinkiplex process course-name --transcribe [options]
```

### Options

- `--transcribe`: Enable transcription and AI summary generation
- `--claude-model MODEL`: Specify the Claude model to use
- `--no-diarization`: Disable speaker diarization
- `--prompt-type TYPE`: Specify the prompt type for AI summaries
- `--sessions SESSIONS`: Comma-separated list of session numbers to process
