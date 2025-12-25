import subprocess
from pathlib import Path

def compress(input_path: Path, output_path: Path, quality: int):
    cmd = [
        "ffmpeg",
        "-i", str(input_path),
        "-map", "0:v",
        "-map", "0:a?",
        "-c:v", "libx265",
        "-crf", "18",
        "-preset", "slow",
        "-c:a", "aac",
        "-b:a", "160k",
        "-movflags", "+faststart",
        str(output_path),
    ]
    subprocess.run(cmd, check=True)
