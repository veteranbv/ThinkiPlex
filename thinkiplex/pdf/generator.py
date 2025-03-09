"""
PDF Generator for ThinkiPlex.

This module provides the main functionality for generating a single PDF from course resources.
"""

import json
import re
import shutil
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Union

import PyPDF2

from ..utils.config import Config
from ..utils.logging import get_logger
from .converters import (
    convert_html_to_pdf,
    convert_markdown_to_pdf,
    convert_text_to_pdf,
    merge_pdfs,
    normalize_pdf_page_size,
)
from .formatter import (
    create_cover_page,
    create_toc_page,
    create_section_header,
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
            
            # Find the downloads directory
            base_dir = Path(self.config.config["global"]["base_dir"])
            downloads_dir = base_dir / "data" / "courses" / course_id / "downloads"
            
            # Check if the downloads directory exists
            if not downloads_dir.exists():
                # Try to find the downloads directory in the current working directory
                alt_downloads_dir = Path.cwd() / "data" / "courses" / course_id / "downloads"
                if alt_downloads_dir.exists():
                    downloads_dir = alt_downloads_dir
                    logger.info(f"Using alternative downloads directory: {downloads_dir}")
                else:
                    logger.warning(f"Downloads directory not found: {downloads_dir}")
                    raise ValueError(f"Downloads directory not found: {downloads_dir}")
            
            # Get course JSON data if available for author info and course name
            course_author = ""
            
            # Try different JSON file naming patterns
            json_files_to_try = [
                Path(downloads_dir.parent / f"{course_id}.json"),
                Path(downloads_dir.parent / f"{course_id.replace('-', '')}.json"),
                Path(downloads_dir.parent / "course.json"),
                Path(downloads_dir.parent / "metadata.json")
            ]
            
            course_json_file = None
            for json_path in json_files_to_try:
                if json_path.exists():
                    course_json_file = json_path
                    logger.info(f"Found course JSON file: {json_path}")
                    break
                    
            if course_json_file and course_json_file.exists():
                try:
                    with open(course_json_file, "r") as f:
                        course_data = json.load(f)
                        
                        # Check for nested course data structure
                        if "course" in course_data and isinstance(course_data["course"], dict):
                            # Extract from nested course object
                            course_obj = course_data["course"]
                            
                            # Get author info
                            if "author" in course_obj:
                                course_author = course_obj["author"]
                            elif "instructors" in course_obj:
                                course_author = ", ".join(course_obj["instructors"])
                                
                            # Get better course name from JSON if available
                            if "name" in course_obj:
                                course_name = course_obj["name"]
                                logger.info(f"Using course name from nested JSON: {course_name}")
                            elif "title" in course_obj:
                                course_name = course_obj["title"]
                                logger.info(f"Using course title from nested JSON: {course_name}")
                        else:
                            # Get author info from flat structure
                            if "author" in course_data:
                                course_author = course_data["author"]
                            elif "instructors" in course_data:
                                course_author = ", ".join(course_data["instructors"])
                                
                            # Get better course name from JSON if available
                            if "name" in course_data:
                                course_name = course_data["name"]
                                logger.info(f"Using course name from JSON: {course_name}")
                            elif "title" in course_data:
                                course_name = course_data["title"]
                                logger.info(f"Using course title from JSON: {course_name}")
                except Exception as e:
                    logger.warning(f"Error reading course JSON data: {e}")
                    
            # Ensure course name is in proper title case
            try:
                words = course_name.split()
                # Capitalize first letter of each word, except for common words that should be lowercase
                lowercase_words = {'a', 'an', 'the', 'and', 'but', 'or', 'for', 'nor', 'on', 'at', 'to', 'from', 'by', 'with', 'in', 'of'}
                for i in range(len(words)):
                    if i > 0 and words[i].lower() in lowercase_words:
                        words[i] = words[i].lower()
                    else:
                        words[i] = words[i].capitalize()
                course_name = " ".join(words)
            except Exception:
                # If formatting fails, just capitalize the string
                course_name = " ".join(word.capitalize() for word in course_name.split())
            
            # Try to find course image
            course_image = None
            course_image_path = downloads_dir.parent / "course_image.jpg"
            if not course_image_path.exists():
                # Try other common image filenames
                for img_name in ["cover.jpg", "cover.png", "thumbnail.jpg", "thumbnail.png"]:
                    alt_image_path = downloads_dir.parent / img_name
                    if alt_image_path.exists():
                        course_image_path = alt_image_path
                        break
            
            if course_image_path.exists():
                course_image = str(course_image_path)
                logger.info(f"Using course image: {course_image}")
            
            # Create title page
            logger.info(f"Creating title page for course: {course_name}")
            title_page = create_cover_page(
                course_name=course_name,
                author=course_author,
                output_file=self.temp_dir / "00_title_page.pdf",
                course_image=course_image
            )
            
            # Process content files
            content_files = self._process_course_files(course_id)
            
            if not content_files:
                logger.error("No content files generated")
                raise ValueError("No content files generated")
            
            # Insert section dividers between modules
            logger.info("Inserting module divider pages")
            enriched_content_files = self._insert_module_dividers(content_files, course_name)
            
            # Normalize page sizes for content PDFs
            logger.info("Normalizing page sizes for content PDFs")
            normalized_content_pdfs = []
            for idx, pdf_file in enumerate(enriched_content_files):
                try:
                    # Use improved normalize function to preserve standard paper sizes
                    norm_file = normalize_pdf_page_size(
                        pdf_file,
                        output_file=self.temp_dir / f"norm_{idx:03d}_{Path(pdf_file).name}",
                        preserve_aspect_ratio=True,
                        standard_sizes=True
                    )
                    normalized_content_pdfs.append(norm_file)
                except Exception as e:
                    logger.warning(f"Error normalizing PDF {pdf_file}: {e}")
                    normalized_content_pdfs.append(pdf_file)  # Use original if normalization fails
            
            # Create temporary PDF without TOC to get page numbers
            logger.info("Creating temporary PDF to determine page numbers")
            temp_merged_path = self.temp_dir / "temp_merged.pdf"
            temp_pdf_files = [title_page] + normalized_content_pdfs
            self._merge_pdf_files(temp_pdf_files, temp_merged_path)
            
            # Get page numbers for TOC entries
            logger.info("Extracting page numbers for TOC")
            # Generate TOC sections directly from content files (bypassing page number extraction)
            # We'll set page numbers manually
            toc_sections = []
            current_page = 3  # Start after cover (1) and TOC (2)
            current_module = None
            
            # Scan through files to build TOC with page numbers
            for pdf_file in normalized_content_pdfs:
                filename = Path(pdf_file).name
                
                # Skip divider pages in the TOC but count them for page numbers
                if "divider_" in filename:
                    # Extract module number
                    module_match = re.search(r"divider_(\d+)", filename)
                    if module_match:
                        module_num = int(module_match.group(1))
                        module_name = self._clean_name(f"Module {module_num}")
                        
                        # Try to find the real module name from the file system
                        course_id = None
                        for key in self.config.config:
                            if key.startswith("course:"):
                                course_id = key.split(":")[1]
                                break
                        
                        if course_id:
                            downloads_dir = Path.cwd() / "data" / "courses" / course_id / "downloads"
                            if downloads_dir.exists():
                                for dir_path in downloads_dir.iterdir():
                                    if dir_path.is_dir():
                                        match = re.match(r"^(\d+)\.", dir_path.name)
                                        if match and int(match.group(1)) == module_num:
                                            module_name = self._clean_name(dir_path.name)
                                            break
                        
                        # Add module section to TOC
                        toc_sections.append({
                            "title": module_name,
                            "level": 0,
                            "page": str(current_page)
                        })
                        current_module = module_num
                    
                    current_page += 1
                    continue
                
                # For content files
                # Try to parse the filename to extract module info and title
                if "norm_" in filename:
                    # Handles normalized filenames like norm_001_0002_0003_0000_original.pdf
                    parts = filename.split("_")
                    if len(parts) >= 5:
                        try:
                            # Get original filename (last part or parts) - handle special cases
                            filename_part = parts[-1] if len(parts) > 4 else filename
                            title = self._extract_title_from_filename(filename_part)
                            
                            # Add content entry to TOC
                            toc_sections.append({
                                "title": title,
                                "level": 1,
                                "page": str(current_page)
                            })
                        except Exception as e:
                            # In case of parsing error, add a simple entry
                            logger.warning(f"Error parsing filename for TOC: {e}")
                            toc_sections.append({
                                "title": Path(filename).stem,
                                "level": 1,
                                "page": str(current_page)
                            })
                else:
                    # Original format: 0001_0001_0000_filename.pdf
                    parts = filename.split("_", 3)
                    if len(parts) >= 3:
                        original_filename = parts[3] if len(parts) > 3 else ""
                        title = self._extract_title_from_filename(original_filename)
                        
                        toc_sections.append({
                            "title": title,
                            "level": 1,
                            "page": str(current_page)
                        })
                
                current_page += 1
            
            # Use the manually generated TOC with page numbers
            toc_sections_with_pages = toc_sections
            
            # Generate table of contents with page numbers
            logger.info("Generating table of contents with page numbers")
            toc_page = create_toc_page(
                sections=toc_sections_with_pages,
                output_file=self.temp_dir / "01_toc_page.pdf",
                course_name=course_name
            )
            
            # Merge final PDF with updated TOC
            all_pdf_files = [title_page, toc_page] + normalized_content_pdfs
            
            # Since we already normalized the content PDFs, just normalize the title and TOC
            try:
                norm_title = normalize_pdf_page_size(
                    title_page,
                    output_file=self.temp_dir / f"norm_000_title_page.pdf"
                )
                norm_toc = normalize_pdf_page_size(
                    toc_page,
                    output_file=self.temp_dir / f"norm_001_toc_page.pdf"
                )
                all_normalized_pdfs = [norm_title, norm_toc] + normalized_content_pdfs
            except Exception as e:
                logger.warning(f"Error normalizing title/TOC pages: {e}")
                all_normalized_pdfs = all_pdf_files  # Use originals if normalization fails
            
            # Merge all PDFs
            output_path = self._merge_pdf_files(all_normalized_pdfs, output_file)
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
        
    def _generate_toc_sections(self, pdf_files: List[Union[str, Path]]) -> List[Dict[str, str]]:
        """
        Generate table of contents sections from PDF files.
        
        Args:
            pdf_files: List of PDF file paths
            
        Returns:
            List of dictionaries with section information for the TOC
        """
        toc_sections = []
        current_module = None
        
        for pdf_file in pdf_files:
            # Extract module info from filename
            filename = Path(pdf_file).name
            # Expected format: 0001_0001_0001_filename.pdf
            parts = filename.split("_", 3)
            if len(parts) >= 3:
                module_num = int(parts[0])
                subdir_num = int(parts[1])
                
                # Get the original filename (last part)
                original_filename = parts[3] if len(parts) > 3 else ""
                
                # Extract title from filename
                title = self._extract_title_from_filename(original_filename)
                
                # Add module header if it's a new module
                if current_module != module_num:
                    # Find the module directory name
                    module_dir_name = self._clean_name(f"Module {module_num}")
                    
                    # Try to find the real module name from the file system
                    base_dir = Path(self.config.config["global"]["base_dir"])
                    course_id = None
                    for key in self.config.config:
                        if key.startswith("course:"):
                            course_id = key.split(":")[1]
                            break
                    
                    if not course_id:
                        course_id = "reclaiming-you-2025"  # Default fallback
                        
                    downloads_dir = Path.cwd() / "data" / "courses" / course_id / "downloads"
                    for dir_path in downloads_dir.iterdir():
                        if dir_path.is_dir():
                            match = re.match(r"^(\d+)\.", dir_path.name)
                            if match and int(match.group(1)) == module_num:
                                module_dir_name = self._clean_name(dir_path.name)
                                break
                    
                    # Add module section to TOC
                    toc_sections.append({
                        "title": module_dir_name,
                        "level": 0,
                        "page": "",  # Page numbers will be filled in later
                        "filename": f"module_{module_num}",  # Used for page number lookup
                    })
                    current_module = module_num
                
                # Add the item to TOC
                # Skip summaries for items that are just PDF versions of other files
                if "summary" not in original_filename.lower():
                    toc_sections.append({
                        "title": title,
                        "level": 1,
                        "page": "",  # Page numbers will be filled in later
                        "filename": Path(pdf_file).name,  # Used for page number lookup
                    })
        
        return toc_sections
        
    def _add_page_numbers_to_toc(self, toc_sections: List[Dict[str, str]], pdf_path: Path) -> List[Dict[str, str]]:
        """
        Add page numbers to TOC sections based on the merged PDF.
        
        Args:
            toc_sections: List of dictionaries with TOC sections
            pdf_path: Path to the merged PDF file with page numbers
            
        Returns:
            Updated TOC sections with page numbers
        """
        try:
            # Open the merged PDF to get page numbers
            with open(pdf_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                total_pages = len(reader.pages)
                logger.info(f"PDF has {total_pages} pages")
                
                # Start counting from page 2 (after cover page)
                current_page = 2  # Cover page is 1, TOC will be page 2 in the final PDF
                
                # Simple approach: assign sequential page numbers to content items
                content_sections = []
                module_sections = []
                
                # First pass - separate module headers and content items
                for section in toc_sections:
                    level = section.get("level", 0)
                    if level == 0:
                        module_sections.append(section)
                    else:
                        content_sections.append(section)
                        # Assign page numbers to content items
                        section["page"] = str(current_page)
                        current_page += 1
                
                # Second pass - assign page numbers to module headers
                # (point to the first content item in that module)
                for module_section in module_sections:
                    module_name = module_section.get("filename", "")
                    if not module_name:
                        continue
                        
                    # Extract module number
                    module_match = re.match(r"module_(\d+)", module_name)
                    if not module_match:
                        continue
                        
                    module_num = module_match.group(1)
                    
                    # Find the first content item in this module
                    for content_section in content_sections:
                        content_filename = content_section.get("filename", "")
                        # Check if the content filename starts with this module number
                        if content_filename.startswith(f"{int(module_num):04d}_"):
                            module_section["page"] = content_section["page"]
                            break
            
            return toc_sections
            
        except Exception as e:
            logger.error(f"Error adding page numbers to TOC: {e}")
            # Log the traceback for debugging
            import traceback
            logger.error(traceback.format_exc())
            return toc_sections
    
    def _extract_title_from_filename(self, filename: str) -> str:
        """
        Extract a readable title from a filename.
        
        Args:
            filename: Original filename
            
        Returns:
            Human-readable title
        """
        try:
            # Remove file extensions
            basename = Path(filename).stem
            
            # Import library for URL decoding - needed for handling percent-encoded characters
            import urllib.parse
            
            # URL decode first to handle %20 and other encoded characters
            try:
                basename = urllib.parse.unquote(basename)
            except Exception:
                # Continue with original if decoding fails
                pass
            
            # Handle common patterns that indicate an ID or hash prefix
            # Remove random-looking alphanumeric prefixes like "q2jgdeessmmkkywkpvnz"
            cleaned = re.sub(r"^[a-zA-Z0-9]{15,25}[\s_-]+", "", basename)
            
            # Remove common prefixes like numbers
            cleaned = re.sub(r"^\d+[\.-]", "", cleaned)
            
            # Remove numeric IDs pattern like "0000 12345678" often seen in Thinkific content
            cleaned = re.sub(r"\b\d{4}\s+\d{8}\b[-\s]*", "", cleaned)
            
            # Remove any standalone numbers at the start
            cleaned = re.sub(r"^\s*\d+\s+", "", cleaned)
            
            # Replace common separators with spaces
            cleaned = cleaned.replace("-", " ").replace("_", " ").replace(".", " ")
            
            # Handle common encoded strings for apostrophes and other special characters
            cleaned = cleaned.replace("%e2%80%99s", "'s").replace("%e2%80%99", "'").replace("%e2%80%9c", "\"").replace("%e2%80%9d", "\"")
            
            # Remove common content indicators
            cleaned = re.sub(r"(html?|pdf|md|markdown|text|summary)$", "", cleaned, flags=re.IGNORECASE)
            
            # Remove week indicators
            cleaned = re.sub(r"\b(week|module)\s+\d+\b", "", cleaned, flags=re.IGNORECASE)
            
            # Clean up multiple spaces
            cleaned = re.sub(r"\s+", " ", cleaned).strip()
            
            # Capital case and trim
            words = cleaned.split()
            if words:
                # Capitalize first letter of each word, except for common words that should be lowercase
                lowercase_words = {'a', 'an', 'the', 'and', 'but', 'or', 'for', 'nor', 'on', 'at', 'to', 'from', 'by', 'with', 'in', 'of', 'vs'}
                result = []
                
                for i, word in enumerate(words):
                    if word.strip():
                        if i > 0 and word.lower() in lowercase_words:
                            result.append(word.lower())
                        else:
                            result.append(word.capitalize())
                
                return " ".join(result)
            
            return basename
        
        except Exception as e:
            # If anything fails, return a cleaned-up version of the original
            logger.warning(f"Error extracting title from filename '{filename}': {e}")
            try:
                # Simple fallback cleanup
                clean = re.sub(r'[_\.-]', ' ', filename)
                clean = " ".join(word.capitalize() for word in clean.split())
                return clean
            except:
                return filename
    
    def _clean_name(self, name: str) -> str:
        """
        Clean a directory or file name for display.
        
        Args:
            name: Directory or file name
            
        Returns:
            Cleaned name for display
        """
        # Remove leading numbers and dots
        cleaned = re.sub(r"^\d+\.\s*", "", name)
        
        # Replace separators with spaces
        cleaned = cleaned.replace("-", " ").replace("_", " ")
        
        # Capital case
        words = cleaned.split()
        if words:
            words = [w.capitalize() for w in words if w.strip()]
            return " ".join(words)
        
        return name

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
        Merge PDF files into a single PDF with bookmarks.

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

        # Extract bookmark information
        bookmarks = self._create_bookmarks_from_files(pdf_files)

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

            # Add bookmarks to the final PDF
            self._add_bookmarks_to_pdf(output_file, bookmarks)

            print(f"Successfully merged PDFs into {output_file}")
            return output_file
        except Exception as e:
            print(f"Error merging PDFs: {e}")
            logger.error(f"Error merging PDFs: {e}")

            # Fallback: try direct merge if batch processing failed
            try:
                logger.info("Attempting direct merge as fallback")
                merge_pdfs(pdf_files, output_file)
                
                # Try to add bookmarks
                try:
                    self._add_bookmarks_to_pdf(output_file, bookmarks)
                except Exception as bookmark_error:
                    logger.warning(f"Failed to add bookmarks: {bookmark_error}")
                
                print(f"Successfully merged PDFs using fallback method into {output_file}")
                return output_file
            except Exception as fallback_error:
                logger.error(f"Fallback merge also failed: {fallback_error}")
                raise
                
    def _create_bookmarks_from_files(self, pdf_files: List[Union[str, Path]]) -> List[dict]:
        """
        Create bookmark entries from PDF file paths.
        
        Args:
            pdf_files: List of PDF file paths
            
        Returns:
            List of bookmark entries with title, level, and page number
        """
        bookmarks = []
        current_page = 0
        current_module = None
        
        for pdf_file in pdf_files:
            filename = Path(pdf_file).name
            
            # Skip the first two files (cover and TOC)
            if "title_page" in filename or "toc_page" in filename:
                current_page += 1
                continue
                
            # Check if this is a module divider - handle both normalized and raw files
            if "divider_" in filename:
                # Extract module number, handling both formats:
                # - divider_0001.pdf
                # - norm_123_divider_0001.pdf
                if filename.startswith("divider_"):
                    module_match = re.search(r"divider_(\d+)", filename)
                else:
                    module_match = re.search(r"divider_(\d+)", filename)
                
                if module_match:
                    module_num = int(module_match.group(1))
                    module_name = self._clean_name(f"Module {module_num}")
                    
                    # Add module bookmark
                    bookmarks.append({
                        "title": module_name,
                        "level": 0,
                        "page": current_page
                    })
                    current_module = module_num
                
                current_page += 1
                continue
            
            # Normal content file - handle normalized filenames
            # Extract the module number from the path
            if "norm_" in filename:
                # Format: norm_001_0002_0001_0000_filename.pdf
                parts = filename.split("_")
                # Skip the norm prefix and index
                if len(parts) >= 4:
                    try:
                        module_num = int(parts[2])  # Module number is after the norm index
                    except ValueError:
                        # If we can't parse the module number, skip this file
                        current_page += 1
                        continue
                else:
                    # If the filename doesn't have enough parts, skip it
                    current_page += 1
                    continue
            else:
                # Original format: 0002_0001_0000_filename.pdf
                parts = filename.split("_", 3)
                if len(parts) < 3:
                    # If the filename doesn't have enough parts, skip it
                    current_page += 1
                    continue
                
                try:
                    module_num = int(parts[0])
                except ValueError:
                    # If we can't parse the module number, skip this file
                    current_page += 1
                    continue
            
            # Get the original filename (last part)
            if len(parts) > 3:
                original_filename = parts[-1]  # Use the last part as the original filename
            else:
                original_filename = filename
                
            title = self._extract_title_from_filename(original_filename)
            
            # Add content bookmark
            bookmarks.append({
                "title": title,
                "level": 1,
                "page": current_page
            })
            
            current_page += 1
        
        return bookmarks
    
    def _add_bookmarks_to_pdf(self, pdf_path: Path, bookmarks: List[dict]) -> None:
        """
        Add bookmarks to an existing PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            bookmarks: List of bookmark entries with title, level, and page number
        """
        try:
            logger.info(f"Adding {len(bookmarks)} bookmarks to {pdf_path}")
            
            # Open the PDF
            with open(pdf_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                writer = PyPDF2.PdfWriter()
                
                # Copy all pages from the input PDF
                for page in reader.pages:
                    writer.add_page(page)
                
                # Dictionary to store bookmark references by title
                bookmark_refs = {}
                
                # First add all top-level bookmarks
                for i, bookmark in enumerate(bookmarks):
                    title = bookmark.get("title", f"Untitled {i}")
                    level = bookmark.get("level", 0)
                    page_num = bookmark.get("page", 0)
                    
                    # Make sure page number is valid (convert to int if it's a string)
                    try:
                        if isinstance(page_num, str):
                            page_num = int(page_num)
                        if page_num < 0 or page_num >= len(reader.pages):
                            continue
                    except (ValueError, TypeError):
                        continue
                        
                    if level == 0:
                        # Add top-level bookmark and store reference
                        bookmark_obj = writer.add_outline_item(title, page_num)
                        bookmark_refs[title] = bookmark_obj
                
                # Then add child bookmarks (level > 0)
                for i, bookmark in enumerate(bookmarks):
                    title = bookmark.get("title", f"Untitled {i}")
                    level = bookmark.get("level", 0)
                    page_num = bookmark.get("page", 0)
                    
                    # Make sure page number is valid (convert to int if it's a string)
                    try:
                        if isinstance(page_num, str):
                            page_num = int(page_num)
                        if page_num < 0 or page_num >= len(reader.pages):
                            continue
                    except (ValueError, TypeError):
                        continue
                    
                    # Skip top-level bookmarks as they were already added
                    if level == 0:
                        continue
                        
                    # Find parent bookmark
                    parent_title = None
                    for j in range(i-1, -1, -1):
                        if bookmarks[j].get("level", 0) < level:
                            parent_title = bookmarks[j].get("title", f"Untitled {j}")
                            break
                    
                    if parent_title and parent_title in bookmark_refs:
                        # Add as child of parent
                        parent_ref = bookmark_refs[parent_title]
                        child_ref = writer.add_outline_item(title, page_num, parent=parent_ref)
                        bookmark_refs[title] = child_ref
                    else:
                        # Add as top-level if parent not found
                        bookmark_obj = writer.add_outline_item(title, page_num)
                        bookmark_refs[title] = bookmark_obj
                
                # Write the output PDF
                temp_output = Path(str(pdf_path) + ".tmp")
                with open(temp_output, 'wb') as out_f:
                    writer.write(out_f)
                
                # Replace the original file
                temp_output.replace(pdf_path)
                logger.info(f"Successfully added bookmarks to {pdf_path}")
                
        except Exception as e:
            logger.error(f"Error adding bookmarks to PDF: {e}")
            import traceback
            logger.error(traceback.format_exc())

    def _insert_module_dividers(self, content_files: List[Path], course_name: str) -> List[Path]:
        """
        Insert module divider pages between modules.
        
        Args:
            content_files: List of content PDF file paths
            course_name: Course name for header
            
        Returns:
            List of content files with module dividers inserted
        """
        if not content_files:
            return content_files
            
        # Group files by module number
        module_files = {}
        for file_path in content_files:
            # Extract module number from filename
            file_name = Path(file_path).name
            parts = file_name.split("_", 3)
            if len(parts) < 3:
                continue
                
            module_num = int(parts[0])
            if module_num not in module_files:
                module_files[module_num] = []
            module_files[module_num].append(file_path)
            
        if not module_files:
            return content_files
            
        # Create module divider pages and insert them
        enriched_files = []
        modules = sorted(module_files.keys())
        
        for module_num in modules:
            # Find the module name
            module_name = self._clean_name(f"Module {module_num}")
            
            # Try to find the real module name from the file system
            base_dir = Path(self.config.config["global"]["base_dir"])
            course_id = None
            for key in self.config.config:
                if key.startswith("course:"):
                    course_id = key.split(":")[1]
                    break
                
            if not course_id:
                # Try to extract course ID from content file paths
                for file_path in content_files:
                    if "courses" in file_path.parts:
                        course_idx = file_path.parts.index("courses")
                        if course_idx < len(file_path.parts) - 1:
                            course_id = file_path.parts[course_idx + 1]
                            break
            
            if course_id:
                downloads_dir = Path.cwd() / "data" / "courses" / course_id / "downloads"
                if downloads_dir.exists():
                    for dir_path in downloads_dir.iterdir():
                        if dir_path.is_dir():
                            match = re.match(r"^(\d+)\.", dir_path.name)
                            if match and int(match.group(1)) == module_num:
                                module_name = self._clean_name(dir_path.name)
                                break
            
            # Create divider page
            divider_path = self.temp_dir / f"divider_{module_num:04d}.pdf"
            divider_page = create_section_header(
                section_title=module_name,
                output_file=divider_path,
                course_name=course_name
            )
            
            # Add the divider and then the module files
            enriched_files.append(divider_page)
            enriched_files.extend(module_files[module_num])
            
        return enriched_files

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