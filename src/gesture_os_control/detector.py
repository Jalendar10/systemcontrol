"""Hand gesture detection with MediaPipe."""

from __future__ import annotations

import math
import time
from collections import deque
from typing import Any

import cv2
import mediapipe as mp


class GestureDetector:
    """Converts hand landmarks into simple gesture labels."""

    def __init__(
        self,
        min_detection_confidence: float = 0.7,
        min_tracking_confidence: float = 0.6,
    ) -> None:
        self._mp_hands = mp.solutions.hands
        self._hands = self._mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )
        self._drawer = mp.solutions.drawing_utils
        self._palm_history: deque[tuple[float, float, float]] = deque(maxlen=24)
        self._last_swipe_at = 0.0
        self._last_state = self._empty_state()

    @staticmethod
    def _empty_state() -> dict[str, Any]:
        return {
            "hand_present": False,
            "gesture": None,
            "index_tip": None,
            "palm_center": None,
            "pinch": False,
            "pinch_distance": 1.0,
            "fingers": {
                "thumb": False,
                "index": False,
                "middle": False,
                "ring": False,
                "pinky": False,
            },
        }

    def process(
        self, frame: Any, draw_landmarks: bool = True
    ) -> tuple[str | None, Any, dict[str, Any]]:
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = self._hands.process(rgb)

        if not result.multi_hand_landmarks:
            self._palm_history.clear()
            self._last_state = self._empty_state()
            return None, frame, self._last_state

        landmarks = result.multi_hand_landmarks[0]

        if draw_landmarks:
            self._drawer.draw_landmarks(
                frame,
                landmarks,
                self._mp_hands.HAND_CONNECTIONS,
            )

        gesture, state = self._classify_gesture(landmarks.landmark)
        state["gesture"] = gesture
        self._last_state = state
        return gesture, frame, state

    def _classify_gesture(self, lm: Any) -> tuple[str | None, dict[str, Any]]:
        now = time.time()
        palm_x, palm_y = self._palm_center(lm)
        self._palm_history.append((now, palm_x, palm_y))

        thumb = self._thumb_extended(lm)
        index = self._finger_extended(lm, tip_id=8, pip_id=6)
        middle = self._finger_extended(lm, tip_id=12, pip_id=10)
        ring = self._finger_extended(lm, tip_id=16, pip_id=14)
        pinky = self._finger_extended(lm, tip_id=20, pip_id=18)

        pinch_distance = self._distance(lm[4], lm[8])
        pinch = pinch_distance < 0.05

        state = {
            "hand_present": True,
            "index_tip": (lm[8].x, lm[8].y),
            "palm_center": (palm_x, palm_y),
            "pinch": pinch,
            "pinch_distance": pinch_distance,
            "fingers": {
                "thumb": thumb,
                "index": index,
                "middle": middle,
                "ring": ring,
                "pinky": pinky,
            },
        }

        swipe = self._detect_swipe(
            now,
            thumb=thumb,
            index=index,
            middle=middle,
            ring=ring,
            pinky=pinky,
        )
        if swipe:
            return swipe, state

        if pinch:
            return "pinch", state

        if all([thumb, index, middle, ring, pinky]):
            return "open_palm", state

        if not any([thumb, index, middle, ring, pinky]):
            return "fist", state

        if thumb and not any([index, middle, ring, pinky]):
            return "thumbs_up", state

        if index and middle and not ring and not pinky:
            if thumb:
                return "peace", state
            return "two_finger", state

        if index and not any([middle, ring, pinky]):
            return "point", state

        return None, state

    def _detect_swipe(
        self,
        now: float,
        *,
        thumb: bool,
        index: bool,
        middle: bool,
        ring: bool,
        pinky: bool,
    ) -> str | None:
        while self._palm_history and now - self._palm_history[0][0] > 0.55:
            self._palm_history.popleft()

        if now - self._last_swipe_at < 0.55:
            return None

        if len(self._palm_history) < 6:
            return None

        extended_count = sum([thumb, index, middle, ring, pinky])
        if extended_count < 2:
            return None

        start_t, start_x, start_y = self._palm_history[0]
        end_t, end_x, end_y = self._palm_history[-1]
        duration = end_t - start_t
        delta_x = end_x - start_x
        delta_y = end_y - start_y
        speed_x = abs(delta_x) / duration if duration > 0 else 0.0

        if (
            0 < duration <= 0.55
            and abs(delta_x) >= 0.10
            and speed_x >= 0.28
            and abs(delta_x) >= (abs(delta_y) * 1.25)
        ):
            self._last_swipe_at = now
            self._palm_history.clear()
            return "swipe_right" if delta_x > 0 else "swipe_left"

        return None

    def _thumb_extended(self, lm: Any) -> bool:
        tip_to_index = self._distance(lm[4], lm[5])
        ip_to_index = self._distance(lm[3], lm[5])
        return tip_to_index > (ip_to_index * 1.15)

    @staticmethod
    def _finger_extended(lm: Any, tip_id: int, pip_id: int) -> bool:
        return (lm[pip_id].y - lm[tip_id].y) > 0.02

    @staticmethod
    def _distance(a: Any, b: Any) -> float:
        return math.hypot(a.x - b.x, a.y - b.y)

    @staticmethod
    def _palm_center(lm: Any) -> tuple[float, float]:
        ids = [0, 5, 9, 13, 17]
        x = sum(lm[i].x for i in ids) / len(ids)
        y = sum(lm[i].y for i in ids) / len(ids)
        return x, y
