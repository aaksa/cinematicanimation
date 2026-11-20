---
name: robloxcinematic
description: >-
  Make premium, cinematic short films and reels with blocky Roblox-style characters: toy figures with drawn swap faces acting in a
  photoreal, low-key miniature world (worn wood, brick, wet asphalt, haze, neon, practical lamps), rendered in Blender Cycles with
  shallow depth of field, motion blur, film grain and a graded look, cut to the beat of the music and told with almost no words
  (hands, props, faces, inserts). Built on robloxmaxxing (same Blender, same stud scale) and measured from two reference films
  (13.7 M and 3.4 M views): brightness, saturation, shot lengths in beats, lens choices, loudness. Ships cine_kit (characters,
  materials, lamps, haze, cameras, beat-based cut lists), a look gate that measures a render against the references, a shot-list
  and beat-grid analyser, and an ffmpeg finishing pass. Use whenever the user wants a cinematic / premium / moody / dramatic /
  "film look" Roblox animation, a Roblox short film or story reel, a Blender Cycles Roblox scene, a noir or thriller or emotional
  Roblox story, "like GibbsonTV / Liar's Bar / Fugitive", a trailer-style Roblox video, or says a Roblox reel looks cheap, flat,
  too bright or "like a game" and should look like a movie. For bright explainer reels in a big Roblox world with a voice-over use
  robloxmaxxing's film lane instead; for game assets going into Roblox Studio use robloxmaxxing.
---

# robloxcinematic

The premium lane next to `robloxmaxxing`. That skill makes game assets and bright, busy explainer worlds in EEVEE. This one makes
**a film**: few characters, dark rooms, one lamp, a story you can follow with the sound off, rendered in Cycles.

`SKILL` = this folder. `B` = `/Applications/Blender.app/Contents/MacOS/Blender` (5.1). `BP` = Blender's Python
(`/Applications/Blender.app/Contents/Resources/5.1/python/bin/python3.13`), needed only for `beatgrid.py`. Other scripts: `python3 -I`.

Read once per session: `references/craft.md` (story, shots, edit, animation, sound) and `references/look.md` (light, materials,
lens, grade, render time). `references/reference-films.md` is the evidence: both films measured shot by shot. Read it before
arguing with a number in this file.

## The look in six lines
1. **Toy characters, real world.** Blocks with drawn faces; everything around them photoreal, worn and small-scale.
2. **Dark.** Median frame brightness 0.10-0.26 of full range. One visible lamp is the key. No fill light, no sky.
3. **Prop height.** The camera sits at table level, close, with shallow focus and something soft in the foreground.
4. **Inserts carry the story.** Hands, objects, readable props. About half the shots have no face.
5. **Cut on the grid.** Shot lengths are whole or half beats of the music. Speed changes with the story.
6. **Silence is a shot.** The music stops once, at the turn. The ending is a face or an object, then black.

## Pipeline
| stage | do | gate |
|---|---|---|
| 0. brief | logline, the loop or chain, the stake object, palette per location, the track and its BPM (`beatgrid.py`) | **GATE B**: every line of the brief is an observable thing |
| 1. shot plan | shots as rows: size, lens, what moves, length in beats; one master per scene | **GATE S**: rules in `craft.md` hold on paper |
| 2. world + cast | `cine_kit`: room/street, props, lamps, haze; `K.Char` figures | stills of the master, describe each in one sentence |
| 3. light | key from a visible lamp, accents, edge; `still` each camera at preview size | **GATE L** on every shot's still (`look_gate.py`) |
| 4. performance | poses on beats (`hit`, `pose`, `face`, `talk`), camera moves, `life()` | a contact sheet reads as the story with no sound |
| 5. render | `render_range` in 2-3 processes, 16-bit PNG, skip-existing | frame count = film length |
| 6. finish | `finish.py` (glow, grade, softness, vignette, grain) + sound mix | **GATE L** on the film, **GATE E** (`shotlist.py --bpm`), -14 LUFS |

A gate that fails is fixed at its own stage: a bright frame is a lighting problem, never a grading one.

### GATE B - the brief (a docstring at the top of the build script)
- **Logline** in one sentence with a want and a price.
- **Shape:** a loop that shortens (rule shown once, then repeated faster) or a chain (each scene ends on the object that starts the next).
- **The stake object:** one small thing with a face or a number on it (a photo, a bill, a ticket). Where the camera pushes in on it.
- **Palette per location:** one dominant light colour, one shadow colour, one accent. Different for each place.
- **Sound:** the track, its BPM, where the music drops in, the 3-8 s where it stops.
- **Ending:** the last image (a face or an object) and the one or two words on black after it.
- **Exclusions:** what this film must not look like.

