#!/usr/bin/env python3
"""Shot list of any film: yours (to check the edit) or a reference (to study it).

  python3 -I shotlist.py film.mp4 [--bpm 100] [--json out.json]

Prints every shot with its length in seconds, frames and (with --bpm) beats, plus brightness, saturation and motion.
"""
import sys, os, json, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _probe import probe, cuts, pct

ap = argparse.ArgumentParser(); ap.add_argument("src"); ap.add_argument("--bpm", type=float); ap.add_argument("--json"); ap.add_argument("--fps", type=float, default=24)
a = ap.parse_args(); fr = probe(a.src, a.fps); c = cuts(fr); end = fr[-1]["t"] + (fr[1]["t"] - fr[0]["t"] if len(fr) > 1 else 0)
shots = []
for i, s in enumerate(c):
    e = c[i + 1] if i + 1 < len(c) else end; g = [f for f in fr if s <= f["t"] < e]
    if not g: continue
    m = lambda k: sum(f[k] for f in g) / len(g)
    shots.append(dict(n=i + 1, start=round(s, 3), dur=round(e - s, 3), frames=len(g), bright=round(m("Y"), 3), sat=round(m("sat"), 3), motion=round(m("dif"), 2)))
    if a.bpm: shots[-1]["beats"] = round((e - s) * a.bpm / 60 * 2) / 2
d = [s["dur"] for s in shots]
print(f"{a.src}\n{len(shots)} shots, average {sum(d) / len(d):.2f} s, median {pct(d, .5):.2f} s, shortest {min(d):.2f} s, longest {max(d):.2f} s")
print(f"median brightness {pct([f['Y'] for f in fr], .5):.2f}, saturation {pct([f['sat'] for f in fr], .5):.2f}")
print(" #   start    len  frames" + ("  beats" if a.bpm else "") + "  bright   sat  motion")
for s in shots:
    print(f"{s['n']:2d} {s['start']:7.2f} {s['dur']:6.2f} {s['frames']:6d}" + (f" {s['beats']:6.1f}" if a.bpm else "") + f" {s['bright']:7.2f} {s['sat']:5.2f} {s['motion']:7.2f}")
if a.json: json.dump(shots, open(a.json, "w"), indent=1)
