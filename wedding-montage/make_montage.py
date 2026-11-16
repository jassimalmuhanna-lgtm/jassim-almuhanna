#!/usr/bin/env python3
"""Wedding (عقد قران) montage builder.

Takes N video clips, cuts them into short segments, stabilises and colour-grades
each one (warm, soft, clear light), joins them with soft cross-fades and keeps
the final video at or under --max seconds. Music is optional (--music).

Usage:
  python3 make_montage.py clip1.mov clip2.mov clip3.mov -o montage.mp4 \
      [--music song.mp3] [--max 40] [--res 2160] [--work /tmp/work]
"""
import argparse, json, os, subprocess, sys

XF = 0.6          # cross-fade length (s)
TRIM = 0.4        # skip shaky start/end of every clip (s)
SEG_MIN, SEG_MAX = 2.8, 5.0
FPS = 30

# Warm, soft, clear look: light denoise, lifted shadows, gentle highlight
# roll-off, slight warmth and saturation, mild sharpening.
GRADE = (
    "hqdn3d=1.5:1.5:3:3,"
    "eq=contrast=1.04:brightness=0.015:saturation=1.08:gamma=1.03,"
    "curves=all='0/0.02 0.25/0.27 0.5/0.52 0.85/0.85 1/0.96',"
    "colorbalance=rs=0.02:bs=-0.02:rm=0.03:bm=-0.03:rh=0.015:bh=-0.02,"
    "unsharp=5:5:0.35:5:5:0"
)


def run(cmd):
    print("+", " ".join(cmd[:6]), "...", flush=True)
    subprocess.run(cmd, check=True)


def probe(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-print_format", "json", "-show_streams",
         "-show_format", path], capture_output=True, text=True, check=True).stdout
    j = json.loads(out)
    v = next(s for s in j["streams"] if s["codec_type"] == "video")
    w, h = int(v["width"]), int(v["height"])
    rot = 0
    for sd in v.get("side_data_list", []):
        if "rotation" in sd:
            rot = int(sd["rotation"])
    if abs(rot) % 180 == 90:
        w, h = h, w
    has_audio = any(s["codec_type"] == "audio" for s in j["streams"])
    ctime = j["format"].get("tags", {}).get("creation_time", "")
    return dict(path=path, w=w, h=h, dur=float(j["format"]["duration"]),
                audio=has_audio, ctime=ctime)