### GATE L - the look (numbers from the references; `scripts/look_gate.py`)
| measure (0-1 of full range) | pass | references |
|---|---|---|
| median frame brightness | 0.10-0.26 | 0.20, 0.17 |
| shadow level (10th percentile pixel) | under 0.09 | 0.06, 0.04 |
| bright level (90th percentile pixel) | 0.22-0.56 | 0.46, 0.36 |
| peak (brightest pixel) | over 0.85 | 0.91, 0.98 |
| black floor | under 0.05 | 0.02, 0.02 |
| saturation | amber 0.10-0.30, noir 0.03-0.14 | 0.18, 0.07 |

Run it on the finished still of each shot, then on the whole film. A single bright insert may WARN; a FAIL is fixed. "Peak under
0.85" means there is no real highlight in frame: put a lamp, a glint or a neon tube where the lens can see it.

### GATE E - the edit (`scripts/shotlist.py film.mp4 --bpm N`)
Every shot's length is a whole or half number of beats. Average shot 1-3.5 s. The first two shots are the longest of their scene.
No two consecutive shots have the same size and angle. One stretch of 3-8 s has no music. The film ends within a second of black.

## Building a scene
```bash
"$B" -b --factory-startup -P build.py -- --out out --stills        # one still per shot, half size, about 10 s each
python3 -I "$SKILL/scripts/finish.py" out/still_master.png --out out/fin_master.jpg --look amber
python3 -I "$SKILL/scripts/look_gate.py" out/fin_master.jpg --look amber
"$B" -b --factory-startup -P build.py -- --out out --frames --final &   # start it 2-3 times: frames that exist are skipped
python3 -I "$SKILL/scripts/finish.py" out/frames --out out/film.mp4 --look amber --audio mix.wav
```
```python
import sys; sys.path.insert(0, SKILL + "/blender"); import cine_kit as K
K.setup(aspect="16:9", height=1080, preview=True)            # "9:16" for a reel; preview=False for the delivery
K.room(26, 22, 10); K.round_table("Table", 3.2, 2.9); K.pendant("Lamp", (0, 0, 6.5), power=2600, spot=125)
K.neon("Ring", (0, 10.8, 5.6), radius=1.7, color="#FFB020"); K.bokeh_lights("Shelf", ((-11, 10.2, 2.5), (11, 10.6, 8)))
K.light("TableBounce", "AREA", (0, 0, 3.05), 260, 2300, target=(0, 0, 9), size=4); K.haze((26, 22, 10), (0, 0, 5), 0.006)
hero = K.Char("Hero", skin="#F2C230", shirt="#20242C", hat="hair", at=(-4.5, 0, 0), yaw=90); hero.sit(1)
master = K.Cam("Master", (-2.2, -9.6, 3.1), (0.2, 0, 4.3), lens=28, stop=5.6)
cu = K.Cam("HeroCU", (-1.6, -6.2, 4.1), (-4.4, 0, 4.4), lens=50, stop=4, focus=hero.head)
S = K.cut_list([("master", master, 4), ("hero", cu, 2.5)], bpm=100); B = K.beats(100)
hero.hit(B(4.5), 3, head=(2, -60, -5)).face(B(4.5), "smirk"); cu.push(*S["hero"], 0.06).handheld(0.3); hero.life()
```
`examples/standoff/build.py` is the complete, tested version (4 shots, 7.2 s): copy it as the starting point of a new film.

