"""Render ONE part of the long film:  python3 part.py c03 stills|render
Output: out/c03.mp4 (video), out/c03.wav (mix), out/c03.json (duration + captions).
Change a chapter -> re-run only that chapter, then join.py."""
import sys, time
sys.path.insert(0, __import__("os").path.dirname(__file__))
import kit

if __name__ == "__main__":
    cid, mode = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else "stills")
    t = time.time()
    P, caps = kit.load(cid)
    print(f"{cid}: {P.total:.1f}s, {len(P.shots)} shots, {len(P.sfx)} sfx, {len(P.music)} cues")
    if mode == "stills":
        print(kit.stills(cid))
    else:
        print(kit.render_part(cid, int(sys.argv[3]) if len(sys.argv) > 3 else 10), f"({time.time() - t:.0f}s)")
