"""
Scripts Module
------------
This module provides functions that replace the shell scripts in the root directory.
"""

import json
import logging
import os
import shutil
import subprocess
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


def run_php_downloader(
    course_link: Optional[str] = None,
    json_file: Optional[str] = None,
    client_date: str = "",
    cookie_data: str = "",
    video_quality: str = "720p",
) -> bool:
    """
    Run the PHP downloader directly.

    Args:
        course_link: URL of the course to download
        json_file: Path to a JSON file for selective downloading
        client_date: Client date for authentication
        cookie_data: Cookie data for authentication
        video_quality: Video quality to download

    Returns:
        True if successful, False otherwise
    """
    logger.info("Running PHP downloader...")

    # Get the base directory
    base_dir = Path.cwd()

    # Set up paths
    php_dir = base_dir / "thinkiplex" / "downloader" / "php"
    php_env_file = php_dir / ".env"

    # Check if the PHP directory exists
    if not php_dir.exists():
        logger.error(f"PHP directory not found: {php_dir}")
        return False

    # Create a new environment file with the provided parameters
    try:
        if json_file:
            env_content = f"""# For downloading all content, use the course link.
COURSE_LINK=""

# For selective content downloads, use the JSON file created from Thinki Parser.
# Copy the file to Thinki Downloader root folder (where thinkidownloader3.php is there).
# Specify the file name below. Ex. COURSE_DATA_FILE="modified-course.json"
COURSE_DATA_FILE="{json_file}"

CLIENT_DATE="{client_date}"
COOKIE_DATA="{cookie_data}"

# Quality Available: "Original File", "1080p", "720p", "540p", "360p", "224p"
VIDEO_DOWNLOAD_QUALITY="{video_quality}"
"""
        else:
            env_content = f"""# For downloading all content, use the course link.
COURSE_LINK="{course_link}"

# For selective content downloads, use the JSON file created from Thinki Parser.
# Copy the file to Thinki Downloader root folder (where thinkidownloader3.php is there).
# Specify the file name below. Ex. COURSE_DATA_FILE="modified-course.json"
COURSE_DATA_FILE=""

CLIENT_DATE="{client_date}"
COOKIE_DATA="{cookie_data}"

# Quality Available: "Original File", "1080p", "720p", "540p", "360p", "224p"
VIDEO_DOWNLOAD_QUALITY="{video_quality}"
"""
        with open(php_env_file, "w") as dest:
            dest.write(env_content)
    except Exception as e:
        logger.error(f"Error creating environment file: {e}")
        return False

    # Change to the PHP directory
    os.chdir(php_dir)

    # Build the command
    cmd = ["php", "thinkidownloader3.php"]

    if json_file:
        cmd.extend(["--json", str(json_file)])
    elif course_link:
        cmd.append(str(course_link))
    else:
        logger.error("No course link or JSON file specified")
        return False

    # Run the command
    try:
        subprocess.run(cmd, check=True)
        logger.info("PHP downloader completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running PHP downloader: {e}")
        return False
    finally:
        # Change back to the base directory
        os.chdir(base_dir)


