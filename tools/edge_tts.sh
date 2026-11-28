#!/usr/bin/env bash
# Free Microsoft Edge neural voices (no account, no key). Unofficial: may stop working.
# Usage: tools/edge_tts.sh "النص" out.mp3 [voice] [rate]
# Gulf voices: ar-BH-LailaNeural (Bahrain), ar-KW-NouraNeural (Kuwait), ar-AE-FatimaNeural (UAE)
# Needs host speech.platform.bing.com allowed (done in the cloud environment).
set -euo pipefail
command -v edge-tts >/dev/null || pip install -q --break-system-packages edge-tts
export SSL_CERT_FILE="${SSL_CERT_FILE:-/root/.ccr/ca-bundle.crt}"
P="${HTTPS_PROXY:-${https_proxy:-}}"
edge-tts ${P:+--proxy "$P"} --voice "${3:-ar-BH-LailaNeural}" --rate="${4:-+0%}" --text "$1" --write-media "$2"
