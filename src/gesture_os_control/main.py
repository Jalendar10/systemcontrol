"""Main loop for HandPilot."""

from __future__ import annotations

import argparse
import platform
import time
from pathlib import Path

import cv2

from .actions import ActionExecutor
from .config import load_config
from .detector import GestureDetector
from .mouse_controller import MouseController


def _resolve_default_config(config_path: str | None) -> Path:
    if config_path:
        return Path(config_path)

    local_path = Path("config/gestures.local.json")
    if local_path.exists():
        return local_path

    return Path("config/gestures.example.json")


def _camera_candidates(config: dict) -> list[int]:
    configured = config.get("camera_indices")
    if isinstance(configured, list) and configured:
        candidates: list[int] = []
        for value in configured:
            try:
                candidates.append(int(value))
            except (TypeError, ValueError):
                continue
        if candidates:
            return list(dict.fromkeys(candidates))

    primary = int(config.get("camera_index", 0))
    fallback = [0, 1, 2, 3]
    ordered = [primary] + [idx for idx in fallback if idx != primary]
    return list(dict.fromkeys(ordered))


def _open_camera(config: dict) -> tuple[cv2.VideoCapture, int]:
    candidates = _camera_candidates(config)
    is_mac = platform.system().lower() == "darwin"
    backend = cv2.CAP_AVFOUNDATION if is_mac else cv2.CAP_ANY

    for index in candidates:
        cap = cv2.VideoCapture(index, backend)
        if not cap.isOpened():
            cap.release()
            continue
        ok, _ = cap.read()
        if ok:
            return cap, index
        cap.release()

    candidate_text = ", ".join(str(idx) for idx in candidates)
    raise RuntimeError(
        "Cannot open any camera index (tried: "
        f"{candidate_text}). Check camera permission and update config camera_index/camera_indices."
    )


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

    mirror = bool(config.get("mirror", True))
    draw_landmarks = bool(config.get("draw_landmarks", True))
    default_cooldown = float(config.get("cooldown_ms", 850)) / 1000.0
    gesture_actions = config.get("gesture_actions", {})
    mouse_controller = MouseController(config.get("mouse_control", {}))

    cap, active_camera_index = _open_camera(config)

    window_name = f"{config.get('project_name', 'HandPilot')} | q=quit p=pause r=reload"

    last_trigger: dict[str, float] = {}
    active = True
    last_gesture = "none"
    last_result = "ready"

    print(f"Loaded config: {config_path}")
    print(f"Using camera index: {active_camera_index}")
    print("Press q to quit, p to pause/resume control, r to reload config.")

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break

            if mirror:
                frame = cv2.flip(frame, 1)

            gesture, frame, hand_state = detector.process(frame, draw_landmarks=draw_landmarks)
            mouse_result = mouse_controller.update(hand_state, active=active)
            if mouse_result:
                last_result = mouse_result

            if gesture:
                last_gesture = gesture
                if gesture in mouse_controller.consumed_gestures:
                    action_def = None
                else:
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
                if not active:
                    mouse_controller.reset()
            if key == ord("r"):
                config = load_config(config_path)
                mirror = bool(config.get("mirror", True))
                draw_landmarks = bool(config.get("draw_landmarks", True))
                default_cooldown = float(config.get("cooldown_ms", 850)) / 1000.0
                gesture_actions = config.get("gesture_actions", {})
                mouse_controller = MouseController(config.get("mouse_control", {}))
                last_result = "config reloaded"

    finally:
        mouse_controller.reset()
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    run()
