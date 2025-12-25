import subprocess
from pathlib import Path

def compress(input_path: Path, output_path: Path, quality: int = 30):
    """
    HEVC encoding via Apple VideoToolbox.
    quality ≈ HandBrake RF (mapped internally).
    """

    # HandBrake RF → approximate bitrate (kbps)
    rf_to_bitrate = {
        18: 8000,
        20: 6000,
        22: 4500,
        24: 3500,
        26: 2500,
        28: 1800,
        30: 1400,
    }
    bitrate = rf_to_bitrate.get(quality, 3500)

    cmd = [
        "ffmpeg",
        "-y",
        "-hwaccel", "videotoolbox",
        "-i", str(input_path),

        "-map", "0:v:0",
        "-map", "0:a?",

        "-c:v", "hevc_videotoolbox",
        "-tag:v", "hvc1",
        "-b:v", f"{bitrate}k",

        "-pix_fmt", "yuv420p",
        "-g", "48",

        "-c:a", "aac",
        "-b:a", "160k",

        "-movflags", "+faststart",
        str(output_path)
    ]

    subprocess.run(cmd, check=True)
