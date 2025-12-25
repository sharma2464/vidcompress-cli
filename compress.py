#!/usr/bin/env python3

import subprocess
import sys
import os
import shutil
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

# ---------------- CONFIG ----------------
MAX_JOBS = 2
DEFAULT_QUALITY = 30
VIDEO_EXTS = {".avi", ".mp4", ".mov", ".mkv", ".m4v"}
# ---------------------------------------


def which(cmd):
    return shutil.which(cmd) is not None


def platform():
    if sys.platform.startswith("darwin"):
        return "macos"
    if sys.platform.startswith("linux"):
        return "linux"
    if sys.platform.startswith("win"):
        return "windows"
    if "ANDROID_ROOT" in os.environ:
        return "android"
    return "unknown"


# ---------------- DEPENDENCIES ----------------

def ensure_dependencies(engine):
    os_type = platform()

    if os_type == "unknown":
        print("❌ Unsupported platform")
        sys.exit(1)

    if os_type == "ios":
        print("❌ iOS cannot install ffmpeg / HandBrakeCLI")
        sys.exit(1)

    if engine in ("auto", "handbrake"):
        if which("HandBrakeCLI"):
            return "handbrake"

    if engine in ("auto", "ffmpeg"):
        if which("ffmpeg"):
            return "ffmpeg"

    print("⚠️ Required tools not found, attempting install...")

    if os_type == "macos":
        if not which("brew"):
            print("❌ Homebrew not installed")
            sys.exit(1)
        subprocess.run(["brew", "install", "handbrake", "ffmpeg"], check=False)

    elif os_type == "linux":
        if which("apt"):
            subprocess.run(["sudo", "apt", "install", "-y", "handbrake-cli", "ffmpeg"], check=False)
        elif which("dnf"):
            subprocess.run(["sudo", "dnf", "install", "-y", "HandBrake-cli", "ffmpeg"], check=False)

    elif os_type == "android":
        subprocess.run(["pkg", "install", "-y", "ffmpeg"], check=False)

    # Recheck
    if engine != "ffmpeg" and which("HandBrakeCLI"):
        return "handbrake"
    if which("ffmpeg"):
        return "ffmpeg"

    print("❌ Could not install required tools")
    sys.exit(1)


# ---------------- LOGIC ----------------

def is_video(path):
    return path.suffix.lower() in VIDEO_EXTS


def compress(input_path, input_root, output_root, quality, engine, single):
    if "_compressed.mp4" in input_path.name:
        return

    if single:
        out_dir = output_root
        name = input_path.name
    else:
        rel = input_path.relative_to(input_root)
        out_dir = output_root / rel.parent
        name = rel.name

    out_dir.mkdir(parents=True, exist_ok=True)
    output = out_dir / f"{Path(name).stem}_compressed.mp4"

    print(f"🎞 {name} [{engine}]")

    if engine == "handbrake":
        cmd = [
            "HandBrakeCLI",
            "-i", str(input_path),
            "-o", str(output),
            "--preset", "H.265 Apple VideoToolbox 1080p",
            "-q", str(quality),
            "--all-audio",
            "--markers",
            "--optimize",
        ]
    else:
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
            str(output),
        ]

    try:
        subprocess.run(cmd, check=True)
        subprocess.run(["touch", "-r", str(input_path), str(output)], check=False)
        print(f"✅ Done → {output}")
    except subprocess.CalledProcessError:
        print(f"❌ Failed: {input_path}")


# ---------------- MAIN ----------------

def main():
    if len(sys.argv) < 3:
        print("Usage: convert.py <input> <output> [quality] [--engine auto|handbrake|ffmpeg]")
        sys.exit(1)

    engine = "auto"
    if "--engine" in sys.argv:
        idx = sys.argv.index("--engine")
        engine = sys.argv[idx + 1]
        del sys.argv[idx:idx + 2]

    input_root = Path(sys.argv[1]).expanduser().resolve()
    output_root = Path(sys.argv[2]).expanduser().resolve()
    quality = int(sys.argv[3]) if len(sys.argv) > 3 else DEFAULT_QUALITY

    engine = ensure_dependencies(engine)

    jobs = []
    single = input_root.is_file()

    if single:
        jobs.append(input_root)
    else:
        for root, dirs, files in os.walk(input_root):
            if output_root.name in dirs:
                dirs.remove(output_root.name)
            for f in files:
                p = Path(root) / f
                if is_video(p):
                    jobs.append(p)

    print(f"Found {len(jobs)} video(s) → using {engine}")

    with ThreadPoolExecutor(MAX_JOBS) as pool:
        for job in jobs:
            pool.submit(compress, job, input_root, output_root, quality, engine, single)

    print("🎉 All conversions complete")


if __name__ == "__main__":
    main()
