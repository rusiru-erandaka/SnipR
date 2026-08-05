from __future__ import annotations

import os
import shutil
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote, urlparse


def screenshots_dir() -> Path:
    """Return the desktop's screenshot folder without hard-coding a user name."""
    pictures = Path.home() / "Pictures"
    user_dirs = Path.home() / ".config" / "user-dirs.dirs"
    try:
        for line in user_dirs.read_text(encoding="utf-8").splitlines():
            if line.startswith("XDG_PICTURES_DIR="):
                value = line.split("=", 1)[1].strip().strip('"')
                pictures = Path(os.path.expandvars(value.replace("$HOME", str(Path.home()))))
                break
    except OSError:
        pass
    target = pictures / "Screenshots"
    target.mkdir(parents=True, exist_ok=True)
    return target


def unique_capture_path(directory: Path | None = None) -> Path:
    directory = directory or screenshots_dir()
    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    candidate = directory / f"Screenshot_{stamp}.png"
    index = 2
    while candidate.exists():
        candidate = directory / f"Screenshot_{stamp}_{index}.png"
        index += 1
    return candidate


def copy_portal_capture(uri: str) -> Path:
    parsed = urlparse(uri)
    if parsed.scheme != "file":
        raise ValueError("The screenshot portal returned an unsupported URI")
    source = Path(unquote(parsed.path))
    target = unique_capture_path()
    shutil.copy2(source, target)
    return target
