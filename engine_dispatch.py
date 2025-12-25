from engines.remux import remux
from engines.videotoolbox import encode_ffmpeg

def process_video(engine, input_path, output_path, quality):
    if engine == "remux":
        success = remux(input_path, output_path)
        if success:
            return
        print("🔄 Falling back to ffmpeg encode")

    # Default encode path
    encode_ffmpeg(input_path, output_path, quality)
