"""
ThinkiPlex CLI Module
--------------------
This module provides the command-line interface for ThinkiPlex.
"""

import argparse
import logging
import os
import sys
from pathlib import Path

import yaml

from thinkiplex.cli.course_selector import load_config
from thinkiplex.downloader import PHPDownloader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


def create_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="ThinkiPlex: Download and organize Thinkific courses for Plex",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run the setup wizard to configure a new course
  thinkiplex --setup
        
  # List configured courses
  thinkiplex --list-courses
  
  # Process a specific course
  thinkiplex --course <course-name>
  
  # Update authentication data for a course
  thinkiplex --course <course-name> --update-auth --client-date "..." --cookie-data "..."
"""
    )

    parser.add_argument(
        "--config",
        help="Path to the configuration file (default: config/thinkiplex.yaml)",
        default="config/thinkiplex.yaml",
    )

    parser.add_argument(
        "--course", help="Name of the course to process (if not specified, will prompt)"
    )

    parser.add_argument(
        "--setup",
        action="store_true",
        help="Run the setup wizard to configure ThinkiPlex",
    )

    parser.add_argument(
        "--list-courses", action="store_true", help="List available courses and exit"
    )

    parser.add_argument(
        "--run-downloader",
        action="store_true",
        help="Force run the downloader even if disabled in config",
    )

    parser.add_argument(
        "--skip-downloader",
        action="store_true",
        help="Skip running the downloader even if enabled in config",
    )

    parser.add_argument(
        "--skip-organize",
        action="store_true",
        help="Skip organizing the course content",
    )

    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    parser.add_argument("--log-file", help="Path to the log file")

    return parser


def list_courses(config_path: Path) -> None:
    """List available courses and exit."""
    if not config_path.exists():
        print(f"Configuration file not found: {config_path}")
        print("Please run the setup wizard first.")
        return

    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        if not config or "courses" not in config or not config["courses"]:
            print("No courses found in configuration file.")
            return

        print("\nAvailable courses:")
        print("-----------------")
        for course_name, course_config in config["courses"].items():
            show_name = course_config.get("show_name", course_name)
            print(f"- {course_name}: {show_name}")

            # Check if course has been downloaded
            course_dir = Path("data/courses") / course_name
            if course_dir.exists() and any(course_dir.iterdir()):
                print("  Status: Downloaded")
            else:
                print("  Status: Not downloaded")

            # Check if course has been organized for Plex
            plex_dir = Path("data/courses") / course_name / "plex"
            if plex_dir.exists() and any(plex_dir.iterdir()):
                print("  Plex: Organized")
            else:
                print("  Plex: Not organized")

            print()
    except Exception as e:
        print(f"Error loading configuration: {e}")


def ensure_directories() -> None:
    """Ensure that the required directories exist."""
    dirs = [
        "config",
        "data/courses",
        "logs",
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)


def main() -> int:
    """Main entry point for the CLI."""
    # Create the argument parser
    parser = create_parser()
    args = parser.parse_args()

    # Set up logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.log_file:
        file_handler = logging.FileHandler(args.log_file)
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        logging.getLogger().addHandler(file_handler)

    # Ensure directories exist
    ensure_directories()

    # Get the base directory
    base_dir = Path.cwd()

    # Convert config path to Path object
    config_path = Path(args.config)

    # If setup flag is set, run the setup wizard
    if args.setup:
        try:
            from thinkiplex.cli.wizard import setup_wizard

            setup_wizard()
            return 0
        except ImportError:
            logger.error(
                "Setup wizard not found. Please check installation."
            )
            return 1

    # If list-courses flag is set, list available courses and exit
    if args.list_courses:
        list_courses(config_path)
        return 0

    # Load configuration
    course_name, course_config = load_config(args.course, config_path)
    if course_name is None or course_config is None:
        return 1

    logger.info(f"Processing course: {course_name}")

    # Create course directories if they don't exist
    course_dir = Path("data/courses") / course_name
    os.makedirs(course_dir, exist_ok=True)

    # Initialize the downloader
    downloader = PHPDownloader(base_dir)

    # Determine whether to run the downloader
    run_downloader = course_config.get("run_downloader", False)
    if args.run_downloader:
        run_downloader = True
    if args.skip_downloader:
        run_downloader = False

    # Run the downloader if enabled
    if run_downloader:
        logger.info("Running downloader...")

        # Check if we have a course link
        course_link = course_config.get("course_link")
        if not course_link:
            logger.error("No course link specified in configuration.")
            return 1

        # Set up the PHP environment
        env_file = Path("config/php_downloader.env")
        if not env_file.exists():
            # Create the environment file from the course configuration
            env_content = f"""# Generated by ThinkiPlex
# For downloading all content, use the course link.
COURSE_LINK="{course_config.get("course_link", "")}"

# For selective content downloads, use the JSON file created from Thinki Parser.
# COURSE_DATA_FILE=""

CLIENT_DATE="{course_config.get("client_date", "")}"
COOKIE_DATA="{course_config.get("cookie_data", "")}"

# Quality Available: "Original File", "1080p", "720p", "540p", "360p", "224p"
VIDEO_DOWNLOAD_QUALITY="{course_config.get("video_quality", "720p")}"
"""
            with open(env_file, "w") as f:
                f.write(env_content)

        # Run the downloader
        success = downloader.download_course(course_link)
        if not success:
            logger.error("Downloader failed.")
            return 1

        logger.info("Downloader completed successfully.")

    # Organize the course content if not skipped
    if not args.skip_organize:
        logger.info("Organizing course content...")

        # Import the organizer module
        try:
            from thinkiplex.organizer import organize_course

            # Get the course data
            course_data = downloader.get_course_data(course_name)
            if not course_data:
                logger.error(f"No course data found for {course_name}.")
                return 1

            # Set up the paths
            source_dir = Path("data/courses") / course_name
            plex_dir = Path("data/courses") / course_name / "plex"

            # Create the Plex directory if it doesn't exist
            os.makedirs(plex_dir, exist_ok=True)

            # Organize the course
            organize_course(
                source_dir=source_dir,
                plex_dir=plex_dir,
                course_data=course_data,
                show_name=course_config.get("show_name", course_name),
                season=course_config.get("season", "01"),
                extract_audio=course_config.get("extract_audio", True),
                audio_quality=course_config.get("audio_quality", 0),
                audio_format=course_config.get("audio_format", "mp3"),
            )

            logger.info("Course organization completed successfully.")
        except ImportError:
            logger.error("Organizer module not found.")
            return 1

    logger.info(f"Processing of course {course_name} completed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
