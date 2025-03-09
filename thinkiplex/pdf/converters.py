"""
Converters for different file types to PDF.

This module provides functions to convert various file types to PDF format.
"""

import io
import os
import tempfile
from pathlib import Path
from typing import Optional, Tuple, Union

import markdown
import PyPDF2
from weasyprint import HTML

from ..utils.logging import get_logger

logger = get_logger()


def normalize_pdf_page_size(
    pdf_file: Union[str, Path], 
    output_file: Optional[Union[str, Path]] = None,
    target_size: Tuple[float, float] = (8.5*72, 11*72),  # Letter size in points
    preserve_aspect_ratio: bool = True,
    standard_sizes: bool = True
) -> Path:
    """
    Normalize the page size of a PDF file to make all pages consistent.
    
    Args:
        pdf_file: Path to the PDF file
        output_file: Path to save the normalized PDF file (optional)
        target_size: Target page size in points (width, height)
        preserve_aspect_ratio: Whether to preserve aspect ratio when resizing
        standard_sizes: Whether to detect and preserve standard paper sizes
        
    Returns:
        Path to the normalized PDF file
    """
    pdf_file = Path(pdf_file)
    
    if not pdf_file.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_file}")
    
    # If output file is not specified, use a temporary file
    if output_file is None:
        fd, output_file = tempfile.mkstemp(suffix=".pdf")
        os.close(fd)
    else:
        output_file = Path(output_file)
    
    # Standard paper sizes in points (width, height)
    standard_paper_sizes = {
        # US sizes
        'letter': (8.5*72, 11*72),        # 8.5 x 11 inches
        'legal': (8.5*72, 14*72),         # 8.5 x 14 inches
        'tabloid': (11*72, 17*72),        # 11 x 17 inches
        # ISO A sizes
        'a4': (595, 842),                 # 210 x 297 mm
        'a3': (842, 1190),                # 297 x 420 mm
        'a5': (420, 595),                 # 148 x 210 mm
    }
        
    try:
        # Open the input PDF
        with open(pdf_file, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            writer = PyPDF2.PdfWriter()
            
            # Process each page
            for page in reader.pages:
                # Get the current page size
                current_size = (page.mediabox.width, page.mediabox.height)
                current_width, current_height = current_size
                
                # Check if this is a standard paper size (or its rotated version)
                detected_paper_size = None
                if standard_sizes:
                    for paper_name, (std_width, std_height) in standard_paper_sizes.items():
                        # Check both orientations with some tolerance (1%)
                        if (abs(current_width - std_width) / std_width <= 0.01 and
                            abs(current_height - std_height) / std_height <= 0.01):
                            detected_paper_size = (std_width, std_height)
                            break
                        # Check rotated orientation
                        if (abs(current_width - std_height) / std_height <= 0.01 and
                            abs(current_height - std_width) / std_width <= 0.01):
                            detected_paper_size = (std_height, std_width)
                            break
                
                # If it's a standard paper size and it's already the target size
                target_width, target_height = target_size
                if detected_paper_size and abs(detected_paper_size[0] - target_width) <= 0.01 * target_width and abs(detected_paper_size[1] - target_height) <= 0.01 * target_height:
                    # Already the target size, keep as is
                    writer.add_page(page)
                    continue
                
                # If it's a different standard paper size but we want to preserve it
                if detected_paper_size and standard_sizes:
                    # We'll keep this page at its original size
                    writer.add_page(page)
                    continue

                # Determine if we need to create a new page
                # If the page size is close to the target size (within 5%), keep it as is
                width_diff = abs(current_width - target_width) / target_width
                height_diff = abs(current_height - target_height) / target_height
                
                if width_diff <= 0.05 and height_diff <= 0.05:
                    # Page size is close enough to target, keep as is
                    writer.add_page(page)
                else:
                    # Create a new page with the target size
                    new_page = PyPDF2.PageObject.create_blank_page(
                        width=target_width,
                        height=target_height
                    )
                    
                    # Scale the content to fit the new page
                    if preserve_aspect_ratio:
                        # Calculate scaling factor (smaller of width/height ratios)
                        scale_x = target_width / current_width
                        scale_y = target_height / current_height
                        scale = min(scale_x, scale_y) * 0.95  # 95% to leave a small margin
                        
                        # Calculate position to center the content
                        x_offset = (target_width - current_width * scale) / 2
                        y_offset = (target_height - current_height * scale) / 2
                    else:
                        # Stretch to fill (not preserving aspect ratio)
                        scale_x = target_width / current_width * 0.95
                        scale_y = target_height / current_height * 0.95
                        x_offset = target_width * 0.025
                        y_offset = target_height * 0.025
                        
                        # Use separate scaling for x and y
                        new_page.merge_page(page)
                        writer.add_page(new_page)
                        continue
                    
                    # Merge the content with preserved aspect ratio
                    new_page.merge_transformed_page(
                        page,
                        PyPDF2.Transformation().scale(scale).translate(x_offset, y_offset)
                    )
                    
                    writer.add_page(new_page)
            
            # Write the output PDF
            with open(output_file, 'wb') as out_f:
                writer.write(out_f)
            
            logger.info(f"Normalized PDF page size: {output_file}")
            return Path(output_file)
            
    except Exception as e:
        logger.error(f"Error normalizing PDF page size: {e}")
        if output_file != pdf_file:
            # If we were creating a new file and there was an error, just return the original
            return pdf_file


def convert_markdown_to_pdf(
    markdown_file: Union[str, Path], output_file: Optional[Union[str, Path]] = None
) -> Path:
    """
    Convert a markdown file to PDF.

    Args:
        markdown_file: Path to the markdown file
        output_file: Path to save the PDF file (optional)

    Returns:
        Path to the generated PDF file
    """
    markdown_file = Path(markdown_file)

    if not markdown_file.exists():
        raise FileNotFoundError(f"Markdown file not found: {markdown_file}")

    # If output file is not specified, use the same name with .pdf extension
    if output_file is None:
        output_file = markdown_file.with_suffix(".pdf")
    else:
        output_file = Path(output_file)

    # Read markdown content
    with open(markdown_file, "r", encoding="utf-8") as f:
        md_content = f.read()

    # Convert markdown to HTML
    html_content = markdown.markdown(
        md_content,
        extensions=[
            "markdown.extensions.tables",
            "markdown.extensions.fenced_code",
            "markdown.extensions.toc",
            "markdown.extensions.nl2br",
        ],
    )

    # Add basic styling
    styled_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>{markdown_file.stem}</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                margin: 2em;
                font-size: 12pt;
            }}
            h1, h2, h3, h4, h5, h6 {{
                margin-top: 1.5em;
                margin-bottom: 0.5em;
                page-break-after: avoid;
            }}
            h1 {{
                font-size: 24pt;
                border-bottom: 1px solid #ddd;
                padding-bottom: 0.3em;
            }}
            h2 {{
                font-size: 20pt;
                border-bottom: 1px solid #eee;
                padding-bottom: 0.2em;
            }}
            h3 {{ font-size: 16pt; }}
            h4 {{ font-size: 14pt; }}
            p, ul, ol, table {{
                margin-bottom: 1em;
            }}
            pre {{
                background-color: #f5f5f5;
                padding: 1em;
                border-radius: 5px;
                overflow-x: auto;
                font-size: 10pt;
            }}
            code {{
                background-color: #f5f5f5;
                padding: 0.2em 0.4em;
                border-radius: 3px;
                font-size: 10pt;
            }}
            blockquote {{
                border-left: 4px solid #ddd;
                padding-left: 1em;
                color: #666;
                margin-left: 0;
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
            }}
            table, th, td {{
                border: 1px solid #ddd;
            }}
            th, td {{
                padding: 0.5em;
                text-align: left;
            }}
            th {{
                background-color: #f5f5f5;
            }}
            img {{
                max-width: 100%;
                height: auto;
            }}
            @page {{
                size: letter;
                margin: 2cm;
                @top-center {{
                    content: "{markdown_file.stem}";
                    font-size: 9pt;
                    color: #7f8c8d;
                    font-style: italic;
                    border-bottom: 1px solid #ecf0f1;
                    padding-bottom: 0.3em;
                    margin-bottom: 1em;
                    font-family: Arial, sans-serif;
                }}
                @bottom-center {{
                    content: counter(page);
                    font-size: 10pt;
                    font-family: Arial, sans-serif;
                }}
                @bottom-right {{
                    content: "Generated with ThinkiPlex";
                    font-size: 8pt;
                    color: #95a5a6;
                    font-family: Arial, sans-serif;
                }}
            }}
        </style>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """

    # Convert HTML to PDF
    try:
        HTML(string=styled_html).write_pdf(output_file)
        logger.info(f"Converted markdown to PDF: {output_file}")
        return output_file
    except Exception as e:
        logger.error(f"Error converting markdown to PDF: {e}")
        raise


def convert_html_to_pdf(
    html_file: Union[str, Path], output_file: Optional[Union[str, Path]] = None
) -> Path:
    """
    Convert an HTML file to PDF.

    Args:
        html_file: Path to the HTML file
        output_file: Path to save the PDF file (optional)

    Returns:
        Path to the generated PDF file
    """
    html_file = Path(html_file)

    if not html_file.exists():
        raise FileNotFoundError(f"HTML file not found: {html_file}")

    # If output file is not specified, use the same name with .pdf extension
    if output_file is None:
        output_file = html_file.with_suffix(".pdf")
    else:
        output_file = Path(output_file)

    # Read HTML content
    with open(html_file, "r", encoding="utf-8") as f:
        html_content = f.read()

    # Create a simple HTML wrapper with styling
    styled_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>{html_file.stem}</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                margin: 2em;
                font-size: 12pt;
            }}
            h1, h2, h3, h4, h5, h6 {{
                margin-top: 1.5em;
                margin-bottom: 0.5em;
            }}
            p, ul, ol, table {{
                margin-bottom: 1em;
            }}
            img {{
                max-width: 100%;
                height: auto;
            }}
            @page {{
                size: letter;
                margin: 2cm;
                @top-center {{
                    content: "{html_file.stem}";
                    font-size: 9pt;
                    color: #7f8c8d;
                    font-style: italic;
                    border-bottom: 1px solid #ecf0f1;
                    padding-bottom: 0.3em;
                    margin-bottom: 1em;
                    font-family: Arial, sans-serif;
                }}
                @bottom-center {{
                    content: counter(page);
                    font-size: 10pt;
                    font-family: Arial, sans-serif;
                }}
                @bottom-right {{
                    content: "Generated with ThinkiPlex";
                    font-size: 8pt;
                    color: #95a5a6;
                    font-family: Arial, sans-serif;
                }}
            }}
        </style>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """

    # Convert HTML to PDF
    try:
        HTML(string=styled_html).write_pdf(output_file)
        logger.info(f"Converted HTML to PDF: {output_file}")
        return output_file
    except Exception as e:
        logger.error(f"Error converting HTML to PDF: {e}")
        raise


