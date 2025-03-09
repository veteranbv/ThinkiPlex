"""
ThinkiPlex Main Module
---------------------
Main entry point for the ThinkiPlex package.
"""

import argparse
import logging
import os
import re
import sys
from pathlib import Path
from typing import List, Optional, cast

import inquirer
from dotenv import load_dotenv

from .pdf import PDFGenerator
from .utils.config import Config

# Load environment variables from .env file
config_dir = Path(__file__).resolve().parent.parent / "config"
env_path = config_dir / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    # Try to load from the root directory as fallback
    root_env_path = Path(__file__).resolve().parent.parent / ".env"
    if root_env_path.exists():
        load_dotenv(root_env_path)

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
  # Interactive mode (menu-driven)
  thinkiplex

  # Run the setup wizard to configure a new course
  thinkiplex --setup

  # List configured courses
  thinkiplex --list-courses

  # Process a specific course
  thinkiplex --course <course-name>

  # Update authentication data for a course
  thinkiplex --course <course-name> --update-auth --client-date "..." --cookie-data "..."
""",
    )

    # Main options
    parser.add_argument(
        "--course", help="Name of the course to process (if not specified, will prompt)"
    )

    parser.add_argument(
        "--list-courses", action="store_true", help="List available courses and exit"
    )

    parser.add_argument(
        "--generate-pdf", action="store_true", help="Generate a PDF of course resources"
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

    # Transcription and AI summary options
    transcription_group = parser.add_argument_group("Transcription and AI Summary")
    transcription_group.add_argument(
        "--transcribe",
        action="store_true",
        help="Generate transcriptions and AI summaries for course materials",
    )
    transcription_group.add_argument(
        "--claude-model",
        help="Claude model to use for AI summaries (default: uses the default model from config)",
    )
    transcription_group.add_argument(
        "--no-diarization",
        action="store_true",
        help="Disable speaker diarization in transcriptions",
    )
    transcription_group.add_argument(
        "--prompt-type",
        help="Type of prompt to use for AI summaries (options: comprehensive, course_notes, summarize, transcribe, analyze)",
    )

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


def generate_pdf(course_id: str) -> bool:
    """Generate a PDF of course resources.

    Args:
        course_id: ID of the course

    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info(f"Generating PDF for course: {course_id}")

        # Initialize the PDF generator
        pdf_generator = PDFGenerator()

        # Generate the PDF
        output_file = pdf_generator.generate_course_pdf(course_id)

        logger.info(f"PDF generation complete: {output_file}")
        print(f"PDF generated successfully: {output_file}")
        return True
    except Exception as e:
        logger.error(f"Error generating PDF: {e}")
        print(f"Error generating PDF: {e}")
        return False


def interactive_menu_pdf_generation() -> bool:
    """Interactive menu for PDF generation.

    Returns:
        True if successful, False otherwise
    """
    # Get list of available courses
    courses = get_available_courses()

    if not courses:
        print("No courses found. Please configure a course first.")
        return False

    # Ask user to select a course
    questions = [
        inquirer.List(
            "course",
            message="Select a course to generate PDF for",
            choices=courses,
        ),
    ]

    answers = inquirer.prompt(questions)

    if not answers:
        return False

    course_id = answers["course"]

    # Generate PDF
    return generate_pdf(course_id)


def get_available_courses() -> List[str]:
    """Get a list of available courses.

    Returns:
        List of course IDs
    """
    try:
        config = Config()
        courses = list(config.config.get("courses", {}).keys())
        return courses
    except Exception as e:
        logger.error(f"Error getting available courses: {e}")
        return []


