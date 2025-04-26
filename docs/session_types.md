# Session Types Configuration

## Overview

The session types configuration allows you to define patterns for different types of course sessions (like live calls, workshops, or guided practices) and customize how they are described in the metadata of processed files.

This configuration is useful for:

- Creating consistent descriptions across all files of the same session type
- Extracting session numbers from directory names
- Customizing descriptions for different course formats

## Configuration Levels

Session types can be configured at two levels:

1. **Global level**: Applies to all courses
2. **Course-specific level**: Overrides global settings for a specific course

## Configuration Format

Session types are defined in the `thinkiplex.yaml` configuration file with the following structure:

```yaml
session_types:
  session-key:
    pattern: "regex-pattern-(\\d+)"
    template: "Description template {0} with {title} for {show_name}"
    default_template: "Fallback template if pattern doesn't match"
```

### Fields

- `session-key`: A unique identifier for the session type (e.g., "live-session")
- `pattern`: A regular expression to extract information (typically a session number) from directory names
- `template`: A template string for the description, which can use the following placeholders:
  - `{0}`, `{1}`, etc.: Captured groups from the regex pattern
  - `{title}`: The title of the episode
  - `{show_name}`: The name of the show/course
  - `{ep_num}`: The episode number
  - `{session_num}`: Same as `{0}` (the first captured group from the pattern)
- `default_template`: A fallback template to use if the pattern doesn't match

## Examples

### Global Configuration

```yaml
global:
  session_types:
    live-session:
      pattern: "live-session-(\\d+)"
      template: "Live session {0} focusing on {title}. Part of the {show_name} course."

    workshop:
      pattern: "workshop-(\\d+)"
      template: "Workshop session {0} providing hands-on practice and experiential learning."
```

### Course-Specific Configuration

```yaml
courses:
  my-course:
    session_types:
      qa-session:
        pattern: "qa-session-(\\d+)"
        template: "Q&A Session {0}: Addressing questions about {title} techniques."

      # Override global workshop for this course
      workshop:
        pattern: "workshop-(\\d+)"
        template: "Practical Workshop {0} - Advanced techniques for {title}."
```

## How It Works

1. When processing video files for Plex, the system examines each directory name.
2. If the directory name contains any of the session type keys, the corresponding pattern is applied.
3. If the pattern matches, session numbers are extracted and inserted into the template.
4. The resulting description is used as metadata for the video and audio files.

## Tips

- Make your patterns specific enough to match only the intended directories
- Use capturing groups `(\\d+)` to extract session numbers
- Test your regex patterns with a tool like regex101.com
- You can override specific session types for individual courses while inheriting others
- The directory name is converted to lowercase before matching, so patterns are case-insensitive
