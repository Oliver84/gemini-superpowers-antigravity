#!/usr/bin/env python3
"""Configuration manager for Superpowers."""

import json
import os
from pathlib import Path
from typing import Any, Dict


def find_agent_root(start: Path) -> Path:
    """Traverse upwards to find the .agent directory."""
    curr = start.resolve()
    for _ in range(10):
        if (curr / ".agent").exists():
            return curr / ".agent"
        if (curr / "skills").exists() and (curr.parent / ".agent").exists():
             return curr.parent / ".agent"
        if curr.parent == curr:
            break
        curr = curr.parent
    # Fallback to relative path if not found (e.g., during install)
    return Path(".agent")


def load_config(root_path: Path = None) -> Dict[str, Any]:
    """Load configuration from .agent/config.json."""
    if root_path is None:
        root_path = find_agent_root(Path.cwd())

    config_path = root_path / "config.json"

    if not config_path.exists():
        # Return default config
        return {"execution_backend": "gemini"}

    try:
        return json.loads(config_path.read_text(encoding="utf-8"))
    except Exception:
        return {"execution_backend": "gemini"}


def save_config(config: Dict[str, Any], root_path: Path = None) -> None:
    """Save configuration to .agent/config.json."""
    if root_path is None:
        root_path = find_agent_root(Path.cwd())

    config_path = root_path / "config.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)

    config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
