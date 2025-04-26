# ThinkiPlex

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.6%2B-blue)](https://www.python.org/downloads/)

A comprehensive tool for downloading and organizing Thinkific courses for Plex media server. ThinkiPlex combines the power of the Thinki-Downloader PHP script with Python-based organization tools to create a seamless workflow for managing your Thinkific courses in Plex.

## Enhance Your Learning Experience

ThinkiPlex is designed to help you get the most out of your online courses:

- **Focus on Learning, Not Note-Taking**: With automatic transcription and AI-generated summaries, you can fully engage with the course content without worrying about taking notes.
- **Create a Personal Knowledge Base**: Build a searchable archive of your courses with transcripts and summaries for easy reference.
- **Review Key Concepts**: AI summaries highlight the most important concepts, making review sessions more efficient.
- **Offline Access**: Download courses for offline viewing in your preferred media player or Plex.
- **Organized Content**: Keep all your course materials neatly organized and easily accessible.

## Features

- **Course Download**: Download Thinkific courses using the PHP-based downloader
- **Plex Organization**: Organize course content into a Plex-friendly structure
- **Metadata Management**: Add proper metadata to video files for better Plex integration
- **Audio Extraction**: Extract audio from videos and add metadata to audio files
- **Transcription**: Transcribe audio files using AssemblyAI with speaker diarization
- **AI Summaries**: Generate comprehensive class notes from transcriptions using Claude AI
  - Multiple prompt types for different summary styles (comprehensive, course notes, analysis)
  - Support for latest Claude models (3.7, 3.5)
  - Process specific sessions or entire courses
- **PDF Generation**: Combine all class resources into a single well-formatted PDF
  - Includes AI summaries, text content, HTML, and PDF resources
  - Excludes video, audio, and transcripts
  - Creates a table of contents and section headers
  - Saves to the course downloads folder for easy access
- **Incremental Updates**: Support for checking and downloading only new course content
- **Docker Support**: Run the PHP downloader in a Docker container for easier setup
- **Interactive CLI**: User-friendly command-line interface with interactive prompts
- **Configurable**: Extensive configuration options via YAML files

## Supported Content Types

The following content types are currently supported:

1. ✅ Videos
2. ✅ Presentations (PDFs/PPTs with audio)
3. ✅ Notes
4. ✅ Shared Files
5. ✅ Quiz with Answers
6. ✅ Audio

## Installation

### Prerequisites

- Python 3.8 or higher
- Docker (optional, but recommended for the PHP downloader)
- ffmpeg (required for media processing)
- AssemblyAI API key (for transcription)
- Anthropic API key (for Claude AI summaries)

### Installation Steps

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/thinkiplex.git
   cd thinkiplex
   ```

2. Create a virtual environment (recommended):

   ```bash
   python -m venv venv

   # On macOS/Linux
   source venv/bin/activate

   # On Windows
   venv\Scripts\activate
   ```

3. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Install the package in development mode:

   ```bash
   pip install -e .
   ```

5. Set up API keys:

   ```bash
   # Copy the sample .env file
   cp config/.env.sample config/.env

   # Edit the .env file with your API keys
   nano config/.env  # or use any editor
   ```

## Quick Start

1. Run the setup wizard to configure your first course:

   ```bash
   python -m thinkiplex
   ```

2. Follow the interactive prompts to set up your course.

3. Process your course:

   ```bash
   python -m thinkiplex --course your-course-name
   ```

## Getting Authentication Data

To download courses from Thinkific, you need to provide authentication data from your browser session. Here's a detailed guide on how to get this data:

### Using Chrome/Edge Developer Tools

1. Open your Thinkific course in Chrome or Edge
2. Open Developer Tools:
   - Windows/Linux: Press `F12` or `Ctrl+Shift+I`
   - macOS: Press `Cmd+Option+I`
   - Or right-click anywhere on the page and select "Inspect"

3. In Developer Tools:
   - Click the "Network" tab
   - Check the "Preserve log" checkbox
   - Make sure "XHR" filter is selected

4. Refresh the page and look for this specific request:

   ```text
   /api/course_player/v2/courses/your-course-name
   ```

   (where "your-course-name" is your actual course name)

5. Click on this request and find:
   - In the "Request Headers" section:
     - Look for `x-thinkific-client-date` - This is your `client_date`
     - Look for `cookie` - This is your `cookie_data`

### Using Firefox Developer Tools

1. Open your Thinkific course in Firefox
2. Open Developer Tools:
   - Press `F12` or `Cmd+Option+I`
   - Or right-click and select "Inspect Element"

3. In Developer Tools:
   - Click the "Network" tab
   - Check "Persist Logs"
   - Filter by "XHR"

4. Follow the same steps as Chrome to find the request and headers

### Updating Your Configuration

Once you have the authentication data, you can update it in two ways:

1. **Using the CLI Command**:

   ```bash
   python -m thinkiplex --update-auth --course your-course-name --client-date "2025-04-25T17:36:48.198Z" --cookie-data "your-cookie-data"
   ```

2. **Editing thinkiplex.yaml**:

   ```yaml
   courses:
     your-course-name:
       client_date: "2025-04-25T17:36:48.198Z"
       cookie_data: "your-cookie-data"
   ```

### Important Notes

- The cookie data is sensitive authentication information. Never share it publicly.
- Authentication data typically expires after some time. If downloads stop working, you'll need to update these values.
- Make sure to copy the ENTIRE cookie string from the developer tools.
- The client date should be in ISO 8601 format (e.g., "2025-04-25T17:36:48.198Z").

## Transcription and AI Summaries

ThinkiPlex includes powerful features for transcribing course content and generating AI summaries, allowing you to focus on learning rather than note-taking. These features help you:

- **Focus on the content** during live sessions without worrying about taking notes
- **Review key concepts** with AI-generated summaries that capture the essence of each session
- **Search through transcripts** to find specific information mentioned in the course
- **Create a knowledge base** of your courses for future reference

### Setting Up Transcription and AI Summaries

1. **Setup API Keys**: You need API keys for AssemblyAI and Anthropic:
   - Get an AssemblyAI API key from [https://www.assemblyai.com/](https://www.assemblyai.com/)
   - Get an Anthropic API key from [https://console.anthropic.com/](https://console.anthropic.com/)
   - Add both keys to your `.env` file:

     ```bash
     ASSEMBLYAI_API_KEY=your_assemblyai_key
     ANTHROPIC_API_KEY=your_anthropic_key
     ```

2. **Configure Claude Models and Prompts**: ThinkiPlex supports multiple Claude models and prompt types. You can configure these in `config/thinkiplex.yaml`:

   ```yaml
   claude:
     models:
       claude-3-7-sonnet-latest:
         name: "Claude 3.7 Sonnet"
         context_window: 200000
         max_output_tokens: 8192
         description: "Latest Claude model with hybrid reasoning capabilities"
         is_default: true
       claude-3-5-sonnet-latest:
         name: "Claude 3.5 Sonnet"
         context_window: 200000
         max_output_tokens: 8192
         description: "Enhanced reasoning and coding skills"
         is_default: false

     prompts:
       defaults:
         summarize: |
           Please provide a concise summary of the following content.
         transcribe: |
           Please analyze this transcript and provide a well-structured summary.
         analyze: |
           Please perform a detailed analysis of the following content.
         comprehensive: |
           ===Comprehensive Content Summarizer===

           You are an Expert Content Summarizer with a talent for capturing both key facts and underlying context.
           Your summaries include essential information, meaningful context, philosophical underpinnings, and subtle nuances.
           You prioritize comprehensiveness over brevity, ensuring nothing important is missed.
         course_notes: |
           ===Course Notes Generator===

           Create detailed course notes from this transcript, organizing key concepts, examples, and actionable takeaways.
           Format with clear headings, bullet points, and highlight important terminology.
   ```

### Using Transcription and AI Summaries

You can generate transcriptions and summaries in several ways:

1. **Command Line**:

   ```bash
   # Process a course with transcription and AI summaries
   python -m thinkiplex --course your-course-name --transcribe

   # Customize the Claude model and prompt type
   python -m thinkiplex --course your-course-name --transcribe --claude-model claude-3-7-sonnet-latest --prompt-type comprehensive

   # Disable speaker diarization (not recommended for multi-speaker content)
   python -m thinkiplex --course your-course-name --transcribe --no-diarization
   ```

2. **Interactive Menu**:
   - Run `python -m thinkiplex`
   - Select option 9: "Generate transcriptions and AI summaries"
   - Follow the interactive prompts to:
     - Select a course
     - Choose a Claude model
     - Enable/disable speaker diarization
     - Select a prompt type
     - Process specific download directories or all course materials

3. **Process Specific Sessions**:
   - The interactive menu allows you to select specific download directories to process
   - This is useful for processing only new content or reprocessing specific sessions

### Output Files

The transcription and AI summary process creates:

- **Transcripts**: Saved as `{class_name}_transcript.txt` in a `transcripts` directory within each class folder
- **AI Summaries**: Saved as `{class_name}_summary.md` in a `summaries` directory within each class folder

The summaries are formatted in Markdown, making them easy to read and navigate.

### Available Prompt Types

ThinkiPlex includes several pre-configured prompt types for different summary styles:

- **summarize**: Basic summary focusing on key points
- **transcribe**: Summary specifically designed for transcripts
- **analyze**: Detailed analysis with themes, arguments, and insights
- **comprehensive**: In-depth summary capturing key facts, context, and nuances
- **course_notes**: Structured course notes with key concepts and actionable takeaways

You can customize these prompts or add your own in the configuration file.

### Speaker Diarization

Speaker diarization identifies different speakers in the audio, making transcripts more readable by labeling who is speaking. This is especially useful for:

- Courses with multiple instructors
- Q&A sessions
- Panel discussions
- Interactive workshops

Speaker diarization is enabled by default but can be disabled if not needed.

## Configuration

ThinkiPlex uses a YAML configuration file located at `config/thinkiplex.yaml`. A sample configuration file is provided at `config/thinkiplex.yaml.sample`.

### Global Configuration

```yaml
global:
  base_dir: "/path/to/thinkiplex"
  video_quality: "720p"  # Options: Original File, 1080p, 720p, 540p, 360p, 224p
  extract_audio: true
  audio_quality: 0  # 0 (best) to 9 (worst)
  audio_format: "mp3"  # Options: mp3, aac, flac, ogg
  ffmpeg_presentation_merge: true  # Whether to merge audio and video files of presentations
```

### Claude AI Configuration

```yaml
claude:
  models:
    claude-3-7-sonnet-latest:
      name: "Claude 3.7 Sonnet"
      context_window: 200000
      max_output_tokens: 8192
      description: "Latest Claude model with hybrid reasoning capabilities"
      is_default: true
    claude-3-5-sonnet-latest:
      name: "Claude 3.5 Sonnet"
      context_window: 200000
      max_output_tokens: 8192
      description: "Enhanced reasoning and coding skills"
      is_default: false

  prompts:
    defaults:
      summarize: |
        Please provide a concise summary of the following content.
      transcribe: |
        Please analyze this transcript and provide a well-structured summary.
      analyze: |
        Please perform a detailed analysis of the following content.
      comprehensive: |
        ===Comprehensive Content Summarizer===

        You are an Expert Content Summarizer with a talent for capturing both key facts and underlying context.
      course_notes: |
        ===Course Notes Generator===

        Create detailed course notes from this transcript, organizing key concepts, examples, and actionable takeaways.
        Format with clear headings, bullet points, and highlight important terminology.
```

> **Note**: The comprehensive prompt is inspired by [Dan Koe's excellent prompt](https://x.com/thedankoe/status/1897996820716175735) shared on X.com. Follow him at [@thedankoe](https://x.com/thedankoe) for more valuable insights.

### Course Configuration

```yaml
courses:
  course-name:
    course_link: "https://example.thinkific.com/courses/take/course-name"
    show_name: "Course Name"  # Name to use in Plex
    season: "01"  # Season number for Plex
    video_quality: "720p"  # Override global setting
    extract_audio: true  # Override global setting
    audio_quality: 0  # Override global setting
    audio_format: "mp3"  # Override global setting
    client_date: ""  # Date header from network request
    cookie_data: ""  # Cookie data from network request
    video_download_quality: "720p"  # Options: Original File, 1080p, 720p, 540p, 360p, 224p
```

## Usage

### Basic Commands

```bash
# Run the interactive CLI
python -m thinkiplex

# Process a specific course
python -m thinkiplex --course course-name

# List available courses
python -m thinkiplex --list-courses

# Update authentication data for a course
python -m thinkiplex --update-auth --course course-name --client-date "..." --cookie-data "..."

# Run the PHP downloader directly
python -m thinkiplex --run-php "https://example.thinkific.com/courses/take/course-name"

# Run the PHP downloader with Docker
python -m thinkiplex --run-docker --run-php "https://example.thinkific.com/courses/take/course-name"

# Extract audio from videos
python -m thinkiplex --extract-audio --course course-name

# Consolidate the data structure
python -m thinkiplex --cleanup

# Generate a PDF of course resources
python -m thinkiplex --generate-pdf --course course-name
```

### Command-line Options

| Option | Description |
|--------|-------------|
| `--course COURSE` | Name of the course to process |
| `--list-courses` | List available courses and exit |
| `--run-downloader` | Force run the downloader even if disabled in config |
| `--skip-downloader` | Skip running the downloader even if enabled in config |
| `--run-php LINK` | Run the PHP downloader directly with the specified course link |
| `--run-php-json FILE` | Run the PHP downloader directly with the specified JSON file |
| `--run-docker` | Run the PHP downloader with Docker |
| `--update-auth` | Update authentication data for a course |
| `--client-date DATE` | Set the client date for the course |
| `--cookie-data DATA` | Set the cookie data for the course |
| `--cleanup` | Consolidate the data structure |
| `--skip-organize` | Skip organizing the course content |
| `--extract-audio` | Extract audio from video files |
| `--skip-audio` | Skip extracting audio from video files |
| `--transcribe` | Generate transcriptions and AI summaries for course materials |
| `--claude-model MODEL` | Claude model to use for AI summaries (default: uses the model marked as default in config) |
| `--no-diarization` | Disable speaker diarization in transcriptions |
| `--prompt-type TYPE` | Prompt type to use for AI summaries (options: summarize, transcribe, analyze, comprehensive, course_notes) |
| `--generate-pdf` | Generate a PDF of course resources (excluding video, audio, and transcripts) |
| `--verbose` | Enable verbose logging |
| `--log-file FILE` | Path to the log file |

## Project Structure

```bash
thinkiplex/              # Main package
├── __init__.py          # Package initialization
├── __main__.py          # Entry point for running as a module
├── main.py              # Main CLI module
├── cli/                 # CLI modules
│   ├── __init__.py
│   ├── cleanup.py       # Data structure cleanup utilities
│   ├── course_selector.py # Course selection utilities
│   ├── scripts.py       # Helper scripts
│   └── wizard.py        # Setup wizard
├── downloader/          # Downloader functionality
│   ├── __init__.py
│   ├── php_wrapper.py   # Python wrapper for PHP downloader
│   └── php/             # PHP downloader files
│       ├── thinkidownloader3.php
│       ├── include/
│       └── ...
├── organizer/           # Organizer functionality
│   ├── __init__.py
│   ├── metadata.py      # Metadata handling
│   ├── media.py         # Media processing
│   └── main.py          # Main organizer module
├── transcribe/          # Transcription and AI summary functionality
│   ├── __init__.py
│   ├── processor.py     # Main transcription processor
│   └── services/        # External service integrations
│       ├── __init__.py
│       ├── assemblyai_service.py  # AssemblyAI integration
│       └── claude_service.py      # Claude AI integration
└── utils/               # Utility modules
    ├── __init__.py
    ├── config.py        # Configuration utilities
    ├── exceptions.py    # Custom exceptions
    ├── logging.py       # Logging utilities
    ├── parallel.py      # Parallel processing utilities
    └── schemas.py       # Configuration schemas

config/                  # Configuration files
├── thinkiplex.yaml      # Main configuration file
└── .env                 # Environment variables for API keys

data/                    # Data directory
└── courses/             # Course data
    └── course-name/     # Course-specific directory
        ├── course-name.json  # Course JSON data
        ├── downloads/   # Downloaded course content
        └── plex/        # Organized content for Plex

logs/                    # Log files
```

## Development

For development instructions, see [DEVELOPMENT.md](DEVELOPMENT.md).

## Acknowledgments

ThinkiPlex builds upon the excellent work of the [Thinki-Downloader](https://github.com/sumeetweb/Thinki-Downloader) project by [Sumeet Naik](https://github.com/sumeetweb).

## Disclaimer

This tool is intended for personal use only, to download courses you have legitimately purchased for offline viewing. Please respect the terms of service of the platforms you use and the intellectual property rights of content creators.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
