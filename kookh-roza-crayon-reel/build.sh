#!/bin/sh
# One command: voice → events → picture → mix → master.  Needs the Lemo-Opuscar library (LIB) and ffmpeg 7+.
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
LIB=${LIB:-$HOME/lemo-opuscar}
export LIB
[ -f "$LIB/core/render/video.mjs" ] || { echo "set LIB to the Lemo-Opuscar library folder"; exit 1; }
[ -f "$HERE/voice/l1.wav" ] || { python3 "$HERE/tts_gemini.py" "$HERE/lines.json" "$HERE/voice"; }
cd "$LIB"
export LEMO_ANGLE=${LEMO_ANGLE:-swiftshader}
node core/render/events.mjs "$HERE" --size 1080x1920
node core/render/readcheck.mjs "$HERE" --size 1080x1920 --step 0.1
node core/render/video.mjs "$HERE" --size 1080x1920 --fps 24 --workers 2 --out "$HERE/out/video.mp4"
"$LIB/.venv/bin/python" "$HERE/mix.py"
sh core/render/mux.sh "$HERE/out/video.mp4" "$HERE/out/mix.wav" "$HERE/kookh-roza-reel.mp4" 24 0
