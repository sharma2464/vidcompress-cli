from pathlib import Path
import os
from config import VIDEO_EXTS

def is_video(path: Path) -> bool:
    return path.suffix.lower() in VIDEO_EXTS

def scan_inputs(input_root: Path, output_root: Path):
    jobs = []

    if input_root.is_file():
        return [input_root], True

    for root, dirs, files in os.walk(input_root):
        if output_root.name in dirs:
            dirs.remove(output_root.name)

        for f in files:
            p = Path(root) / f
            if is_video(p):
                jobs.append(p)

    return jobs, False
