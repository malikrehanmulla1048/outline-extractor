#!/usr/bin/env python3
"""
Outline Extractor - Extracts glowing outlines from images on a black background.
"""

import cv2
import numpy as np
import argparse
import os
import sys
from pathlib import Path


# Predefined neon color presets (BGR format for OpenCV)
COLOR_PRESETS = {
    "neon-cyan":    (255, 255, 0),
    "neon-green":   (0, 255, 0),
    "neon-pink":    (180, 0, 255),
    "neon-orange":  (0, 165, 255),
    "neon-yellow":  (0, 255, 255),
    "neon-blue":    (255, 100, 0),
    "neon-red":     (0, 0, 255),
    "neon-purple":  (255, 0, 180),
    "white":        (255, 255, 255),
    "gold":         (0, 215, 255),
}


def hex_to_bgr(hex_color: str):
    """Convert a hex color string (#RRGGBB or RRGGBB) to BGR tuple."""
    hex_color = hex_color.lstrip("#")
    if len(hex_color) != 6:
        raise ValueError(f"Invalid hex color: #{hex_color}")
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return (b, g, r)


def get_color(color_input: str):
    """Resolve color name or hex string to BGR tuple."""
    lower = color_input.lower()
    if lower in COLOR_PRESETS:
        return COLOR_PRESETS[lower]
    elif lower.startswith("#") or (len(lower) == 6 and all(c in "0123456789abcdef" for c in lower)):
        return hex_to_bgr(lower)
    else:
        raise ValueError(
            f"Unknown color '{color_input}'.\n"
            f"Available presets: {', '.join(COLOR_PRESETS.keys())}\n"
            f"Or use a hex code like: #FF00FF"
        )


def extract_outline(
    input_path: str,
    output_path: str,
    color_input: str = "neon-cyan",
    thickness: int = 1,
    blur_before: int = 3,
    canny_low: int = 30,
    canny_high: int = 100,
    glow: bool = True,
    glow_strength: int = 5,
):
    """
    Extract outline from an image and render it on a black background.

    Args:
        input_path:    Path to input image (.jpg / .png)
        output_path:   Path to save output image
        color_input:   Color name preset or hex (#RRGGBB)
        thickness:     Outline line thickness in pixels
        blur_before:   Gaussian blur kernel size before edge detection (odd number, 0 = off)
        canny_low:     Canny lower threshold
        canny_high:    Canny upper threshold
        glow:          Whether to add neon glow effect
        glow_strength: Number of glow dilation/blur passes
    """
    # ── Load image ──────────────────────────────────────────────────────────
    img = cv2.imread(input_path)
    if img is None:
        raise FileNotFoundError(f"Could not open image: {input_path}")

    h, w = img.shape[:2]
    color_bgr = get_color(color_input)

    # ── Pre-processing ───────────────────────────────────────────────────────
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    if blur_before > 0:
        ksize = blur_before if blur_before % 2 == 1 else blur_before + 1
        gray = cv2.GaussianBlur(gray, (ksize, ksize), 0)

    # ── Edge detection ───────────────────────────────────────────────────────
    edges = cv2.Canny(gray, canny_low, canny_high)

    # Optionally thicken the raw edge mask
    if thickness > 1:
        kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE, (thickness, thickness)
        )
        edges = cv2.dilate(edges, kernel, iterations=1)

    # ── Build colored outline on black canvas ────────────────────────────────
    canvas = np.zeros((h, w, 3), dtype=np.uint8)

    # Paint edges with chosen color
    mask = edges > 0
    canvas[mask] = color_bgr

    # ── Neon glow effect ─────────────────────────────────────────────────────
    if glow and glow_strength > 0:
        glow_layer = canvas.astype(np.float32)
        for i in range(glow_strength):
            k = 3 + i * 4        # growing kernel: 3, 7, 11, 15, ...
            k = k if k % 2 == 1 else k + 1
            sigma = 1.5 + i * 1.2
            blurred = cv2.GaussianBlur(glow_layer, (k, k), sigma)
            glow_layer = np.maximum(glow_layer, blurred * (0.6 - i * 0.08))

        # Clamp and convert back
        glow_layer = np.clip(glow_layer, 0, 255).astype(np.uint8)

        # Re-stamp the sharp edges on top so lines stay crisp
        glow_layer[mask] = color_bgr
        canvas = glow_layer

    # ── Save ─────────────────────────────────────────────────────────────────
    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    success = cv2.imwrite(output_path, canvas)
    if not success:
        raise IOError(f"Failed to write output image: {output_path}")

    print(f"✅  Outline saved → {output_path}")
    print(f"    Size      : {w} × {h} px")
    print(f"    Color     : {color_input}  {color_bgr}")
    print(f"    Glow      : {'on' if glow else 'off'}")
    print(f"    Thickness : {thickness}")
    return output_path


# ── CLI ───────────────────────────────────────────────────────────────────────

def build_parser():
    p = argparse.ArgumentParser(
        description="Extract glowing outlines from images on a black background.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
COLOR PRESETS:
  neon-cyan  neon-green  neon-pink  neon-orange  neon-yellow
  neon-blue  neon-red    neon-purple  white  gold

  Or supply a hex code:  #FF00FF

EXAMPLES:
  python outline_extractor.py hand.jpg
  python outline_extractor.py hand.jpg -o hand_outline.png -c neon-pink
  python outline_extractor.py face.png  -c "#00FFFF" --thickness 2 --glow-strength 7
  python outline_extractor.py logo.png  -c gold --no-glow
        """,
    )
    p.add_argument("input", help="Input image path (.jpg or .png)")
    p.add_argument("-o", "--output", default=None,
                   help="Output image path (default: <input>_outline.png)")
    p.add_argument("-c", "--color", default="neon-cyan",
                   help="Outline color: preset name or hex (#RRGGBB). Default: neon-cyan")
    p.add_argument("--thickness", type=int, default=1,
                   help="Line thickness in pixels (default: 1)")
    p.add_argument("--blur", type=int, default=3,
                   help="Gaussian blur before edge detection, odd number (default: 3, 0=off)")
    p.add_argument("--canny-low", type=int, default=30,
                   help="Canny lower threshold (default: 30)")
    p.add_argument("--canny-high", type=int, default=100,
                   help="Canny upper threshold (default: 100)")
    p.add_argument("--glow-strength", type=int, default=5,
                   help="Glow intensity 0-10 (default: 5, 0 = plain lines)")
    p.add_argument("--no-glow", action="store_true",
                   help="Disable glow effect (plain colored lines only)")
    return p


def main():
    parser = build_parser()
    args = parser.parse_args()

    # Resolve output path
    if args.output is None:
        stem = Path(args.input).stem
        args.output = f"{stem}_outline.png"

    try:
        extract_outline(
            input_path=args.input,
            output_path=args.output,
            color_input=args.color,
            thickness=args.thickness,
            blur_before=args.blur,
            canny_low=args.canny_low,
            canny_high=args.canny_high,
            glow=not args.no_glow,
            glow_strength=args.glow_strength,
        )
    except (FileNotFoundError, ValueError, IOError) as e:
        print(f"❌  Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
