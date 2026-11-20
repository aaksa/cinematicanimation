#!/usr/bin/env python3
"""The lab: glow, grade, lens softness, vignette and grain, in ffmpeg. Raw renders stay untouched, so a look change
never costs a re-render.

  python3 -I finish.py <frames_dir | still.png | plates.mp4> --out film.mp4 [--look amber|noir|sick|cold|clean]
                       [--audio mix.wav] [--fps 24] [--grain 6] [--glow 0.5] [--crf 14]

Looks (measured from the references): amber = warm bar, rich; noir = desaturated street, teal shadow, warm lights;
sick = green-yellow menace; cold = blue hospital/night; clean = glow + grain only.
"""
import sys, os, argparse, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _probe import src_args

LOOKS = {  # saturation, contrast, colorbalance (shadows r g b, mids r g b, highs r g b)
    "amber": (1.12, 1.04, (0.05, 0.00, -0.06, 0.03, 0.00, -0.04, 0.02, 0.00, -0.03)),
    "noir": (0.55, 1.08, (-0.05, 0.01, 0.05, -0.01, 0.00, 0.01, 0.04, 0.01, -0.04)),
    "sick": (0.80, 1.05, (-0.02, 0.03, -0.05, 0.00, 0.04, -0.03, 0.02, 0.02, -0.04)),
    "cold": (0.85, 1.05, (-0.04, 0.00, 0.07, -0.02, 0.00, 0.04, 0.00, 0.00, 0.02)),
    "clean": (1.0, 1.0, (0,) * 9),
}
ap = argparse.ArgumentParser(); ap.add_argument("src"); ap.add_argument("--out", required=True); ap.add_argument("--look", default="amber", choices=LOOKS)
ap.add_argument("--audio"); ap.add_argument("--fps", type=float, default=24); ap.add_argument("--grain", type=int, default=6)
ap.add_argument("--glow", type=float, default=0.5); ap.add_argument("--crf", type=int, default=14)
a = ap.parse_args(); sat, con, cb = LOOKS[a.look]; args, n = src_args(a.src, a.fps)
w = int(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width", "-of", "csv=p=0",
                        *( [args[-1]] if n is None else ["-f", "concat", "-safe", "0", args[-1]])], capture_output=True, text=True).stdout.split()[0])
k = max(1, round(w / 1920))                               # pixel-sized effects scale with the frame
cbs = ":".join(f"{nm}={v}" for nm, v in zip(("rs", "gs", "bs", "rm", "gm", "bm", "rh", "gh", "bh"), cb))
vf = (f"format=gbrp16le,split[a][b];[b]curves=all='0/0 0.55/0 1/1',gblur=sigma={w * 0.014:.1f}[g];"       # highlights only, blurred wide
      f"[a][g]blend=all_mode=screen:all_opacity={a.glow},"                                               # = glow round lamps and neon
      f"colorbalance={cbs},eq=saturation={sat}:contrast={con},"
      f"curves=all='0/0.018 0.25/0.235 0.75/0.76 1/0.975',"                                               # lifted black, soft shoulder (film print)
      f"gblur=sigma={0.45 * k:.2f},rgbashift=rh={-k}:bh={k},"                                             # lens softness + a hair of colour fringing
      f"vignette=angle=PI/5.5,noise=alls={a.grain}:allf=t+u,format=yuv420p")
still = a.out.lower().endswith((".png", ".jpg", ".jpeg"))
cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *args] + (["-i", a.audio] if a.audio else []) + ["-vf", vf]
if still: cmd += ["-frames:v", "1", "-update", "1", "-q:v", "2", a.out]
else:
    cmd += ["-r", str(a.fps), "-c:v", "libx264", "-preset", "slow", "-crf", str(a.crf), "-pix_fmt", "yuv420p", "-colorspace", "bt709",
            "-color_primaries", "bt709", "-color_trc", "bt709", "-movflags", "+faststart"]
    if a.audio: cmd += ["-c:a", "aac", "-b:a", "256k", "-shortest"]
    cmd += [a.out]
subprocess.run(cmd, check=True); print("finish:", a.out, f"(look={a.look})")
