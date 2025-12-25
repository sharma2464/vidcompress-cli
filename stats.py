import json
import subprocess
from pathlib import Path
from datetime import datetime

def probe(path: Path):
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_format",
        "-show_streams",
        "-of", "json",
        str(path)
    ]
    out = subprocess.check_output(cmd)
    return json.loads(out)

def write_stats(input_path: Path, output_path: Path, engine: str, stats_dir: Path):
    stats_dir.mkdir(parents=True, exist_ok=True)

    data = {
        "input": str(input_path),
        "output": str(output_path),
        "engine": engine,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "input_probe": probe(input_path),
        "output_probe": probe(output_path),
    }

    stats_file = stats_dir / f"{output_path.stem}.json"
    with open(stats_file, "w") as f:
        json.dump(data, f, indent=2)

    return stats_file
