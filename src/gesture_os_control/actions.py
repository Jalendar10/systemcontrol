"""OS action execution for gestures."""

from __future__ import annotations

import platform
import subprocess
from typing import Any

import pyautogui

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0


class ActionExecutor:
    """Executes built-in and custom action definitions."""

    def __init__(self) -> None:
        system_name = platform.system().lower()
        if "darwin" in system_name:
            self.os_key = "mac"
        elif "windows" in system_name:
            self.os_key = "windows"
        else:
            self.os_key = "linux"

    def execute(self, action_def: dict[str, Any]) -> str:
        action_type = action_def.get("type", "builtin")

        if action_type == "builtin":
            action_name = action_def.get("name", "")
            return self._execute_builtin(action_name)

        if action_type == "hotkey":
            keys = self._resolve_for_os(action_def.get("keys"))
            if not keys:
                return "hotkey ignored (no keys configured)"
            self._send_hotkey(keys)
            return f"hotkey: {' + '.join(keys)}"

        if action_type == "command":
            command = self._resolve_for_os(action_def.get("command"))
            if not command:
                return "command ignored (not configured)"
            subprocess.Popen(command, shell=True)
            return f"command: {command}"

        if action_type == "text":
            text = action_def.get("value", "")
            if text:
                pyautogui.typewrite(text)
                return f"typed: {text}"
            return "text ignored (empty value)"

        return f"unknown action type: {action_type}"

    def _execute_builtin(self, name: str) -> str:
        if name == "next_app":
            keys = ["command", "tab"] if self.os_key == "mac" else ["alt", "tab"]
            self._send_hotkey(keys)
            return "next app"

        if name == "previous_app":
            keys = (
                ["command", "shift", "tab"]
                if self.os_key == "mac"
                else ["alt", "shift", "tab"]
            )
            self._send_hotkey(keys)
            return "previous app"

        if name == "browser_next_tab":
            keys = ["ctrl", "tab"]
            self._send_hotkey(keys)
            return "browser next tab"

        if name == "browser_previous_tab":
            keys = ["ctrl", "shift", "tab"]
            self._send_hotkey(keys)
            return "browser previous tab"

        if name == "close_tab":
            keys = ["command", "w"] if self.os_key == "mac" else ["ctrl", "w"]
            self._send_hotkey(keys)
            return "close tab"

        if name == "reopen_tab":
            keys = (
                ["command", "shift", "t"]
                if self.os_key == "mac"
                else ["ctrl", "shift", "t"]
            )
            self._send_hotkey(keys)
            return "reopen tab"

        if name == "volume_up":
            pyautogui.press("volumeup")
            return "volume up"

        if name == "volume_down":
            pyautogui.press("volumedown")
            return "volume down"

        if name == "mute":
            pyautogui.press("volumemute")
            return "toggle mute"

        return f"unknown builtin action: {name}"

    def _resolve_for_os(self, value: Any) -> Any:
        if isinstance(value, dict):
            return value.get(self.os_key) or value.get("default")
        return value

    def _send_hotkey(self, keys: list[str] | tuple[str, ...]) -> None:
        pyautogui.hotkey(*keys)
