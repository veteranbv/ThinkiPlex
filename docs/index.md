# ThinkiPlex Documentation

Welcome to the ThinkiPlex documentation. ThinkiPlex is a comprehensive tool for downloading and organizing Thinkific courses for Plex media server.

## Features

- **Course Download**: Download Thinkific courses using the PHP-based downloader
- **Plex Organization**: Organize course content into a Plex-friendly structure
- **Metadata Management**: Add proper metadata to video files for better Plex integration
- **Audio Extraction**: Extract audio from videos and add metadata to audio files
- **Transcription**: Transcribe audio files using AssemblyAI with speaker diarization
- **AI Summaries**: Generate comprehensive class notes from transcriptions using Claude AI
  - Multiple prompt types for different summary styles
  - Support for latest Claude models
  - Process specific sessions or entire courses
- **Incremental Updates**: Support for checking and downloading only new course content
- **Docker Support**: Run the PHP downloader in a Docker container for easier setup
- **Interactive CLI**: User-friendly command-line interface with interactive prompts
- **Configurable**: Extensive configuration options via YAML files
- **Parallel Processing**: Process videos and extract audio in parallel for better performance

## Getting Started

- [Installation](guides/installation.md): Install ThinkiPlex on your system
- [Configuration](guides/configuration.md): Configure ThinkiPlex for your courses
- [Authentication](guides/authentication.md): Authenticate with Thinkific
- [Transcription & AI](guides/transcription.md): Generate transcriptions and AI summaries

## API Reference

- [CLI](api/cli.md): Command-line interface reference
- [Configuration](api/config.md): Configuration utilities reference
- [Downloader](api/downloader.md): Downloader module reference
- [Organizer](api/organizer.md): Organizer module reference
- [Transcription](api/transcription.md): Transcription and AI summary reference
- [Utilities](api/utils.md): Utility modules reference
