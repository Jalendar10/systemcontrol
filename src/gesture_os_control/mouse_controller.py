"""Mouse control from hand state."""

from __future__ import annotations

import time
from typing import Any

import pyautogui

pyautogui.FAILSAFE = False


class MouseController:
    """Converts continuous hand state into pointer actions."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        cfg = config or {}
        self.enabled = bool(cfg.get("enabled", True))
        self.pointer_gestures = set(cfg.get("pointer_gestures", ["point", "pinch", "two_finger"]))
        self.consumed_gestures = set(
            cfg.get("consume_gestures", ["point", "pinch", "two_finger"])
        )
        self.left_click_gesture = str(cfg.get("left_click_gesture", "pinch"))
        self.scroll_gesture = str(cfg.get("scroll_gesture", "two_finger"))
        self.drag_hold_ms = float(cfg.get("drag_hold_ms", 320.0))
        self.click_max_tap_ms = float(cfg.get("click_max_tap_ms", 260.0))
        self.move_speed = float(cfg.get("move_speed", 1.6))
        self.smoothing = float(cfg.get("smoothing", 0.35))
        self.deadzone = float(cfg.get("deadzone", 0.008))
        self.scroll_scale = float(cfg.get("scroll_scale", 2200.0))

        screen_w, screen_h = pyautogui.size()
        self._screen_w = int(screen_w)
        self._screen_h = int(screen_h)

        self._smooth_x = 0.5
        self._smooth_y = 0.5
        self._pinch_started_at = 0.0
        self._pinch_prev = False
        self._dragging = False
        self._last_scroll_y: float | None = None

    def reset(self) -> None:
        if self._dragging:
            pyautogui.mouseUp()
        self._dragging = False
        self._pinch_prev = False
        self._pinch_started_at = 0.0
        self._last_scroll_y = None

    def update(self, state: dict[str, Any], active: bool = True) -> str | None:
        if not self.enabled or not active:
            self.reset()
            return None

        if not state.get("hand_present"):
            self.reset()
            return None

        gesture = state.get("gesture")
        result: str | None = None

        if gesture in self.pointer_gestures:
            index_tip = state.get("index_tip")
            if index_tip:
                self._move_cursor(index_tip[0], index_tip[1])

        if self.left_click_gesture == "pinch":
            result = self._handle_pinch_click_drag(bool(state.get("pinch")))

        if gesture == self.scroll_gesture:
            palm = state.get("palm_center")
            if palm:
                scroll_result = self._handle_scroll(palm[1])
                if scroll_result:
                    result = scroll_result
        else:
            self._last_scroll_y = None

        return result

    def _move_cursor(self, nx: float, ny: float) -> None:
        nx = min(max(nx, 0.0), 1.0)
        ny = min(max(ny, 0.0), 1.0)

        target_x = self._smooth_x + (nx - self._smooth_x) * self.move_speed
        target_y = self._smooth_y + (ny - self._smooth_y) * self.move_speed
        target_x = min(max(target_x, 0.0), 1.0)
        target_y = min(max(target_y, 0.0), 1.0)

        dx = abs(target_x - self._smooth_x)
        dy = abs(target_y - self._smooth_y)
        if dx < self.deadzone and dy < self.deadzone:
            return

        self._smooth_x = self._smooth_x + (target_x - self._smooth_x) * self.smoothing
        self._smooth_y = self._smooth_y + (target_y - self._smooth_y) * self.smoothing

        px = int(self._smooth_x * (self._screen_w - 1))
        py = int(self._smooth_y * (self._screen_h - 1))
        pyautogui.moveTo(px, py, duration=0)

    def _handle_pinch_click_drag(self, pinch_now: bool) -> str | None:
        now = time.time()

        if pinch_now and not self._pinch_prev:
            self._pinch_started_at = now

        if pinch_now and not self._dragging and self._pinch_started_at > 0:
            hold_ms = (now - self._pinch_started_at) * 1000.0
            if hold_ms >= self.drag_hold_ms:
                pyautogui.mouseDown()
                self._dragging = True
                self._pinch_prev = pinch_now
                return "drag start"

        if not pinch_now and self._pinch_prev:
            hold_ms = (now - self._pinch_started_at) * 1000.0
            if self._dragging:
                pyautogui.mouseUp()
                self._dragging = False
                self._pinch_prev = pinch_now
                return "drag end"
            if hold_ms <= self.click_max_tap_ms:
                pyautogui.click()
                self._pinch_prev = pinch_now
                return "left click"

        self._pinch_prev = pinch_now
        if not pinch_now:
            self._pinch_started_at = 0.0
        return None

    def _handle_scroll(self, palm_y: float) -> str | None:
        if self._last_scroll_y is None:
            self._last_scroll_y = palm_y
            return None

        delta = self._last_scroll_y - palm_y
        self._last_scroll_y = palm_y

        if abs(delta) < 0.004:
            return None

        amount = int(delta * self.scroll_scale)
        if amount == 0:
            return None

        pyautogui.scroll(amount)
        return f"scroll {amount}"