def convert_text_to_pdf(
    text_file: Union[str, Path], output_file: Optional[Union[str, Path]] = None
) -> Path:
    """
    Convert a text file to PDF.

    Args:
        text_file: Path to the text file
        output_file: Path to save the PDF file (optional)

    Returns:
        Path to the generated PDF file
    """
    text_file = Path(text_file)

    if not text_file.exists():
        raise FileNotFoundError(f"Text file not found: {text_file}")

    # If output file is not specified, use the same name with .pdf extension
    if output_file is None:
        output_file = text_file.with_suffix(".pdf")
    else:
        output_file = Path(output_file)

    # Read text content
    with open(text_file, "r", encoding="utf-8") as f:
        text_content = f.read()

    # Convert text to HTML
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>{text_file.stem}</title>
        <style>
            body {{
                font-family: monospace;
                line-height: 1.6;
                margin: 2em;
                white-space: pre-wrap;
                font-size: 11pt;
            }}
            @page {{
                size: letter;
                margin: 2cm;
                @top-center {{
                    content: "{text_file.stem}";
                    font-size: 9pt;
                    color: #7f8c8d;
                    font-style: italic;
                    border-bottom: 1px solid #ecf0f1;
                    padding-bottom: 0.3em;
                    margin-bottom: 1em;
                    font-family: Arial, sans-serif;
                }}
                @bottom-center {{
                    content: counter(page);
                    font-size: 10pt;
                    font-family: Arial, sans-serif;
                }}
                @bottom-right {{
                    content: "Generated with ThinkiPlex";
                    font-size: 8pt;
                    color: #95a5a6;
                    font-family: Arial, sans-serif;
                }}
            }}
        </style>
    </head>
    <body>
        {text_content.replace("<", "&lt;").replace(">", "&gt;")}
    </body>
    </html>
    """

    # Convert HTML to PDF
    try:
        HTML(string=html_content).write_pdf(output_file)
        logger.info(f"Converted text to PDF: {output_file}")
        return output_file
    except Exception as e:
        logger.error(f"Error converting text to PDF: {e}")
        raise


def merge_pdfs(pdf_files: list[Union[str, Path]], output_file: Union[str, Path]) -> Path:
    """
    Merge multiple PDF files into a single PDF.

    Args:
        pdf_files: List of paths to PDF files
        output_file: Path to save the merged PDF file

    Returns:
        Path to the merged PDF file
    """
    try:
        import PyPDF2
    except ImportError:
        logger.error("PyPDF2 is not installed. Please install it with 'pip install PyPDF2'")
        raise

    output_file = Path(output_file)

    # Create a PDF merger object
    merger = PyPDF2.PdfMerger()

    # Add each PDF file to the merger
    for pdf_file in pdf_files:
        pdf_file = Path(pdf_file)
        if not pdf_file.exists():
            logger.warning(f"PDF file not found: {pdf_file}")
            continue

        try:
            merger.append(str(pdf_file))
        except Exception as e:
            logger.warning(f"Error adding PDF file {pdf_file}: {e}")

    # Write the merged PDF to the output file
    try:
        merger.write(str(output_file))
        merger.close()
        logger.info(f"Merged {len(pdf_files)} PDF files into: {output_file}")
        return output_file
    except Exception as e:
        logger.error(f"Error merging PDF files: {e}")
        raise
