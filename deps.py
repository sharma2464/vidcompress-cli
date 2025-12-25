import subprocess
import sys
from utils import which, detect_platform

def ensure_dependencies(engine: str) -> str:
    os_type = detect_platform()

    if os_type == "unknown":
        print("❌ Unsupported platform")
        sys.exit(1)

    if engine in ("auto", "handbrake") and which("HandBrakeCLI"):
        return "handbrake"

    if engine in ("auto", "ffmpeg") and which("ffmpeg"):
        return "ffmpeg"

    print("⚠️ Installing dependencies...")

    if os_type == "macos":
        if not which("brew"):
            print("❌ Homebrew not installed")
            sys.exit(1)
        subprocess.run(["brew", "install", "handbrake", "ffmpeg"], check=False)

    elif os_type == "linux":
        subprocess.run(["sudo", "apt", "install", "-y", "handbrake-cli", "ffmpeg"], check=False)

    elif os_type == "android":
        subprocess.run(["pkg", "install", "-y", "ffmpeg"], check=False)

    if which("HandBrakeCLI"):
        return "handbrake"
    if which("ffmpeg"):
        return "ffmpeg"

    print("❌ Required tools not available")
    sys.exit(1)
