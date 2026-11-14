"""Safe atomic storage and file operations for Japan Deal Watcher."""

import json
import logging
import os
import shutil
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Union

logger = logging.getLogger(__name__)

def atomic_write_json(
    filepath: Union[Path, str],
    data: Any,
    indent: int = 2,
    ensure_ascii: bool = False
) -> Path:
    """
    Atomically writes data to a JSON file using a temporary file in the same
    directory and os.replace to guarantee atomic replacement and prevent corruption.
    """
    path = Path(filepath).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)

    timestamp = int(time.time() * 1000)
    pid = os.getpid()
    temp_file = path.parent / f".{path.name}.tmp.{pid}_{timestamp}"

    try:
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent, ensure_ascii=ensure_ascii)
            f.flush()
            os.fsync(f.fileno())

        os.replace(temp_file, path)
        return path
    except Exception as e:
        if temp_file.exists():
            try:
                temp_file.unlink()
            except OSError:
                pass
        logger.error(f"Failed to atomically write JSON to {path}: {e}")
        raise

def quarantine_corrupt_file(filepath: Union[Path, str], reason: str = "") -> Optional[Path]:
    """
    Preserves a corrupt file by moving it to <filename>.corrupt.<timestamp>.
    Prevents silent overwrites and data loss.
    """
    path = Path(filepath).resolve()
    if not path.exists():
        return None

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    quarantine_path = path.parent / f"{path.name}.corrupt.{timestamp}"
    try:
        shutil.move(str(path), str(quarantine_path))
        logger.warning(
            f"Quarantined corrupt file {path.name} -> {quarantine_path.name}. Reason: {reason}"
        )
        return quarantine_path
    except Exception as e:
        logger.error(f"Failed to quarantine corrupt file {path}: {e}")
        return None

def read_json_safe(
    filepath: Union[Path, str],
    default: Any = None,
    quarantine_corrupt: bool = True
) -> Any:
    """
    Safely reads JSON from disk. If the file is missing, returns default.
    If the file exists but is corrupt or invalid JSON, it is quarantined to
    preserve its data for recovery, and default is returned.
    """
    path = Path(filepath).resolve()
    if not path.exists():
        if callable(default):
            return default()
        return default

    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                raise ValueError("JSON file is empty")
            return json.loads(content)
    except Exception as e:
        logger.warning(f"Corrupt or invalid JSON file encountered at {path}: {e}")
        if quarantine_corrupt:
            quarantine_corrupt_file(path, reason=str(e))
        if callable(default):
            return default()
        return default
