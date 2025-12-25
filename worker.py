from pathlib import Path
import subprocess
from stats import write_stats

def run_job(engine_module, engine_name, input_path, input_root, output_root, quality, single):
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

    print(f"🎞 {name} [{engine_name}]")

    engine_module.compress(input_path, output, quality)
    subprocess.run(["touch", "-r", str(input_path), str(output)], check=False)

    stats_path = write_stats(input_path, output, engine_name, output_root / "_stats")
    print(f"📊 Stats → {stats_path}")
    print(f"✅ Done → {output}")
