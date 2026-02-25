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
        self._wrist_x_history: deque[tuple[float, float]] = deque(maxlen=20)

    def process(self, frame: Any, draw_landmarks: bool = True) -> tuple[str | None, Any]:
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = self._hands.process(rgb)

        if not result.multi_hand_landmarks:
            self._wrist_x_history.clear()
            return None, frame

        landmarks = result.multi_hand_landmarks[0]

        if draw_landmarks:
            self._drawer.draw_landmarks(
                frame,
                landmarks,
                self._mp_hands.HAND_CONNECTIONS,
            )

        gesture = self._classify_gesture(landmarks.landmark)
        return gesture, frame

    def _classify_gesture(self, lm: Any) -> str | None:
        now = time.time()
        wrist_x = lm[0].x
        self._wrist_x_history.append((now, wrist_x))

        swipe = self._detect_swipe(now)
        if swipe:
            return swipe

        thumb = self._thumb_extended(lm)
        index = self._finger_extended(lm, tip_id=8, pip_id=6)
        middle = self._finger_extended(lm, tip_id=12, pip_id=10)
        ring = self._finger_extended(lm, tip_id=16, pip_id=14)
        pinky = self._finger_extended(lm, tip_id=20, pip_id=18)

        pinch = self._distance(lm[4], lm[8]) < 0.045
        if pinch:
            return "pinch"

        if all([thumb, index, middle, ring, pinky]):
            return "open_palm"

        if not any([thumb, index, middle, ring, pinky]):
            return "fist"

        if index and not any([middle, ring, pinky]):
            return "point"

        if index and middle and not ring and not pinky:
            return "peace"

        return None

    def _detect_swipe(self, now: float) -> str | None:
        while self._wrist_x_history and now - self._wrist_x_history[0][0] > 0.45:
            self._wrist_x_history.popleft()

        if len(self._wrist_x_history) < 5:
            return None

        start_t, start_x = self._wrist_x_history[0]
        end_t, end_x = self._wrist_x_history[-1]
        duration = end_t - start_t
        delta_x = end_x - start_x

        if duration <= 0.45 and abs(delta_x) >= 0.18:
            self._wrist_x_history.clear()
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
