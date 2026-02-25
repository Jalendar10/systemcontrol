# HandPilot

HandPilot is a cross-platform starter system to control your PC using hand gestures from a webcam on **macOS** and **Windows**.

## Features

- Webcam-based hand tracking with MediaPipe.
- Gesture-based app switching (`swipe_left` / `swipe_right`).
- Browser tab controls (`open_palm`, `fist`, `point`).
- Custom gesture mapping to built-in actions, hotkeys, or shell commands.
- Toggle control ON/OFF with a gesture (`pinch`) or keyboard (`p`).

## Default Gesture Map

- `swipe_left` -> Next app (`Cmd+Tab` on macOS, `Alt+Tab` on Windows)
- `swipe_right` -> Previous app
- `open_palm` -> Browser next tab
- `fist` -> Browser previous tab
- `point` -> Close current tab
- `peace` -> Open Calculator
- `pinch` -> Toggle control ON/OFF

## Requirements

- Python 3.10+
- Webcam access permission
- Accessibility/automation permissions for keyboard control

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Windows (PowerShell):

```powershell
python -m venv .venv
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

## Notes

- Gesture detection thresholds are intentionally conservative to reduce accidental triggers.
- On macOS, allow Terminal/Python in **System Settings -> Privacy & Security -> Accessibility**.
