#!/usr/bin/env python3
"""
Batch Outline Extractor — process an entire folder of images at once.
"""

import os
import sys
import argparse
from pathlib import Path
from outline_extractor import extract_outline, COLOR_PRESETS

SUPPORTED = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}


def batch_process(
    input_dir: str,
    output_dir: str,
    color: str = "neon-cyan",
    thickness: int = 1,
    blur: int = 3,
    canny_low: int = 30,
    canny_high: int = 100,
    glow: bool = True,
    glow_strength: int = 5,
):
    in_path = Path(input_dir)
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    images = [f for f in in_path.iterdir() if f.suffix.lower() in SUPPORTED]

    if not images:
        print(f"No supported images found in: {input_dir}")
        return

    print(f"Found {len(images)} image(s) in '{input_dir}' → saving to '{output_dir}'\n")

    ok, fail = 0, 0
    for img_file in sorted(images):
        out_file = out_path / (img_file.stem + "_outline.png")
        try:
            extract_outline(
                input_path=str(img_file),
                output_path=str(out_file),
                color_input=color,
                thickness=thickness,
                blur_before=blur,
                canny_low=canny_low,
                canny_high=canny_high,
                glow=glow,
                glow_strength=glow_strength,
            )
            ok += 1
        except Exception as e:
            print(f"  ❌  {img_file.name}: {e}")
            fail += 1

    print(f"\n✅  Done — {ok} succeeded, {fail} failed.")


def main():
    p = argparse.ArgumentParser(
        description="Batch-process a folder of images into outlines.",
    )
    p.add_argument("input_dir",  help="Folder containing input images")
    p.add_argument("output_dir", help="Folder where outlines will be saved")
    p.add_argument("-c", "--color",        default="neon-cyan")
    p.add_argument("--thickness",   type=int, default=1)
    p.add_argument("--blur",        type=int, default=3)
    p.add_argument("--canny-low",   type=int, default=30)
    p.add_argument("--canny-high",  type=int, default=100)
    p.add_argument("--glow-strength", type=int, default=5)
    p.add_argument("--no-glow", action="store_true")
    args = p.parse_args()

    batch_process(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        color=args.color,
        thickness=args.thickness,
        blur=args.blur,
        canny_low=args.canny_low,
        canny_high=args.canny_high,
        glow=not args.no_glow,
        glow_strength=args.glow_strength,
    )


if __name__ == "__main__":
    main()