### cine_kit in one table
| need | call |
|---|---|
| scene | `setup(aspect, height, samples, preview)`, `world()`, `room()`, `haze(size, loc, density)` |
| surfaces | `plastic` (toy skin, glows when backlit), `cloth(kind=weave/knit/leather)`, `wood(planks=)`, `brick`, `asphalt(wet=)`, `flat` (felt, plaster, metal), `glass`, `emit` (neon, bulbs, screens) |
| shapes | `box` (always bevelled), `cyl`, `torus(arc=)`, `text` (3D letters, neon words), `paper` (poster / bill / card with readable lines), `round_table`, `chair` |
| lamps | `pendant` (visible shade + bulb + spot), `neon` (tube + matching fill), `bokeh_lights`, `light(kind, loc, power, color=kelvin or hex, target, size)` |
| cast | `Char(name, skin, shirt, pants, hat=hair/cap/fedora/beanie)`: `.pose(frame, arm_l=(fwd, out, twist), head=(nod, turn, tilt), torso, leg_l, at, yaw)`, `.hit(frame, dur, ...)` (snap + hold), `.face(frame, expr)`, `.talk(f0, f1)`, `.sit`, `.walk`, `.life()` |
| supplied characters | `Rigged("bugis_man" / "bugis_woman" / path.blend, at, yaw)`: a character model from a file, at Char height, with **the same pose channels as `Char`** (`arm_l`, `head`, `torso`, `leg_l`, `.hit`, `.sit`, `.walk`, `.life`, `.head`). Painted faces: no swaps, so emotion comes from head, arms and the cut. A new one-piece model is rigged once with `scripts/rig_block.py` (measure neck, hip and arm border from slices first) and added to `K.CAST` |
| the user's avatar | `Avatar(at, yaw, pose)`: Aksa's rigged Roblox character (`Roblox/blender/hero_face.blend`) at Char height. `.pose(frame, "table" / "stand" / "relax" / "reach" / "chin" / "hips", head=(nod, tilt, turn), arm_L=...)`, `.hit`, `.sit`, `.life()`, `.head` (camera target), `.face.expr(f, eyes, brows, mouth)` / `.face.lipsync(words, vo_frame, fps=24)` / `.face.blink`, then `.finish()` once. **The user is the hero of his own films: use `Avatar` for the lead unless he says otherwise, `Char` for everyone else** |
| faces | `K.EXPRESSIONS`: neutral, smirk, grin, angry, shout, shock, sad, shut, talk_a, talk_o, talk_m, side. Swaps only, never morphs |
| camera | `Cam(name, loc, target, lens, stop, focus, roll)`: `.at(frame, loc, target, focus, roll)`, `.push(f0, f1, 0.06)`, `.handheld(amount)` |
| edit | `beats(bpm)` -> frame of beat n; `cut_list([(name, cam, beats), ...], bpm)` binds cameras to markers and returns each shot's frames |
| output | `still(path, frame)`, `render_range(dir, f0, f1)` |

`stop` is the f-number as if the figure were a 40 cm collectible: 2-2.8 inserts, 4 faces, 5.6-8 masters. Smaller = blurrier.

## Fits with the user's other skills
- **Script:** `scriptmaxxing` for any Indonesian voice-over. Keep it to a few lines; the reference with 13.7 M views has none.
- **Music and effects:** `~/Ngonten/Maxxing/audio-lib` (CC0). Run `beatgrid.py` on the track before planning shots.
- **The user's own avatar:** `K.Avatar()` loads it with its face rig (blink, brows, word-accurate Indonesian lip sync from
  `Roblox/blender/face/face_rig.py`). `K.Char.talk()` is limited animation for other speakers only. Try it:
  `build.py -- --avatar --stills`.
- **Props and sets:** `robloxmaxxing/blender/rbx_kit.py` builds at the same stud scale; Poly Haven (MCP for Blender `search_assets`,
  or the 3d-assets MCP) for CC0 PBR textures and real-world props; Meshy for one hero prop. Realistic props are the point.
- **Vertical reels:** `--aspect 9:16`. Everything here holds; masters go to 24-28 mm and depth is stacked along the lens axis.

## Never ship
A frame lit by the world or by an invisible fill; a shot with nothing in front of the subject and nothing glowing behind it; a
morphing face; a box with sharp edges; a character standing in empty space; a cut that is not on the grid; music from start to
end with no silence; a master above -14 LUFS (one reference is at -6.4 and clipped: do not copy that); the reference films'
characters, sets, story, title or music; a weapon-to-the-head beat in a reel for a young audience; "it looks cinematic" without
the GATE L lines.

## Files
| file | use |
|---|---|
| `blender/cine_kit.py` | the kit (Blender 5.x, Cycles, Metal) |
| `scripts/rig_block.py` | rigid skeleton (head, torso, arms, lower body, optional legs) for a static one-piece blocky character |
| `characters/` | rigged cast: `bugis_man.blend`, `bugis_woman.blend` (the user's Bugis Roblox characters; large, not in git) |
| `scripts/look_gate.py` | GATE L on a still, a frame folder or a film |
| `scripts/finish.py` | glow, grade (`amber`, `noir`, `sick`, `cold`, `clean`), softness, vignette, grain, mux audio |
| `scripts/shotlist.py` | shot list of any film, lengths in beats: GATE E, or to study a new reference |
| `scripts/beatgrid.py` | BPM, beat frames, loudness jumps, quiet stretches of a track (run with `BP`) |
| `references/craft.md` | story shapes, shot grammar, the edit, animation, sound, text on screen |
| `references/look.md` | lighting recipes per location, materials, lens table, grade, render budget, mistakes |
| `references/reference-films.md` | the two films measured: numbers, colour scripts, full shot lists |
| `examples/standoff/` | the proof scene: `build.py`, stills, the rendered 7 s film |
