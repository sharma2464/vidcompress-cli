import os
import subprocess
import sys
import time
import shutil
from pathlib import Path

# ================= CONFIG =================
SERIAL = "192.168.1.11:5555"
DEVICE_SRC_DIR = "/sdcard/DCIM/Camera/"
DEVICE_DEST_DIR = "/sdcard/DCIM/Videos/"
DEVICE_ORIG_DIR = "/sdcard/DCIM/Originals/"

LOCAL_TMP_DIR = Path("tmp_processing").resolve()
LOCAL_INPUT_DIR = LOCAL_TMP_DIR / "input"
LOCAL_OUTPUT_DIR = LOCAL_TMP_DIR / "output"
LOG_FILE = Path("compression_log.txt").resolve()

# Supported video extensions
VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".m4v", ".avi", ".webm", ".3gp"}
# ==========================================


def log(message):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    formatted_msg = f"[{timestamp}] {message}"
    print(formatted_msg, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(formatted_msg + "\n")


def run_cmd(cmd, check=True):
    try:
        # log(f"▶ {' '.join(cmd)}")
        res = subprocess.run(cmd, capture_output=True, text=True, check=check)
        return res
    except subprocess.CalledProcessError as e:
        log(f"❌ ERROR executing: {' '.join(cmd)}")
        log(f"STDOUT: {e.stdout}")
        log(f"STDERR: {e.stderr}")
        raise


def adb_shell(command, check=True):
    return run_cmd(["adb", "-s", SERIAL, "shell", command], check=check)


def get_all_device_videos():
    # Gets all videos from device source directory
    cmd = f"ls -1 {DEVICE_SRC_DIR}"
    res = adb_shell(cmd)
    all_files = res.stdout.splitlines()

    videos = []
    for f in all_files:
        f = f.strip()
        if not f:
            continue
        if Path(f).suffix.lower() in VIDEO_EXTS:
            videos.append(f)
    return videos


def bulk_pull():
    log("🚀 Starting bulk pull from device...")
    if not LOCAL_INPUT_DIR.exists():
        LOCAL_INPUT_DIR.mkdir(parents=True, exist_ok=True)

    videos = get_all_device_videos()
    log(f"📱 Found {len(videos)} video(s) on device.")

    pulled_count = 0
    skipped_count = 0

    for video_name in videos:
        local_path = LOCAL_INPUT_DIR / video_name
        device_path = f"{DEVICE_SRC_DIR}{video_name}"

        # Skip if already pulled and size matches (basic check)
        if local_path.exists():
            # Get device size
            size_res = adb_shell(f'stat -c %s "{device_path}"')
            device_size = int(size_res.stdout.strip())
            if local_path.stat().st_size == device_size:
                log(f"⏭ Skipping already pulled: {video_name}")
                skipped_count += 1
                continue

        log(f"📥 Pulling: {video_name}...")
        try:
            run_cmd(["adb", "-s", SERIAL, "pull", device_path, str(local_path)])
            if local_path.exists() and local_path.stat().st_size > 0:
                log(
                    f"✅ Pull success: {video_name} ({local_path.stat().st_size / 1024 / 1024:.2f} MB)"
                )
                pulled_count += 1
            else:
                log(f"❌ Pull failed or file empty: {video_name}")
        except Exception as e:
            log(f"❌ Pull error: {video_name} - {str(e)}")

    log(f"--- Bulk pull finished: {pulled_count} new, {skipped_count} skipped. ---")


def bulk_compress():
    log("🚀 Starting sequential compression using HandBrakeCLI via main.py...")
    if not LOCAL_OUTPUT_DIR.exists():
        LOCAL_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    videos = [
        f for f in os.listdir(LOCAL_INPUT_DIR) if Path(f).suffix.lower() in VIDEO_EXTS
    ]
    videos.sort(
        key=lambda x: (LOCAL_INPUT_DIR / x).stat().st_size
    )  # Process small files first

    log(f"🎬 Found {len(videos)} local video(s) to compress.")

    success_count = 0
    fail_count = 0

    for video_name in videos:
        input_file = LOCAL_INPUT_DIR / video_name
        # main.py adds _compressed.mp4
        output_name = input_file.stem + "_compressed.mp4"
        output_file = LOCAL_OUTPUT_DIR / output_name

        if (
            output_file.exists() and output_file.stat().st_size > 1000
        ):  # Simple valid check
            log(f"⏭ Skipping already compressed: {video_name}")
            success_count += 1
            continue

        log(
            f"🎞 Compressing ({success_count + fail_count + 1}/{len(videos)}): {video_name}..."
        )

        cmd = [
            sys.executable,
            "main.py",
            str(input_file),
            str(LOCAL_OUTPUT_DIR),
            "--quality",
            "42",  # VideoToolbox 0-100 (Higher is better), 42 is high quality
        ]

        try:
            res = subprocess.run(cmd, capture_output=True, text=True)
            if (
                res.returncode == 0
                and output_file.exists()
                and output_file.stat().st_size > 1000
            ):
                log(
                    f"✅ Success: {video_name} ({output_file.stat().st_size / 1024 / 1024:.2f} MB)"
                )
                success_count += 1
            else:
                log(f"❌ Failed: {video_name}")
                log(f"STDERR: {res.stderr}")
                fail_count += 1
        except Exception as e:
            log(f"❌ Error: {video_name} - {str(e)}")
            fail_count += 1

    log(f"--- Compression finished: {success_count} success, {fail_count} failed. ---")


def bulk_push():
    log("🚀 Starting bulk push to device...")

    # Ensure device target directories exist
    adb_shell(f"mkdir -p {DEVICE_DEST_DIR}")
    adb_shell(f"mkdir -p {DEVICE_ORIG_DIR}")

    local_videos = [
        f for f in os.listdir(LOCAL_OUTPUT_DIR) if f.endswith("_compressed.mp4")
    ]
    log(f"📦 Found {len(local_videos)} compressed video(s) to push.")

    pushed_count = 0
    moved_count = 0

    for compressed_name in local_videos:
        local_path = LOCAL_OUTPUT_DIR / compressed_name
        # The original name is the stem minus '_compressed'
        original_name = compressed_name.replace(
            "_compressed.mp4", ".mp4"
        )  # This handles our OUTPUT_SUFFIX

        device_dest_path = f"{DEVICE_DEST_DIR}{compressed_name}"
        device_src_path = f"{DEVICE_SRC_DIR}{original_name}"
        device_orig_path = f"{DEVICE_ORIG_DIR}{original_name}"

        # 1. Push compressed file
        log(f"📤 Pushing: {compressed_name}...")
        try:
            # Check if already pushed
            size_res = adb_shell(f'stat -c %s "{device_dest_path}"', check=False)
            if size_res.returncode == 0:
                device_size = int(size_res.stdout.strip())
                if local_path.stat().st_size == device_size:
                    log(f"⏭ Already pushed: {compressed_name}")
                else:
                    run_cmd(
                        ["adb", "-s", SERIAL, "push", str(local_path), device_dest_path]
                    )
            else:
                run_cmd(
                    ["adb", "-s", SERIAL, "push", str(local_path), device_dest_path]
                )

            # Verify push
            size_res = adb_shell(f'stat -c %s "{device_dest_path}"')
            if int(size_res.stdout.strip()) == local_path.stat().st_size:
                log(f"✅ Push verified: {compressed_name}")
                pushed_count += 1
            else:
                log(f"❌ Push verification failed: {compressed_name}")
                continue

            # 2. Move original file on device
            # Check if original exists in source
            src_exists = adb_shell(f'ls "{device_src_path}"', check=False)
            if src_exists.returncode == 0:
                log(f"📦 Moving original: {original_name} -> {DEVICE_ORIG_DIR}")
                adb_shell(f'mv "{device_src_path}" "{device_orig_path}"')
                moved_count += 1
            else:
                # Check if already in Originals
                orig_exists = adb_shell(f'ls "{device_orig_path}"', check=False)
                if orig_exists.returncode == 0:
                    log(f"⏭ Original already moved: {original_name}")
                else:
                    log(f"⚠️ Original not found in source or archive: {original_name}")

        except Exception as e:
            log(f"❌ Sync error: {compressed_name} - {str(e)}")

    log(
        f"--- Sync finished: {pushed_count} pushed, {moved_count} originals archived. ---"
    )


def main():
    if not LOCAL_TMP_DIR.exists():
        LOCAL_TMP_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Pull all files
    # bulk_pull() # Already pulled 39 videos

    # 2. Compress all files
    # bulk_compress() # Already compressed 39 videos

    # 3. Push compressed back and archive originals
    bulk_push()

    log("========================================")
    log("Done! Compressed videos are in '/sdcard/DCIM/Videos/'.")
    log("Originals have been moved to '/sdcard/DCIM/Originals/'.")
    log("========================================")


if __name__ == "__main__":
    main()
