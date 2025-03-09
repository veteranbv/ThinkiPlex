"""
Course Selector Module
---------------------
This module provides functionality to interactively select a course to process.
"""

import logging
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)


def get_available_courses(config_path=None):
    """
    Get a list of available courses from the configuration file.

    Args:
        config_path: Path to the configuration file. If None, uses the default.

    Returns:
        A list of course names.
    """
    if config_path is None:
        config_path = Path("config/thinkiplex.yaml")

    if not config_path.exists():
        logger.warning(f"Configuration file not found: {config_path}")
        return []

    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        if not config or "courses" not in config:
            logger.warning("No courses found in configuration file")
            return []

        return list(config["courses"].keys())
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        return []


def select_course_interactive(config_path=None):
    """
    Interactively select a course to process.

    Args:
        config_path: Path to the configuration file. If None, uses the default.

    Returns:
        The selected course name or None if no selection was made.
    """
    courses = get_available_courses(config_path)

    if not courses:
        print("No courses found. Please run the setup wizard first.")
        return None

    # Try to use inquirer for a nice UI if available
    try:
        import inquirer

        questions = [
            inquirer.List(
                "course", message="Select a course to process:", choices=courses
            ),
        ]
        answers = inquirer.prompt(questions)
        return answers["course"]
    except ImportError:
        # Fall back to simple console input if inquirer is not available
        print("Available courses:")
        for i, course in enumerate(courses, 1):
            print(f"{i}. {course}")

        while True:
            try:
                choice = input(
                    "Enter the number of the course to process (or 'q' to quit): "
                )
                if choice.lower() == "q":
                    return None

                choice = int(choice)
                if 1 <= choice <= len(courses):
                    return courses[choice - 1]
                else:
                    print(f"Please enter a number between 1 and {len(courses)}")
            except ValueError:
                print("Please enter a valid number")


def get_course_config(course_name, config_path=None):
    """
    Get the configuration for a specific course.

    Args:
        course_name: Name of the course.
        config_path: Path to the configuration file. If None, uses the default.

    Returns:
        A dictionary with the course configuration or None if not found.
    """
    if config_path is None:
        config_path = Path("config/thinkiplex.yaml")

    if not config_path.exists():
        logger.warning(f"Configuration file not found: {config_path}")
        return None

    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        if (
            not config
            or "courses" not in config
            or course_name not in config["courses"]
        ):
            logger.warning(f"Course not found in configuration: {course_name}")
            return None

        # Merge global defaults with course-specific settings
        course_config = config["courses"][course_name].copy()

        # Add global settings as defaults if not specified in course
        for key, value in config["global"].items():
            if key not in course_config:
                course_config[key] = value

        return course_config
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        return None


def load_config(course_name=None, config_path=None):
    """
    Load the configuration for a course or prompt the user to select one.

    Args:
        course_name: Name of the course. If None, prompts the user to select one.
        config_path: Path to the configuration file. If None, uses the default.

    Returns:
        A tuple of (course_name, course_config) or (None, None) if no selection was made.
    """
    if config_path is None:
        config_path = Path("config/thinkiplex.yaml")

    if not config_path.exists():
        logger.warning(f"Configuration file not found: {config_path}")
        print(f"Configuration file not found: {config_path}")
        print("Please run the setup wizard first.")
        return None, None

    # If no course name provided, prompt the user to select one
    if course_name is None:
        course_name = select_course_interactive(config_path)
        if course_name is None:
            return None, None

    course_config = get_course_config(course_name, config_path)
    if course_config is None:
        logger.warning(f"Course not found in configuration: {course_name}")
        print(f"Course not found in configuration: {course_name}")
        return None, None

    return course_name, course_config
