import json,sys,base64,subprocess,urllib.request,time
text,out=sys.argv[1],sys.argv[2]
body={"contents":[{"parts":[{"text":"اقرئي بصوت بنت خليجية دافي ومبتسم وهادي: "+text}]}],
 "generationConfig":{"responseModalities":["AUDIO"],"speechConfig":{"voiceConfig":{"prebuiltVoiceConfig":{"voiceName":"Zephyr"}}}}}
for m in ["gemini-2.5-flash-preview-tts","gemini-3.1-flash-tts-preview"]:
  for t in range(3):
    try:
      r=urllib.request.Request(f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent",json.dumps(body).encode(),{"Content-Type":"application/json","x-goog-api-key":"proxy-injected"})
      d=json.load(urllib.request.urlopen(r,timeout=120))
      pcm=base64.b64decode(d["candidates"][0]["content"]["parts"][0]["inlineData"]["data"])
      open(out+".pcm","wb").write(pcm)
      subprocess.run(["ffmpeg","-v","error","-y","-f","s16le","-ar","24000","-ac","1","-i",out+".pcm","-af","silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse",out],check=True)
      print(m,"ok");sys.exit(0)
    except Exception as e: print(m,e); time.sleep(4)
sys.exit(1)
