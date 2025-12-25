import subprocess
from pathlib import Path

def remux(input_path: Path, output_path: Path) -> bool:
    """
    Returns True if remux succeeded
    Returns False if remux not possible (caller must fallback)
    """

    cmd = [
        "ffmpeg",
        "-y",
        "-i", str(input_path),

        # Copy only compatible streams
        "-map", "0:v:0",
        "-map", "0:a?",
        "-map_metadata", "0",

        "-c", "copy",
        "-movflags", "+faststart",

        str(output_path)
    ]

    print(f"🔁 Remux attempt: {input_path.name}")

    result = subprocess.run(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True
    )

    if result.returncode != 0:
        print("⚠️ Remux failed, will re-encode")
        return False

    if output_path.exists() and output_path.stat().st_size > 0:
        print("✅ Remux successful")
        return True

    print("⚠️ Remux produced empty file")
    return False
