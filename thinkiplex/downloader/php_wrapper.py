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
from typing import Any, Dict, Optional, Tuple

from thinkiplex.utils import Config

logger = logging.getLogger(__name__)


class PHPDownloader:
    """Python wrapper for the PHP downloader."""

    def __init__(self, base_dir: Path, config: Optional[Config] = None):
        """
        Initialize the PHP downloader wrapper.

        Args:
            base_dir: Base directory of the project
            config: Configuration object (optional)
        """
        self.base_dir = base_dir
        self.config = config
        self.php_script = (
            self.base_dir / "thinkiplex" / "downloader" / "php" / "thinkidownloader3.php"
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
            logger.error("PHP is not installed or not in the PATH. Cannot download course.")
            return False

        # Check if the PHP script exists
        if not self.php_script.exists():
            logger.error(f"PHP script not found: {self.php_script}")
            return False

        # Extract course folder name from the URL
        course_folder = course_link.split("/")[-1]

        # Check if we have an existing tracking file in the downloads directory
        # and copy it to the PHP directory if it exists
        downloads_dir = Path(self.base_dir) / "data" / "courses" / course_folder / "downloads"
        if self.config and "global" in self.config.config:
            base_dir_template = self.config.config["global"].get("base_dir")
            if base_dir_template:
                downloads_dir = Path(self.base_dir) / base_dir_template.format(
                    course_name=course_folder
                )

        existing_tracking_file = downloads_dir / ".download_tracking"
        php_tracking_file = self.php_script.parent / course_folder / ".download_tracking"

        # Create PHP course directory if it doesn't exist yet
        php_course_dir = self.php_script.parent / course_folder
        if not php_course_dir.exists():
            os.makedirs(php_course_dir, exist_ok=True)

        # Copy tracking file if it exists
        if existing_tracking_file.exists() and existing_tracking_file.is_file():
            logger.info(
                "Found existing tracking file. Copying to PHP directory to resume download."
            )
            try:
                # Make sure the directory exists
                os.makedirs(php_course_dir, exist_ok=True)
                shutil.copy2(existing_tracking_file, php_tracking_file)
            except Exception as e:
                logger.warning(f"Failed to copy existing tracking file: {e}")

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

            # Remove the old tracking file from the PHP directory if it exists
            old_tracking_file = self.php_script.parent / ".download_tracking"
            if old_tracking_file.exists():
                try:
                    os.remove(old_tracking_file)
                    logger.info("Removed old tracking file from PHP directory")
                except Exception as e:
                    logger.warning(f"Failed to remove old tracking file: {e}")

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
        Download selective content from a course using the PHP downloader.

        Args:
            json_file: Path to the JSON file with course data
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
            logger.error("PHP is not installed or not in the PATH. Cannot download course.")
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
        try:
            with open(json_file, "r") as f:
                course_data = json.load(f)
                course_folder = course_data["course"]["slug"]
                course_name = course_data["course"]["name"]
        except Exception as e:
            logger.error(f"Error reading JSON file: {e}")
            return False

        # Determine the target directory for the course
        target_dir = Path(self.base_dir) / "data" / "courses" / course_folder / "downloads"

        # If we have a config object, use its base_dir setting
        if self.config and "global" in self.config.config:
            base_dir_template = self.config.config["global"].get("base_dir")
            if base_dir_template:
                target_dir = Path(self.base_dir) / base_dir_template.format(
                    course_name=course_folder
                )

        # Create the target directory if it doesn't exist
        os.makedirs(target_dir, exist_ok=True)

        # Check if we have an existing tracking file in the downloads directory
        existing_tracking_file = target_dir / ".download_tracking"

        # Set up environment variables
        env = os.environ.copy()
        env["COURSE_LINK"] = ""  # Not used for selective download
        env["CLIENT_DATE"] = client_date
        env["COOKIE_DATA"] = cookie_data
        env["VIDEO_DOWNLOAD_QUALITY"] = video_quality
        env["CHECK_UPDATES_ONLY"] = "false"
        env["COURSE_NAME"] = course_folder
        env["TARGET_DIR"] = str(target_dir)
        env["JSON_FILE"] = str(json_file.absolute())

        # Change to the PHP script directory
        prev_dir = os.getcwd()
        os.chdir(self.php_script.parent)

        try:
            # Run docker compose for selective download
            cmd = ["docker", "compose", "-f", "compose.selective.yaml", "up"]
            result = subprocess.run(cmd, capture_output=True, text=True, env=env)

            if result.returncode != 0:
                logger.error(f"Error running Docker Compose: {result.stderr}")
                return False

            logger.info("PHP downloader completed successfully")
            return True
        except Exception as e:
            logger.error(f"Error running PHP downloader: {e}")
            return False
        finally:
            # Change back to the previous directory
            os.chdir(prev_dir)

    def _move_downloaded_course(self, course_folder: str) -> None:
        """
        Move the downloaded course to the data/courses directory.

        Args:
            course_folder: Name of the course folder
        """
        # Set up paths
        php_dir = self.php_script.parent
        downloads_dir = Path(self.base_dir) / "data" / "courses" / course_folder / "downloads"

        # If we have a config object, use its base_dir setting
        if self.config and "global" in self.config.config:
            base_dir_template = self.config.config["global"].get("base_dir")
            if base_dir_template:
                downloads_dir = Path(self.base_dir) / base_dir_template.format(
                    course_name=course_folder
                )

        # Create the downloads directory if it doesn't exist
        os.makedirs(downloads_dir, exist_ok=True)

        # Check if the course was downloaded to the PHP directory
        downloaded_dir = php_dir / course_folder
        if downloaded_dir.exists():
            logger.info(f"Moving downloaded course from PHP directory to: {downloads_dir}")

            # Copy the course files
            for item in downloaded_dir.iterdir():
                if item.is_dir():
                    # Copy directory
                    shutil.copytree(item, downloads_dir / item.name, dirs_exist_ok=True)
                elif item.name == ".download_tracking":
                    # Special handling for tracking file - merge with existing if available
                    dest_tracking_file = downloads_dir / item.name
                    if dest_tracking_file.exists():
                        try:
                            # Load existing tracking data
                            with open(dest_tracking_file, "r") as f:
                                existing_tracking = json.load(f)

                            # Load new tracking data
                            with open(item, "r") as f:
                                new_tracking = json.load(f)

                            # Merge tracking data (new data overwrites existing)
                            existing_tracking.update(new_tracking)

                            # Write back merged tracking data
                            with open(dest_tracking_file, "w") as f:
                                json.dump(existing_tracking, f, indent=4)

                            logger.info("Updated tracking file with new download information")
                        except Exception as e:
                            logger.warning(f"Failed to merge tracking files: {e}")
                            # If merge fails, just copy the new file
                            shutil.copy2(item, dest_tracking_file)
                    else:
                        # No existing tracking file, just copy it
                        shutil.copy2(item, dest_tracking_file)
                else:
                    # Copy file
                    shutil.copy2(item, downloads_dir / item.name)

            # Clean up the downloaded directory after copying
            try:
                shutil.rmtree(downloaded_dir)
                logger.info(f"Removed temporary course directory: {downloaded_dir}")
            except Exception as e:
                logger.warning(f"Failed to remove temporary course directory: {e}")
        else:
            # Check if the course was downloaded directly to the target directory
            if any(downloads_dir.iterdir()):
                logger.info(
                    f"Course was downloaded directly to the target directory: {downloads_dir}"
                )
            else:
                logger.warning("No course files found in either PHP directory or target directory")

    def get_course_data(self, course_folder: str) -> Dict[str, Any]:
        """
        Get the course data from the JSON file.

        Args:
            course_folder: Name of the course folder

        Returns:
            Course data as a dictionary
        """
        logger.info(f"Getting course data for: {course_folder}")

        # Look for the JSON file in the course directory
        course_dir = self.base_dir / "data" / "courses" / course_folder
        json_file = course_dir / f"{course_folder}.json"

        if json_file.exists():
            try:
                with open(json_file, "r") as f:
                    data = json.load(f)
                    logger.info(f"Loaded course data from: {json_file}")
                    return data if isinstance(data, dict) else {}
            except Exception as e:
                logger.error(f"Error loading course data from {json_file}: {e}")

        # If not found, look for any JSON file in the course directory
        if course_dir.exists():
            json_files = list(course_dir.glob("*.json"))
            if json_files:
                try:
                    with open(json_files[0], "r") as f:
                        data = json.load(f)
                        logger.info(f"Loaded course data from: {json_files[0]}")
                        return data if isinstance(data, dict) else {}
                except Exception as e:
                    logger.error(f"Error loading course data from {json_files[0]}: {e}")

        # If not found, look in the downloads directory
        downloads_dir = course_dir / "downloads"
        if downloads_dir.exists():
            json_files = list(downloads_dir.glob("*.json"))
            if json_files:
                try:
                    with open(json_files[0], "r") as f:
                        data = json.load(f)
                        logger.info(f"Loaded course data from: {json_files[0]}")
                        return data if isinstance(data, dict) else {}
                except Exception as e:
                    logger.error(f"Error loading course data from {json_files[0]}: {e}")

        logger.warning(f"No course data found for: {course_folder}")
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
        Check for updates to a course and download new content.

        Args:
            course_folder: Name of the course folder
            course_link: URL of the course to check
            client_date: Client date for authentication
            cookie_data: Cookie data for authentication
            video_quality: Video quality to download

        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Checking for updates to course: {course_folder}")

        # Check if PHP is installed
        try:
            subprocess.run(["php", "--version"], check=True, capture_output=True)
        except (subprocess.SubprocessError, FileNotFoundError):
            logger.error("PHP is not installed or not in the PATH. Cannot check for updates.")
            return False

        # Check if the PHP script exists
        if not self.php_script.exists():
            logger.error(f"PHP script not found: {self.php_script}")
            return False

        # Set up paths
        course_dir = self.base_dir / "data" / "courses" / course_folder
        downloads_dir = course_dir / "downloads"
        json_file = course_dir / f"{course_folder}.json"

        # If we have a config object, use its base_dir setting
        if self.config and "global" in self.config.config:
            base_dir_template = self.config.config["global"].get("base_dir")
            if base_dir_template:
                downloads_dir = Path(self.base_dir) / base_dir_template.format(
                    course_name=course_folder
                )

        # Check if the course directory exists
        if not course_dir.exists():
            logger.error(f"Course directory not found: {course_dir}")
            return False

        # Check if the JSON file exists
        if not json_file.exists():
            logger.error(f"Course JSON file not found: {json_file}")
            return False

        # Create the course directory in the PHP directory
        php_dir = self.php_script.parent
        php_course_dir = php_dir / course_folder
        os.makedirs(php_course_dir, exist_ok=True)

        # Check if we have an existing tracking file in the downloads directory
        # and copy it to the PHP directory if it exists
        existing_tracking_file = downloads_dir / ".download_tracking"
        php_tracking_file = php_course_dir / ".download_tracking"

        # Copy tracking file if it exists
        if existing_tracking_file.exists() and existing_tracking_file.is_file():
            logger.info(
                "Found existing tracking file. Copying to PHP directory to resume download."
            )
            try:
                shutil.copy2(existing_tracking_file, php_tracking_file)
            except Exception as e:
                logger.warning(f"Failed to copy existing tracking file: {e}")

        # Copy the JSON file to the course directory in the PHP directory
        php_json_file = php_course_dir / json_file.name
        shutil.copy2(json_file, php_json_file)

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

            # Remove the old tracking file from the PHP directory if it exists
            old_tracking_file = self.php_script.parent / ".download_tracking"
            if old_tracking_file.exists():
                try:
                    os.remove(old_tracking_file)
                    logger.info("Removed old tracking file from PHP directory")
                except Exception as e:
                    logger.warning(f"Failed to remove old tracking file: {e}")

            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Error running PHP downloader: {e}")
            return False
        finally:
            # Change back to the base directory
            os.chdir(self.base_dir)
            # Clean up the copied JSON file if it exists
            if php_json_file.exists() and php_json_file.is_file():
                try:
                    php_json_file.unlink()
                except Exception as e:
                    logger.warning(f"Failed to remove temporary JSON file: {e}")

    def _compare_course_data(self, current_data: Dict[str, Any], new_data: Dict[str, Any]) -> bool:
        """
        Compare current and new course data to check for updates.

        Args:
            current_data: Current course data
            new_data: New course data

        Returns:
            True if updates were found, False otherwise
        """
        # Check if the course has new chapters
        current_chapters = set(chapter["id"] for chapter in current_data.get("chapters", []))
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
                (c for c in current_data.get("chapters", []) if c["id"] == new_chapter["id"]),
                None,
            )
            if not current_chapter:
                continue

            # Compare lessons
            current_lessons = set(lesson["id"] for lesson in current_chapter.get("lessons", []))
            new_lessons = set(lesson["id"] for lesson in new_chapter.get("lessons", []))

            if new_lessons - current_lessons:
                logger.info(
                    f"Found {len(new_lessons - current_lessons)} new lessons in chapter {new_chapter['title']}"
                )
                return True

        # Check if any lesson content has been updated
        for new_chapter in new_data.get("chapters", []):
            current_chapter = next(
                (c for c in current_data.get("chapters", []) if c["id"] == new_chapter["id"]),
                None,
            )
            if not current_chapter:
                continue

            for new_lesson in new_chapter.get("lessons", []):
                current_lesson = next(
                    (l for l in current_chapter.get("lessons", []) if l["id"] == new_lesson["id"]),
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
        Run the PHP script using Docker.

        Args:
            course_url: URL of the course to download
            cookie_data: Cookie data for authentication
            video_quality: Video quality to download
            check_updates_only: Whether to only check for updates without downloading

        Returns:
            Tuple of (return code, output)
        """
        # Extract course folder name from the URL
        course_folder = course_url.split("/")[-1]

        # Determine the target directory for the course
        target_dir = Path(self.base_dir) / "data" / "courses" / course_folder / "downloads"

        # If we have a config object, use its base_dir setting
        if self.config and "global" in self.config.config:
            base_dir_template = self.config.config["global"].get("base_dir")
            if base_dir_template:
                target_dir = Path(self.base_dir) / base_dir_template.format(
                    course_name=course_folder
                )

        # Create the target directory if it doesn't exist
        os.makedirs(target_dir, exist_ok=True)

        # Set up environment variables
        env = os.environ.copy()
        env["COURSE_LINK"] = course_url
        env["CLIENT_DATE"] = ""
        env["COOKIE_DATA"] = cookie_data
        env["VIDEO_DOWNLOAD_QUALITY"] = video_quality
        env["CHECK_UPDATES_ONLY"] = str(check_updates_only).lower()
        env["COURSE_NAME"] = course_folder
        env["TARGET_DIR"] = str(target_dir)  # Pass the target directory to the PHP script

        # Change to the PHP script directory
        prev_dir = os.getcwd()
        os.chdir(self.php_script.parent)

        try:
            # Run docker compose
            cmd = ["docker", "compose", "-f", "compose.yaml", "up"]
            result = subprocess.run(cmd, capture_output=True, text=True, env=env)
            return result.returncode, result.stdout
        finally:
            # Change back to the previous directory
            os.chdir(prev_dir)
