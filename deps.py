import subprocess
import sys
from utils import which, detect_platform

def ensure_dependencies(engine: str) -> str:
    os_type = detect_platform()

    # -------- Android / Termux --------
    if os_type == "android":
        print("📱 Android detected (Termux)")
        if which("ffmpeg"):
            return "ffmpeg"

        print("📦 Installing ffmpeg (Termux)...")
        subprocess.run(["pkg", "install", "-y", "ffmpeg"], check=False)

        if which("ffmpeg"):
            return "ffmpeg"

        print("❌ ffmpeg installation failed on Termux")
        sys.exit(1)

    # -------- macOS --------
    if os_type == "macos":
        if engine in ("auto", "handbrake") and which("HandBrakeCLI"):
            return "handbrake"
        if engine in ("auto", "ffmpeg") and which("ffmpeg"):
            return "ffmpeg"

        if not which("brew"):
            print("❌ Homebrew not installed")
            sys.exit(1)

        print("📦 Installing ffmpeg + handbrake (brew)")
        subprocess.run(["brew", "install", "ffmpeg", "handbrake"], check=False)

    # -------- Linux --------
    elif os_type == "linux":
        if engine in ("auto", "handbrake") and which("HandBrakeCLI"):
            return "handbrake"
        if engine in ("auto", "ffmpeg") and which("ffmpeg"):
            return "ffmpeg"

        print("📦 Installing ffmpeg + handbrake (apt)")
        subprocess.run(
            ["sudo", "apt", "install", "-y", "ffmpeg", "handbrake-cli"],
            check=False,
        )

    # -------- Windows --------
    elif os_type == "windows":
        if which("ffmpeg"):
            return "ffmpeg"
        if which("HandBrakeCLI"):
            return "handbrake"

        print("❌ Please install ffmpeg or HandBrakeCLI manually on Windows")
        sys.exit(1)

    # -------- Final check --------
    if which("HandBrakeCLI"):
        return "handbrake"
    if which("ffmpeg"):
        return "ffmpeg"

    print("❌ No supported video engine available")
    sys.exit(1)
