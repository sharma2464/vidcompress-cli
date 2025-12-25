from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import sys
import os

from engine_dispatch import process_video
from utils import is_video_file

MAX_JOBS = 2

def main():
    if len(sys.argv) < 3:
        print("Usage: main.py <input> <output> [--engine remux|ffmpeg]")
        sys.exit(1)

    input_root = Path(sys.argv[1]).expanduser().resolve()
    output_root = Path(sys.argv[2]).expanduser().resolve()

    engine = "ffmpeg"
    if "--engine" in sys.argv:
        engine = sys.argv[sys.argv.index("--engine") + 1]

    output_root.mkdir(parents=True, exist_ok=True)

    jobs = []

    if input_root.is_file():
        jobs.append(input_root)
    else:
        for root, _, files in os.walk(input_root):
            for f in files:
                p = Path(root) / f
                if is_video_file(p):
                    jobs.append(p)

    print(f"Found {len(jobs)} video(s) → using {engine}")

    with ThreadPoolExecutor(max_workers=MAX_JOBS) as ex:
        for job in jobs:
            ex.submit(
                process_video,
                job,
                input_root,
                output_root,
                engine
            )

    print("🎉 All conversions complete.")

if __name__ == "__main__":
    main()
