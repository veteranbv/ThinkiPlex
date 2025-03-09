"""
Converters for different file types to PDF.

This module provides functions to convert various file types to PDF format.
"""

from pathlib import Path
from typing import Optional, Union

import markdown
from weasyprint import HTML

from ..utils.logging import get_logger

logger = get_logger()


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
                @bottom-center {{
                    content: counter(page);
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
                @bottom-center {{
                    content: counter(page);
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
                @bottom-center {{
                    content: counter(page);
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
