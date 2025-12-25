import shutil
import sys
import os

def which(cmd: str) -> bool:
    return shutil.which(cmd) is not None


def detect_platform() -> str:
    # -------- Termux / Android --------
    if os.environ.get("TERMUX_VERSION"):
        return "android"

    if os.path.exists("/data/data/com.termux"):
        return "android"

    # -------- iOS (Pythonista, Pyto) --------
    if sys.platform == "darwin" and os.path.exists("/Applications"):
        if "iPhone" in os.uname().machine or "iPad" in os.uname().machine:
            return "ios"

    # -------- Desktop --------
    if sys.platform == "darwin":
        return "macos"

    if sys.platform.startswith("linux"):
        return "linux"

    if sys.platform.startswith("win"):
        return "windows"

    return "unknown"
