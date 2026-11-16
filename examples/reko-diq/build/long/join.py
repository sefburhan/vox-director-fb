"""Join rendered parts into the full film (+ optional outro):  python3 join.py [--outro path.mp4]
Video is stream-copied (no re-encode); audio is concatenated, loudness-normalised once."""
import json, subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
ORDER = ["c00", "c01", "c02", "c03", "c04", "c05", "c06", "c07", "c08", "c09"]
parts = [c for c in ORDER if (OUT / f"{c}.mp4").exists()]
missing = [c for c in ORDER if c not in parts]
if missing:
    print("missing parts:", missing)
OUTRO = Path("/Volumes/Data/Claude.io/Video/video-gen/vox/resources/theindus.org/outro/outro-horizontal_v5/outro-horizontal_v5.mp4")
ov, oa = OUT / "outro_24.mp4", OUT / "outro.wav"
if OUTRO.exists() and (not ov.exists() or ov.stat().st_mtime < OUTRO.stat().st_mtime):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(OUTRO), "-vf", "fps=24,scale=1920:1080,format=yuv420p", "-an",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-g", "48", str(ov)], check=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(OUTRO), "-vn", "-ac", "2", "-ar", "48000", "-c:a", "pcm_s16le", str(oa)], check=True)
vids = [OUT / f"{c}.mp4" for c in parts]
(OUT / "join_v.txt").write_text("".join(f"file '{v}'\n" for v in vids))
(OUT / "join_a.txt").write_text("".join(f"file '{OUT / c}.wav'\n" for c in parts))
final = HERE.parent.parent / "reko_diq_long.mp4"
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(OUT / "join_v.txt"),
                "-f", "concat", "-safe", "0", "-i", str(OUT / "join_a.txt"), "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                "-af", "loudnorm=I=-14:TP=-1.5:LRA=11,alimiter=limit=0.84:level=false", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                str(OUT / "film_only.mp4")], check=True)
# append the outro (already -14 LUFS) without touching the film's loudness
(OUT / "join_o.txt").write_text(f"file '{OUT / 'film_only.mp4'}'\nfile '{OUT / 'outro_full.mp4'}'\n")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(ov), "-i", str(oa), "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                "-shortest", str(OUT / "outro_full.mp4")], check=True)
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(OUT / "join_o.txt"), "-c", "copy", str(final)], check=True)
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(final), "-c:v", "libx264", "-preset", "slow", "-crf", "21", "-pix_fmt", "yuv420p",
                "-c:a", "copy", "-movflags", "+faststart", str(final.with_name("reko_diq_long_upload.mp4"))], check=True)
# captions with part offsets + chapter markers for the description
off, n, srt, chap = 0.0, 1, [], []
ts = lambda x: f"{int(x // 3600):02d}:{int(x % 3600 // 60):02d}:{x % 60:06.3f}".replace(".", ",")
script = {c["id"]: c for c in json.load(open(HERE / "script.json"))}
for c in parts:
    meta = json.load(open(OUT / f"{c}.json"))
    chap.append(f"{int(off // 60)}:{int(off % 60):02d} {script[c]['title']}")
    for s, e, tx in meta["caps"]:
        srt.append(f"{n}\n{ts(s + off)} --> {ts(e + off)}\n{tx}\n")
        n += 1
    off += meta["total"]
final.with_suffix(".srt").write_text("\n".join(srt))
(HERE.parent.parent / "reko_diq_long_chapters.txt").write_text("\n".join(chap) + "\n")
print(final, f"{off / 60:.1f} min", "\n" + "\n".join(chap))