def plan(clips, max_len):
    """Return list of (clip, start, length) in chronological order."""
    usable = [max(0.0, c["dur"] - 2 * TRIM) for c in clips]
    total_usable = sum(usable)
    # content we may use: final = sum(seg) - (n-1)*XF  <= max_len - 0.3
    n_target = max(len(clips), min(10, int(total_usable // 3.5)))
    budget = max_len - 0.3 + (n_target - 1) * XF
    segs = []
    for c, u in zip(clips, usable):
        if u <= 0.5:
            continue
        share = budget * u / total_usable
        avail = min(share, u)
        k = max(1, round(avail / 4.5))
        seg_len = max(min(SEG_MIN, u), min(SEG_MAX, avail / k))
        # spread k segments evenly over the usable range
        gap = (u - k * seg_len) / (k + 1) if k > 0 else 0
        for i in range(k):
            start = TRIM + gap * (i + 1) + seg_len * i
            segs.append([c, start, seg_len])
    # shrink uniformly if still too long
    final = sum(s[2] for s in segs) - (len(segs) - 1) * XF
    if final > max_len - 0.3:
        scale = (max_len - 0.3 + (len(segs) - 1) * XF) / sum(s[2] for s in segs)
        for s in segs:
            s[2] *= scale
    return segs


def render_segment(i, seg, W, H, work, stabilise):
    c, start, length = seg
    out = os.path.join(work, f"seg_{i:02d}.mov")
    trf = os.path.join(work, f"seg_{i:02d}.trf")
    base = ["ffmpeg", "-v", "error", "-y", "-ss", f"{start:.3f}", "-t",
            f"{length:.3f}", "-i", c["path"]]
    stab = ""
    if stabilise:
        run(base + ["-vf", f"vidstabdetect=shakiness=5:accuracy=15:result={trf}",
                    "-f", "null", "-"])
        stab = f"vidstabtransform=input={trf}:smoothing=20:zoom=3:interpol=bicubic,"
    portrait_target = H > W
    portrait_src = c["h"] > c["w"]
    if portrait_target == portrait_src:
        fit = (f"scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,"
               f"crop={W}:{H}")
        vf = f"[0:v]{stab}{fit},{GRADE},fps={FPS},format=yuv420p[v]"
    else:
        # orientation mismatch: blurred fill background + sharp centred clip
        vf = (f"[0:v]{stab}{GRADE},fps={FPS},split[a][b];"
              f"[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
              f"gblur=sigma=40,eq=brightness=-0.08[bg];"
              f"[b]scale={W}:{H}:force_original_aspect_ratio=decrease:flags=lanczos[fg];"
              f"[bg][fg]overlay=(W-w)/2:(H-h)/2,format=yuv420p[v]")
    cmd = base + ["-filter_complex", vf, "-map", "[v]"]
    if c["audio"]:
        cmd += ["-map", "0:a:0", "-c:a", "pcm_s16le", "-ar", "48000", "-ac", "2"]
    else:
        cmd += ["-f", "lavfi", "-t", f"{length:.3f}", "-i",
                "anullsrc=r=48000:cl=stereo", "-map", "1:a", "-c:a", "pcm_s16le"]
    cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "12", out]
    run(cmd)
    return out


def assemble(files, lengths, out, music, ambient_vol, W, H):
    n = len(files)
    total = sum(lengths) - (n - 1) * XF
    cmd = ["ffmpeg", "-v", "error", "-y"]
    for f in files:
        cmd += ["-i", f]
    if music:
        cmd += ["-i", music]
    fc, vlast, alast, off = [], "[0:v]", "[0:a]", 0.0
    for i in range(1, n):
        off += lengths[i - 1] - XF
        fc.append(f"{vlast}[{i}:v]xfade=transition=fade:duration={XF}:offset={off:.3f}[v{i}]")
        fc.append(f"{alast}[{i}:a]acrossfade=d={XF}[a{i}]")
        vlast, alast = f"[v{i}]", f"[a{i}]"
    fo = max(0.0, total - 1.2)
    fc.append(f"{vlast}fade=t=in:st=0:d=0.8,fade=t=out:st={fo:.3f}:d=1.2[vout]")
    amb = f"{alast}volume={ambient_vol}"
    if music:
        fc.append(f"{amb}[amb]")
        fc.append(f"[{n}:a]atrim=0:{total:.3f},asetpts=PTS-STARTPTS,"
                  f"afade=t=in:st=0:d=1,afade=t=out:st={max(0, total - 2.5):.3f}:d=2.5[mus]")
        fc.append("[mus][amb]amix=inputs=2:normalize=0,loudnorm=I=-16:TP=-1.5[aout]")
    else:
        fc.append(f"{amb},afade=t=in:st=0:d=0.8,afade=t=out:st={fo:.3f}:d=1.2,"
                  f"loudnorm=I=-18:TP=-1.5[aout]")
    cmd += ["-filter_complex", ";".join(fc), "-map", "[vout]", "-map", "[aout]",
            "-t", f"{total:.3f}",
            "-c:v", "libx264", "-preset", "slow", "-crf", "17",
            "-profile:v", "high", "-pix_fmt", "yuv420p",
            "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
            "-c:a", "aac", "-b:a", "256k", "-ar", "48000",
            "-movflags", "+faststart", out]
    run(cmd)
    return total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("clips", nargs="+")
    ap.add_argument("-o", "--out", default="montage.mp4")
    ap.add_argument("--music")
    ap.add_argument("--max", type=float, default=40.0)
    ap.add_argument("--res", type=int, default=2160, help="short side in px")
    ap.add_argument("--work", default="montage_work")
    ap.add_argument("--no-stab", action="store_true")
    ap.add_argument("--ambient", type=float, default=None,
                    help="original-audio volume (default 0.12 with music, 0.8 without)")
    a = ap.parse_args()

    os.makedirs(a.work, exist_ok=True)
    clips = sorted((probe(p) for p in a.clips), key=lambda c: (c["ctime"], c["path"]))
    portrait = sum(c["h"] > c["w"] for c in clips) * 2 >= len(clips)
    W, H = (a.res, a.res * 16 // 9) if portrait else (a.res * 16 // 9, a.res)
    W -= W % 2; H -= H % 2
    segs = plan(clips, a.max)
    for c in clips:
        print(f"clip {os.path.basename(c['path'])}: {c['dur']:.1f}s {c['w']}x{c['h']}")
    for s in segs:
        print(f"  seg {os.path.basename(s[0]['path'])} @ {s[1]:.2f}s for {s[2]:.2f}s")
    files = [render_segment(i, s, W, H, a.work, not a.no_stab) for i, s in enumerate(segs)]
    amb = a.ambient if a.ambient is not None else (0.12 if a.music else 0.8)
    total = assemble(files, [s[2] for s in segs], a.out, a.music, amb, W, H)
    print(f"done: {a.out} ({total:.1f}s, {W}x{H})")


if __name__ == "__main__":
    sys.exit(main())
