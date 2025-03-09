"""
Cleanup Module
------------
This module provides functions to clean up and consolidate the data structure.
"""

import logging
import os
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)


def consolidate_data_structure() -> bool:
    """
    Consolidate the data structure by moving everything to data/courses.

    Returns:
        True if successful, False otherwise
    """
    logger.info("Consolidating data structure...")

    # Get the base directory
    base_dir = Path.cwd()

    # Set up paths
    courses_dir = base_dir / "data" / "courses"
    downloads_dir = base_dir / "data" / "downloads"
    plex_dir = base_dir / "data" / "plex"

    # Create the courses directory if it doesn't exist
    os.makedirs(courses_dir, exist_ok=True)

    # Process downloads directory
    if downloads_dir.exists():
        logger.info("Processing downloads directory...")
        for item in downloads_dir.iterdir():
            if item.is_dir():
                course_name = item.name
                course_dir = courses_dir / course_name
                course_downloads_dir = course_dir / "downloads"

                # Create the course directory if it doesn't exist
                os.makedirs(course_dir, exist_ok=True)
                os.makedirs(course_downloads_dir, exist_ok=True)

                logger.info(f"Moving {course_name} downloads to {course_downloads_dir}")

                # Copy the course files
                for subitem in item.iterdir():
                    if subitem.is_dir():
                        # Copy directory
                        shutil.copytree(
                            subitem,
                            course_downloads_dir / subitem.name,
                            dirs_exist_ok=True,
                        )
                    else:
                        # Copy file
                        shutil.copy2(subitem, course_downloads_dir / subitem.name)

    # Process plex directory
    if plex_dir.exists():
        logger.info("Processing plex directory...")
        for item in plex_dir.iterdir():
            if item.is_dir():
                course_name = item.name
                course_dir = courses_dir / course_name
                course_plex_dir = course_dir / "plex"

                # Create the course directory if it doesn't exist
                os.makedirs(course_dir, exist_ok=True)
                os.makedirs(course_plex_dir, exist_ok=True)

                logger.info(f"Moving {course_name} plex content to {course_plex_dir}")

                # Copy the course files
                for subitem in item.iterdir():
                    if subitem.is_dir():
                        # Copy directory
                        shutil.copytree(
                            subitem, course_plex_dir / subitem.name, dirs_exist_ok=True
                        )
                    else:
                        # Copy file
                        shutil.copy2(subitem, course_plex_dir / subitem.name)

    # Process JSON files in the courses directory
    for item in courses_dir.glob("*.json"):
        if item.is_file():
            course_name = item.stem
            course_dir = courses_dir / course_name

            # Create the course directory if it doesn't exist
            os.makedirs(course_dir, exist_ok=True)

            logger.info(f"Moving {item.name} to {course_dir}")

            # Copy the JSON file
            shutil.copy2(item, course_dir / item.name)

    # Ask if we should remove the old directories
    print("\nAll data has been consolidated into the data/courses directory.")
    print("Would you like to remove the old data/downloads and data/plex directories?")
    response = input("Enter 'y' to remove, any other key to keep them: ")

    if response.lower() == "y":
        logger.info("Removing old directories...")

        # Remove the downloads directory
        if downloads_dir.exists():
            shutil.rmtree(downloads_dir)
            logger.info(f"Removed {downloads_dir}")

        # Remove the plex directory
        if plex_dir.exists():
            shutil.rmtree(plex_dir)
            logger.info(f"Removed {plex_dir}")

        # Remove JSON files in the courses directory
        for item in courses_dir.glob("*.json"):
            if item.is_file():
                os.remove(item)
                logger.info(f"Removed {item}")

        print("Old directories and files removed.")
    else:
        print("Old directories and files kept.")

    print("\nData structure consolidation complete.")
    return True


def run_cleanup() -> bool:
    """
    Run the cleanup process.

    Returns:
        True if successful, False otherwise
    """
    print("ThinkiPlex Data Structure Cleanup")
    print("================================")
    print("This will consolidate all data into the data/courses directory.")
    print("Each course will have its own directory with downloads, plex, and metadata.")
    print()

    # Confirm with the user
    response = input("Are you sure you want to continue? (y/n): ")
    if response.lower() != "y":
        print("Cleanup cancelled.")
        return False

    # Run the consolidation
    return consolidate_data_structure()
