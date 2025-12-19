#!/usr/bin/env bash
set -euo pipefail

############################################
# CONFIG (safe defaults)
############################################
CRF_LIKE=15                 # 10–30 (HandBrake-like)
PARALLEL=4                  # GPU-safe parallel jobs
OUTPUT_ROOT="compressed"
REALTIME=false

############################################
# USAGE / VALIDATION
############################################
if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <file-or-directory> [crf-like]"
  exit 1
fi

INPUT_PATH="$1"
CRF_LIKE="${2:-$CRF_LIKE}"

############################################
# FUNCTIONS
############################################

compress_one() {
  ############################################
  # File / Folder Skipper
  if [[ "$INPUT" == *"/$OUTPUT_ROOT/"* || "$INPUT" == *_compressed.mp4 ]]; then
    echo "⏭ Skipping already compressed file: $INPUT"
    return
  fi
  ############################################


  local INPUT="$1"
  local REL_PATH="$2"
  local OUTPUT_DIR="$OUTPUT_ROOT/$(dirname "$REL_PATH")"
  local BASENAME="$(basename "$INPUT")"
  local OUTPUT="$OUTPUT_DIR/${BASENAME%.*}_compressed.mp4"

  mkdir -p "$OUTPUT_DIR"

  ############################
  # Probe resolution
  ############################
  read WIDTH HEIGHT <<<"$(
    ffprobe -v error -select_streams v:0 \
    -show_entries stream=width,height \
    -of csv=p=0:s=' ' \
    "$INPUT"
  )"

  ############################
  # Probe duration
  ############################
  DURATION="$(
    ffprobe -v error \
    -show_entries format=duration \
    -of default=noprint_wrappers=1:nokey=1 \
    "$INPUT"
  )"
  DURATION=${DURATION%.*}

  ############################
  # 4K → 1080p scaling
  ############################
  SCALE_FILTER=""
  if (( WIDTH >= 3840 || HEIGHT >= 2160 )); then
    SCALE_FILTER="-vf scale='min(1920,iw)':-2"
  fi

  ############################
  # CRF-like → base bitrate
  ############################
  case "$CRF_LIKE" in
    10) BASE_BR=10000 ;;
    11) BASE_BR=9000 ;;
    12) BASE_BR=8000 ;;
    13) BASE_BR=7000 ;;
    14) BASE_BR=6000 ;;
    15) BASE_BR=5000 ;;
    16) BASE_BR=4000 ;;
    18) BASE_BR=3500 ;;
    20) BASE_BR=3000 ;;
    22) BASE_BR=2500 ;;
    24) BASE_BR=2000 ;;
    26) BASE_BR=1600 ;;
    28) BASE_BR=1200 ;;
    *)  BASE_BR=2000 ;;
  esac

  ############################
  # Auto bitrate by duration
  ############################
  if (( DURATION > 60 )); then
    BR=$((BASE_BR * 70 / 100))
  elif (( DURATION < 30 )); then
    BR=$((BASE_BR * 120 / 100))
  else
    BR=$BASE_BR
  fi

  MAXRATE=$((BR * 125 / 100))
  BUFSIZE=$((BR * 200 / 100))

  ############################
  # HDR detection → 10-bit
  ############################
  HDR=false
  VT_PROFILE=""

  HDR_INFO="$(
    ffprobe -v error -select_streams v:0 \
    -show_entries stream=color_primaries,color_transfer,color_space \
    -of default=noprint_wrappers=1 \
    "$INPUT"
  )"

  if echo "$HDR_INFO" | grep -qiE "bt2020|smpte2084|arib-std-b67"; then
    HDR=true
    VT_PROFILE="-profile:v main10"
  fi

  # Pixel format selection
  PIX_FMT="yuv420p"
  COLOR_OPTS=""
  
  if [[ "$HDR" == true ]]; then
    PIX_FMT="yuv420p10le"
    COLOR_OPTS="-color_primaries bt2020 -color_trc smpte2084 -colorspace bt2020nc"
  fi

  # Build filter chain
  FILTERS="hqdn3d=1.0:1.0:2.0:2.0"
  if [[ -n "$SCALE_FILTER" ]]; then
    FILTERS="${FILTERS},scale='min(1920,iw)':-2"
  fi

  ############################
  # Info
  ############################
  echo "────────────────────────────────────────────"
  echo "🎞  $REL_PATH"
  echo "Res: ${WIDTH}x${HEIGHT}  Dur: ${DURATION}s"
  echo "BR:  ${BR}k  HDR: $HDR"
  echo "────────────────────────────────────────────"

  ############################
  # Encode (with fallback)
  ############################
  if ! ffmpeg \
    -hide_banner \
    -stats -stats_period 1 \
    -hwaccel videotoolbox \
    -i "$INPUT" \
    \
    -map 0:v \
    -map 0:a? \
    -map_metadata 0 \
    -map_chapters 0 \
    \
    -vf "$FILTERS" \
    \
    -c:v hevc_videotoolbox \
    $VT_PROFILE \
    -allow_sw 0 \
    -tag:v hvc1 \
    -pix_fmt "$PIX_FMT" \
    -color_range tv \
    $COLOR_OPTS \
    \
    -g 48 \
    -b:v "${BR}k" \
    -maxrate "${MAXRATE}k" \
    -bufsize "${BUFSIZE}k" \
    -realtime "$REALTIME" \
    \
    -c:a aac -b:a 128k \
    \
    -movflags +faststart+write_colr \
    "$OUTPUT"
  then
    echo "⚠️ VideoToolbox failed — retrying without HDR profile"
    ffmpeg \
      -hide_banner \
      -stats -stats_period 1 \
      -hwaccel videotoolbox \
      -i "$INPUT" \
      \
      -map 0:v \
      -map 0:a? \
      -map_metadata 0 \
      -map_chapters 0 \
      \
      ${SCALE_FILTER} \
      \
      -c:v hevc_videotoolbox \
      -allow_sw 0 \
      -tag:v hvc1 \
      -pix_fmt "$PIX_FMT" \
      -b:v "${BR}k" \
      -maxrate "${MAXRATE}k" \
      -bufsize "${BUFSIZE}k" \
      -realtime "$REALTIME" \
      \
      -c:a aac -b:a 128k \
      \
      -movflags +faststart \
      "$OUTPUT"
  fi

  touch -r "$INPUT" "$OUTPUT"
  echo "✅ Done → $OUTPUT"
}

export -f compress_one
export CRF_LIKE OUTPUT_ROOT

############################################
# FILE COLLECTION (exclude output dir)
############################################
FILES=()

if [[ -f "$INPUT_PATH" ]]; then
  FILES+=("$INPUT_PATH")

elif [[ -d "$INPUT_PATH" ]]; then
  while IFS= read -r -d '' f; do
    FILES+=("$f")
  done < <(
    find "$INPUT_PATH" \
      -type d -name "$OUTPUT_ROOT" -prune -o \
      -type f \( -iname "*.mp4" -o -iname "*.mov" -o -iname "*.mkv" -o -iname "*.m4v" \) \
      -print0
  )
else
  echo "❌ Invalid input: $INPUT_PATH"
  exit 1
fi


############################################
# RUN IN PARALLEL
############################################
echo "Found ${#FILES[@]} video(s)"
printf "%s\n" "${FILES[@]}" | xargs -P "$PARALLEL" -I{} bash -c '
  REL="${1#'"$INPUT_PATH"'/}"
  compress_one "$1" "$REL"
' _ {}

echo "🎉 All conversions complete."
