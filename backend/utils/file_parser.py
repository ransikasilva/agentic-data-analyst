"""
File parsing utilities for CSV and Excel files.

This module handles ingestion of uploaded data files and converts them
to pandas DataFrames with comprehensive error handling.
"""

import pandas as pd
from pathlib import Path
from typing import Dict, Any, Tuple, List
from loguru import logger


class FileParserError(Exception):
    """Custom exception for file parsing errors."""
    pass


def parse_file(file_path: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Parse a CSV or Excel file into a pandas DataFrame with metadata.

    Args:
        file_path: Absolute path to the file to parse

    Returns:
        Tuple of (DataFrame, metadata_dict) where metadata includes:
        - shape: (rows, columns)
        - columns: list of column names
        - dtypes: dict mapping column names to data types
        - null_counts: dict mapping column names to null counts
        - preview: first 5 rows as dict

    Raises:
        FileParserError: If file cannot be parsed or is invalid
    """
    path = Path(file_path)

    # Validate file exists
    if not path.exists():
        raise FileParserError(f"File not found: {file_path}")

    # Validate file size (max 50MB)
    max_size_mb = 50
    file_size_mb = path.stat().st_size / (1024 * 1024)
    if file_size_mb > max_size_mb:
        raise FileParserError(
            f"File size ({file_size_mb:.2f}MB) exceeds maximum allowed size ({max_size_mb}MB)"
        )

    # Parse based on file extension
    suffix = path.suffix.lower()

    try:
        if suffix == ".csv":
            df = _parse_csv(file_path)
        elif suffix in [".xlsx", ".xls"]:
            df = _parse_excel(file_path)
        else:
            raise FileParserError(
                f"Unsupported file format: {suffix}. Only .csv, .xlsx, and .xls are supported."
            )
    except FileParserError:
        raise
    except Exception as e:
        logger.error(f"Error parsing file {file_path}: {e}")
        raise FileParserError(f"Failed to parse file: {str(e)}")

    # Validate DataFrame is not empty
    if df.empty:
        raise FileParserError("File is empty or contains no valid data")

    # Generate metadata
    metadata = _generate_metadata(df)

    logger.info(f"Successfully parsed {file_path}: shape={df.shape}")
    return df, metadata


def _parse_csv(file_path: str) -> pd.DataFrame:
    """
    Parse a CSV file with multiple encoding attempts.

    Args:
        file_path: Path to CSV file

    Returns:
        Parsed DataFrame

    Raises:
        FileParserError: If CSV cannot be parsed with any encoding
    """
    encodings = ["utf-8", "latin-1", "iso-8859-1", "cp1252"]

    for encoding in encodings:
        try:
            df = pd.read_csv(file_path, encoding=encoding)
            logger.debug(f"Successfully parsed CSV with encoding: {encoding}")
            return df
        except UnicodeDecodeError:
            continue
        except Exception as e:
            raise FileParserError(f"CSV parsing error: {str(e)}")

    raise FileParserError(
        "Failed to parse CSV with any supported encoding (utf-8, latin-1, iso-8859-1, cp1252)"
    )


def _parse_excel(file_path: str) -> pd.DataFrame:
    """
    Parse an Excel file (.xlsx or .xls).

    Args:
        file_path: Path to Excel file

    Returns:
        Parsed DataFrame from the first sheet

    Raises:
        FileParserError: If Excel file cannot be parsed
    """
    try:
        # Read first sheet by default
        df = pd.read_excel(file_path, sheet_name=0, engine="openpyxl")
        return df
    except Exception as e:
        raise FileParserError(f"Excel parsing error: {str(e)}")


def _generate_metadata(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate comprehensive metadata about a DataFrame.

    Args:
        df: Input DataFrame

    Returns:
        Dictionary containing shape, columns, dtypes, null counts, and preview
    """
    # Convert dtypes to string representation
    dtypes_dict = {col: str(dtype) for col, dtype in df.dtypes.items()}

    # Get null counts
    null_counts = df.isnull().sum().to_dict()

    # Get preview (first 5 rows)
    preview_rows = df.head(5).to_dict(orient="records")

    metadata = {
        "shape": list(df.shape),  # [rows, columns]
        "columns": df.columns.tolist(),
        "dtypes": dtypes_dict,
        "null_counts": null_counts,
        "preview": preview_rows,
    }

    return metadata


def get_dataset_schema_summary(df: pd.DataFrame) -> str:
    """
    Generate a human-readable schema summary for LLM consumption.

    This is used by the planner node to understand the dataset structure.

    Args:
        df: Input DataFrame

    Returns:
        Formatted string describing the dataset schema
    """
    lines: List[str] = []

    lines.append(f"Dataset Shape: {df.shape[0]} rows × {df.shape[1]} columns")
    lines.append("\nColumns:")

    for col in df.columns:
        dtype = df[col].dtype
        null_count = df[col].isnull().sum()
        null_pct = (null_count / len(df)) * 100

        # Get sample values (non-null, unique, first 3)
        sample_values = df[col].dropna().unique()[:3].tolist()
        sample_str = ", ".join(str(v) for v in sample_values)

        lines.append(
            f"  - {col} ({dtype}): {null_count} nulls ({null_pct:.1f}%), "
            f"sample values: [{sample_str}]"
        )

    lines.append(f"\nFirst 5 rows:\n{df.head(5).to_string()}")

    return "\n".join(lines)
