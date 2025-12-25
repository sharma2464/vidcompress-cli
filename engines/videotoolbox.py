import subprocess
from pathlib import Path

def encode_ffmpeg(input_path: Path, output_path: Path, quality: int):
    cmd = [
        "ffmpeg", "-y",
        "-i", str(input_path),
        "-map", "0:v:0",
        "-map", "0:a?",
        "-c:v", "libx264",
        "-crf", str(quality),
        "-preset", "veryfast",
        "-c:a", "aac",
        "-b:a", "128k",
        "-movflags", "+faststart",
        str(output_path)
    ]

    subprocess.run(cmd, check=True)
