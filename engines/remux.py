import subprocess
from pathlib import Path

def remux(input_path: Path, output_path: Path) -> bool:
    print(f"🔁 Remux attempt: {input_path.name}")

    cmd = [
        "ffmpeg", "-y",
        "-i", str(input_path),
        "-map", "0:v:0",
        "-map", "0:a?",
        "-c", "copy",
        "-movflags", "+faststart",
        str(output_path)
    ]

    r = subprocess.run(cmd)

    if r.returncode != 0:
        return False

    return output_path.exists() and output_path.stat().st_size > 0