def main() -> int:
    """Main entry point for the CLI."""
    # Create the argument parser
    parser = create_parser()

    # If no arguments are provided, show interactive menu by setting no course
    if len(sys.argv) == 1:
        args = argparse.Namespace(
            course=None,
            list_courses=False,
            generate_pdf=False,
            run_downloader=False,
            skip_downloader=False,
            run_php=None,
            run_php_json=None,
            run_docker=False,
            update_auth=False,
            client_date=None,
            cookie_data=None,
            cleanup=False,
            skip_organize=False,
            extract_audio=False,
            skip_audio=False,
            verbose=False,
            log_file=None,
            transcribe=False,
            claude_model="claude-3-5-sonnet-20240620",
            no_diarization=False,
            prompt_type="comprehensive",
        )
    else:
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

    # Handle generate-pdf option
    if args.generate_pdf:
        course_id = args.course

        if not course_id:
            # If no course specified, show interactive menu
            return 0 if interactive_menu_pdf_generation() else 1

        # Generate PDF for the specified course
        return 0 if generate_pdf(course_id) else 1

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
        print("9. Generate transcriptions and AI summaries")
        print("10. Generate PDF of course resources")
        print("11. Exit")

        choice = input("\nEnter your choice (1-11): ")

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
            video_quality = input("Enter video quality (leave empty for 720p): ") or "720p"

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

            current_client_date = course_config.get("client_date", "")
            current_cookie_data = course_config.get("cookie_data", "")

            # Only show first/last few characters of current values for better UX
            display_client_date = (
                current_client_date[:10] + "..."
                if len(current_client_date) > 10
                else current_client_date
            )
            display_cookie_data = (
                current_cookie_data[:10] + "..."
                if len(current_cookie_data) > 10
                else current_cookie_data
            )

            print("\nTIP: To get these values:")
            print("1. Open your course in Chrome/Firefox Developer Tools (F12)")
            print("2. Go to Network tab and refresh the page")
            print("3. Find a request to your course page and check Headers")
            print("4. Look for 'date' and 'cookie' request headers")

            client_date = input(f"Client date [{display_client_date}]: ")
            cookie_data = input(f"Cookie data [{display_cookie_data}]: ")

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
            # Generate transcriptions and AI summaries
            interactive_menu_transcription()
        elif choice == "10":
            # Generate PDF of course resources
            return 0 if interactive_menu_pdf_generation() else 1
        elif choice == "11":
            return 0
        else:
            print("Invalid choice. Please enter a number between 1 and 11.")
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
        logger.warning("The downloader may not work correctly without authentication data.")
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

    # Handle audio extraction
    if args.extract_audio or course_config.get("extract_audio", False):
        logger.info("Extracting audio from videos...")

        try:
            from thinkiplex.organizer import extract_course_audio

            success = extract_course_audio(
                course_name=course_name,
                base_dir=base_dir,
                show_name=course_config.get("show_name"),
                season=course_config.get("season", "01"),
                audio_quality=course_config.get("audio_quality", 0),
                audio_format=course_config.get("audio_format", "mp3"),
            )

            if success:
                logger.info("Audio extraction completed successfully.")
            else:
                logger.error("Audio extraction failed.")
        except Exception as e:
            logger.error(f"Error extracting audio: {e}")
            logger.warning("Continuing despite audio extraction failure.")

    # Generate transcriptions and AI summaries if requested
    if args.transcribe:
        logger.info("Generating transcriptions and AI summaries...")

        try:
            # Import the transcription module
            from thinkiplex.transcribe import TranscriptionProcessor

            # Initialize the processor
            processor = TranscriptionProcessor()

            # Set the Claude model if specified
            if args.claude_model:
                processor.set_claude_model(args.claude_model)
                logger.info(f"Using Claude model: {args.claude_model}")
            else:
                default_model = processor.get_available_claude_models()[0]
                logger.info(f"Using default Claude model: {default_model}")

            # Set up diarization option
            diarization = not args.no_diarization
            if args.no_diarization:
                logger.info("Speaker diarization is disabled")
            else:
                logger.info("Speaker diarization is enabled")

            # Log the prompt type being used
            if args.prompt_type:
                logger.info(f"Using prompt type: {args.prompt_type}")
            else:
                default_prompt = processor.get_default_prompt_type()
                logger.info(f"Using default prompt type: {default_prompt}")

            # Process the course
            results = processor.process_course_materials(
                course_name=course_name,
                prompt_type=args.prompt_type,
                base_dir=base_dir,
                diarization=diarization,
            )

            # Print summary of results
            for season, season_results in results.items():
                completed = sum(1 for r in season_results if r.get("status") == "completed")
                skipped = sum(1 for r in season_results if r.get("status") == "skipped")
                failed = sum(1 for r in season_results if "error" in r)

                logger.info(
                    f"Season {season}: {completed} completed, {skipped} skipped, {failed} failed"
                )

                # Print details for failed items
                for result in season_results:
                    if "error" in result:
                        logger.error(f"Failed to process {result['class_name']}: {result['error']}")

            logger.info("Transcription and AI summary generation completed")

        except Exception as e:
            logger.error(f"Error generating transcriptions and summaries: {e}")
            logger.warning("Continuing despite transcription and summary failure.")

    logger.info(f"Processing of course {course_name} completed.")
    return 0


