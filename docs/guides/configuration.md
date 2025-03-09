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