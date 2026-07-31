"""
Shared logic for template-matching based coordinate reading.

Why this exists: Tesseract OCR was unreliable on the game's blocky pixel
font, consistently dropping or misreading digits even when the input image
looked clean. Since this font is fixed-width with a tiny character set
(0-9 and comma), template matching against captured reference glyphs is
far more reliable than general-purpose OCR here.
"""

import pickle
import numpy as np
import pyautogui
from PIL import Image

# Screen region where the game displays current coordinates.
OCR_REGION = (48, 48, 67, 14)

# How many times to upscale the raw screenshot before processing.
UPSCALE = 6

# Pixel brightness threshold (0-255) above which a pixel is treated as
# foreground (text) rather than background.
THRESHOLD = 128

# Fixed size each character glyph is resized to before comparison, so
# templates and live reads are always compared like-for-like.
TEMPLATE_SIZE = (24, 36)  # (width, height)

TEMPLATE_FILE = "char_templates.pkl"
DEBUG_IMAGE_PATH = "debug_ocr_last.png"


def capture_binary_image():
    """Screenshot the coordinate region and return a clean black/white image."""
    screenshot = pyautogui.screenshot(region=OCR_REGION)
    w, h = screenshot.size
    screenshot = screenshot.resize((w * UPSCALE, h * UPSCALE), Image.NEAREST)
    gray = screenshot.convert("L")
    binary = gray.point(lambda p: 255 if p > THRESHOLD else 0)
    return binary


def segment_characters(binary_image):
    """
    Splits a binary (black background, white text) image into per-character
    column ranges, by finding columns that contain any foreground pixel and
    grouping consecutive such columns into one character segment.
    Returns a list of (start_col, end_col) tuples, left to right.
    """
    arr = np.array(binary_image)
    col_has_fg = (arr > 0).any(axis=0)

    segments = []
    in_segment = False
    start = 0
    for i, has_fg in enumerate(col_has_fg):
        if has_fg and not in_segment:
            start = i
            in_segment = True
        elif not has_fg and in_segment:
            segments.append((start, i))
            in_segment = False
    if in_segment:
        segments.append((start, len(col_has_fg)))

    return segments


def crop_to_template(binary_image, start_col, end_col):
    """Crops one character segment out and resizes it to TEMPLATE_SIZE,
    returning a 0/1 numpy array."""
    arr = np.array(binary_image)
    crop = arr[:, start_col:end_col]
    crop_img = Image.fromarray(crop).resize(TEMPLATE_SIZE, Image.NEAREST)
    return (np.array(crop_img) > 0).astype(np.uint8)


def load_templates():
    with open(TEMPLATE_FILE, "rb") as f:
        return pickle.load(f)


def classify_char(crop_arr, templates, max_diff_ratio=0.35):
    """
    Compares a character's pixel array against every stored template and
    returns the best-matching character, or None if nothing is close enough
    (better to flag an unknown character than silently guess wrong).
    """
    best_char = None
    best_score = None

    for char, samples in templates.items():
        for sample in samples:
            diff = np.sum(crop_arr != sample)
            if best_score is None or diff < best_score:
                best_score = diff
                best_char = char

    total_pixels = TEMPLATE_SIZE[0] * TEMPLATE_SIZE[1]
    if best_score is not None and best_score / total_pixels <= max_diff_ratio:
        return best_char
    return None


def read_text(templates):
    """Full pipeline: screenshot -> segment -> classify -> assembled string.
    Also saves a debug image for troubleshooting. Returns the recognized
    string, or None if any character couldn't be confidently classified."""
    binary = capture_binary_image()
    binary.save(DEBUG_IMAGE_PATH)

    segments = segment_characters(binary)
    chars = []
    for (start, end) in segments:
        crop_arr = crop_to_template(binary, start, end)
        char = classify_char(crop_arr, templates)
        if char is None:
            return None
        chars.append(char)

    return "".join(chars)