# Configuration

This guide explains how to configure ThinkiPlex for your Thinkific courses.

## Configuration File

ThinkiPlex uses a YAML configuration file located at `config/thinkiplex.yaml`. If this file doesn't exist when you run ThinkiPlex, a default configuration file will be created automatically.

You can also specify a different configuration file path using the `--config` command-line option:

```bash
thinkiplex --config path/to/config.yaml
```

## Configuration Structure

The configuration file has the following structure:

```yaml
global:
  base_dir: "/path/to/thinkiplex"
  video_quality: "720p"
  extract_audio: true
  audio_quality: 0
  audio_format: "mp3"
  ffmpeg_presentation_merge: true

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

        Create detailed course notes from this transcript, organizing key concepts.

courses:
  course-name:
    course_link: "https://example.thinkific.com/courses/take/course-name"
    show_name: "Course Name"
    season: "01"
    video_quality: "720p"
    extract_audio: true
    audio_quality: 0
    audio_format: "mp3"
    client_date: "..."
    cookie_data: "..."
    video_download_quality: "720p"
```

### Global Settings

- `base_dir`: The base directory for ThinkiPlex data
- `video_quality`: Default video quality for Plex (options: "Original File", "1080p", "720p", "540p", "360p", "224p")
- `extract_audio`: Whether to extract audio from videos by default
- `audio_quality`: Default audio quality (0-9, where 0 is best)
- `audio_format`: Default audio format (options: "mp3", "aac", "flac", "ogg")
- `ffmpeg_presentation_merge`: Whether to merge presentation files

### Claude AI Settings

The `claude` section configures the AI models and prompts used for generating summaries:

#### Models

- `name`: Display name for the model
- `context_window`: Maximum context window size in tokens
- `max_output_tokens`: Maximum output tokens for the model
- `description`: Description of the model's capabilities
- `is_default`: Whether this is the default model (only one model should be marked as default)

#### Prompts

The `prompts.defaults` section defines the prompt templates for different summary types:

- `summarize`: Basic summary focusing on key points
- `transcribe`: Summary specifically designed for transcripts
- `analyze`: Detailed analysis with themes, arguments, and insights
- `comprehensive`: In-depth summary capturing key facts, context, and nuances
- `course_notes`: Structured course notes with key concepts and actionable takeaways

You can customize these prompts or add your own to create different summary styles.

### Course Settings

Each course has its own configuration under the `courses` section:

- `course_link`: URL to the Thinkific course
- `show_name`: Name to use in Plex
- `season`: Season number for Plex
- `video_quality`: Video quality for Plex (overrides global setting)
- `extract_audio`: Whether to extract audio from videos (overrides global setting)
- `audio_quality`: Audio quality (overrides global setting)
- `audio_format`: Audio format (overrides global setting)
- `client_date`: Date header from network request (see Authentication Guide)
- `cookie_data`: Cookie data from network request (see Authentication Guide)
- `video_download_quality`: Quality for video downloads (options: "Original File", "1080p", "720p", "540p", "360p", "224p")

## Adding or Updating a Course

### Using the Setup Wizard

The easiest way to add or edit a course is using the interactive setup wizard:

```bash
thinkiplex --setup
```

The wizard will guide you through the process and offer helpful tips for obtaining authentication data.

### Using the Interactive Mode

You can also use the interactive menu to manage courses:

```bash
thinkiplex
```

Then select "Configure courses" from the menu.

### Manually Editing the Configuration

Alternatively, you can edit the configuration file directly to add a new course:

```yaml
courses:
  new-course:
    course_link: "https://example.thinkific.com/courses/take/new-course"
    show_name: "New Course"
    season: "01"
    video_quality: "720p"
    extract_audio: true
    audio_quality: 0
    audio_format: "mp3"
    client_date: "..."
    cookie_data: "..."
    video_download_quality: "720p"
```

## Next Steps

Now that you have configured your courses, you need to authenticate with Thinkific. See the [Authentication Guide](authentication.md) for details.
