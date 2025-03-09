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
    course_image: Optional[str] = None,
) -> Path:
    """
    Create a cover page for the course PDF.

    Args:
        course_name: Name of the course
        output_file: Path to save the cover page PDF (optional)
        author: Author of the course (optional)
        date: Date of PDF generation (optional, defaults to current date)
        course_image: Path to course image (optional)

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

    # Image HTML if available
    image_html = ""
    if course_image and Path(course_image).exists():
        image_html = f"""
        <div class="course-image">
            <img src="{course_image}" alt="{course_name} Cover Image">
        </div>
        """

    # Clean up the course name to make it title case
    course_name_display = " ".join(word.capitalize() for word in course_name.split())

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
                font-family: 'Helvetica Neue', Arial, sans-serif;
                margin: 0;
                padding: 0;
                height: 100vh;
                text-align: center;
                background: linear-gradient(135deg, #2c3e50 0%, #4a6b8a 100%);
                color: white;
            }}
            .cover-container {{
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                height: 100vh;
                padding: 2em;
            }}
            .cover {{
                width: 85%;
                max-width: 800px;
                padding: 3em;
                background-color: #2c3e50;
                box-shadow: 0 15px 35px rgba(0, 0, 0, 0.3);
                border-radius: 12px;
                color: white;
                position: relative;
                overflow: hidden;
            }}
            .cover::before {{
                content: "";
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 8px;
                background: linear-gradient(to right, #3498db, #2ecc71);
                border-radius: 12px 12px 0 0;
            }}
            .logo {{
                margin-bottom: 2.5em;
                font-size: 22pt;
                font-weight: bold;
                letter-spacing: 2px;
                color: #3498db;
                text-transform: uppercase;
                position: relative;
                display: inline-block;
                padding: 0 10px;
            }}
            .logo::after {{
                content: "";
                position: absolute;
                bottom: -5px;
                left: 0;
                width: 100%;
                height: 2px;
                background: linear-gradient(to right, #3498db, #2ecc71);
            }}
            h1 {{
                font-size: 42pt;
                margin-bottom: 0.5em;
                line-height: 1.2;
                color: #ffffff;
                text-shadow: 0px 2px 4px rgba(0,0,0,0.3);
                font-weight: 600;
            }}
            .subtitle {{
                font-size: 18pt;
                margin-bottom: 2.5em;
                color: #9ea7b0;
                font-weight: 300;
                letter-spacing: 1px;
            }}
            .author {{
                font-size: 16pt;
                margin-bottom: 1.5em;
                color: #9ea7b0;
                border-bottom: 1px solid #4a6b8a;
                padding-bottom: 0.5em;
                display: inline-block;
            }}
            .date {{
                font-size: 14pt;
                color: #9ea7b0;
                font-style: italic;
                margin-top: 2em;
            }}
            .divider {{
                width: 30%;
                height: 3px;
                background: linear-gradient(to right, #3498db, #2ecc71);
                margin: 2em auto;
                border-radius: 3px;
            }}
            .course-image {{
                margin-bottom: 2em;
                border-radius: 8px;
                overflow: hidden;
                box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
                max-width: 90%;
                height: auto;
            }}
            .course-image img {{
                max-width: 100%;
                height: auto;
                display: block;
            }}
            .decoration {{
                position: absolute;
                width: 200px;
                height: 200px;
                border-radius: 50%;
                background: radial-gradient(circle, rgba(52, 152, 219, 0.1) 0%, rgba(46, 204, 113, 0.05) 100%);
                z-index: -1;
            }}
            .decoration-1 {{
                top: -100px;
                right: -100px;
            }}
            .decoration-2 {{
                bottom: -50px;
                left: -50px;
            }}
        </style>
    </head>
    <body>
        <div class="cover-container">
            <div class="cover">
                <div class="decoration decoration-1"></div>
                <div class="decoration decoration-2"></div>
                <div class="logo">ThinkiPlex</div>
                {image_html}
                <h1>{course_name_display}</h1>
                <div class="subtitle">Course Resources</div>
                <div class="divider"></div>
                {f'<div class="author">By {author}</div>' if author else ""}
                <div class="date">Generated on {date_str}</div>
            </div>
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
    course_name: str = "",
) -> Path:
    """
    Create a table of contents page.

    Args:
        sections: List of dictionaries with 'title', 'level', and 'page' keys
        output_file: Path to save the TOC page PDF (optional)
        title: Title for the TOC page (optional)
        course_name: Course name for header (optional)

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
    current_level = -1
    current_module = None
    
    for section in sections:
        level = section.get("level", 0)
        section_title = section.get("title", "")
        page_num = section.get("page", "")
        
        # For module-level entries (level 0)
        if level == 0:
            current_module = section_title
            # Add a visual separator if not the first module
            if current_level != -1:
                toc_items += '<div class="module-separator"></div>'
                
            toc_items += f'<div class="toc-module">{section_title}</div>'
        else:
            # For content-level entries (level 1, 2, etc.)
            dot_leaders = '<span class="dots"></span>'
            indent_class = f"level-{level}"
            
            toc_items += f"""
            <div class="toc-item {indent_class}">
                <span class="toc-number">{page_num}</span>
                <span class="toc-title">{section_title}</span>
                {dot_leaders}
            </div>
            """
        
        current_level = level

    # Header with course name if provided
    header_html = ""
    if course_name:
        header_html = f'<div class="course-name">{course_name}</div>'

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
                font-family: 'Helvetica Neue', Arial, sans-serif;
                line-height: 1.6;
                margin: 2em;
                font-size: 12pt;
                color: #2c3e50;
                counter-reset: page 2; /* Start page counter at 2 */
            }}
            .header {{
                display: flex;
                flex-direction: column;
                align-items: center;
                margin-bottom: 2em;
            }}
            .course-name {{
                font-size: 16pt;
                color: #7f8c8d;
                margin-bottom: 0.5em;
            }}
            h1 {{
                font-size: 28pt;
                text-align: center;
                color: #2c3e50;
                margin-bottom: 0.5em;
                position: relative;
            }}
            h1::after {{
                content: "";
                position: absolute;
                bottom: -10px;
                left: 50%;
                transform: translateX(-50%);
                width: 100px;
                height: 3px;
                background: linear-gradient(to right, #3498db, #2ecc71);
                border-radius: 3px;
            }}
            .toc {{
                max-width: 800px;
                margin: 2em auto;
                padding: 1em 2em;
                background-color: white;
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
            }}
            .toc-module {{
                font-size: 16pt;
                font-weight: bold;
                margin-top: 1.2em;
                margin-bottom: 0.8em;
                color: #2c3e50;
                padding: 0.3em 0.5em;
                background: linear-gradient(to right, rgba(52, 152, 219, 0.1), rgba(46, 204, 113, 0.05));
                border-radius: 4px;
                border-left: 4px solid #3498db;
            }}
            .module-separator {{
                height: 1em;
            }}
            .toc-item {{
                display: flex;
                justify-content: space-between;
                margin-bottom: 0.6em;
                position: relative;
                padding: 0.2em 0.5em;
                border-radius: 4px;
                transition: background-color 0.2s;
            }}
            .toc-item:hover {{
                background-color: rgba(236, 240, 241, 0.5);
            }}
            .level-1 {{
                padding-left: 1.5em;
            }}
            .level-2 {{
                padding-left: 3em;
                font-size: 11pt;
            }}
            .toc-number {{
                width: 2em;
                text-align: right;
                margin-right: 1em;
                color: #3498db;
                font-weight: bold;
            }}
            .toc-title {{
                flex-grow: 1;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
                max-width: 80%;
            }}
            .dots {{
                flex-grow: 1;
                margin: 0 0.5em;
                border-bottom: 1px dotted #bdc3c7;
                height: 1em;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            {header_html}
            <h1>{title}</h1>
        </div>
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
    course_name: str = "",
) -> Path:
    """
    Create a section header page.

    Args:
        section_title: Title of the section
        output_file: Path to save the section header PDF (optional)
        course_name: Course name to display (optional)

    Returns:
        Path to the generated section header PDF
    """
    # Create a temporary file if output_file is not specified
    if output_file is None:
        fd, output_file = tempfile.mkstemp(suffix=".pdf")
        os.close(fd)
    else:
        output_file = Path(output_file)

    # Create the course name element if provided
    course_html = ""
    if course_name:
        course_html = f'<div class="course-name">{course_name}</div>'

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
                margin: 0;
            }}
            body {{
                font-family: 'Helvetica Neue', Arial, sans-serif;
                margin: 0;
                padding: 0;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                height: 100vh;
                text-align: center;
                background: linear-gradient(135deg, #f5f7fa 0%, #e0e4ea 100%);
            }}
            .header-container {{
                background-color: white;
                padding: 4em 3em;
                border-radius: 12px;
                box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
                width: 80%;
                max-width: 800px;
                position: relative;
                overflow: hidden;
            }}
            .header-container::before {{
                content: "";
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 6px;
                background: linear-gradient(to right, #3498db, #2ecc71);
            }}
            .course-name {{
                font-size: 14pt;
                color: #7f8c8d;
                margin-bottom: 1em;
                text-transform: uppercase;
                letter-spacing: 2px;
            }}
            h1 {{
                font-size: 36pt;
                margin-bottom: 0.5em;
                color: #2c3e50;
                line-height: 1.2;
                position: relative;
                display: inline-block;
            }}
            h1::after {{
                content: "";
                position: absolute;
                bottom: -10px;
                left: 50%;
                transform: translateX(-50%);
                width: 60%;
                height: 3px;
                background: linear-gradient(to right, #3498db, #2ecc71);
                border-radius: 3px;
            }}
            .subtitle {{
                font-size: 16pt;
                color: #7f8c8d;
                margin-top: 1.5em;
                font-style: italic;
            }}
            .decoration {{
                position: absolute;
                border-radius: 50%;
                background: radial-gradient(circle, rgba(52, 152, 219, 0.05) 0%, rgba(46, 204, 113, 0.02) 70%);
                z-index: 0;
            }}
            .decoration-1 {{
                width: 300px;
                height: 300px;
                bottom: -150px;
                right: -100px;
            }}
            .decoration-2 {{
                width: 200px;
                height: 200px;
                top: -100px;
                left: -50px;
            }}
        </style>
    </head>
    <body>
        <div class="header-container">
            <div class="decoration decoration-1"></div>
            <div class="decoration decoration-2"></div>
            {course_html}
            <h1>{section_title}</h1>
            <div class="subtitle">Module Resources</div>
        </div>
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