def run_php_downloader_docker(
    client_date: str = "",
    cookie_data: str = "",
    video_quality: str = "720p",
    course_link: str = "",
    check_updates_only: bool = False,
    course_name: str = "",
) -> bool:
    """
    Run the PHP downloader with Docker.

    Args:
        client_date: Client date for authentication
        cookie_data: Cookie data for authentication
        video_quality: Video quality to download
        course_link: URL of the course to download
        check_updates_only: Whether to only check for updates without downloading
        course_name: Name of the course folder

    Returns:
        True if successful, False otherwise
    """
    logger.info("Running PHP downloader with Docker...")

    if check_updates_only:
        logger.warning("The check_updates_only flag is not directly supported by the PHP script.")
        logger.warning(
            "The Docker container will download all content, but we'll treat it as an update check."
        )

    # Get the base directory
    base_dir = Path.cwd()

    # Set up paths
    php_dir = base_dir / "thinkiplex" / "downloader" / "php"

    # Check if the PHP directory exists
    if not php_dir.exists():
        logger.error(f"PHP directory not found: {php_dir}")
        return False

    # Check if Docker files exist
    compose_file = php_dir / "compose.yaml"
    if not compose_file.exists():
        logger.error(f"Docker compose file not found: {compose_file}")
        return False

    # Extract course name from URL if not provided
    if not course_name and course_link:
        try:
            # Extract the course name from the URL
            # Format: https://domain.thinkific.com/courses/take/course-name
            parts = course_link.split("/")
            course_name = parts[-1]  # Get the last part of the URL
            logger.info(f"Extracted course name from URL: {course_name}")
        except Exception as e:
            logger.warning(
                f"Could not extract course name from URL: {e}. Using 'course' as default."
            )
            course_name = "course"

    if not course_name:
        logger.error("No course name provided or could be extracted from the URL.")
        return False

    # Create the course data directory if it doesn't exist
    course_data_dir = base_dir / "data" / "courses" / course_name / "downloads"
    os.makedirs(course_data_dir, exist_ok=True)
    logger.info(f"Ensuring course data directory exists: {course_data_dir}")

    # Change to the PHP directory
    os.chdir(php_dir)

    try:
        # Set environment variables for Docker
        env = os.environ.copy()
        env["COURSE_LINK"] = course_link
        env["CLIENT_DATE"] = client_date
        env["COOKIE_DATA"] = cookie_data
        env["VIDEO_DOWNLOAD_QUALITY"] = video_quality
        env["CHECK_UPDATES_ONLY"] = str(check_updates_only).lower()
        env["COURSE_NAME"] = course_name

        # Run docker compose with environment variables
        cmd = ["docker", "compose", "-f", "compose.yaml", "up"]

        logger.info(f"Running Docker command from directory: {os.getcwd()}")
        logger.info(f"Command: {' '.join(cmd)}")
        logger.info(f"Course link: {course_link}")
        logger.info(f"Course name: {course_name}")
        logger.info(f"Data directory: {course_data_dir}")

        subprocess.run(cmd, check=True, env=env)

        if check_updates_only:
            logger.info("Docker update check completed successfully")
        else:
            logger.info("Docker download completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        if check_updates_only:
            logger.error(f"Error running Docker update check: {e}")
        else:
            logger.error(f"Error running Docker: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error running Docker: {e}")
        return False
    finally:
        # Change back to the base directory
        os.chdir(base_dir)


def run_php_downloader_docker_selective(
    json_file: str,
    client_date: str = "",
    cookie_data: str = "",
    video_quality: str = "720p",
    course_name: str = "",
) -> bool:
    """
    Run the PHP downloader with Docker for selective downloads.

    Args:
        json_file: Path to the JSON file with course data
        client_date: Client date for authentication
        cookie_data: Cookie data for authentication
        video_quality: Video quality to download
        course_name: Name of the course folder

    Returns:
        True if successful, False otherwise
    """
    logger.info("Running PHP downloader with Docker for selective downloads...")

    # Get the base directory
    base_dir = Path.cwd()

    # Set up paths
    php_dir = base_dir / "thinkiplex" / "downloader" / "php"

    # Check if the PHP directory exists
    if not php_dir.exists():
        logger.error(f"PHP directory not found: {php_dir}")
        return False

    # Check if Docker files exist
    compose_file = php_dir / "compose.selective.yaml"
    if not compose_file.exists():
        logger.error(f"Docker compose file not found: {compose_file}")
        return False

    # Check if the JSON file exists
    json_path = Path(json_file)
    if not json_path.exists():
        logger.error(f"JSON file not found: {json_path}")
        return False

    # Extract course name from JSON if not provided
    if not course_name:
        try:
            with open(json_path, "r") as f:
                data = json.load(f)
                course_name = data["course"]["slug"]
                logger.info(f"Extracted course name from JSON: {course_name}")
        except Exception as e:
            logger.warning(
                f"Could not extract course name from JSON: {e}. Using 'course' as default."
            )
            course_name = "course"

    # Create the course data directory if it doesn't exist
    course_data_dir = base_dir / "data" / "courses" / course_name / "downloads"
    os.makedirs(course_data_dir, exist_ok=True)
    logger.info(f"Ensuring course data directory exists: {course_data_dir}")

    # Copy the JSON file to the PHP directory
    json_dest = php_dir / json_path.name
    shutil.copy2(json_path, json_dest)
    logger.info(f"Copied JSON file to: {json_dest}")

    # Change to the PHP directory
    os.chdir(php_dir)

    try:
        # Set environment variables for Docker
        env = os.environ.copy()
        env["COURSE_DATA_FILE"] = json_path.name
        env["CLIENT_DATE"] = client_date
        env["COOKIE_DATA"] = cookie_data
        env["VIDEO_DOWNLOAD_QUALITY"] = video_quality
        env["COURSE_NAME"] = course_name

        # Run docker compose with environment variables
        cmd = ["docker", "compose", "-f", "compose.selective.yaml", "up"]

        logger.info(f"Running Docker command from directory: {os.getcwd()}")
        logger.info(f"Command: {' '.join(cmd)}")
        logger.info(f"JSON file: {json_path.name}")
        logger.info(f"Course name: {course_name}")
        logger.info(f"Data directory: {course_data_dir}")

        subprocess.run(cmd, check=True, env=env)

        logger.info("Docker selective download completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running Docker for selective download: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error running Docker for selective download: {e}")
        return False
    finally:
        # Clean up the copied JSON file
        if json_dest.exists():
            json_dest.unlink()
            logger.info(f"Removed temporary JSON file: {json_dest}")

        # Change back to the base directory
        os.chdir(base_dir)


def list_courses() -> List[str]:
    """
    List available courses.

    Returns:
        List of course names
    """
    logger.info("Listing available courses...")

    # Get the base directory
    base_dir = Path.cwd()

    # Set up paths - everything is now in data/courses
    courses_dir = base_dir / "data" / "courses"

    # Get the list of courses
    courses = []

    print("\nAvailable courses:")
    print("------------------")
    if courses_dir.exists():
        for item in courses_dir.iterdir():
            if item.is_dir():
                course_name = item.name
                courses.append(course_name)

                # Check if course has been downloaded
                downloads_dir = item / "downloads"
                if downloads_dir.exists() and any(downloads_dir.iterdir()):
                    status = "Downloaded"
                else:
                    status = "Not downloaded"

                # Check if course has been organized for Plex
                plex_dir = item / "plex"
                if plex_dir.exists() and any(plex_dir.iterdir()):
                    plex_status = "Organized"
                else:
                    plex_status = "Not organized"

                print(f"- {course_name}")
                print(f"  Status: {status}")
                print(f"  Plex: {plex_status}")
                print()
    else:
        print("No courses directory found.")

    return courses
