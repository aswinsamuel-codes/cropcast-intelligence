"""
Configuration loading for CropCast.

All file paths, the random seed, and experiment parameters come from
`configs/config.json` (or the file named by the CROPCAST_CONFIG environment
variable). Paths in the config are relative to the repository root.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = REPO_ROOT / "configs" / "config.json"


def load_config(path: str | os.PathLike | None = None) -> Dict[str, Any]:
    """Load the project configuration as a dict."""
    config_path = Path(path or os.environ.get("CROPCAST_CONFIG", DEFAULT_CONFIG))
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def resolve_path(relative: str) -> Path:
    """Resolve a config path relative to the repository root."""
    p = Path(relative)
    return p if p.is_absolute() else REPO_ROOT / p
