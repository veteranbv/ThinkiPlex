# Development Guide

This guide provides instructions for setting up a development environment and contributing to ThinkiPlex.

## Setting Up a Development Environment

### Prerequisites

- Python 3.8 or higher
- Docker (optional, but recommended for the PHP downloader)
- ffmpeg (required for media processing)
- Git

### Installation Steps

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/thinkiplex.git
   cd thinkiplex
   ```

2. Create a virtual environment:

   ```bash
   python -m venv venv

   # On macOS/Linux
   source venv/bin/activate

   # On Windows
   venv\Scripts\activate
   ```

3. Install the package in development mode with development dependencies:

   ```bash
   pip install -e ".[dev]"
   ```

4. Set up pre-commit hooks (optional but recommended):

   ```bash
   pre-commit install
   ```

## Project Structure

```
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
├── organizer/           # Organizer functionality
│   ├── __init__.py
│   ├── metadata.py      # Metadata handling
│   ├── media.py         # Media processing
│   └── main.py          # Main organizer module
└── utils/               # Utility modules
    ├── __init__.py
    ├── config.py        # Configuration utilities
    ├── exceptions.py    # Custom exceptions
    ├── logging.py       # Logging utilities
    ├── parallel.py      # Parallel processing utilities
    └── schemas.py       # Configuration schema validation
```

## Development Workflow

1. Create a feature branch:

   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and run the linters:

   ```bash
   # Run code formatting
   black thinkiplex tests

   # Run import sorting
   isort thinkiplex tests

   # Run type checking
   mypy thinkiplex

   # Run linter
   ruff thinkiplex tests
   ```

3. Run the tests:

   ```bash
   pytest
   ```

4. Commit your changes:

   ```bash
   git add .
   git commit -m "Add your feature"
   ```

5. Push your changes:

   ```bash
   git push origin feature/your-feature-name
   ```

6. Create a pull request

## Code Style

ThinkiPlex follows the following code style guidelines:

- **Formatting**: Code is formatted with Black using a line length of 100 characters
- **Imports**: Imports are sorted with isort using the Black profile
- **Type Checking**: All functions should include type hints
- **Documentation**: All public functions and classes should have docstrings in Google style
- **Error Handling**: Use custom exceptions from `thinkiplex.utils.exceptions` for consistent error handling
- **Logging**: Use the logger from `thinkiplex.utils.logging` for consistent logging

## Building Documentation

The documentation is built using MkDocs with the Material theme:

```bash
# Install documentation dependencies
pip install mkdocs mkdocs-material mkdocstrings

# Build the documentation
mkdocs build

# Preview the documentation
mkdocs serve
```

## Releasing

To release a new version:

1. Update the version number in `thinkiplex/__init__.py`
2. Update the CHANGELOG.md file
3. Commit the changes
4. Tag the commit with the version number
5. Push the changes and the tag
6. Build the package
7. Upload the package to PyPI

```bash
# Build the package
python -m build

# Upload the package to PyPI
twine upload dist/*
```