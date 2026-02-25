"""Configuration loading utilities."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULT_CONFIG: dict[str, Any] = {
    "project_name": "HandPilot",
    "camera_index": 0,
    "mirror": True,
    "draw_landmarks": True,
    "cooldown_ms": 850,
    "gesture_actions": {
        "swipe_left": {"type": "builtin", "name": "next_app", "cooldown_ms": 650},
        "swipe_right": {
            "type": "builtin",
            "name": "previous_app",
            "cooldown_ms": 650,
        },
        "open_palm": {"type": "builtin", "name": "browser_next_tab"},
        "fist": {"type": "builtin", "name": "browser_previous_tab"},
        "point": {"type": "builtin", "name": "close_tab"},
        "peace": {
            "type": "command",
            "command": {
                "mac": "open -a Calculator",
                "windows": "start calc",
                "linux": "gnome-calculator",
            },
        },
        "pinch": {
            "type": "builtin",
            "name": "toggle_control",
            "cooldown_ms": 1200,
        },
    },
}


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            merged[key] = _deep_merge(base[key], value)
        else:
            merged[key] = value
    return merged


def load_config(path: str | Path) -> dict[str, Any]:
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(
            f"Config file not found: {config_path}. Copy config/gestures.example.json to your own file first."
        )

    with config_path.open("r", encoding="utf-8") as handle:
        user_config = json.load(handle)

    config = _deep_merge(DEFAULT_CONFIG, user_config)

    if not isinstance(config.get("gesture_actions"), dict):
        raise ValueError("`gesture_actions` must be a JSON object")

    return config
