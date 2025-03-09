# Development Guide

This guide provides instructions for setting up a development environment for ThinkiPlex.

## Setting Up a Virtual Environment

1. Create a virtual environment:

   ```bash
   python3 -m venv venv
   ```

2. Activate the virtual environment:

   ```bash
   # On macOS/Linux
   source venv/bin/activate

   # On Windows
   venv\Scripts\activate
   ```

3. Install the package in development mode:

   ```bash
   pip install -e .
   ```

## Running the Package

Once installed in development mode, you can run the package using the `thinkiplex` command:

```bash
thinkiplex --list-courses
```

Or using the Python module syntax:

```bash
python -m thinkiplex --list-courses
```

## Running Tests

To run the tests:

```bash
pytest
```

## Code Style

This project follows PEP 8 style guidelines. You can check your code style using:

```bash
flake8
```

## Type Checking

This project uses mypy for type checking. You can run mypy with:

```bash
mypy thinkiplex
```

## Building the Package

To build the package:

```bash
python setup.py sdist bdist_wheel
```

## Releasing

To release a new version:

1. Update the version number in `thinkiplex/__init__.py`
2. Update the CHANGELOG.md file
3. Commit the changes
4. Tag the commit with the version number
5. Push the changes and the tag
6. Build the package
7. Upload the package to PyPI:

   ```bash
   twine upload dist/*
   ```
