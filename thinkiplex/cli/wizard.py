#!/usr/bin/env python3
"""
ThinkiPlex Setup Wizard
-----------------------
This script guides users through setting up ThinkiPlex by creating a unified
configuration file that replaces the multiple config files in the old structure.
"""

import os
import re
import sys
from datetime import datetime
from pathlib import Path

import inquirer
import yaml
from inquirer import errors


# Ensure the required directories exist
def ensure_dirs():
    """Create the required directories if they don't exist."""
    dirs = [
        "config",
        "data/courses",
        "logs",
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)


# Load existing configuration if available
def load_existing_config():
    """Load existing configuration if available."""
    config_file = Path("config/thinkiplex.yaml")
    if config_file.exists():
        with open(config_file, "r") as f:
            return yaml.safe_load(f)
    return {
        "global": {
            "base_dir": str(Path.cwd()),
            "video_quality": "720p",
            "extract_audio": True,
            "audio_quality": 0,
            "audio_format": "mp3",
        },
        "courses": {},
    }


# Load course data from .env file
def load_env_data():
    """Load course data from .env file if it exists."""
    env_file = Path(".env")
    if not env_file.exists():
        return {}

    env_data = {}
    with open(env_file, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                # Remove quotes if present
                value = value.strip("\"'")
                env_data[key] = value

    return env_data


# Validate course link
def validate_course_link(answers, current):
    """Validate that the course link is a valid Thinkific URL."""
    if not current:
        return True  # Allow empty for now

    if not re.match(r"^https?://.*\.thinkific\.com/courses/take/.*$", current):
        raise errors.ValidationError(
            "",
            reason="Please enter a valid Thinkific course URL (e.g., https://example.thinkific.com/courses/take/course-name)",
        )

    return True


# Get course name from URL
def get_course_name_from_url(url):
    """Extract course name from URL."""
    if not url:
        return ""

    match = re.search(r"/courses/take/([^/]+)", url)
    if match:
        return match.group(1)
    return ""


# Detect existing courses
def detect_existing_courses():
    """Detect existing courses in the data directory."""
    courses = []

    # Check downloads directory
    downloads_dir = Path("data/courses")
    if downloads_dir.exists():
        for item in downloads_dir.iterdir():
            if item.is_dir():
                courses.append(item.name)

    return courses


# Main wizard function
def setup_wizard():
    """Run the setup wizard to configure ThinkiPlex."""
    print("ThinkiPlex Setup Wizard")
    print("======================")
    print("This wizard will help you configure ThinkiPlex for your courses.")
    print()
    print("TIP: To authenticate with Thinkific, follow these steps:")
    print("1. Open your Thinkific course in Chrome/Firefox and log in")
    print("2. Press F12 to open Developer Tools and go to the Network tab")
    print("3. Refresh the page")
    print("4. Find a request to 'courses/take/your-course-name'")
    print("5. Look for 'date' in request headers for Client Date value")
    print("6. Look for 'cookie' in request headers for Cookie Data value")
    print()

    # Ensure directories exist
    ensure_dirs()

    # Load existing configuration
    config = load_existing_config()
    env_data = load_env_data()

    # Detect existing courses
    existing_courses = detect_existing_courses()

    # Global settings
    questions = [
        inquirer.List(
            "action",
            message="What would you like to do?",
            choices=[
                ("Configure a new course", "new"),
                ("Edit an existing course configuration", "edit"),
                ("Update global settings", "global"),
            ],
        ),
    ]

    answers = inquirer.prompt(questions)

    if answers["action"] == "global":
        # Global settings
        global_questions = [
            inquirer.List(
                "video_quality",
                message="Default video quality to download:",
                choices=[
                    ("Original File", "Original File"),
                    ("1080p", "1080p"),
                    ("720p", "720p"),
                    ("540p", "540p"),
                    ("360p", "360p"),
                    ("224p", "224p"),
                ],
                default=config["global"].get("video_quality", "720p"),
            ),
            inquirer.Confirm(
                "extract_audio",
                message="Extract audio from videos by default?",
                default=config["global"].get("extract_audio", True),
            ),
            inquirer.List(
                "audio_quality",
                message="Default audio quality (0=best, 9=worst):",
                choices=[
                    ("0 (Best)", 0),
                    ("1", 1),
                    ("2", 2),
                    ("3", 3),
                    ("4", 4),
                    ("5", 5),
                    ("6", 6),
                    ("7", 7),
                    ("8", 8),
                    ("9 (Worst)", 9),
                ],
                default=config["global"].get("audio_quality", 0),
            ),
            inquirer.List(
                "audio_format",
                message="Default audio format:",
                choices=["mp3", "aac", "flac", "ogg"],
                default=config["global"].get("audio_format", "mp3"),
            ),
        ]

        global_answers = inquirer.prompt(global_questions)

        # Update global settings
        config["global"].update(global_answers)

    elif answers["action"] == "edit":
        # Edit existing course
        if not config["courses"]:
            print("No courses configured yet. Please add a course first.")
            return

        course_choices = list(config["courses"].keys())
        edit_questions = [
            inquirer.List(
                "course",
                message="Which course would you like to edit?",
                choices=course_choices,
            ),
        ]

        edit_answers = inquirer.prompt(edit_questions)
        selected_course = edit_answers["course"]
        course_config = config["courses"][selected_course]

        # Now edit this course
        edit_course_questions = [
            inquirer.Text(
                "course_link",
                message="Course link (leave empty to keep current):",
                default=course_config.get("course_link", ""),
            ),
            inquirer.Text(
                "show_name",
                message="Show name for Plex:",
                default=course_config.get("show_name", ""),
            ),
            inquirer.Text(
                "season",
                message="Season number:",
                default=course_config.get("season", "01"),
            ),
            inquirer.List(
                "video_quality",
                message="Video quality to download:",
                choices=[
                    ("Original File", "Original File"),
                    ("1080p", "1080p"),
                    ("720p", "720p"),
                    ("540p", "540p"),
                    ("360p", "360p"),
                    ("224p", "224p"),
                ],
                default=course_config.get(
                    "video_quality", config["global"]["video_quality"]
                ),
            ),
            inquirer.Confirm(
                "extract_audio",
                message="Extract audio from videos:",
                default=course_config.get(
                    "extract_audio", config["global"].get("extract_audio", True)
                ),
            ),
            inquirer.Text(
                "client_date",
                message="Client date (from browser network request 'date' header):",
                default=course_config.get("client_date", ""),
            ),
            inquirer.Text(
                "cookie_data",
                message="Cookie data (from browser network request 'cookie' header):",
                default=course_config.get("cookie_data", ""),
            ),
            inquirer.List(
                "video_download_quality",
                message="Video download quality:",
                choices=[
                    ("Original File", "Original File"),
                    ("1080p", "1080p"),
                    ("720p", "720p"),
                    ("540p", "540p"),
                    ("360p", "360p"),
                    ("224p", "224p"),
                ],
                default=course_config.get("video_download_quality", "720p"),
            ),
        ]

        course_answers = inquirer.prompt(edit_course_questions)

        # Only update if link is provided
        if course_answers["course_link"]:
            course_config["course_link"] = course_answers["course_link"]

        # Update other settings
        course_config["show_name"] = course_answers["show_name"]
        course_config["season"] = course_answers["season"]
        course_config["video_quality"] = course_answers["video_quality"]
        course_config["extract_audio"] = course_answers["extract_audio"]
        course_config["client_date"] = course_answers["client_date"]
        course_config["cookie_data"] = course_answers["cookie_data"]
        course_config["video_download_quality"] = course_answers[
            "video_download_quality"
        ]

        # Update the course in the config
        config["courses"][selected_course] = course_config

    else:  # New course
        # Get course details
        course_questions = [
            inquirer.Text(
                "course_link",
                message="Course link (e.g., https://example.thinkific.com/courses/take/course-name):",
                validate=validate_course_link,
            ),
            inquirer.Text(
                "show_name",
                message="Show name for Plex:",
                default=lambda answers: get_course_name_from_url(answers["course_link"])
                .replace("-", " ")
                .title(),
            ),
            inquirer.Text(
                "season",
                message="Season number:",
                default="01",
            ),
            inquirer.List(
                "video_quality",
                message="Video quality to download:",
                choices=[
                    ("Original File", "Original File"),
                    ("1080p", "1080p"),
                    ("720p", "720p"),
                    ("540p", "540p"),
                    ("360p", "360p"),
                    ("224p", "224p"),
                ],
                default=config["global"]["video_quality"],
            ),
            inquirer.Confirm(
                "extract_audio",
                message="Extract audio from videos:",
                default=config["global"].get("extract_audio", True),
            ),
            inquirer.Text(
                "client_date",
                message="Client date (from browser network request 'date' header):",
                default="",
            ),
            inquirer.Text(
                "cookie_data",
                message="Cookie data (from browser network request 'cookie' header):",
                default="",
            ),
            inquirer.List(
                "video_download_quality",
                message="Video download quality:",
                choices=[
                    ("Original File", "Original File"),
                    ("1080p", "1080p"),
                    ("720p", "720p"),
                    ("540p", "540p"),
                    ("360p", "360p"),
                    ("224p", "224p"),
                ],
                default="720p",
            ),
        ]

        course_answers = inquirer.prompt(course_questions)

        # Extract the course name from the URL to use as a key
        course_name = get_course_name_from_url(course_answers["course_link"])
        if not course_name:
            course_name = course_answers["show_name"].lower().replace(" ", "-")
        
        # Add the course to the config
        config["courses"][course_name] = course_answers
        print(f"\nAdded course with identifier: {course_name}")
        print("Use this identifier when running commands like:")
        print(f"  thinkiplex --course {course_name}")

    # Save the configuration
    with open("config/thinkiplex.yaml", "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    print("\nConfiguration saved to config/thinkiplex.yaml")
    
    if answers["action"] == "new":
        course_name = get_course_name_from_url(course_answers["course_link"])
        if not course_name:
            course_name = course_answers["show_name"].lower().replace(" ", "-")
        print(f"\nYou can now process your course with:")
        print(f"  thinkiplex --course {course_name}")
    elif answers["action"] == "edit":
        course_name = edit_answers["course"]
        print(f"\nYou can now process your updated course with:")
        print(f"  thinkiplex --course {course_name}")

    # Create PHP environment file if needed
    if answers["action"] == "new" or answers["action"] == "edit":
        # Get the appropriate course identifier
        if answers["action"] == "new":
            selected_course = course_name  # Use the extracted course name
        else:
            selected_course = edit_answers["course"]
            
        course_config = config["courses"][selected_course]

        # Create PHP environment file
        env_content = f"""# Generated by ThinkiPlex Setup Wizard on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
# For downloading all content, use the course link.
COURSE_LINK="{course_config.get("course_link", "")}"

# For selective content downloads, use the JSON file created from Think Parser.
# COURSE_DATA_FILE=""

CLIENT_DATE="{course_config.get("client_date", "")}"
COOKIE_DATA="{course_config.get("cookie_data", "")}"

# Quality Available: "Original File", "1080p", "720p", "540p", "360p", "224p"
VIDEO_DOWNLOAD_QUALITY="{course_config.get("video_download_quality", "720p")}"
"""

        with open("config/php_downloader.env", "w") as f:
            f.write(env_content)

        print("PHP downloader environment file created at config/php_downloader.env")

    print("\nSetup complete! You can now run ThinkiPlex with:")
    print("  python -m thinkiplex")
    print("Or to select a specific course:")
    print("  python -m thinkiplex --course <course-name>")


if __name__ == "__main__":
    try:
        setup_wizard()
    except KeyboardInterrupt:
        print("\nSetup cancelled.")
        sys.exit(1)
