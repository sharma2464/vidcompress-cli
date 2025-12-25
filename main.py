#!/usr/bin/env python3

import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

from config import MAX_JOBS, DEFAULT_QUALITY
from deps import ensure_dependencies
from scanner import scan_inputs
from worker import run_job

def main():
    if len(sys.argv) < 3:
        print("Usage: main.py <input> <output> [quality] [--engine auto|handbrake|ffmpeg]")
        sys.exit(1)

    engine = "auto"
    if "--engine" in sys.argv:
        idx = sys.argv.index("--engine")
        engine = sys.argv[idx + 1]
        del sys.argv[idx:idx + 2]

    input_root = Path(sys.argv[1]).expanduser().resolve()
    output_root = Path(sys.argv[2]).expanduser().resolve()
    quality = int(sys.argv[3]) if len(sys.argv) > 3 else DEFAULT_QUALITY

    engine = ensure_dependencies(engine)

    if engine == "handbrake":
        from engines import handbrake as engine_module
    else:
        from engines import ffmpeg as engine_module

    jobs, single = scan_inputs(input_root, output_root)
    print(f"Found {len(jobs)} video(s) → using {engine}")

    with ThreadPoolExecutor(MAX_JOBS) as pool:
        for job in jobs:
            pool.submit(run_job, engine_module, job, input_root, output_root, quality, single)

    print("🎉 All conversions complete.")

if __name__ == "__main__":
    main()
