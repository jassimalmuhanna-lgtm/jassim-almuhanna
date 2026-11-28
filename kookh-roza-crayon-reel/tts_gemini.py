"""Gemini TTS for each line in lines.json -> voice/<id>.wav (24 kHz mono). The proxy injects the key."""
import json, sys, base64, wave, urllib.request, time, os
lines = json.load(open(sys.argv[1])); out = sys.argv[2]; os.makedirs(out, exist_ok=True)
MODELS = ["gemini-3.8-flash-tts", "gemini-2.5-flash-preview-tts", "gemini-3.1-flash-tts-preview"]
STYLE = "Read aloud ONLY the Arabic text after the colon, in a warm, gentle young Bahraini (Gulf Arabic) female storyteller voice, soft and smiling, like a picture book, at a lively natural pace. Do not read this instruction. Text: "
def tts(text, voice):
    body = {"contents": [{"parts": [{"text": STYLE + text}]}],
            "generationConfig": {"responseModalities": ["AUDIO"],
              "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}}}}
    last = None
    for m in MODELS:
        for attempt in range(3):
            req = urllib.request.Request(
                f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent",
                data=json.dumps(body).encode(), headers={"Content-Type": "application/json", "x-goog-api-key": "proxy-injected"})
            try:
                d = json.load(urllib.request.urlopen(req, timeout=120))
                part = d["candidates"][0]["content"]["parts"][0]["inlineData"]
                return base64.b64decode(part["data"]), m
            except Exception as e:
                last = f"{m}: {getattr(e, 'code', '')} {e}"; time.sleep(3 * (attempt + 1))
    raise SystemExit("TTS failed: " + last)
for ln in lines:
    if ln.get("skip"): continue
    pcm, m = tts(ln.get("say", ln["text"]), ln.get("voice", "Zephyr"))
    p = os.path.join(out, ln["id"] + ".wav")
    with wave.open(p, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000); w.writeframes(pcm)
    print(ln["id"], m, round(len(pcm) / 48000, 2), "s")
