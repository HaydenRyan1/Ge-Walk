"""
Run this once (or a few times, from different tiles, for extra samples)
to build the character template library used by ge_walker.py.

How it works: stand somewhere your coordinates are visible, run this
script, and type EXACTLY what the readout shows (e.g. 3164,3485 -- no
spaces). It screenshots the region, splits it into one image per
character, and saves each one labeled with the character you typed.

Run it multiple times at different coordinates to capture more digit
variety (0-9 and comma) -- a single reading likely won't contain every
digit. Re-running just adds more samples; it doesn't overwrite old ones.
"""

import pickle
import numpy as np
from PIL import Image

from ocr_common import (
    capture_binary_image,
    segment_characters,
    crop_to_template,
    TEMPLATE_FILE,
)


def main():
    print("Stand somewhere your coordinates are clearly visible.")
    actual_text = input("Type EXACTLY what the readout shows (e.g. 3164,3485): ").strip()

    binary = capture_binary_image()
    segments = segment_characters(binary)

    print(f"Found {len(segments)} character segment(s) in the image, "
          f"expected {len(actual_text)} based on what you typed.")

    if len(segments) != len(actual_text):
        print("Mismatch -- nothing was saved. This usually means either:")
        print("  - two characters are touching and got merged into one segment")
        print("  - OCR_REGION doesn't fully capture the text (check debug_ocr_last.png)")
        print("  - what you typed didn't exactly match what's on screen")
        binary.save("debug_calibration_failed.png")
        print("Saved debug_calibration_failed.png for inspection.")
        return

    try:
        with open(TEMPLATE_FILE, "rb") as f:
            templates = pickle.load(f)
    except FileNotFoundError:
        templates = {}

    for (start, end), char in zip(segments, actual_text):
        crop_arr = crop_to_template(binary, start, end)
        templates.setdefault(char, []).append(crop_arr)
        print(f"Captured template for '{char}'")

    with open(TEMPLATE_FILE, "wb") as f:
        pickle.dump(templates, f)

    total = sum(len(v) for v in templates.values())
    chars_known = sorted(templates.keys())
    print(f"\nSaved. Library now has {total} samples across characters: {chars_known}")

    needed = set("0123456789,")
    missing = needed - set(chars_known)
    if missing:
        print(f"Still missing samples for: {sorted(missing)} -- "
              f"run this again at a location/time where those digits appear.")
    else:
        print("All digits and comma are covered. Ready to use ge_walker.py.")


if __name__ == "__main__":
    main()