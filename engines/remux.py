import subprocess
from pathlib import Path

def compress(input_path: Path, output_path: Path, quality: int = None):
    """
    Remux to MP4 without re-encoding.
    Drops unsupported streams (timecode).
    """
    cmd = [
        "ffmpeg",
        "-y",
        "-i", str(input_path),

        "-map", "0:v",
        "-map", "0:a?",
        "-map_metadata", "0",
        "-map_chapters", "0",

        "-c", "copy",
        "-movflags", "+faststart",
        str(output_path)
    ]

    subprocess.run(cmd, check=True)
