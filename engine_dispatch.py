from pathlib import Path
from engines.remux import remux
from engines.videotoolbox import encode_ffmpeg

def process_video(input_path, input_root, output_root, engine):
    rel = input_path.relative_to(input_root) if input_path.is_relative_to(input_root) else input_path.name
    out_dir = output_root / (rel.parent if isinstance(rel, Path) else "")
    out_dir.mkdir(parents=True, exist_ok=True)

    output = out_dir / f"{input_path.stem}_compressed.mp4"

    print(f"🎞 Processing: {input_path.name}")

    if engine == "remux":
        if remux(input_path, output):
            print(f"✅ Remuxed → {output}")
            return
        print("🔄 Falling back to encode")

    encode_ffmpeg(input_path, output, quality=30)
    print(f"✅ Encoded → {output}")
