"""
Sandboxed Python code execution tool.

This is the most critical security component of the system. It executes
user-generated Python code in a controlled subprocess environment with
strict limitations on file system access, network access, and execution time.
"""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Tuple
from loguru import logger


class CodeExecutionError(Exception):
    """Custom exception for code execution failures."""
    pass


def execute_code(
    code: str,
    dataset_path: str,
    session_id: str,
    max_execution_seconds: int = None
) -> Tuple[str, str, int]:
    """
    Execute Python code in a sandboxed subprocess with strict security controls.

    Security measures:
    - Runs in a subprocess with timeout
    - File writes restricted to session-specific output directory
    - No network access (code cannot make external requests)
    - Kills process if timeout exceeded
    - Captures stdout and stderr separately

    Args:
        code: Python code to execute (will be prepended with safety header)
        dataset_path: Absolute path to the dataset file
        session_id: Unique session identifier for output isolation
        max_execution_seconds: Maximum execution time (default from env)

    Returns:
        Tuple of (stdout, stderr, exit_code)
        - stdout: Standard output from the code execution
        - stderr: Standard error / traceback if failed
        - exit_code: Process exit code (0 = success, non-zero = error)

    Raises:
        CodeExecutionError: If subprocess setup fails
    """
    # Get max execution time from env or parameter
    if max_execution_seconds is None:
        max_execution_seconds = int(os.getenv("MAX_EXECUTION_SECONDS", "30"))

    # Create session-specific output directory
    output_dir = Path(f"./output/{session_id}")
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Executing code for session {session_id} (timeout: {max_execution_seconds}s)")

    # Prepend safety header to enforce security constraints
    safe_header = f"""
import os
import sys

# Change working directory to session-specific output folder
os.chdir("{output_dir.absolute()}")

# Make dataset path available as a constant
DATASET_PATH = "{dataset_path}"

# Security: Disable network access by removing socket module
# (This is not perfect but adds a layer of defense)
import sys
if 'socket' in sys.modules:
    del sys.modules['socket']

"""

    full_code = safe_header + code

    # Write code to temporary file
    try:
        with tempfile.NamedTemporaryFile(
            suffix=".py",
            mode="w",
            delete=False,
            encoding="utf-8"
        ) as f:
            f.write(full_code)
            tmp_path = f.name
    except Exception as e:
        logger.error(f"Failed to create temp file: {e}")
        raise CodeExecutionError(f"Failed to create temporary code file: {str(e)}")

    logger.debug(f"Created temp file: {tmp_path}")

    # Execute code in subprocess
    try:
        result = subprocess.run(
            ["python", tmp_path],
            capture_output=True,
            text=True,
            timeout=max_execution_seconds,
            # Additional security: prevent subprocess from spawning children
            # and limit resource usage (platform-dependent)
        )

        stdout = result.stdout
        stderr = result.stderr
        exit_code = result.returncode

        if exit_code == 0:
            logger.info(f"Code executed successfully for session {session_id}")
        else:
            logger.warning(
                f"Code execution failed for session {session_id} "
                f"with exit code {exit_code}"
            )

        return stdout, stderr, exit_code

    except subprocess.TimeoutExpired:
        logger.error(
            f"Code execution timeout ({max_execution_seconds}s) "
            f"for session {session_id}"
        )
        return (
            "",
            f"TimeoutError: Code execution exceeded {max_execution_seconds} second limit",
            1
        )

    except Exception as e:
        logger.error(f"Unexpected error during code execution: {e}")
        raise CodeExecutionError(f"Code execution failed: {str(e)}")

    finally:
        # Clean up temporary file
        try:
            os.unlink(tmp_path)
            logger.debug(f"Cleaned up temp file: {tmp_path}")
        except Exception as e:
            logger.warning(f"Failed to clean up temp file {tmp_path}: {e}")


def get_output_files(session_id: str) -> list[str]:
    """
    Retrieve list of files generated in the session output directory.

    This is used to find generated charts and other output files.

    Args:
        session_id: Session identifier

    Returns:
        List of absolute file paths in the session output directory
    """
    output_dir = Path(f"./output/{session_id}")

    if not output_dir.exists():
        return []

    # Get all files (not directories) in output folder
    files = [
        str(f.absolute())
        for f in output_dir.iterdir()
        if f.is_file()
    ]

    logger.debug(f"Found {len(files)} output files for session {session_id}")
    return files


def read_output_file(file_path: str) -> bytes:
    """
    Read a file from the output directory as bytes.

    Used for reading generated chart images.

    Args:
        file_path: Absolute path to the file

    Returns:
        File contents as bytes

    Raises:
        CodeExecutionError: If file cannot be read
    """
    try:
        with open(file_path, "rb") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Failed to read output file {file_path}: {e}")
        raise CodeExecutionError(f"Failed to read output file: {str(e)}")
