# ThinkiPlex

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.6%2B-blue)](https://www.python.org/downloads/)

A comprehensive tool for downloading and organizing Thinkific courses for Plex media server. ThinkiPlex combines the power of the Thinki-Downloader PHP script with Python-based organization tools to create a seamless workflow for managing your Thinkific courses in Plex.

## Features

- **Course Download**: Download Thinkific courses using the PHP-based downloader
- **Plex Organization**: Organize course content into a Plex-friendly structure
- **Metadata Management**: Add proper metadata to video files for better Plex integration
- **Audio Extraction**: Extract audio from videos and add metadata to audio files
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

- Python 3.6 or higher
- Docker (optional, but recommended for the PHP downloader)
- ffmpeg (optional, but recommended for media processing)

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

To download courses from Thinkific, you need to provide authentication data:

1. Open your browser and navigate to your Thinkific course.
2. Open the browser's Developer Tools (F12 or right-click > Inspect).
3. Go to the "Network" tab.
4. Refresh the page and look for requests containing `course_player/v2/courses/`.
5. Click on the matched request and look for:
   - `date` header value (for CLIENT_DATE)
   - `cookie` header value (for COOKIE_DATA)

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
│   └── plex.py          # Plex organization
└── utils/               # Utility modules
    ├── __init__.py
    ├── config.py        # Configuration utilities
    └── logging.py       # Logging utilities

config/                  # Configuration files
├── thinkiplex.yaml      # Main configuration file
└── php_downloader.env   # PHP downloader environment file

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
