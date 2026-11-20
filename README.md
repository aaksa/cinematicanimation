# robloxcinematic

A skill for Claude Code (and Antigravity) that makes **cinematic short films with blocky Roblox-style characters** in Blender
Cycles: toy figures with drawn swap faces in a photoreal, dark, miniature world, cut to the beat and told almost without words.

It is the premium lane next to [robloxmaxxing](https://github.com/aaksa/robloxmaxxing) (game assets and bright explainer worlds).

## What is in it
- `blender/cine_kit.py`: characters (pose, snap-and-hold, face swaps, limited speech), materials (toy plastic, cloth, worn wood,
  brick, wet asphalt), lamps you can see (pendant, neon, bokeh points), haze, cameras with depth of field sized for a miniature,
  and cut lists written in beats.
- `scripts/look_gate.py`: measures a still or a film against the reference numbers (brightness, shadows, highlights, saturation).
- `scripts/finish.py`: glow, grade, lens softness, vignette and grain in ffmpeg; five looks.
- `scripts/shotlist.py`, `scripts/beatgrid.py`: shot list of any film in seconds, frames and beats; tempo and beat frames of a track.
- `references/`: the craft rules, the lighting and lens recipes, and the full measurement of two reference films.
- `examples/standoff/`: a tested four-shot scene.

## Install
```bash
bash install.sh            # links this folder into ~/.claude/skills/robloxcinematic
```
Needs Blender 5.x, Python 3 and ffmpeg. Tested on Blender 5.1.2, macOS, Apple M4.

## Try it
```bash
B=/Applications/Blender.app/Contents/MacOS/Blender
"$B" -b --factory-startup -P examples/standoff/build.py -- --out examples/standoff/out --stills
python3 -I scripts/finish.py examples/standoff/out/still_master.png --out examples/standoff/out/fin_master.jpg --look amber
python3 -I scripts/look_gate.py examples/standoff/out/fin_master.jpg --look amber
```

## Credits and limits
The look was studied from two films by GibbsonTV ("Liar's Bar - Roblox Animation", "Fugitive - Roblox Animation"). This skill
measures their craft; it does not contain or reproduce their characters, sets, story or music, and films made with it must not
either. The reference frames used during the study are not part of this repository. Roblox is a trademark of Roblox Corporation;
this project is not affiliated with it.

MIT licence.
