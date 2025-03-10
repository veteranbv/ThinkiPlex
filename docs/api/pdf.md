# PDF Generation API

The PDF generation module provides functionality for creating well-formatted PDF documents from course resources.

## PDFGenerator

::: thinkiplex.pdf.generator.PDFGenerator
    handler: python
    selection:
      members:
        - __init__
        - generate_course_pdf

## Formatting Utilities

::: thinkiplex.pdf.formatter
    handler: python
    selection:
      members:
        - create_cover_page
        - create_toc_page
        - create_section_header

## Conversion Utilities

::: thinkiplex.pdf.converters
    handler: python
    selection:
      members:
        - normalize_pdf_page_size
        - convert_markdown_to_pdf
        - convert_html_to_pdf
        - convert_text_to_pdf
        - merge_pdfs