Here’s a clean, clear, copy-paste ready README.md for your project.
It’s written to be understandable by macOS, Linux, Windows, and Android (Termux) users, with zero ambiguity about behavior.


---

🎞️ VidCompress CLI

A cross-platform video compression CLI written in Python that intelligently uses HandBrakeCLI or ffmpeg, with explicit control over remuxing vs encoding.

No silent failures. No auto-magic. You choose exactly what happens.


---

✨ Features

✅ Works on macOS, Linux, Windows, Android (Termux)

🎛 Supports HandBrakeCLI and ffmpeg

🔁 Remux is opt-in only (--remux)

🎥 Directory or single-file input

🚫 Prevents recursive compression

⚡ Uses hardware acceleration when available

📦 Zero external Python dependencies

🧵 Safe parallel processing

📜 Clear logs for every file



---

📦 Requirements

Mandatory (at least one):

ffmpeg OR

HandBrakeCLI


Optional:

Both installed → automatic best selection



---

🔧 Installation

macOS

```brew install ffmpeg handbrake```

Ubuntu / Debian

```sudo apt install ffmpeg handbrake-cli```

Arch Linux

```sudo pacman -S ffmpeg handbrake```

Windows

Install ffmpeg: https://ffmpeg.org/download.html

Install HandBrakeCLI: https://handbrake.fr/downloads2.php
Ensure both are in PATH.


Android (Termux)

```pkg install ffmpeg python```

> ⚠️ HandBrakeCLI is not supported on Android




---

🚀 Usage

```python main.py <input_path> <output_path> [options]```

Examples

Compress a directory

```python main.py ./videos ./compressed```

Compress a single file

```python main.py video.mov ./out```

Set quality (lower = better quality)

```python main.py ./videos ./out --quality 22```

Force ffmpeg

```python main.py ./videos ./out --engine ffmpeg```

Force HandBrake

```python main.py ./videos ./out --engine handbrake```

Explicit remux (no re-encode)

```python main.py ./videos ./out --remux```


---

🎛 Options

Option	Description

`--quality <int>`	Encoding quality (default: 28)
`--engine ffmpeg|handbrake`	Force encoder
`--remux`	Copy streams without re-encoding



---

🔁 Remux vs Encode

🔁 Remux (--remux)

No quality loss

Extremely fast

Only changes container (e.g. .MOV → .mp4)

Requires ffmpeg


🎞 Encode (default)

Compresses video

Smaller file size

Uses hardware acceleration when possible


> ❗ Remux is never automatic — you must explicitly enable it.




---

⚡ Hardware Acceleration

Platform	Method

macOS	VideoToolbox (HEVC)
Linux	CPU (x265)
Windows	CPU (x265)
Android	CPU (Termux ffmpeg)



---

🚫 What This Tool Will NOT Do

❌ Auto-remux behind your back

❌ Produce zero-byte files silently

❌ Re-compress already compressed output

❌ Install system packages automatically



---

🧪 Tested Platforms

✅ macOS (Apple Silicon)

✅ Linux (Ubuntu, Arch)

✅ Windows 10 / 11

✅ Android (Termux)



---

📂 Output Structure

Input directory structure is preserved:
```
input/
  A/video1.mov
  B/video2.mp4

output/
  A/video1_compressed.mp4
  B/video2_compressed.mp4
```

---

🛠 Troubleshooting

Nothing happens?

Ensure ffmpeg or HandBrakeCLI is installed

Run without --remux to force encoding

Check logs — every file prints its action


Zero-byte output?

Caused by remuxing incompatible streams

Re-run without --remux



---

📜 License

MIT — do whatever you want, just don’t blame the author 🙂


---

⭐ Future Ideas (Optional)

JSON stats per file

SSIM-based quality tuning

GUI wrapper

Preset export/import

Batch comparison vs HandBrake GUI



---

If you want, I can also generate:

--help output screenshot

Example JSON stats schema

A pyproject.toml

A GitHub Actions CI pipeline


Just say the word 🚀
