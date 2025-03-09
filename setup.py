#!/usr/bin/env python3
"""
Setup script for ThinkiPlex.

This script installs the ThinkiPlex package.
"""

import os

from setuptools import find_packages, setup

# Get version from package
with open(os.path.join("thinkiplex", "__init__.py"), "r") as f:
    for line in f:
        if line.startswith("__version__"):
            version = line.split("=")[1].strip().strip("\"'")
            break
    else:
        version = "0.1.0"  # Default version if not found

# Get long description from README
with open("README.md", "r") as f:
    long_description = f.read()

setup(
    name="thinkiplex",
    version=version,
    description="Download and organize Thinkific courses for Plex",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="ThinkiPlex Contributors",
    author_email="",
    url="https://github.com/yourusername/thinkiplex",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "thinkiplex=thinkiplex.main:main",
        ],
    },
    install_requires=[
        "pyyaml>=6.0",
        "inquirer>=3.1.3",
        "pathlib>=1.0.1",
        "ffmpeg-python>=0.2.0",
        "types-PyYAML>=6.0.12.12",
        "types-setuptools",
    ],
    python_requires=">=3.6",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Multimedia :: Video",
    ],
)
