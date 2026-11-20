"""Tempo, beat frames, the drop and the quiet stretches of a music track. Needs numpy: run it with Blender's Python.

  /Applications/Blender.app/Contents/Resources/5.1/python/bin/python3.13 -I beatgrid.py track.mp3 [--fps 24] [--cuts shots.json]

Plan the edit from its output: shot lengths in beats (K.cut_list), the big story turn on the drop, the silence on a quiet stretch.
With --cuts (from shotlist.py --json) it reports how far each cut of an existing edit sits from the nearest hit.
"""
import sys, os, json, wave, subprocess, tempfile, argparse
import numpy as np

ap = argparse.ArgumentParser(); ap.add_argument("src"); ap.add_argument("--fps", type=float, default=24); ap.add_argument("--cuts"); ap.add_argument("--json")
a = ap.parse_args(); tmp = os.path.join(tempfile.mkdtemp(), "a.wav")
subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", a.src, "-vn", "-ac", "1", "-ar", "22050", tmp], check=True)
w = wave.open(tmp); sr = w.getframerate(); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
hop, win = sr // 100, 1024                                   # 10 ms steps
fr = np.lib.stride_tricks.sliding_window_view(np.pad(x, (win // 2, win // 2)), win)[::hop]
S = np.abs(np.fft.rfft(fr * np.hanning(win), axis=1))
flux = np.r_[0, np.maximum(0, np.diff(np.log1p(50 * S), axis=0)).sum(1)]; z = (flux - flux.mean()) / (flux.std() + 1e-9)
db = 20 * np.log10(np.sqrt((fr ** 2).mean(1)) + 1e-6)
o = z - z.mean(); ac = np.correlate(o, o, "full")[len(o) - 1:]; lags = np.arange(33, 100)            # 60-180 BPM
lag = lags[np.argmax(ac[lags] * np.exp(-0.5 * ((np.log2(lags / 55.0)) / 0.6) ** 2))]               # prefer about 110 BPM
best = max(np.arange(lag - 1, lag + 1.01, 0.02), key=lambda L: max(z[np.round(np.arange(p, len(z), L)).astype(int).clip(0, len(z) - 1)].mean() for p in range(0, int(L), 2)))
phase = max(range(0, int(best)), key=lambda p: z[np.round(np.arange(p, len(z), best)).astype(int).clip(0, len(z) - 1)].mean())
bpm = 6000.0 / best; first = phase / 100.0
cs = np.r_[0, np.cumsum(db.clip(-70, 0))]; W = 100                                         # mean level of the next second minus the last second
jump = np.array([(cs[i + W] - cs[i]) / W - (cs[i] - cs[i - W]) / W for i in range(W, len(db) - W)])
drops = []
for i in np.argsort(jump)[::-1]:
    t = (i + W) / 100.0
    if all(abs(t - d) > 3 for d in drops): drops.append(t)
    if len(drops) == 3: break
drops.sort(); drop = drops[0] if drops else 0.0
quiet, i = [], 0; thr = np.percentile(db, 75) - 14
while i < len(db):
    if db[i] < thr:
        j = i
        while j < len(db) and db[j] < thr: j += 1
        if j - i >= 60: quiet.append((round(i / 100, 2), round(j / 100, 2)))
        i = j
    else: i += 1
n = int((len(x) / sr - first) * bpm / 60); beat_frames = [int(round((first + k * 60 / bpm) * a.fps)) + 1 for k in range(n)]
print(f"{a.src}: {len(x) / sr:.1f} s, {bpm:.1f} BPM, first beat at {first:.2f} s, one beat = {60 / bpm * a.fps:.1f} frames at {a.fps:g} fps")
print("three biggest loudness jumps (a drop, or sound returning after a silence):", ", ".join(f"{d:.1f} s = beat {max(0, round((d - first) * bpm / 60))}" for d in drops))
print("quiet stretches (s):", quiet or "none")
print("beat frames:", beat_frames[:64], "..." if len(beat_frames) > 64 else "")
if a.cuts:
    cs = [s["start"] for s in json.load(open(a.cuts))][1:]
    pk = np.array([i for i in range(1, len(z) - 1) if z[i] > 1.5 and z[i] >= z[i - 1] and z[i] >= z[i + 1]]) * 0.01
    off = [float(pk[np.argmin(abs(pk - c))] - c) * 1000 for c in cs]; near = [o for o in off if abs(o) <= 125]
    print(f"cuts within 3 frames of a hit: {len(near)} of {len(cs)}; median offset {np.median(near) if near else 0:+.0f} ms (+ = the sound lands after the cut)")
if a.json: json.dump(dict(bpm=bpm, first=first, drop=drop, quiet=quiet, beat_frames=beat_frames), open(a.json, "w"))