def interactive_menu_transcription() -> None:
    """Interactive menu for transcription options."""
    print("\n=== Transcription Options ===")
    print("1. Generate transcriptions and AI summaries")
    print("2. Return to main menu")

    choice = input("\nEnter your choice (1-2): ")

    if choice == "1":
        # Initialize the transcription processor
        from thinkiplex.transcribe.processor import TranscriptionProcessor

        processor = TranscriptionProcessor()

        # Get available models and prompt types
        available_models = processor.get_available_claude_models()
        available_prompt_types = processor.get_available_prompt_types()

        # Select a course
        course_name = select_course_interactive()
        if not course_name:
            return

        # Get course configuration
        from thinkiplex.utils.config import Config

        config = Config()
        course_config = config.get_course_config(course_name)

        # Select Claude model
        print("\n=== Available Claude Models ===")
        for i, model_name in enumerate(available_models, 1):
            model_info = processor.get_claude_model_info(model_name)
            model_description = model_info.get("description", "")
            is_default = model_info.get("is_default", False)
            default_marker = " (default)" if is_default else ""
            print(f"{i}. {model_name} - {model_description}{default_marker}")

        model_choice = input(
            "\nSelect an AI model for generating summaries:\n"
            "- Different models have different capabilities and speeds\n"
            "- Enter a number or press Enter for default\n"
            "Your selection: "
        )
        if model_choice.isdigit() and 1 <= int(model_choice) <= len(available_models):
            selected_model = available_models[int(model_choice) - 1]
            processor.set_claude_model(selected_model)
            print(f"Using model: {selected_model}")
        else:
            # Find the default model
            default_model = next(
                (
                    model
                    for model in available_models
                    if processor.get_claude_model_info(model).get("is_default", False)
                ),
                available_models[0] if available_models else None,
            )
            if default_model:
                processor.set_claude_model(default_model)
                print(f"Using default model: {default_model}")
            else:
                print("No models available.")
                return

        # Ask for diarization
        diarization = (
            input(
                "\nEnable speaker diarization for transcription?\n"
                "- Speaker diarization identifies different speakers in the audio\n"
                "- Recommended for content with multiple speakers\n"
                "- Enter 'y' for yes or 'n' for no (default: y): "
            ).lower()
            != "n"
        )

        # Display available prompt types
        print("\n=== Available Prompt Types ===")
        for i, prompt_type in enumerate(available_prompt_types, 1):
            print(f"{i}. {prompt_type}")

        # Select prompt type
        prompt_choice = input(
            "\nSelect a prompt type for AI summaries:\n"
            "- Each prompt type generates different styles of summaries\n"
            "- Enter a number or press Enter for default\n"
            "Your selection: "
        )
        if prompt_choice.isdigit() and 1 <= int(prompt_choice) <= len(available_prompt_types):
            selected_prompt_type = available_prompt_types[int(prompt_choice) - 1]
        else:
            selected_prompt_type = processor.get_default_prompt_type()

        print(f"Using prompt type: {selected_prompt_type}")

        # Process specific download directories or all
        process_specific = (
            input(
                "\nDo you want to select specific download directories to process? (y/n)\n"
                "- Choose 'y' to manually select which download directories to process (useful for processing specific sessions)\n"
                "- Choose 'n' to process all course materials automatically\n"
                "Your choice: "
            ).lower()
            == "y"
        )

        if process_specific:
            from pathlib import Path

            # List available download directories
            downloads_dir = Path(f"data/courses/{course_name}/downloads")
            if not downloads_dir.exists():
                print(f"Error: Downloads directory not found: {downloads_dir}")
                return

            # Get all download directories sorted by their episode number
            download_dirs = []
            for dir_path in downloads_dir.glob("*"):
                if dir_path.is_dir():
                    # Extract episode number from directory name
                    match = re.match(r"^(\d+)\.", dir_path.name)
                    if match:
                        episode_number = int(match.group(1))
                        download_dirs.append((episode_number, dir_path))
                    else:
                        # If no episode number found, add to the end
                        download_dirs.append((999, dir_path))

            # Sort by episode number
            download_dirs.sort(key=lambda x: x[0])

            # Extract just the paths after sorting
            sorted_paths = [dir_path for _, dir_path in download_dirs]

            print("\n=== Available Download Directories ===")
            for i, dir_path in enumerate(sorted_paths, 1):
                print(f"{i}. {dir_path.name}")

            # Select directories to process
            dir_choices = input(
                "\nEnter directory numbers to process:\n"
                "- For multiple directories, separate numbers with commas (e.g., '1,3,5')\n"
                "- Type 'all' to process all directories\n"
                "Your selection: "
            )

            if dir_choices.lower() == "all":
                selected_dirs = sorted_paths
            else:
                selected_indices = [
                    int(idx.strip()) - 1 for idx in dir_choices.split(",") if idx.strip().isdigit()
                ]
                selected_dirs = [
                    sorted_paths[idx] for idx in selected_indices if 0 <= idx < len(sorted_paths)
                ]

            if not selected_dirs:
                print("No valid directories selected.")
                return

            # Process each selected directory
            for dir_path in selected_dirs:
                print(f"\nProcessing directory: {dir_path.name}")
                try:
                    result = processor.process_download_directory(
                        dir_path, selected_prompt_type, diarization
                    )
                    if result:
                        print(f"Successfully processed: {dir_path.name}")
                    else:
                        print(f"Failed to process: {dir_path.name}")
                except Exception as e:
                    print(f"Error processing {dir_path.name}: {str(e)}")
        else:
            # Process all course materials
            print("\nProcessing all course materials...")
            results = processor.process_course_materials(
                course_name=course_name, prompt_type=selected_prompt_type, diarization=diarization
            )

            # Display results
            if results.get("errors"):
                print("\nErrors encountered:")
                for error in results["errors"]:
                    print(f"- {error['directory']}: {error['error']}")

            print(f"\nProcessed {len(results.get('results', {}))} directories successfully.")

        print("\nTranscription and AI summary generation completed.")
    elif choice == "2":
        return
    else:
        print("Invalid choice. Please try again.")
        interactive_menu_transcription()


def select_course_interactive() -> Optional[str]:
    """Select a course interactively.

    Returns:
        Course name or None if no course is selected
    """
    print("\n=== Available Courses ===")

    # Get list of courses
    courses_dir = Path("data/courses")
    if not courses_dir.exists():
        print("No courses directory found.")
        return None

    # Get all course directories
    courses = []
    for dir_path in courses_dir.glob("*"):
        if dir_path.is_dir():
            courses.append(dir_path.name)

    if not courses:
        print("No courses found.")
        return None

    # Sort courses alphabetically
    courses.sort()

    # Display courses
    for i, course in enumerate(courses, 1):
        print(f"{i}. {course}")

    # Select a course
    choice = input("\nSelect a course (or press Enter to cancel): ")
    if not choice:
        return None

    if choice.isdigit() and 1 <= int(choice) <= len(courses):
        return courses[int(choice) - 1]
    else:
        print("Invalid choice.")
        return None


if __name__ == "__main__":
    sys.exit(main())
