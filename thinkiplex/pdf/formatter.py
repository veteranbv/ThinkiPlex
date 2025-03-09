"""
Formatting utilities for PDF generation.

This module provides utilities for formatting PDFs, such as creating cover pages,
table of contents, and section headers.
"""

import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union

from weasyprint import HTML

from ..utils.logging import get_logger

logger = get_logger()


def create_cover_page(
    course_name: str,
    output_file: Optional[Union[str, Path]] = None,
    author: str = "",
    date: Optional[datetime] = None,
) -> Path:
    """
    Create a cover page for the course PDF.

    Args:
        course_name: Name of the course
        output_file: Path to save the cover page PDF (optional)
        author: Author of the course (optional)
        date: Date of PDF generation (optional, defaults to current date)

    Returns:
        Path to the generated cover page PDF
    """
    if date is None:
        date = datetime.now()

    date_str = date.strftime("%B %d, %Y")

    # Create a temporary file if output_file is not specified
    if output_file is None:
        fd, output_file = tempfile.mkstemp(suffix=".pdf")
        os.close(fd)
    else:
        output_file = Path(output_file)

    # Create HTML for the cover page
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>{course_name}</title>
        <style>
            @page {{
                size: letter;
                margin: 0;
            }}
            body {{
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 0;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                height: 100vh;
                text-align: center;
                background-color: #f5f5f5;
            }}
            .cover {{
                width: 80%;
                max-width: 800px;
                padding: 2em;
                background-color: white;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            }}
            h1 {{
                font-size: 32pt;
                margin-bottom: 0.5em;
                color: #333;
            }}
            .subtitle {{
                font-size: 16pt;
                margin-bottom: 2em;
                color: #666;
            }}
            .author {{
                font-size: 14pt;
                margin-bottom: 1em;
                color: #444;
            }}
            .date {{
                font-size: 12pt;
                color: #666;
            }}
            .logo {{
                margin-bottom: 2em;
                font-size: 18pt;
                color: #333;
                font-weight: bold;
            }}
        </style>
    </head>
    <body>
        <div class="cover">
            <div class="logo">ThinkiPlex</div>
            <h1>{course_name}</h1>
            <div class="subtitle">Course Resources</div>
            {f'<div class="author">{author}</div>' if author else ""}
            <div class="date">Generated on {date_str}</div>
        </div>
    </body>
    </html>
    """

    # Convert HTML to PDF
    try:
        HTML(string=html_content).write_pdf(output_file)
        logger.info(f"Created cover page: {output_file}")
        return Path(output_file)
    except Exception as e:
        logger.error(f"Error creating cover page: {e}")
        raise


def create_toc_page(
    sections: List[Dict[str, str]],
    output_file: Optional[Union[str, Path]] = None,
    title: str = "Table of Contents",
) -> Path:
    """
    Create a table of contents page.

    Args:
        sections: List of dictionaries with 'title' and 'page' keys
        output_file: Path to save the TOC page PDF (optional)
        title: Title for the TOC page (optional)

    Returns:
        Path to the generated TOC page PDF
    """
    # Create a temporary file if output_file is not specified
    if output_file is None:
        fd, output_file = tempfile.mkstemp(suffix=".pdf")
        os.close(fd)
    else:
        output_file = Path(output_file)

    # Create HTML for the TOC page
    toc_items = ""
    for section in sections:
        toc_items += f"""
        <div class="toc-item">
            <span class="toc-title">{section["title"]}</span>
            <span class="toc-page">{section.get("page", "")}</span>
        </div>
        """

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>{title}</title>
        <style>
            @page {{
                size: letter;
                margin: 2cm;
                @bottom-center {{
                    content: counter(page);
                }}
            }}
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                margin: 2em;
                font-size: 12pt;
            }}
            h1 {{
                font-size: 24pt;
                margin-bottom: 1em;
                text-align: center;
                border-bottom: 1px solid #ddd;
                padding-bottom: 0.5em;
            }}
            .toc-item {{
                display: flex;
                justify-content: space-between;
                margin-bottom: 0.5em;
                border-bottom: 1px dotted #ddd;
            }}
            .toc-title {{
                flex-grow: 1;
            }}
            .toc-page {{
                margin-left: 1em;
            }}
        </style>
    </head>
    <body>
        <h1>{title}</h1>
        <div class="toc">
            {toc_items}
        </div>
    </body>
    </html>
    """

    # Convert HTML to PDF
    try:
        HTML(string=html_content).write_pdf(output_file)
        logger.info(f"Created TOC page: {output_file}")
        return Path(output_file)
    except Exception as e:
        logger.error(f"Error creating TOC page: {e}")
        raise


def create_section_header(
    section_title: str,
    output_file: Optional[Union[str, Path]] = None,
) -> Path:
    """
    Create a section header page.

    Args:
        section_title: Title of the section
        output_file: Path to save the section header PDF (optional)

    Returns:
        Path to the generated section header PDF
    """
    # Create a temporary file if output_file is not specified
    if output_file is None:
        fd, output_file = tempfile.mkstemp(suffix=".pdf")
        os.close(fd)
    else:
        output_file = Path(output_file)

    # Create HTML for the section header
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>{section_title}</title>
        <style>
            @page {{
                size: letter;
                margin: 2cm;
            }}
            body {{
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 0;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                height: 100vh;
                text-align: center;
            }}
            h1 {{
                font-size: 28pt;
                margin-bottom: 0.5em;
                color: #333;
                border-bottom: 2px solid #ddd;
                padding-bottom: 0.3em;
            }}
        </style>
    </head>
    <body>
        <h1>{section_title}</h1>
    </body>
    </html>
    """

    # Convert HTML to PDF
    try:
        HTML(string=html_content).write_pdf(output_file)
        logger.info(f"Created section header: {output_file}")
        return Path(output_file)
    except Exception as e:
        logger.error(f"Error creating section header: {e}")
        raise
