import subprocess
from pathlib import Path

def compress(input_path: Path, output_path: Path, quality: int):
    cmd = [
        "HandBrakeCLI",
        "-i", str(input_path),
        "-o", str(output_path),
        "--preset", "H.265 Apple VideoToolbox 1080p",
        "-q", str(quality),
        "--all-audio",
        "--markers",
        "--optimize",
    ]
    subprocess.run(cmd, check=True)
