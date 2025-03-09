"""
ThinkiPlex Main Module
---------------------
Main entry point for the ThinkiPlex package.
"""

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import cast

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
        description="ThinkiPlex: Download and organize Thinkific courses for Plex"
    )

    # Main options
    parser.add_argument(
        "--course", help="Name of the course to process (if not specified, will prompt)"
    )

    parser.add_argument(
        "--list-courses", action="store_true", help="List available courses and exit"
    )

    # Downloader options
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

    # Script options
    parser.add_argument(
        "--run-php",
        help="Run the PHP downloader directly with the specified course link",
    )

    parser.add_argument(
        "--run-php-json",
        help="Run the PHP downloader directly with the specified JSON file",
    )

    parser.add_argument(
        "--run-docker",
        action="store_true",
        help="Run the PHP downloader with Docker",
    )

    # Authentication options
    parser.add_argument(
        "--update-auth",
        action="store_true",
        help="Update authentication data (client date and cookie data) for a course",
    )

    parser.add_argument(
        "--client-date",
        help="Set the client date for the course (used with --update-auth)",
    )

    parser.add_argument(
        "--cookie-data",
        help="Set the cookie data for the course (used with --update-auth)",
    )

    # Cleanup options
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Consolidate the data structure into data/courses",
    )

    # Organizer options
    parser.add_argument(
        "--skip-organize",
        action="store_true",
        help="Skip organizing the course content",
    )

    parser.add_argument(
        "--extract-audio",
        action="store_true",
        help="Extract audio from video files",
    )

    parser.add_argument(
        "--skip-audio",
        action="store_true",
        help="Skip extracting audio from video files",
    )

    # Logging options
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    parser.add_argument("--log-file", help="Path to the log file")

    return parser


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

    # Import modules
    try:
        from thinkiplex.cli.cleanup import run_cleanup
        from thinkiplex.cli.course_selector import (
            get_course_config,
            select_course_interactive,
        )
        from thinkiplex.cli.scripts import (
            list_courses,
            run_php_downloader,
            run_php_downloader_docker,
        )
        from thinkiplex.cli.wizard import setup_wizard
        from thinkiplex.downloader import PHPDownloader
        from thinkiplex.utils.config import Config
    except ImportError as e:
        logger.error(f"Error importing required modules: {e}")
        logger.error("Please make sure all dependencies are installed.")
        return 1

    # Handle authentication update
    if args.update_auth:
        if not args.course:
            # If no course specified, prompt the user to select one
            course_name = select_course_interactive()
            if not course_name:
                logger.error("No course selected.")
                return 1
        else:
            course_name = args.course

        # Load the configuration
        config = Config()

        # Check if the course exists
        if f"courses.{course_name}" not in config.get("courses", {}):
            logger.error(f"Course '{course_name}' not found in configuration.")
            return 1

        # Update client date if provided
        if args.client_date:
            config.set(f"courses.{course_name}.client_date", args.client_date)
            logger.info(f"Updated client date for course '{course_name}'.")

        # Update cookie data if provided
        if args.cookie_data:
            config.set(f"courses.{course_name}.cookie_data", args.cookie_data)
            logger.info(f"Updated cookie data for course '{course_name}'.")

        # Save the configuration
        config.save()
        logger.info(f"Authentication data updated for course '{course_name}'.")
        return 0

    # Handle script options
    if args.run_php:
        # Get authentication data from command line or prompt
        client_date = args.client_date
        cookie_data = args.cookie_data

        if not client_date:
            client_date = input("Enter client date (leave empty to skip): ")

        if not cookie_data:
            cookie_data = input("Enter cookie data (leave empty to skip): ")

        return (
            0
            if run_php_downloader(
                course_link=args.run_php,
                client_date=client_date,
                cookie_data=cookie_data,
            )
            else 1
        )

    if args.run_php_json:
        # Get authentication data from command line or prompt
        client_date = args.client_date
        cookie_data = args.cookie_data

        if not client_date:
            client_date = input("Enter client date (leave empty to skip): ")

        if not cookie_data:
            cookie_data = input("Enter cookie data (leave empty to skip): ")

        return (
            0
            if run_php_downloader(
                json_file=args.run_php_json,
                client_date=client_date,
                cookie_data=cookie_data,
            )
            else 1
        )

    if args.run_docker:
        # Get authentication data from command line or prompt
        client_date = args.client_date
        cookie_data = args.cookie_data
        course_link = args.run_php if args.run_php else ""
        video_quality = args.video_quality if hasattr(args, "video_quality") else "720p"

        if not client_date:
            client_date = input("Enter client date (leave empty to skip): ")

        if not cookie_data:
            cookie_data = input("Enter cookie data (leave empty to skip): ")

        # Extract course name from the URL
        course_name = ""
        if course_link:
            try:
                parts = course_link.split("/")
                course_name = parts[-1]  # Get the last part of the URL
            except Exception:
                course_name = ""

        # If extraction failed, ask the user for a course name
        if not course_name:
            course_name = input("Enter course name (required): ")
            if not course_name:
                print("Course name is required.")
                return 1

        return (
            0
            if run_php_downloader_docker(
                client_date=client_date,
                cookie_data=cookie_data,
                video_quality=video_quality,
                course_link=course_link,
                course_name=course_name,
            )
            else 1
        )

    # Handle cleanup option
    if args.cleanup:
        return 0 if run_cleanup() else 1

    # If list-courses flag is set, list available courses and exit
    if args.list_courses:
        list_courses()
        return 0

    # Interactive mode - show main menu
    if not args.course:
        print("ThinkiPlex")
        print("=========")
        print("\nWhat would you like to do?")
        print("1. Configure courses")
        print("2. Process a course")
        print("3. Run PHP downloader directly")
        print("4. Run PHP downloader with Docker")
        print("5. List available courses")
        print("6. Consolidate data structure")
        print("7. Update authentication data")
        print("8. Extract audio from videos")
        print("9. Exit")

        choice = input("\nEnter your choice (1-9): ")

        if choice == "1":
            # Run the configuration wizard
            setup_wizard()
            return 0
        elif choice == "2":
            # Select a course to process
            selected_course = select_course_interactive()
            if not selected_course:
                return 0
            # Set the course name for processing
            course_name = selected_course
        elif choice == "3":
            # Run PHP downloader directly
            course_link = input("Enter course link (or press Enter to cancel): ")
            if not course_link:
                return 0

            # Prompt for authentication data
            client_date = input("Enter client date (leave empty to skip): ")
            cookie_data = input("Enter cookie data (leave empty to skip): ")

            return (
                0
                if run_php_downloader(
                    course_link=course_link,
                    client_date=client_date,
                    cookie_data=cookie_data,
                )
                else 1
            )
        elif choice == "4":
            # Run PHP downloader with Docker
            # Prompt for authentication data
            client_date = input("Enter client date (leave empty to skip): ")
            cookie_data = input("Enter cookie data (leave empty to skip): ")
            course_link = input("Enter course link (required): ")
            video_quality = (
                input("Enter video quality (leave empty for 720p): ") or "720p"
            )

            # Extract course name from the URL
            course_name = ""
            if course_link:
                try:
                    parts = course_link.split("/")
                    course_name = parts[-1]  # Get the last part of the URL
                except Exception:
                    course_name = ""

            # If extraction failed, ask the user for a course name
            if not course_name:
                course_name = input("Enter course name (required): ")
                if not course_name:
                    print("Course name is required.")
                    return 1

            return (
                0
                if run_php_downloader_docker(
                    client_date=client_date,
                    cookie_data=cookie_data,
                    video_quality=video_quality,
                    course_link=course_link,
                    course_name=course_name,
                )
                else 1
            )
        elif choice == "5":
            # List available courses
            list_courses()
            return 0
        elif choice == "6":
            # Consolidate data structure
            return 0 if run_cleanup() else 1
        elif choice == "7":
            # Update authentication data
            selected_course = select_course_interactive()
            if not selected_course:
                return 0

            # Load the configuration
            config = Config()

            # Get the current values
            course_config = config.get_course_config(selected_course)

            # Prompt for new values
            print(f"\nUpdating authentication data for course: {selected_course}")
            print("Leave fields empty to keep current values.")

            client_date = input(
                f"Client date [{course_config.get('client_date', '')}]: "
            )
            cookie_data = input(
                f"Cookie data [{course_config.get('cookie_data', '')}]: "
            )

            # Update values if provided
            if client_date:
                config.set(f"courses.{selected_course}.client_date", client_date)

            if cookie_data:
                config.set(f"courses.{selected_course}.cookie_data", cookie_data)

            # Save the configuration
            config.save()
            print(f"Authentication data updated for course '{selected_course}'.")
            return 0
        elif choice == "8":
            # Extract audio from videos
            selected_course = select_course_interactive()
            if not selected_course:
                return 0

            # Get course configuration
            course_config = get_course_config(selected_course)
            if not course_config:
                logger.error(f"Course '{selected_course}' not found in configuration.")
                return 1

            # Extract audio
            try:
                from thinkiplex.organizer import extract_course_audio

                print(f"\nExtracting audio for course: {selected_course}")

                success = extract_course_audio(
                    course_name=selected_course,
                    base_dir=base_dir,
                    show_name=course_config.get("show_name"),
                    season=course_config.get("season", "01"),
                    audio_quality=course_config.get("audio_quality", 0),
                    audio_format=course_config.get("audio_format", "mp3"),
                )

                if success:
                    print("Audio extraction completed successfully.")
                else:
                    print("Audio extraction failed.")

                return 0 if success else 1
            except Exception as e:
                logger.error(f"Error extracting audio: {e}")
                return 1

        elif choice == "9":
            return 0
        else:
            print("Invalid choice. Please enter a number between 1 and 9.")
            return 1
    else:
        course_name = args.course

    # At this point, course_name is guaranteed to be a string
    course_name = cast(str, course_name)

    # Get course configuration
    course_config = get_course_config(course_name)
    if not course_config:
        logger.error(f"Course '{course_name}' not found in configuration.")
        return 1

    logger.info(f"Processing course: {course_name}")

    # Create course directories if they don't exist
    course_dir = Path("data/courses") / course_name
    downloads_dir = course_dir / "downloads"
    plex_dir = course_dir / "plex"
    os.makedirs(course_dir, exist_ok=True)
    os.makedirs(downloads_dir, exist_ok=True)
    os.makedirs(plex_dir, exist_ok=True)

    # Get course link and authentication data
    course_link = course_config.get("course_link", "")
    if not course_link:
        logger.error(
            "No course link specified in configuration. Please add a course_link in config/thinkiplex.yaml"
        )
        return 1

    # Get authentication data from course configuration
    client_date = course_config.get("client_date", "")
    cookie_data = course_config.get("cookie_data", "")
    video_download_quality = course_config.get("video_download_quality", "720p")

    # Check if authentication data is available
    if not client_date or not cookie_data:
        logger.warning("Authentication data (client date or cookie data) is missing.")
        logger.warning(
            "The downloader may not work correctly without authentication data."
        )
        logger.warning("Use the --update-auth option to update authentication data.")

    # Determine whether to run the downloader
    run_downloader = course_config.get("run_downloader", False)
    if args.run_downloader:
        run_downloader = True
    if args.skip_downloader:
        run_downloader = False

    # Always check for updates using Docker
    if run_downloader:
        # Run the full downloader
        logger.info(f"Downloading course with Docker: {course_name}")
        success = run_php_downloader_docker(
            client_date=client_date,
            cookie_data=cookie_data,
            video_quality=video_download_quality,
            course_link=course_link,
            check_updates_only=False,
            course_name=course_name,
        )
        if not success:
            logger.error("Docker downloader failed.")
            return 1
    else:
        # Just check for updates without downloading
        logger.info(f"Checking for updates with Docker: {course_name}")
        success = run_php_downloader_docker(
            client_date=client_date,
            cookie_data=cookie_data,
            video_quality=video_download_quality,
            course_link=course_link,
            check_updates_only=True,
            course_name=course_name,
        )
        if not success:
            logger.warning("Docker update check failed.")
            logger.warning("Continuing with existing course data.")

    # Organize the course content if not skipped
    if not args.skip_organize:
        logger.info("Organizing course content...")

        # Import the organizer module
        try:
            # We'll implement this function in the organizer module
            # Get the course data
            from thinkiplex.downloader.php_wrapper import PHPDownloader
            from thinkiplex.organizer.main import organize_course

            php_downloader = PHPDownloader(base_dir=Path.cwd())
            course_data = php_downloader.get_course_data(course_name)
            if not course_data:
                logger.error(f"No course data found for {course_name}.")
                return 1

            # Set up the paths
            source_dir = Path("data/courses") / course_name / "downloads"
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

    # Extract audio if enabled
    extract_audio = course_config.get("extract_audio", False)
    if args.extract_audio:
        extract_audio = True
    if args.skip_audio:
        extract_audio = False

    if extract_audio:
        logger.info("Extracting audio from video files...")

        # Import the audio extraction module
        try:
            from thinkiplex.organizer import extract_course_audio

            # Extract audio
            result = extract_course_audio(
                course_name=course_name,
                base_dir=base_dir,
                show_name=course_config.get("show_name"),
                season=course_config.get("season", "01"),
                audio_quality=course_config.get("audio_quality", 0),
                audio_format=course_config.get("audio_format", "mp3"),
            )

            # Consider it a success even if no files were processed
            # This prevents the script from failing when there are no video files
            if isinstance(result, bool) and not result:
                logger.warning(
                    "No audio files were extracted. This may be normal if there are no video files."
                )
            else:
                logger.info("Audio extraction completed successfully.")

        except Exception as e:
            logger.error(f"Error extracting audio: {e}")
            logger.warning("Continuing despite audio extraction failure.")

    logger.info(f"Processing of course {course_name} completed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
