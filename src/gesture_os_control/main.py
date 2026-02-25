"""Main loop for HandPilot."""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import cv2

from .actions import ActionExecutor
from .config import load_config
from .detector import GestureDetector


def _resolve_default_config(config_path: str | None) -> Path:
    if config_path:
        return Path(config_path)

    local_path = Path("config/gestures.local.json")
    if local_path.exists():
        return local_path

    return Path("config/gestures.example.json")


def run() -> None:
    parser = argparse.ArgumentParser(description="HandPilot - control your PC with gestures")
    parser.add_argument(
        "--config",
        help="Path to gesture config JSON (default: config/gestures.local.json or example)",
    )
    args = parser.parse_args()

    config_path = _resolve_default_config(args.config)
    config = load_config(config_path)

    detector = GestureDetector()
    executor = ActionExecutor()

    camera_index = int(config.get("camera_index", 0))
    mirror = bool(config.get("mirror", True))
    draw_landmarks = bool(config.get("draw_landmarks", True))
    default_cooldown = float(config.get("cooldown_ms", 850)) / 1000.0
    gesture_actions = config.get("gesture_actions", {})

    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        raise RuntimeError(
            f"Cannot open camera index {camera_index}. Update your config and check camera permissions."
        )

    window_name = f"{config.get('project_name', 'HandPilot')} | q=quit p=pause r=reload"

    last_trigger: dict[str, float] = {}
    active = True
    last_gesture = "none"
    last_result = "ready"

    print(f"Loaded config: {config_path}")
    print("Press q to quit, p to pause/resume control, r to reload config.")

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break

            if mirror:
                frame = cv2.flip(frame, 1)

            gesture, frame = detector.process(frame, draw_landmarks=draw_landmarks)

            if gesture:
                last_gesture = gesture
                action_def = gesture_actions.get(gesture)
                if action_def:
                    now = time.time()
                    cooldown = float(action_def.get("cooldown_ms", default_cooldown * 1000)) / 1000
                    last_time = last_trigger.get(gesture, 0.0)

                    if now - last_time >= cooldown:
                        last_trigger[gesture] = now

                        if action_def.get("type", "builtin") == "builtin" and action_def.get(
                            "name"
                        ) == "toggle_control":
                            active = not active
                            last_result = f"control {'ON' if active else 'OFF'}"
                        elif active:
                            last_result = executor.execute(action_def)
                        else:
                            last_result = "paused"

            status_text = f"status: {'ACTIVE' if active else 'PAUSED'}"
            gesture_text = f"gesture: {last_gesture}"
            action_text = f"action: {last_result}"

            cv2.putText(frame, status_text, (16, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            cv2.putText(frame, gesture_text, (16, 64), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(frame, action_text, (16, 96), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

            cv2.imshow(window_name, frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            if key == ord("p"):
                active = not active
                last_result = f"control {'ON' if active else 'OFF'}"
            if key == ord("r"):
                config = load_config(config_path)
                mirror = bool(config.get("mirror", True))
                draw_landmarks = bool(config.get("draw_landmarks", True))
                default_cooldown = float(config.get("cooldown_ms", 850)) / 1000.0
                gesture_actions = config.get("gesture_actions", {})
                last_result = "config reloaded"

    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    run()
