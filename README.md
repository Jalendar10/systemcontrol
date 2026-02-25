# HandPilot

HandPilot is a cross-platform system to control your PC using hand gestures from a webcam on **macOS** and **Windows**.

Repository: [https://github.com/Jalendar10/systemcontrol](https://github.com/Jalendar10/systemcontrol)

## Features

- Webcam-based hand tracking with MediaPipe.
- More reliable slide detection for app switching (`swipe_left` / `swipe_right`).
- Full mouse control (`point` move, `pinch` click/drag, `two_finger` scroll).
- Browser tab controls (`open_palm`, `fist`).
- Custom gesture mapping to built-in actions, hotkeys, or shell commands.
- Toggle control ON/OFF with a gesture (`thumbs_up`) or keyboard (`p`).

## Default Gesture Map

- `swipe_left` -> Next app (`Cmd+Tab` on macOS, `Alt+Tab` on Windows)
- `swipe_right` -> Previous app
- `open_palm` -> Browser next tab
- `fist` -> Browser previous tab
- `peace` -> Open Calculator
- `thumbs_up` -> Toggle control ON/OFF
- `point` -> Move mouse cursor
- `pinch` -> Left click (tap) / drag (hold)
- `two_finger` -> Scroll

## Requirements

- Python 3.11 or 3.12 (recommended: 3.11)
- Webcam access permission
- Accessibility/automation permissions for keyboard control

## Setup

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Windows (PowerShell):

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Run

```bash
PYTHONPATH=src python run.py
```

Or install as a package and run:

```bash
pip install -e .
handpilot
```

## Controls

- `q` quit
- `p` pause/resume gesture actions
- `r` reload config file

## Quick Control Check

1. Start the app and keep one hand visible in the camera frame.
2. Try `swipe_left` / `swipe_right` and confirm app switching happens.
3. Show `point` and confirm cursor moves.
4. Do a quick `pinch` and confirm left click works.
5. Hold `pinch` and move hand to drag, then release to drop.
6. Show `two_finger` and move hand up/down to scroll.
7. Try `thumbs_up` to toggle control OFF, then repeat a gesture and confirm no action is triggered.
8. Press `q` to quit.

## Custom Gestures

Edit `config/gestures.example.json` or copy it:

```bash
cp config/gestures.example.json config/gestures.local.json
```

Then update `gesture_actions`:

- `type: "builtin"` with `name`
- `type: "hotkey"` with `keys`
- `type: "command"` with per-OS commands

Example:

```json
"peace": {
  "type": "command",
  "command": {
    "mac": "open -a Safari",
    "windows": "start chrome"
  }
}
```

Optional camera fallback config:

```json
"camera_indices": [0, 1, 2, 3]
```

Mouse control tuning:

```json
"mouse_control": {
  "enabled": true,
  "pointer_gestures": ["point", "pinch", "two_finger"],
  "consume_gestures": ["point", "pinch", "two_finger"],
  "left_click_gesture": "pinch",
  "scroll_gesture": "two_finger",
  "drag_hold_ms": 320,
  "click_max_tap_ms": 260,
  "move_speed": 1.6,
  "smoothing": 0.35,
  "deadzone": 0.008,
  "scroll_scale": 2200.0
}
```

## Notes

- Gesture detection thresholds are intentionally conservative to reduce accidental triggers.
- On macOS, allow Terminal/Python in **System Settings -> Privacy & Security -> Accessibility**.
- On first run, camera and accessibility permissions must be granted.
- License: MIT. See `LICENSE`.

## Troubleshooting

- If startup shows `Cannot open camera index 0`, allow camera access:
  - macOS: **System Settings -> Privacy & Security -> Camera** and enable the app that runs Python (`Terminal`, `iTerm`, or `Codex`).
  - Windows: **Settings -> Privacy & security -> Camera** and allow desktop apps.
- If gestures are detected but actions do not trigger, allow accessibility/input control for Terminal/Python.
