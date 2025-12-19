## 🎞️ Vibe-Compressed: Metadata-Preserving Video Optimizer
A Python-based automation tool that wraps HandBrakeCLI to batch-compress video libraries while strictly preserving the "soul" of your files. Unlike most converters, this tool ensures your original timestamps (Last Modified), all audio tracks, subtitles, and markers remain intact.

## ✨ Why this exists?
Standard video conversion GUIs often strip away metadata or reset file creation dates to the current time. This breaks library organization in apps like Plex, Photos, or Finder. This script was "vibe coded" to solve that—optimizing file size without losing the history of the media.

## 🚀 Features
Timestamp Sync: Uses touch -r to map the original file's modification date to the compressed output.

Hardware Accelerated: Defaulted to H.265 Apple VideoToolbox for blazing-fast encodes on M-series chips.

Batch Processing: Recursively walks through folders to find and compress videos.

Concurrency: Multi-threaded execution (configured for M2 Pro) to handle multiple jobs at once.

Metadata Heavy: Retains all audio streams, subtitle tracks, and chapter markers.

Smart Skipping: Automatically detects and skips already compressed files to prevent loops.

## 🛠️ Prerequisites
Ensure you have the following installed:

Python 3.x

HandBrakeCLI:

Bash
brew install handbrake
## 📥 Installation
Clone this repository or download the script.

Make the script executable:

Bash
chmod +x compress.py
## 📖 Usage
The script takes an input path (file or folder), an output destination, and an optional quality setting.

Bash
python3 compress.py <input_path> <output_path> [quality]
Examples:

Single File:

Bash
python3 compress.py vacation.mov ./backups
Entire Directory:

Bash
python3 compress.py ~/Movies/2023 ~/Movies/Compressed 18
## ⚙️ Configuration
You can tweak the constants at the top of the script to match your hardware:

MAX_GPU_JOBS: Set this based on your GPU cores (Default is 2 for M2 Pro).

DEFAULT_QUALITY: Higher is lower quality (18-22 is the sweet spot for H.265).

VIDEO_EXTS: Add or remove supported file formats.

## 📝 License
MIT License - Feel free to use and modify for your own library vibes.
