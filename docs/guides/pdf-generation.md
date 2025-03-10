# PDF Generation Guide

ThinkiPlex includes a comprehensive PDF generation system that creates beautifully formatted course resource documents. This guide explains how to use and customize the PDF generation features.

## Overview

The PDF generator combines all available course resources (excluding audio and video files) into a single, well-organized PDF document featuring:

- Professional title page with course name and author
- Interactive table of contents with page numbers
- Module divider pages for clear content organization
- Page headers and footers with context information
- PDF bookmarks for easy navigation
- Consistent formatting and normalized page sizes

## Basic Usage

To generate a PDF for a course:

```bash
python -m thinkiplex --course course-id --pdf
```

You can also generate a PDF directly:

```bash
python -m thinkiplex --pdf-only course-id
```

## PDF Structure

The generated PDF will have the following structure:

1. **Title Page**: Displays the course name, author information, and generation date
2. **Table of Contents**: Interactive TOC with page numbers for all content
3. **Module Dividers**: Section header pages introduce each module
4. **Content**: All course resources organized by module

## PDF Metadata Handling

The generator uses several sources to gather metadata for the PDF:

1. Course title from:
   - Course JSON file (looks for `name` field in course data)
   - Configuration file 
   - Course directory name as fallback

2. Author information from:
   - Course JSON file (looks for `author` or `instructors` fields)
   - Blank if not available

3. Course image from:
   - `course_image.jpg` in the course directory
   - `cover.jpg`, `cover.png`, `thumbnail.jpg`, or `thumbnail.png` as alternatives

## Customization

You can customize the PDF generation by modifying the following files:

- `thinkiplex/pdf/formatter.py`: Styling and layout for title page, TOC, and dividers
- `thinkiplex/pdf/converters.py`: File type conversion and page formatting
- `thinkiplex/pdf/generator.py`: Overall PDF structure and organization

## Limitations

- Very large courses with many files may take time to process
- While common file types are supported, custom or unusual formats may be skipped
- Some complex formatting in original files may be simplified