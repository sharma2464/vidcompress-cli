#!/usr/bin/env python3
import sys
import os
import platform
import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

# ================= CONFIG =================
VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".m4v", ".avi", ".webm", ".3gp"}
DEFAULT_QUALITY = 28          # HandBrake RF-like
MAX_WORKERS = 2               # GPU-safe
OUTPUT_SUFFIX = "_compressed.mp4"
# ==========================================


# ================= UTILS ==================
def log(msg):
    print(msg, flush=True)


def which(cmd):
    from shutil import which as _which
    return _which(cmd) is not None


def is_video(path: Path):
    return path.suffix.lower() in VIDEO_EXTS


def already_processed(path: Path, output_root: Path):
    return (
        output_root in path.parents
        or path.name.endswith(OUTPUT_SUFFIX)
    )


def run(cmd):
    log("▶ " + " ".join(cmd))
    return subprocess.run(cmd, check=False)


# ================= PLATFORM =================
def detect_platform():
    sysname = platform.system().lower()

    if "android" in platform.platform().lower():
        return "android"
    if sysname == "darwin":
        return "macos"
    if sysname == "windows":
        return "windows"
    return "linux"


def select_engine():
    plat = detect_platform()

    if plat == "macos" and which("HandBrakeCLI"):
        return "handbrake"
    if which("ffmpeg"):
        return "ffmpeg"

    log("❌ No supported encoder found (HandBrakeCLI or ffmpeg)")
    sys.exit(1)


# ================= ENGINES ==================
def remux_possible(input_path: Path):
    # MOV → MP4 safe remux
    return input_path.suffix.lower() in {".mov", ".mp4", ".m4v"}


def ffmpeg_remux(input_path: Path, output_path: Path):
    cmd = [
        "ffmpeg",
        "-y",
        "-i", str(input_path),
        "-map", "0:v:0",
        "-map", "0:a?",
        "-map_metadata", "0",
        "-c", "copy",
        "-movflags", "+faststart",
        str(output_path)
    ]
    return run(cmd)


def ffmpeg_encode(input_path: Path, output_path: Path, quality: int, platform_name):
    cmd = ["ffmpeg", "-y", "-i", str(input_path)]

    # Hardware acceleration (best effort)
    if platform_name == "macos":
        cmd += ["-c:v", "hevc_videotoolbox", "-tag:v", "hvc1"]
        cmd += ["-b:v", f"{max(800, 6000 - quality * 150)}k"]
    else:
        cmd += ["-c:v", "libx265", "-crf", str(quality)]

    cmd += [
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
        str(output_path)
    ]

    return run(cmd)


def handbrake_encode(input_path: Path, output_path: Path, quality: int):
    cmd = [
        "HandBrakeCLI",
        "-i", str(input_path),
        "-o", str(output_path),
        "--preset", "H.265 Apple VideoToolbox 1080p",
        "-q", str(quality),
        "--all-audio",
        "--all-subtitles",
        "--markers",
        "--optimize"
    ]
    return run(cmd)


# ================= WORKER ==================
def process_one(
    input_path: Path,
    input_root: Path,
    output_root: Path,
    engine: str,
    quality: int,
    platform_name: str,
    single_file: bool,
):
    if already_processed(input_path, output_root):
        log(f"⏭ Skipping: {input_path}")
        return

    if single_file:
        out_dir = output_root
        name = input_path.name
    else:
        rel = input_path.relative_to(input_root)
        out_dir = output_root / rel.parent
        name = rel.name

    out_dir.mkdir(parents=True, exist_ok=True)
    output_path = out_dir / (input_path.stem + OUTPUT_SUFFIX)

    log(f"🎞 Processing: {name}")

    # 1️⃣ Try remux
    if engine == "ffmpeg" and remux_possible(input_path):
        log("🔁 Trying remux (no re-encode)")
        if ffmpeg_remux(input_path, output_path).returncode == 0:
            log(f"✅ Remuxed → {output_path}")
            return
        else:
            log("🔄 Remux failed, encoding instead")

    # 2️⃣ Encode
    if engine == "handbrake":
        res = handbrake_encode(input_path, output_path, quality)
    else:
        res = ffmpeg_encode(input_path, output_path, quality, platform_name)

    if res.returncode != 0 or output_path.stat().st_size == 0:
        log(f"❌ Failed: {input_path}")
        if output_path.exists():
            output_path.unlink()
    else:
        log(f"✅ Done → {output_path}")


# ================= MAIN ====================
def main():
    if len(sys.argv) < 3:
        print(
            f"Usage:\n"
            f"  {sys.argv[0]} <input_path> <output_path> [quality]\n"
        )
        sys.exit(1)

    input_root = Path(sys.argv[1]).expanduser().resolve()
    output_root = Path(sys.argv[2]).expanduser().resolve()
    quality = int(sys.argv[3]) if len(sys.argv) > 3 else DEFAULT_QUALITY

    if not input_root.exists():
        log("❌ Input path does not exist")
        sys.exit(1)

    output_root.mkdir(parents=True, exist_ok=True)

    platform_name = detect_platform()
    engine = select_engine()

    log(f"🖥 Platform: {platform_name}")
    log(f"⚙ Engine: {engine}")

    jobs = []
    single_file = input_root.is_file()

    if single_file:
        jobs.append(input_root)
    else:
        for root, dirs, files in os.walk(input_root):
            if output_root.name in dirs:
                dirs.remove(output_root.name)
            for f in files:
                p = Path(root) / f
                if is_video(p):
                    jobs.append(p)

    log(f"Found {len(jobs)} video(s)")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        for job in jobs:
            pool.submit(
                process_one,
                job,
                input_root,
                output_root,
                engine,
                quality,
                platform_name,
                single_file,
            )

    log("🎉 All conversions complete.")


if __name__ == "__main__":
    main()
