"""Speech check: Gemini Flash transcribes each voice/<id>.wav; prints transcript next to the script."""
import json, sys, base64, urllib.request, time
lines = json.load(open(sys.argv[1])); vd = sys.argv[2]
for ln in lines:
    b64 = base64.b64encode(open(f"{vd}/{ln['id']}.wav", "rb").read()).decode()
    body = {"contents": [{"parts": [{"inline_data": {"mime_type": "audio/wav", "data": b64}},
            {"text": "اكتب الكلام المنطوق في هذا الملف الصوتي حرفياً بالعربي، بدون أي إضافة أو شرح."}]}]}
    for m in ["gemini-3.8-flash", "gemini-3.1-flash-lite"]:
        try:
            req = urllib.request.Request(f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent",
                data=json.dumps(body).encode(), headers={"Content-Type": "application/json", "x-goog-api-key": "proxy-injected"})
            d = json.load(urllib.request.urlopen(req, timeout=120))
            print(ln["id"], "| script:", ln["text"], "\n    heard:", d["candidates"][0]["content"]["parts"][0]["text"].strip()); break
        except Exception as e:
            print("  retry", m, getattr(e, "code", e)); time.sleep(4)
