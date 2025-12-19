#!/usr/bin/env python3

import subprocess
from pathlib import Path
import json

VIDEO_EXTS = {".mov", ".mkv", ".avi", ".webm", ".mp4", ".m4v"}
MP4_VIDEO_CODECS = {"h264", "hevc"}
MP4_AUDIO_CODECS = {"aac", "mp3"}


def probe_codecs(path: Path):
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_streams",
        "-of", "json",
        str(path)
    ]
    out = subprocess.check_output(cmd)
    data = json.loads(out)
    vcodec = acodec = None
    for s in data["streams"]:
        if s["codec_type"] == "video":
            vcodec = s["codec_name"]
        if s["codec_type"] == "audio":
            acodec = s["codec_name"]
    return vcodec, acodec


def convert_to_mp4(input_path: Path, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{input_path.stem}.mp4"

    vcodec, acodec = probe_codecs(input_path)

    print(f"🎞 {input_path.name}")
    print(f"   Video: {vcodec}  Audio: {acodec}")

    if vcodec in MP4_VIDEO_CODECS and acodec in MP4_AUDIO_CODECS:
        print("🔁 Remuxing (lossless)")
        cmd = [
            "ffmpeg",
            "-i", str(input_path),

            "-map", "0:v",
            "-map", "0:a?",
            "-map_metadata", "0",
            "-map_chapters", "0",
            
            "-sn", "-dn",

            "-c", "copy",
            "-movflags", "+faststart",
            str(output_path)
        ]
    else:
        print("🎬 Transcoding (high quality) (GPU Accelerated)")
        cmd = [
            "ffmpeg",
            "-loglevel", "verbose",
            "-hwaccel", "videotoolbox",
            "-i", str(input_path),

            "-map", "0:v",
            "-map", "0:a?",
            "-map_metadata", "0",
            "-map_chapters", "0",
            
            "-sn", "-dn",

            "-c:v", "hevc_videotoolbox",
            "-tag:v", "hvc1",
            "-b:v", "5000k",

            "-preset", "slow",
            "-pix_fmt", "yuv420p",

            "-c:a", "aac",
            "-b:a", "160k",
            "-movflags", "+faststart",
            str(output_path)
        ]

    subprocess.run(cmd, check=True)
    subprocess.run(["touch", "-r", str(input_path), str(output_path)])

    print(f"✅ Output → {output_path}\n")


def main():
    import sys
    if len(sys.argv) < 3:
        print("Usage: convert.py <input> <output_dir>")
        return

    input_path = Path(sys.argv[1]).resolve()
    output_dir = Path(sys.argv[2]).resolve()

    if input_path.is_file():
        convert_to_mp4(input_path, output_dir)
    else:
        for p in input_path.rglob("*"):
            if p.suffix.lower() in VIDEO_EXTS:
                convert_to_mp4(p, output_dir)


if __name__ == "__main__":
    main()
