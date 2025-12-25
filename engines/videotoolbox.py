import subprocess
from pathlib import Path

def encode_ffmpeg(input_path: Path, output_path: Path, quality: int):
    cmd = [
        "ffmpeg",
        "-y",
        "-i", str(input_path),

        "-map", "0:v:0",
        "-map", "0:a?",
        "-map_metadata", "0",

        "-c:v", "libx265",
        "-crf", str(quality),
        "-preset", "medium",

        "-c:a", "aac",
        "-b:a", "128k",

        "-movflags", "+faststart",
        str(output_path)
    ]

    print(f"🎞 Encoding: {input_path.name}")

    subprocess.run(cmd, check=True)
