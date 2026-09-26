"""
Temporary file and resource cleanup services for LegalLens.
Ensures temporary files are removed immediately after use and upon closing the app.
"""

from __future__ import annotations

import gc
import shutil
from pathlib import Path
from typing import Iterable

from app.core.settings import settings


def remove_path_safely(path: Path) -> bool:
    """Safely remove a file or directory with garbage collection retry on Windows."""
    try:
        if not path.exists():
            return False
        if path.is_file() or path.is_symlink():
            path.unlink(missing_ok=True)
            return True
        elif path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
            return True
    except Exception:
        gc.collect()
        try:
            if not path.exists():
                return False
            if path.is_file() or path.is_symlink():
                path.unlink(missing_ok=True)
                return True
            elif path.is_dir():
                shutil.rmtree(path, ignore_errors=True)
                return True
        except Exception:
            return False
    return False


def cleanup_directory(directory: Path) -> int:
    """Remove all contents inside a directory, returning count of removed items."""
    removed_count = 0
    if not directory.exists() or not directory.is_dir():
        return removed_count

    for item in list(directory.iterdir()):
        if remove_path_safely(item):
            removed_count += 1

    return removed_count


def cleanup_temp_files(directories: Iterable[Path] | None = None) -> int:
    """
    Remove all temporary files from upload_dir and output_dir immediately.
    Can be called on file extraction completion, app shutdown, process exit, or user request.
    """
    dirs = list(directories) if directories is not None else [settings.upload_dir, settings.output_dir]
    total_removed = 0
    for d in dirs:
        total_removed += cleanup_directory(d)
    return total_removed
