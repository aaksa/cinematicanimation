#!/usr/bin/env python3
"""GATE L - is this picture as dark, as deep and as controlled as the reference films?

  python3 -I look_gate.py <still.png | frames_dir | film.mp4> [--look amber|noir|any] [--fps 24]

Targets are the measured ranges of the two reference films (references/reference-films.md), with some room.
Exit code 1 when a FAIL is present. A FAIL is fixed in the lighting, never by grading it away.
"""
import sys, os, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _probe import probe, cuts, pct

ap = argparse.ArgumentParser(); ap.add_argument("src"); ap.add_argument("--look", default="any"); ap.add_argument("--fps", type=float, default=24)
a = ap.parse_args(); fr = probe(a.src, a.fps)
fr = [f for f in fr if f["mx"] > 0.06] or fr          # ignore full-black frames (end cards, the cut to black)
SAT = {"amber": (0.10, 0.30), "noir": (0.03, 0.14), "any": (0.03, 0.30)}[a.look]
rows = [  # name, value, pass range, warn range, advice
    ("median brightness", pct([f["Y"] for f in fr], .5), (0.10, 0.26), (0.07, 0.32),
     "too bright: remove fill, lower the key, darken walls / too dark: nothing reads, raise the key (not the world)"),
    ("shadow level (10th pct pixel)", pct([f["lo"] for f in fr], .5), (0.0, 0.09), (0.0, 0.13), "shadows are grey: less haze, less world light, no fill"),
    ("bright level (90th pct pixel)", pct([f["hi"] for f in fr], .5), (0.22, 0.56), (0.15, 0.66), "the lit area is too large or too small: narrow or widen the key"),
    ("peak (brightest pixel)", pct([f["mx"] for f in fr], .5), (0.85, 1.0), (0.70, 1.0), "no true highlight: put a lamp, a glint or a neon tube in frame"),
    ("black floor (darkest pixel)", pct([f["mn"] for f in fr], .5), (0.0, 0.05), (0.0, 0.08), "blacks are lifted too far"),
    ("saturation", pct([f["sat"] for f in fr], .5), SAT, (SAT[0] * 0.6, SAT[1] * 1.3), "outside the look's range: one dominant colour, small accents"),
]
bad = 0; print(f"GATE L  {a.src}  ({len(fr)} frame{'s' * (len(fr) != 1)}, look={a.look})")
for name, v, ok, warn, tip in rows:
    st = "ok  " if ok[0] <= v <= ok[1] else "WARN" if warn[0] <= v <= warn[1] else "FAIL"; bad += st == "FAIL"
    print(f"  [{st}] {name:32s} {v:5.2f}   target {ok[0]:.2f}-{ok[1]:.2f}" + ("" if st == "ok  " else f"   -> {tip}"))
if len(fr) > 2:
    c = cuts(fr); ct = set(round(x, 3) for x in c)
    jumps = [f["t"] for i, f in enumerate(fr[1:], 1) if abs(f["Y"] - fr[i - 1]["Y"]) > 0.06 and round(f["t"], 3) not in ct]
    st = "ok  " if not jumps else "WARN"
    print(f"  [{st}] brightness jumps inside a shot    {len(jumps):3d}" + ("" if not jumps else f"   -> a flash or flicker (fine if it is a designed light, e.g. lightning) near {', '.join(f'{t:.2f}s' for t in jumps[:8])}"))
    d = [b - x for x, b in zip(c, c[1:] + [fr[-1]['t'] + 1 / a.fps])]
    print(f"  shots: {len(c)}, average {sum(d) / len(d):.2f} s, shortest {min(d):.2f} s, longest {max(d):.2f} s")
sys.exit(1 if bad else 0)
