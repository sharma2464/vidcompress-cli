import shutil
import sys
import os

def which(cmd: str) -> bool:
    return shutil.which(cmd) is not None

def detect_platform():
    if sys.platform.startswith("darwin"):
        return "macos"
    if sys.platform.startswith("linux"):
        return "linux"
    if sys.platform.startswith("win"):
        return "windows"
    if "ANDROID_ROOT" in os.environ:
        return "android"
    return "unknown"
