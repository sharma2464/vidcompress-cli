#!/usr/bin/env python3

import subprocess
import sys
import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import threading

# ------------- CONFIG ----------------
MAX_GPU_JOBS = 2                  # Safe for M2 Pro
DEFAULT_QUALITY = 18
VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".m4v"}
# ------------------------------------

lock = threading.Lock()
jobs = []


def is_video_file(path: Path) -> bool:
    return path.suffix.lower() in VIDEO_EXTS


def already_compressed(path: Path, output_root: Path) -> bool:
    s = str(path)
    return (
        output_root in path.parents
        or s.endswith("_compressed.mp4")
    )


def compress_one(
    input_path: Path,
    input_root: Path,
    output_root: Path,
    quality: int,
    single_file: bool,
):
    if already_compressed(input_path, output_root):
        print(f"⏭ Skipping: {input_path}")
        return

    if single_file:
        out_dir = output_root
        rel_name = input_path.name
    else:
        rel_path = input_path.relative_to(input_root)
        out_dir = output_root / rel_path.parent
        rel_name = rel_path.name

    out_dir.mkdir(parents=True, exist_ok=True)
    output_path = out_dir / f"{Path(rel_name).stem}_compressed.mp4"

    print(f"🎞  {rel_name}")

    cmd = [
        "HandBrakeCLI",
        "-i", str(input_path),
        "-o", str(output_path),
        "--preset", "H.265 Apple VideoToolbox 1080p",
        "-q", str(quality),
        "--all-audio",
        "--all-subtitles",
        "--markers",
        "--optimize",
    ]

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError:
        print(f"❌ HandBrake failed: {input_path}")
        return

    subprocess.run(["touch", "-r", str(input_path), str(output_path)])
    print(f"✅ Done → {output_path}")


def main():
    if len(sys.argv) < 3:
        print(
            f"Usage:\n"
            f"  {sys.argv[0]} <input_path> <output_path> [quality]\n\n"
            f"Examples:\n"
            f"  {sys.argv[0]} video.mp4 ./out\n"
            f"  {sys.argv[0]} ~/Videos ~/Compressed 18"
        )
        sys.exit(1)

    input_root = Path(sys.argv[1]).expanduser().resolve()
    output_root = Path(sys.argv[2]).expanduser().resolve()
    quality = int(sys.argv[3]) if len(sys.argv) >= 4 else DEFAULT_QUALITY

    if not input_root.exists():
        print("❌ Input path does not exist")
        sys.exit(1)

    output_root.mkdir(parents=True, exist_ok=True)

    single_file = input_root.is_file()

    if single_file:
        jobs.append(input_root)
    else:
        for root, dirs, files in os.walk(input_root):
            if output_root.name in dirs:
                dirs.remove(output_root.name)

            for f in files:
                p = Path(root) / f
                if is_video_file(p):
                    jobs.append(p)

    print(f"Found {len(jobs)} video(s)")

    with ThreadPoolExecutor(max_workers=MAX_GPU_JOBS) as executor:
        for job in jobs:
            executor.submit(
                compress_one,
                job,
                input_root,
                output_root,
                quality,
                single_file,
            )

    print("🎉 All conversions complete.")


if __name__ == "__main__":
    main()
