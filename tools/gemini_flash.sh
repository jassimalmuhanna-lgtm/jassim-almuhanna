#!/usr/bin/env bash
# Send a prompt to Gemini Flash (cheap model for light tasks).
# The cloud proxy injects the real key; "proxy-injected" is a placeholder.
# Usage: tools/gemini_flash.sh "prompt"   or   echo "prompt" | tools/gemini_flash.sh
# Tries each model up to 3 times (busy/503), then falls back to the next one.
set -uo pipefail
MODELS="${GEMINI_MODEL:-gemini-3.8-flash gemini-3.1-flash-lite}"
PROMPT="${1:-$(cat)}"
BODY=$(python3 -c 'import json,sys;print(json.dumps({"contents":[{"parts":[{"text":sys.argv[1]}]}]}))' "$PROMPT")
for m in $MODELS; do
  for try in 1 2 3; do
    out=$(curl -s -m 120 -H "Content-Type: application/json" -H "x-goog-api-key: proxy-injected" \
      "https://generativelanguage.googleapis.com/v1beta/models/${m}:generateContent" -d "$BODY" |
      python3 -c 'import sys,json
d=json.load(sys.stdin)
if "candidates" in d: print("".join(p.get("text","") for p in d["candidates"][0]["content"]["parts"]))
else: sys.exit("Gemini error ('"$m"'): "+json.dumps(d.get("error",d))[:300])') && { printf '%s\n' "$out"; exit 0; }
    sleep $((try * 3))
  done
done
echo "Gemini failed on all models" >&2; exit 1
