"""
File processing utilities for data feeds.
Handles txt, csv, and xlsx file parsing and content extraction.
"""
from __future__ import annotations

import csv
import io
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB in bytes


def validate_file_size(file_size: int) -> tuple[bool, Optional[str]]:
    """
    Validate that file size is within acceptable limits.
    
    Args:
        file_size: Size of file in bytes
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if file_size > MAX_FILE_SIZE:
        size_mb = file_size / (1024 * 1024)
        return False, (
            f"File size ({size_mb:.2f} MB) exceeds the 100 MB limit. "
            "Please upload larger files to the designated SharePoint location."
        )
    return True, None


def process_txt(file_data: bytes, filename: str = "upload.txt") -> Dict[str, Any]:
    """
    Process a text file and extract content.
    
    Args:
        file_data: Raw file bytes
        filename: Original filename
        
    Returns:
        Dictionary with content, metadata, and processing info
    """
    try:
        # Try different encodings
        content = None
        encoding_used = None
        
        for encoding in ['utf-8', 'latin-1', 'cp1252', 'ascii']:
            try:
                content = file_data.decode(encoding)
                encoding_used = encoding
                break
            except UnicodeDecodeError:
                continue
        
        if content is None:
            raise ValueError("Unable to decode file with supported encodings")
        
        # Extract metadata
        line_count = len(content.splitlines())
        word_count = len(content.split())
        char_count = len(content)
        
        return {
            "content": content,
            "processed_content": content.strip(),
            "metadata": {
                "filename": filename,
                "encoding": encoding_used,
                "line_count": line_count,
                "word_count": word_count,
                "char_count": char_count,
                "file_type": "txt",
            },
            "success": True,
        }
        
    except Exception as exc:
        logger.error(f"Error processing txt file: {exc}", exc_info=True)
        return {
            "content": "",
            "processed_content": "",
            "metadata": {"error": str(exc), "file_type": "txt"},
            "success": False,
        }


def process_csv(file_data: bytes, filename: str = "upload.csv") -> Dict[str, Any]:
    """
    Process a CSV file and extract structured content.
    
    Args:
        file_data: Raw file bytes
        filename: Original filename
        
    Returns:
        Dictionary with content, metadata, row count, and columns
    """
    try:
        # Decode content
        content = None
        encoding_used = None
        
        for encoding in ['utf-8', 'latin-1', 'cp1252']:
            try:
                content = file_data.decode(encoding)
                encoding_used = encoding
                break
            except UnicodeDecodeError:
                continue
        
        if content is None:
            raise ValueError("Unable to decode CSV file")
        
        # Parse CSV
        csv_reader = csv.reader(io.StringIO(content))
        rows = list(csv_reader)
        
        if not rows:
            raise ValueError("CSV file is empty")
        
        # Extract headers and data
        headers = rows[0] if rows else []
        data_rows = rows[1:] if len(rows) > 1 else []
        
        # Create text representation for embedding
        text_parts = []
        text_parts.append(f"CSV file with columns: {', '.join(headers)}")
        
        # Add sample rows (first 5 for context)
        sample_size = min(5, len(data_rows))
        for i, row in enumerate(data_rows[:sample_size]):
            row_text = " | ".join(str(cell) for cell in row)
            text_parts.append(f"Row {i+1}: {row_text}")
        
        if len(data_rows) > sample_size:
            text_parts.append(f"... and {len(data_rows) - sample_size} more rows")
        
        processed_content = "\n".join(text_parts)
        
        return {
            "content": content,
            "processed_content": processed_content,
            "metadata": {
                "filename": filename,
                "encoding": encoding_used,
                "row_count": len(data_rows),
                "total_rows": len(rows),
                "column_count": len(headers),
                "columns": headers,
                "file_type": "csv",
            },
            "rows": data_rows,
            "columns": headers,
            "success": True,
        }
        
    except Exception as exc:
        logger.error(f"Error processing CSV file: {exc}", exc_info=True)
        return {
            "content": "",
            "processed_content": "",
            "metadata": {"error": str(exc), "file_type": "csv"},
            "success": False,
        }


def process_xlsx(file_data: bytes, filename: str = "upload.xlsx") -> Dict[str, Any]:
    """
    Process an Excel file and extract structured content.
    
    Args:
        file_data: Raw file bytes
        filename: Original filename
        
    Returns:
        Dictionary with content, metadata, row count, and columns
    """
    try:
        # Try to import openpyxl
        try:
            from openpyxl import load_workbook
        except ImportError:
            logger.warning("openpyxl not installed, cannot process xlsx files")
            return {
                "content": "",
                "processed_content": "",
                "metadata": {
                    "error": "Excel processing requires openpyxl package",
                    "file_type": "xlsx",
                },
                "success": False,
            }
        
        # Load workbook from bytes
        workbook = load_workbook(filename=io.BytesIO(file_data), read_only=True)
        
        # Get active sheet
        sheet = workbook.active
        
        # Extract all rows
        rows = []
        for row in sheet.iter_rows(values_only=True):
            rows.append([str(cell) if cell is not None else "" for cell in row])
        
        if not rows:
            raise ValueError("Excel file is empty")
        
        # Extract headers and data
        headers = rows[0] if rows else []
        data_rows = rows[1:] if len(rows) > 1 else []
        
        # Create text representation
        text_parts = []
        text_parts.append(f"Excel file '{sheet.title}' with columns: {', '.join(headers)}")
        
        # Add sample rows
        sample_size = min(5, len(data_rows))
        for i, row in enumerate(data_rows[:sample_size]):
            row_text = " | ".join(str(cell) for cell in row)
            text_parts.append(f"Row {i+1}: {row_text}")
        
        if len(data_rows) > sample_size:
            text_parts.append(f"... and {len(data_rows) - sample_size} more rows")
        
        processed_content = "\n".join(text_parts)
        
        # Convert to CSV-like string for storage
        csv_content = io.StringIO()
        csv_writer = csv.writer(csv_content)
        csv_writer.writerows(rows)
        content = csv_content.getvalue()
        
        workbook.close()
        
        return {
            "content": content,
            "processed_content": processed_content,
            "metadata": {
                "filename": filename,
                "sheet_name": sheet.title,
                "row_count": len(data_rows),
                "total_rows": len(rows),
                "column_count": len(headers),
                "columns": headers,
                "file_type": "xlsx",
            },
            "rows": data_rows,
            "columns": headers,
            "success": True,
        }
        
    except Exception as exc:
        logger.error(f"Error processing Excel file: {exc}", exc_info=True)
        return {
            "content": "",
            "processed_content": "",
            "metadata": {"error": str(exc), "file_type": "xlsx"},
            "success": False,
        }


def process_file(file_data: bytes, filename: str, file_type: str) -> Dict[str, Any]:
    """
    Process a file based on its type.
    
    Args:
        file_data: Raw file bytes
        filename: Original filename
        file_type: Type of file (txt, csv, xlsx)
        
    Returns:
        Processing result dictionary
    """
    # Validate file size
    is_valid, error_msg = validate_file_size(len(file_data))
    if not is_valid:
        return {
            "content": "",
            "processed_content": "",
            "metadata": {"error": error_msg, "file_type": file_type},
            "success": False,
        }
    
    # Process based on type
    file_type = file_type.lower()
    
    if file_type == "txt":
        return process_txt(file_data, filename)
    elif file_type == "csv":
        return process_csv(file_data, filename)
    elif file_type == "xlsx":
        return process_xlsx(file_data, filename)
    else:
        return {
            "content": "",
            "processed_content": "",
            "metadata": {
                "error": f"Unsupported file type: {file_type}",
                "file_type": file_type,
            },
            "success": False,
        }


def process_text_input(text: str, name: str = "Text Input") -> Dict[str, Any]:
    """
    Process direct text input.
    
    Args:
        text: Input text
        name: Name/title for the input
        
    Returns:
        Processing result dictionary
    """
    try:
        if not text or not text.strip():
            return {
                "content": "",
                "processed_content": "",
                "metadata": {"error": "Text input is empty", "file_type": "text_input"},
                "success": False,
            }
        
        # Calculate metadata
        line_count = len(text.splitlines())
        word_count = len(text.split())
        char_count = len(text)
        
        return {
            "content": text,
            "processed_content": text.strip(),
            "metadata": {
                "name": name,
                "line_count": line_count,
                "word_count": word_count,
                "char_count": char_count,
                "file_type": "text_input",
            },
            "success": True,
        }
        
    except Exception as exc:
        logger.error(f"Error processing text input: {exc}", exc_info=True)
        return {
            "content": "",
            "processed_content": "",
            "metadata": {"error": str(exc), "file_type": "text_input"},
            "success": False,
        }

