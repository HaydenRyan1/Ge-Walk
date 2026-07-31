# RS Minimap Walker

Reads the player's current coordinates from a fixed screen region using
template matching, then clicks the minimap to walk toward a target
location along a predefined path.

> **Note:** an earlier version of this project used Tesseract OCR to read
> coordinates. It proved unreliable on the game's blocky pixel font,
> frequently misreading or dropping digits. This version replaces it with
> template matching against captured reference glyphs, which is far more
> reliable for a small, fixed-width character set.

## Files

| File | Purpose |
|---|---|
| `ocr_common.py` | Shared logic: screenshot capture, character segmentation, template matching. Imported by the other two scripts. |
| `capture_templates.py` | One-time calibration tool. Captures a real coordinate reading and lets you label it to build the template library. |
| `ge_walker.py` | Main script. Reads current position, determines which zone you're in, and walks a chosen path to the destination. |

All three files must be in the same folder — `ge_walker.py` and
`capture_templates.py` both import from `ocr_common.py`.

## Requirements

- Python 3.10+
- [`pyautogui`](https://pypi.org/project/PyAutoGUI/)
- [`numpy`](https://pypi.org/project/numpy/)
- [`Pillow`](https://pypi.org/project/Pillow/) (installed automatically as a `pyautogui`/`numpy` dependency in most setups, but install directly if needed)

## Setup

### 1. Confirm the coordinate readout region

`OCR_REGION` in `ocr_common.py` is set to `(48, 48, 67, 14)` — the
screen pixel area where your coordinate display appears. If your
game window position, resolution, or UI scale differs from what this
was calibrated on, update this region first.

### 2. Build the character template library

Run the calibration script:

```bash
python capture_templates.py
```

Stand somewhere your coordinates are clearly visible, then type
**exactly** what's shown on screen (e.g. `3164,3485` — no spaces) when
prompted. This captures one template per character.

**Run it multiple times, from different locations**, so you get
samples covering every digit `0–9` plus the comma. The script tells you
after each run which characters are still missing:

```
Still missing samples for: ['7', '9'] -- run this again at a location/time where those digits appear.
```

Once it confirms all digits and the comma are covered, you're done —
this creates `char_templates.pkl` in the same folder.

### 3. Calibrate the minimap click mapping (if needed)

`MINIMAP_ORIGIN` and `SCALE` in `ge_walker.py` are calibrated for a
specific minimap position and zoom level. If clicks land in the wrong
place, these values need to be re-derived for your setup — test by
requesting movement on a single axis at a time and comparing the
requested vs. actual in-game coordinate change.

## Usage

```bash
python ge_walker.py
```

The script will:
1. Read your current coordinates.
2. Determine which known zone you're in (Grand Exchange, Edgeville, or
   Rimmington Mine).
3. Prompt you to choose a destination.
4. Walk the predefined path, clicking the minimap step by step.
