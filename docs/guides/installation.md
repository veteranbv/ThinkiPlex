# Installation

This guide will walk you through the process of installing ThinkiPlex on your system.

## Prerequisites

Before installing ThinkiPlex, ensure that you have the following prerequisites:

- Python 3.8 or higher
- Docker (optional, but recommended for the PHP downloader)
- ffmpeg (required for media processing)

### Installing ffmpeg

ffmpeg is required for media processing, including adding metadata to videos and extracting audio.

#### On macOS:

```bash
brew install ffmpeg
```

#### On Ubuntu/Debian:

```bash
sudo apt-get update
sudo apt-get install ffmpeg
```

#### On Windows:

Download the latest build from [ffmpeg.org](https://ffmpeg.org/download.html) and add it to your PATH.

## Installation Options

There are two options for installing ThinkiPlex:

1. Install from PyPI (recommended)
2. Install from source

### Option 1: Install from PyPI

```bash
# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install ThinkiPlex
pip install thinkiplex
```

### Option 2: Install from Source

```bash
# Clone the repository
git clone https://github.com/yourusername/thinkiplex.git
cd thinkiplex

# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .
```

For development, you can install additional development dependencies:

```bash
pip install -e ".[dev]"
```

## Verifying Installation

To verify that ThinkiPlex is installed correctly, run:

```bash
thinkiplex --help
```

You should see a help message listing the available command-line options.

## Next Steps

Now that you have installed ThinkiPlex, you can proceed to the [Configuration Guide](configuration.md) to set up your courses.