"""
PHP Downloader Wrapper
--------------------
This module provides a Python wrapper for the PHP downloader.
"""

import json
import logging
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, Tuple

logger = logging.getLogger(__name__)


class PHPDownloader:
    """Python wrapper for the PHP downloader."""

    def __init__(self, base_dir: Path):
        """
        Initialize the PHP downloader wrapper.

        Args:
            base_dir: Base directory of the project
        """
        self.base_dir = base_dir
        self.php_script = (
            self.base_dir
            / "thinkiplex"
            / "downloader"
            / "php"
            / "thinkidownloader3.php"
        )

        # Create necessary directories
        self._create_directories()

    def _create_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        os.makedirs(self.base_dir / "data" / "courses", exist_ok=True)
        os.makedirs(self.base_dir / "config", exist_ok=True)

    def download_course(
        self,
        course_link: str,
        client_date: str = "",
        cookie_data: str = "",
        video_quality: str = "720p",
    ) -> bool:
        """
        Download a course using the PHP downloader.

        Args:
            course_link: URL of the course to download
            client_date: Client date for authentication
            cookie_data: Cookie data for authentication
            video_quality: Video quality to download

        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Downloading course: {course_link}")

        # Check if PHP is installed
        try:
            subprocess.run(["php", "--version"], check=True, capture_output=True)
        except (subprocess.SubprocessError, FileNotFoundError):
            logger.error(
                "PHP is not installed or not in the PATH. Cannot download course."
            )
            return False

        # Check if the PHP script exists
        if not self.php_script.exists():
            logger.error(f"PHP script not found: {self.php_script}")
            return False

        # Extract course folder name from the URL
        course_folder = course_link.split("/")[-1]

        # Set up environment file
        env_file = self.base_dir / "config" / "php_downloader.env"
        php_env_file = self.php_script.parent / ".env"

        # Create a new environment file with the provided parameters
        try:
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

        # Change to the PHP script directory
        os.chdir(self.php_script.parent)

        # Run the PHP script
        try:
            subprocess.run(["php", str(self.php_script), course_link], check=True)
            logger.info("PHP downloader completed successfully")

            # Move the downloaded course to the data/courses directory
            self._move_downloaded_course(course_folder)

            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Error running PHP downloader: {e}")
            return False
        finally:
            # Change back to the base directory
            os.chdir(self.base_dir)

    def download_selective(
        self,
        json_file: Path,
        client_date: str = "",
        cookie_data: str = "",
        video_quality: str = "720p",
    ) -> bool:
        """
        Download selected content using the PHP downloader.

        Args:
            json_file: Path to a JSON file for selective downloading
            client_date: Client date for authentication
            cookie_data: Cookie data for authentication
            video_quality: Video quality to download

        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Downloading selective content from: {json_file}")

        # Check if PHP is installed
        try:
            subprocess.run(["php", "--version"], check=True, capture_output=True)
        except (subprocess.SubprocessError, FileNotFoundError):
            logger.error(
                "PHP is not installed or not in the PATH. Cannot download course."
            )
            return False

        # Check if the PHP script exists
        if not self.php_script.exists():
            logger.error(f"PHP script not found: {self.php_script}")
            return False

        # Check if the JSON file exists
        if not json_file.exists():
            logger.error(f"JSON file not found: {json_file}")
            return False

        # Extract course folder name from the JSON file
        course_folder = json_file.stem

        # Set up environment file
        env_file = self.base_dir / "config" / "php_downloader.env"
        php_env_file = self.php_script.parent / ".env"

        # Create a new environment file with the provided parameters
        try:
            env_content = f"""# For downloading all content, use the course link.
COURSE_LINK=""

# For selective content downloads, use the JSON file created from Thinki Parser.
# Copy the file to Thinki Downloader root folder (where thinkidownloader3.php is there).
# Specify the file name below. Ex. COURSE_DATA_FILE="modified-course.json"
COURSE_DATA_FILE="{json_file.name}"

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

        # Copy the JSON file to the PHP script directory
        try:
            shutil.copy2(json_file, self.php_script.parent / json_file.name)
        except Exception as e:
            logger.error(f"Error copying JSON file: {e}")
            return False

        # Change to the PHP script directory
        os.chdir(self.php_script.parent)

        # Run the PHP script
        try:
            subprocess.run(
                ["php", str(self.php_script), "--json", str(json_file.name)], check=True
            )
            logger.info("PHP downloader completed successfully")

            # Move the downloaded course to the data/courses directory
            self._move_downloaded_course(course_folder)

            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Error running PHP downloader: {e}")
            return False
        finally:
            # Change back to the base directory
            os.chdir(self.base_dir)

    def _move_downloaded_course(self, course_folder: str) -> None:
        """
        Move the downloaded course to the data/courses directory.

        Args:
            course_folder: Name of the course folder
        """
        # Set up paths
        php_dir = self.php_script.parent
        course_dir = self.base_dir / "data" / "courses" / course_folder
        downloads_dir = course_dir / "downloads"

        # Create the course directory if it doesn't exist
        os.makedirs(course_dir, exist_ok=True)
        os.makedirs(downloads_dir, exist_ok=True)

        # Check if the course was downloaded
        downloaded_dir = php_dir / course_folder
        if downloaded_dir.exists():
            logger.info(f"Moving downloaded course to: {downloads_dir}")

            # Copy the course files
            for item in downloaded_dir.iterdir():
                if item.is_dir():
                    # Copy directory
                    shutil.copytree(item, downloads_dir / item.name, dirs_exist_ok=True)
                else:
                    # Copy file
                    shutil.copy2(item, downloads_dir / item.name)

            # Copy the JSON file if it exists
            json_file = php_dir / f"{course_folder}.json"
            if json_file.exists():
                shutil.copy2(json_file, course_dir / json_file.name)
        else:
            logger.warning(f"Downloaded course directory not found: {downloaded_dir}")

    def get_course_data(self, course_folder: str) -> Dict[str, Any]:
        """
        Get the course data from the JSON file.

        Args:
            course_folder: Name of the course folder

        Returns:
            Course data as a dictionary
        """
        # First, look in the course_data directory (where Docker compose copies it)
        json_file = (
            self.base_dir
            / "data"
            / "courses"
            / course_folder
            / "course_data"
            / f"{course_folder}.json"
        )

        # If not found, try the old naming convention in course_data
        if not json_file.exists():
            old_name = course_folder.replace("-", "")
            json_file = (
                self.base_dir
                / "data"
                / "courses"
                / course_folder
                / "course_data"
                / f"{old_name}.json"
            )

        # If not found, look for any JSON file in the course_data directory
        if not json_file.exists():
            course_data_dir = (
                self.base_dir / "data" / "courses" / course_folder / "course_data"
            )
            if course_data_dir.exists():
                json_files = list(course_data_dir.glob("*.json"))
                if json_files:
                    json_file = json_files[0]

        # If not found, look in the course directory with the correct name
        if not json_file.exists():
            json_file = (
                self.base_dir
                / "data"
                / "courses"
                / course_folder
                / f"{course_folder}.json"
            )

        # If not found, try the old naming convention (without hyphens)
        if not json_file.exists():
            old_name = course_folder.replace("-", "")
            json_file = (
                self.base_dir / "data" / "courses" / course_folder / f"{old_name}.json"
            )

        # If not found, look in the PHP directory
        if not json_file.exists():
            json_file = self.php_script.parent / f"{course_folder}.json"

        # If still not found, try the old naming convention in the PHP directory
        if not json_file.exists():
            old_name = course_folder.replace("-", "")
            json_file = self.php_script.parent / f"{old_name}.json"

        # If still not found, return empty dictionary
        if not json_file.exists():
            logger.warning(f"Course data file not found: {json_file}")
            return {}

        # Load the JSON file
        try:
            with open(json_file, "r") as f:
                data = json.load(f)

                # Process the data to make it more usable for the organizer
                if (
                    data
                    and isinstance(data, dict)
                    and "contents" in data
                    and "chapters" in data
                ):
                    # Create a mapping of chapter IDs to chapter objects
                    chapter_map = {
                        chapter["id"]: chapter for chapter in data["chapters"]
                    }

                    # Create a mapping of content IDs to content objects
                    content_map = {
                        content["id"]: content for content in data["contents"]
                    }

                    # Create a more structured representation of the course
                    structured_data = {"course": data.get("course", {}), "chapters": []}

                    # Process each chapter
                    for chapter in data["chapters"]:
                        chapter_id = chapter["id"]
                        chapter_name = chapter["name"]

                        # Find all contents for this chapter
                        chapter_contents = [
                            content
                            for content in data["contents"]
                            if content.get("chapter_id") == chapter_id
                        ]

                        # Sort contents by position
                        chapter_contents.sort(key=lambda x: x.get("position", 0))

                        # Create lessons from contents
                        lessons = []
                        for content in chapter_contents:
                            content_type = content.get("contentable_type", "").lower()
                            lesson_type = "unknown"

                            if "lesson" in content_type:
                                lesson_type = "video"
                            elif "pdf" in content_type:
                                lesson_type = "pdf"
                            elif "html" in content_type:
                                lesson_type = "html"

                            lesson = {
                                "id": str(content.get("id", "")),
                                "title": content.get("name", ""),
                                "type": lesson_type,
                                "position": content.get("position", 0),
                                "description": content.get("meta_data", {})
                                if content.get("meta_data")
                                else {},
                                "duration": content.get("meta_data", {}).get(
                                    "duration_in_seconds", 0
                                )
                                if content.get("meta_data")
                                else 0,
                            }

                            lessons.append(lesson)

                        # Add chapter with lessons to structured data
                        structured_chapter = {
                            "id": str(chapter_id),
                            "title": chapter_name,
                            "position": chapter.get("position", 0),
                            "lessons": lessons,
                        }

                        structured_data["chapters"].append(structured_chapter)

                    return structured_data

                return data
        except Exception as e:
            logger.error(f"Error loading course data: {e}")
            return {}

    def check_for_updates(
        self,
        course_folder: str,
        course_link: str,
        client_date: str = "",
        cookie_data: str = "",
        video_quality: str = "720p",
    ) -> bool:
        """
        Check for updates to a course and update the course JSON file.

        This function:
        1. Gets the current course data from the JSON file
        2. Runs the PHP downloader to check for new content
        3. Updates the course JSON file with any new content
        4. Downloads any new content

        Args:
            course_folder: Name of the course folder
            course_link: URL of the course to check
            client_date: Client date for authentication
            cookie_data: Cookie data for authentication
            video_quality: Video quality to download

        Returns:
            True if updates were found and downloaded, False otherwise
        """
        logger.info(f"Checking for updates to course: {course_folder}")

        # Get the current course data
        current_data = self.get_course_data(course_folder)
        if not current_data:
            logger.warning(
                f"No existing course data found for {course_folder}. Will download the full course."
            )

            # Try to use PHP first, fall back to Docker if PHP is not installed
            try:
                subprocess.run(["php", "--version"], check=True, capture_output=True)
                # PHP is installed, use it
                return self.download_course(
                    course_link, client_date, cookie_data, video_quality
                )
            except (subprocess.SubprocessError, FileNotFoundError):
                # PHP is not installed, use Docker
                logger.info("PHP is not installed. Using Docker for download.")

                # Import the Docker function
                try:
                    from thinkiplex.cli.scripts import run_php_downloader_docker

                    # Run the Docker downloader
                    return run_php_downloader_docker(
                        client_date=client_date,
                        cookie_data=cookie_data,
                        video_quality=video_quality,
                        course_link=course_link,
                        course_name=course_link.split("/")[-1] if course_link else "",
                    )
                except ImportError:
                    logger.error(
                        "Could not import Docker functions. Make sure the CLI module is installed."
                    )
                    return False

        # Check if PHP is installed
        try:
            subprocess.run(["php", "--version"], check=True, capture_output=True)
        except (subprocess.SubprocessError, FileNotFoundError):
            logger.error(
                "PHP is not installed or not in the PATH. Cannot check for updates."
            )
            logger.info("Using Docker instead for update check.")

            # Import the Docker function
            try:
                from thinkiplex.cli.scripts import run_php_downloader_docker

                # Run the Docker downloader with check-updates flag
                # Note: This assumes the Docker setup supports the check-updates flag
                # We'll need to modify the Docker setup to support this
                logger.warning(
                    "Docker-based update checking is not fully implemented yet."
                )
                logger.warning("Will attempt to download the full course instead.")

                return run_php_downloader_docker(
                    client_date=client_date,
                    cookie_data=cookie_data,
                    video_quality=video_quality,
                    course_link=course_link,
                    course_name=course_link.split("/")[-1] if course_link else "",
                    check_updates_only=True,
                )
            except ImportError:
                logger.error(
                    "Could not import Docker functions. Make sure the CLI module is installed."
                )
                return False

        # Create a temporary directory for the update check
        temp_dir = self.base_dir / "temp" / course_folder
        os.makedirs(temp_dir, exist_ok=True)

        # Set up environment file for update check
        php_env_file = self.php_script.parent / ".env"

        # Create a new environment file with the provided parameters
        try:
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

# Set to true to only check for updates without downloading
CHECK_UPDATES_ONLY="true"
"""
            with open(php_env_file, "w") as dest:
                dest.write(env_content)
        except Exception as e:
            logger.error(f"Error creating environment file: {e}")
            return False

        # Change to the PHP script directory
        os.chdir(self.php_script.parent)

        # Run the PHP script to check for updates
        try:
            subprocess.run(
                ["php", str(self.php_script), course_link, "--check-updates"],
                check=True,
            )
            logger.info("Update check completed successfully")

            # Check if a new JSON file was created
            new_json_file = self.php_script.parent / f"{course_folder}.json"
            if not new_json_file.exists():
                old_name = course_folder.replace("-", "")
                new_json_file = self.php_script.parent / f"{old_name}.json"

            if not new_json_file.exists():
                logger.warning(
                    "No new course data found. The course may be up to date."
                )
                return False

            # Load the new course data
            try:
                with open(new_json_file, "r") as f:
                    new_data = json.load(f)
            except Exception as e:
                logger.error(f"Error loading new course data: {e}")
                return False

            # Compare the current and new data to check for updates
            has_updates = self._compare_course_data(current_data, new_data)

            if not has_updates:
                logger.info("No updates found for the course.")
                return False

            # Updates found, download the new content
            logger.info("Updates found for the course. Downloading new content...")

            # Reset the environment file to download the updates
            env_content = env_content.replace(
                'CHECK_UPDATES_ONLY="true"', 'CHECK_UPDATES_ONLY="false"'
            )
            with open(php_env_file, "w") as dest:
                dest.write(env_content)

            # Run the PHP script to download the updates
            subprocess.run(["php", str(self.php_script), course_link], check=True)
            logger.info("Update download completed successfully")

            # Move the downloaded course to the data/courses directory
            self._move_downloaded_course(course_folder)

            return True
        except subprocess.SubprocessError as e:
            logger.error(f"Error checking for updates: {e}")
            return False
        finally:
            # Change back to the base directory
            os.chdir(self.base_dir)

    def _compare_course_data(
        self, current_data: Dict[str, Any], new_data: Dict[str, Any]
    ) -> bool:
        """
        Compare current and new course data to check for updates.

        Args:
            current_data: Current course data
            new_data: New course data

        Returns:
            True if updates were found, False otherwise
        """
        # Check if the course has new chapters
        current_chapters = set(
            chapter["id"] for chapter in current_data.get("chapters", [])
        )
        new_chapters = set(chapter["id"] for chapter in new_data.get("chapters", []))

        if new_chapters - current_chapters:
            logger.info(f"Found {len(new_chapters - current_chapters)} new chapters")
            return True

        # Check if existing chapters have new lessons
        for new_chapter in new_data.get("chapters", []):
            # Skip if this is a new chapter (already handled above)
            if new_chapter["id"] not in current_chapters:
                continue

            # Find the corresponding current chapter
            current_chapter = next(
                (
                    c
                    for c in current_data.get("chapters", [])
                    if c["id"] == new_chapter["id"]
                ),
                None,
            )
            if not current_chapter:
                continue

            # Compare lessons
            current_lessons = set(
                lesson["id"] for lesson in current_chapter.get("lessons", [])
            )
            new_lessons = set(lesson["id"] for lesson in new_chapter.get("lessons", []))

            if new_lessons - current_lessons:
                logger.info(
                    f"Found {len(new_lessons - current_lessons)} new lessons in chapter {new_chapter['title']}"
                )
                return True

        # Check if any lesson content has been updated
        for new_chapter in new_data.get("chapters", []):
            current_chapter = next(
                (
                    c
                    for c in current_data.get("chapters", [])
                    if c["id"] == new_chapter["id"]
                ),
                None,
            )
            if not current_chapter:
                continue

            for new_lesson in new_chapter.get("lessons", []):
                current_lesson = next(
                    (
                        l
                        for l in current_chapter.get("lessons", [])
                        if l["id"] == new_lesson["id"]
                    ),
                    None,
                )
                if not current_lesson:
                    continue

                # Compare lesson content (e.g., updated video)
                if new_lesson.get("updated_at") != current_lesson.get("updated_at"):
                    logger.info(f"Lesson '{new_lesson['title']}' has been updated")
                    return True

        return False

    def run_php_script(
        self,
        course_url: str,
        cookie_data: str,
        video_quality: str = "720",
        check_updates_only: bool = False,
    ) -> Tuple[int, str]:
        """
        Run the PHP script with the given parameters.

        Args:
            course_url: The URL of the course to download
            cookie_data: The cookie data for authentication
            video_quality: The quality of the video to download (default: 720)
            check_updates_only: Whether to only check for updates without downloading

        Returns:
            Tuple of (exit_code, output)
        """
        # Check if PHP is installed
        try:
            subprocess.run(["php", "--version"], check=True, capture_output=True)
        except (subprocess.SubprocessError, FileNotFoundError):
            error_msg = (
                "PHP is not installed or not in the PATH. Cannot run PHP script."
            )
            logger.error(error_msg)
            return 1, error_msg

        # Create a temporary cookie file
        cookie_file = os.path.join(self.base_dir, "cookies.txt")
        with open(cookie_file, "w") as f:
            f.write(cookie_data)

        # Prepare the command
        cmd = [
            "php",
            str(self.php_script),
            course_url,
            "--cookie",
            cookie_file,
            "--quality",
            video_quality,
        ]

        # Add check-updates flag if needed
        if check_updates_only:
            cmd.append("--check-updates")

        # Set the working directory to the base directory
        cwd = os.getcwd()
        os.chdir(self.base_dir)

        try:
            # Run the PHP script
            logger.info(f"Running PHP script: {' '.join(cmd)}")
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
            )

            output = ""
            # Stream the output
            if process.stdout is not None:
                for line in process.stdout:
                    print(line, end="")  # Print to console in real-time
                    output += line
            else:
                logger.warning("No stdout available from subprocess")

            # Wait for the process to complete
            exit_code = process.wait()
            logger.info(f"PHP script exited with code {exit_code}")

            return exit_code, output

        finally:
            # Clean up
            if os.path.exists(cookie_file):
                os.remove(cookie_file)
            os.chdir(cwd)
