"""
PDF Generator for ThinkiPlex.

This module provides the main functionality for generating a single PDF from course resources.
"""

import re
import shutil
import tempfile
from pathlib import Path
from typing import List, Optional, Union

from ..utils.config import Config
from ..utils.logging import get_logger
from .converters import (
    convert_html_to_pdf,
    convert_markdown_to_pdf,
    convert_text_to_pdf,
    merge_pdfs,
)

logger = get_logger()


class PDFGenerator:
    """Generator for course PDF resources."""

    def __init__(self, config_file: Optional[str] = None):
        """Initialize the PDF generator.

        Args:
            config_file: Path to the configuration file
        """
        self.config = Config(config_file or "config/thinkiplex.yaml")
        self.temp_dir = Path(tempfile.mkdtemp())
        logger.info(f"Created temporary directory: {self.temp_dir}")

    def __del__(self) -> None:
        """Clean up temporary files."""
        try:
            shutil.rmtree(self.temp_dir)
            logger.info(f"Removed temporary directory: {self.temp_dir}")
        except Exception as e:
            logger.warning(f"Error removing temporary directory: {e}")

    def generate_course_pdf(
        self, course_id: str, output_file: Optional[Union[str, Path]] = None
    ) -> Path:
        """
        Generate a PDF for a course.

        Args:
            course_id: ID of the course
            output_file: Optional output file path

        Returns:
            Path to the generated PDF file
        """
        # Get course info
        course_config = self.config.get_course_config(course_id)
        course_name = course_config.get("show_name", course_id)
        logger.info(f"Generating PDF for course: {course_name}")

        # Set output file path if not provided
        if output_file is None:
            # Try to use the current working directory first
            base_dir = Path.cwd()
            downloads_dir = base_dir / "data" / "courses" / course_id

            # Create the directory if it doesn't exist
            downloads_dir.mkdir(parents=True, exist_ok=True)

            # Set the output file path
            output_file = downloads_dir / f"{course_id}_resources.pdf"

        # Create a temporary directory for processing
        with tempfile.TemporaryDirectory(prefix="thinkiplex_pdf_") as temp_dir:
            self.temp_dir = Path(temp_dir)
            logger.info(f"Created temporary directory: {self.temp_dir}")

            # Process course files
            pdf_files = self._process_course_files(course_id)

            if not pdf_files:
                logger.error("No PDF files generated")
                raise ValueError("No PDF files generated")

            # Merge PDF files
            output_path = self._merge_pdf_files(pdf_files, output_file)
            logger.info(f"Generated PDF: {output_path}")

            return output_path

    def _process_course_files(self, course_id: str) -> List[Union[str, Path]]:
        """
        Process course files in numerical module order.
        
        Args:
            course_id: ID of the course

        Returns:
            List of PDF file paths in numerical order
        """
        pdf_files = []

        # Find the downloads directory
        base_dir = Path(self.config.config["global"]["base_dir"])
        downloads_dir = base_dir / "data" / "courses" / course_id / "downloads"

        # Check if the downloads directory exists at the specified path
        if not downloads_dir.exists():
            # Try to find the downloads directory in the current working directory
            alt_downloads_dir = Path.cwd() / "data" / "courses" / course_id / "downloads"
            if alt_downloads_dir.exists():
                downloads_dir = alt_downloads_dir
                logger.info(f"Using alternative downloads directory: {downloads_dir}")
            else:
                logger.warning(f"Downloads directory not found: {downloads_dir}")
                return pdf_files

        # Skip these directory types
        excluded_dirs = {"audio", "transcripts", "video"}
        logger.info(f"Excluding directory types: {excluded_dirs}")
        
        # Get all top-level module directories and extract their numbers
        modules = []
        for path in downloads_dir.iterdir():
            if path.is_dir():
                match = re.match(r"^(\d+)\.", path.name)
                if match:
                    module_num = int(match.group(1))
                    modules.append((module_num, path))
        
        # Sort modules by their number
        modules.sort()  # This sorts by the first element (module_num)
        
        module_count = len(modules)
        logger.info(f"Found {module_count} modules to process")
        for module_num, module_path in modules:
            logger.info(f"Processing module {module_num}: {module_path.name}")
            
            # For indexing the PDF filenames 
            module_idx = f"{module_num:04d}"
            
            # Find all subdirectories in this module that aren't excluded
            subdirs = []
            for subdir in module_path.iterdir():
                if subdir.is_dir() and subdir.name.lower() not in excluded_dirs:
                    # Extract numeric prefix if available
                    subdir_num = 999  # Default high number for directories without numeric prefix
                    match = re.match(r"^(\d+)\.", subdir.name)
                    if match:
                        subdir_num = int(match.group(1))
                    # Special case: put summaries at the end of each module
                    if subdir.name.lower() == "summaries":
                        subdir_num = 999
                    subdirs.append((subdir_num, subdir))
            
            # Sort subdirectories by their numeric prefix
            subdirs.sort()
            
            # Process each subdirectory
            for subdir_idx, (_, subdir) in enumerate(subdirs):
                subdir_name = subdir.name
                logger.info(f"  Processing subdirectory: {subdir_name}")
                
                # For naming PDFs
                subdir_idx_str = f"{subdir_idx:04d}"
                
                # Process based on directory type
                if subdir_name.lower() == "summaries":
                    # Handle summary files
                    summary_files = list(subdir.glob("*_summary.md"))
                    if not summary_files:
                        continue
                        
                    logger.info(f"    Found {len(summary_files)} summary files")
                    for summary_idx, summary_path in enumerate(sorted(summary_files)):
                        summary_idx_str = f"{summary_idx:04d}"
                        new_filename = f"{module_idx}_{subdir_idx_str}_{summary_idx_str}_{summary_path.name}"
                        
                        pdf_path = self._convert_file_to_pdf(summary_path, new_filename)
                        if pdf_path:
                            pdf_files.append(pdf_path)
                            logger.info(f"    Added summary: {pdf_path.name}")
                else:
                    # Handle regular content files
                    content_files = []
                    for file_path in subdir.glob("**/*"):
                        if file_path.is_file() and not self._should_exclude_file(file_path):
                            content_files.append(file_path)
                    
                    if not content_files:
                        continue
                        
                    logger.info(f"    Found {len(content_files)} content files")
                    # Sort content files alphabetically
                    for file_idx, file_path in enumerate(sorted(content_files)):
                        file_idx_str = f"{file_idx:04d}"
                        new_filename = f"{module_idx}_{subdir_idx_str}_{file_idx_str}_{file_path.name}"
                        
                        pdf_path = self._convert_file_to_pdf(file_path, new_filename)
                        if pdf_path:
                            pdf_files.append(pdf_path)
                            logger.info(f"    Added file: {pdf_path.name}")
        
        # Final sort to ensure correct order
        pdf_files.sort()
        
        # Log the files we'll include in the PDF
        logger.info(f"Final PDF will include {len(pdf_files)} files")
        for i, pdf_file in enumerate(pdf_files[:10]):  # Show first 10
            logger.info(f"  {i+1}. {pdf_file.name}")
        if len(pdf_files) > 10:
            logger.info(f"  ... and {len(pdf_files) - 10} more files")
            
        return pdf_files

    def _convert_file_to_pdf(self, file_path: Path, new_filename: str) -> Optional[Path]:
        """
        Convert a file to PDF.

        Args:
            file_path: Path to the file
            new_filename: New filename for the output PDF

        Returns:
            Path to the converted PDF file, or None if conversion failed
        """
        output_file = self.temp_dir / new_filename.replace(".md", ".pdf").replace(
            ".html", ".pdf"
        ).replace(".txt", ".pdf")

        try:
            # If it's already a PDF, just copy it
            if file_path.suffix.lower() == ".pdf":
                shutil.copy(file_path, output_file)
                return output_file

            # Convert based on file type
            if file_path.suffix.lower() == ".md":
                convert_markdown_to_pdf(file_path, output_file)
                return output_file

            if file_path.suffix.lower() == ".html":
                convert_html_to_pdf(file_path, output_file)
                return output_file

            if file_path.suffix.lower() == ".txt":
                convert_text_to_pdf(file_path, output_file)
                return output_file

            logger.warning(f"Unsupported file type: {file_path.suffix} for {file_path}")
            return None

        except Exception as e:
            logger.error(f"Error converting file to PDF: {e}")
            return None

    def _merge_pdf_files(
        self, pdf_files: List[Union[str, Path]], output_file: Union[str, Path]
    ) -> Path:
        """
        Merge PDF files into a single PDF.

        Args:
            pdf_files: List of PDF file paths
            output_file: Output file path

        Returns:
            Path to the merged PDF file
        """
        output_file = Path(str(output_file))

        # Create the output directory if it doesn't exist
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Debug: Print the files we're about to merge
        print(f"Merging {len(pdf_files)} PDF files into {output_file}")
        for i, pdf_file in enumerate(pdf_files):
            if i < 10 or i >= len(pdf_files) - 5:  # Print first 10 and last 5 files
                print(f"  {i + 1}. {pdf_file}")

        if len(pdf_files) > 15:
            print(f"  ... and {len(pdf_files) - 15} more files ...")

        # Merge the PDFs in batches to avoid memory issues
        try:
            # Create a temporary directory for batch processing
            with tempfile.TemporaryDirectory(prefix="thinkiplex_pdf_merge_") as temp_dir:
                temp_dir_path = Path(temp_dir)
                logger.info(f"Created temporary directory for batch merging: {temp_dir_path}")

                # Process in batches of 10 files
                batch_size = 10
                batch_files = []

                for i in range(0, len(pdf_files), batch_size):
                    batch = pdf_files[i : i + batch_size]
                    batch_output = temp_dir_path / f"batch_{i // batch_size}.pdf"

                    logger.info(f"Merging batch {i // batch_size + 1} with {len(batch)} files")
                    try:
                        # Merge this batch
                        merge_pdfs(batch, batch_output)
                        batch_files.append(batch_output)
                        logger.info(
                            f"Successfully merged batch {i // batch_size + 1} to {batch_output}"
                        )
                    except Exception as e:
                        logger.error(f"Error merging batch {i // batch_size + 1}: {e}")
                        # Continue with the next batch

                # Now merge all the batch files
                if batch_files:
                    logger.info(f"Merging {len(batch_files)} batch files into final PDF")
                    merge_pdfs(batch_files, output_file)
                    logger.info(f"Successfully merged all batches into {output_file}")
                else:
                    logger.error("No batch files were created, cannot create final PDF")
                    raise ValueError("No batch files were created")

            print(f"Successfully merged PDFs into {output_file}")
            return output_file
        except Exception as e:
            print(f"Error merging PDFs: {e}")
            logger.error(f"Error merging PDFs: {e}")

            # Fallback: try direct merge if batch processing failed
            try:
                logger.info("Attempting direct merge as fallback")
                merge_pdfs(pdf_files, output_file)
                print(f"Successfully merged PDFs using fallback method into {output_file}")
                return output_file
            except Exception as fallback_error:
                logger.error(f"Fallback merge also failed: {fallback_error}")
                raise

    def _should_exclude_file(self, file_path: Path) -> bool:
        """
        Check if a file should be excluded from the PDF.

        Args:
            file_path: Path to the file

        Returns:
            True if the file should be excluded, False otherwise
        """
        # Exclude video and audio files
        video_extensions = {".mp4", ".avi", ".mov", ".wmv", ".flv", ".mkv"}
        audio_extensions = {".mp3", ".wav", ".aac", ".ogg", ".flac", ".m4a"}
        excluded_extensions = video_extensions.union(audio_extensions)
        
        # Check if file is in or under a transcripts directory
        if "transcripts" in file_path.parts:
            return True
            
        # Check file extension
        if file_path.suffix.lower() in excluded_extensions:
            return True
            
        return False