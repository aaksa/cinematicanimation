"""Shared: per-frame picture statistics through ffmpeg (no Python packages needed)."""
import subprocess, re, os, tempfile, glob


def src_args(path, fps=24):
    """ffmpeg input args for a video, a single image, or a folder of numbered frames."""
    if os.path.isdir(path):
        files = sorted(glob.glob(os.path.join(path, "*.png")) + glob.glob(os.path.join(path, "*.jpg")))
        files = [f for f in files if os.path.getsize(f) > 0]
        if not files: raise SystemExit(f"no frames in {path}")
        lst = tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False)
        for f in files: lst.write(f"file '{os.path.abspath(f)}'\nduration {1 / fps}\n")
        lst.close(); return ["-f", "concat", "-safe", "0", "-r", str(fps), "-i", lst.name], len(files)
    return ["-i", path], None


def probe(path, fps=24):
    """-> list of dicts per frame: t, Y (mean), lo (10th pct pixel), hi (90th), mn, mx, sat, dif, scene. Brightness as 0-1."""
    args, _ = src_args(path, fps)
    tmp = tempfile.mkdtemp(); a, b, c = (os.path.join(tmp, x) for x in ("luma.txt", "sc.txt", "chroma.txt"))
    # luma from a full-range grey copy (0-255 whatever the source's range), chroma from a video-range copy
    vf = (f"scale=320:-2:out_range=tv,format=yuv420p,split=3[x][y][z];[x]format=gray,signalstats,metadata=print:file={a}[o1];"
          f"[y]format=yuv420p,select='gte(scene,0)',metadata=print:file={b}[o2];"
          f"[z]signalstats,metadata=print:file={c}[o3]")
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostats", *args, "-filter_complex", vf,
                    "-map", "[o1]", "-f", "null", "-", "-map", "[o2]", "-f", "null", "-", "-map", "[o3]", "-f", "null", "-"], check=True)

    def parse(p):
        out, cur = [], None
        for l in open(p):
            if l.startswith("frame:"):
                cur = {"t": float(re.search(r"pts_time:([\d.]+)", l).group(1))}; out.append(cur)
            elif "=" in l and cur is not None:
                k, v = l.strip().split("=", 1)
                try: cur[k.split(".")[-1]] = float(v)
                except ValueError: pass
        return out
    sig, sc, ch = parse(a), parse(b), parse(c); n = lambda y: y / 255.0; fr = []
    for i, s in enumerate(sig):
        fr.append(dict(t=s["t"], Y=n(s["YAVG"]), lo=n(s["YLOW"]), hi=n(s["YHIGH"]), mn=n(s["YMIN"]), mx=n(s["YMAX"]),
                       sat=(ch[i]["SATAVG"] if i < len(ch) else 0.0) / 128.0, dif=s.get("YDIF", 0.0),
                       scene=sc[i].get("scene_score", 0.0) if i < len(sc) else 0.0))
    return fr


def cuts(fr):
    """Cut times: a scene-score spike at least 3x its neighbours. Misses cuts between two near-black frames."""
    c = [0.0]
    for i in range(1, len(fr) - 1):
        s = fr[i]["scene"]
        if s > 0.10 and s > 3 * max(fr[i - 1]["scene"], fr[i + 1]["scene"]) and fr[i]["t"] - c[-1] > 0.2: c.append(fr[i]["t"])
    return c


def pct(a, p):
    a = sorted(a); return a[int(p * (len(a) - 1))] if a else 0.0
