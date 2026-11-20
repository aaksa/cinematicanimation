# cinematicanimation

A Claude Code and Antigravity skill for making **cinematic animated shorts with blocky toy-style characters** in Blender. Think toy figures with hand-drawn expressions, a photoreal miniature world, and cuts that land on the beat.

![Sigajang Laleng Lipa cover: two pairs of eyes, friend and enemy, split by a badik whose blade shows two boys flying a kite at sunset.](docs/sigajang-cover.jpg)

![Four frames from Sigajang Laleng Lipa: two silhouettes and a sarong against the setting sun, Daeng at sunset, the duel inside one sarong at night, and the sarong from straight above.](docs/sigajang-frames.jpg)

*Sigajang Laleng Lipa: a 108-second vertical film about a Bugis tradition. Two friends love the same woman and agree to fight with badik inside one sarong. The characters were made with Meshy Agent, rigged with this skill's [rig_block](scripts/rig_block.py), and directed, lit and cut to the beat in Blender EEVEE.*

## Highlights

- **Direct the performance.** Snap into a pose and hold it, swap drawn expressions, and use short lines of dialogue only when the shot calls for them. See the [Blender toolkit](blender/cine_kit.py).
- **Bring your own cast.** Give a static, one-piece character from Meshy (or any other generator) the rigid skeleton the toolkit expects with [rig_block](scripts/rig_block.py).
- **Light it like a miniature.** Use visible lamps, torches and neon, shallow focus, haze, and materials such as toy plastic, worn wood, and wet sand. See the [lighting and lens recipes](references/look.md).
- **Cut on the beat.** Map a track with [beatgrid](scripts/beatgrid.py) and measure shot lengths in seconds, frames, and beats with [shotlist](scripts/shotlist.py).
- **Finish and check the look.** Apply one of five [finishing looks](scripts/finish.py) in ffmpeg, then use the [look gate](scripts/look_gate.py) to check brightness, shadows, highlights, and saturation.

For game assets and brighter explainer worlds, see the companion project [robloxmaxxing](https://github.com/aaksa/robloxmaxxing). The [craft notes](references/craft.md) and [reference-film studies](references/reference-films.md) cover the decisions behind the cinematic look.

## How I use Meshy to make models

- **[Meshy Agent](https://docs.meshy.ai/en/webapp/3d-agent):** I describe each character in chat (for Sigajang: Daeng in a red passapu, Raka in a black jas tutup and songkok, Sari in a green hijab) and turn the concepts I choose into 3D models.
- **[Meshy MCP](https://docs.meshy.ai/en/api/ai):** When I'm working in an MCP-enabled assistant like Claude Code, I use it to generate props from prompts or reference images and download the results without leaving that workflow.

Once I have a model, I export it and import it into Blender. Meshy is the asset-creation step; `cinematicanimation` is where I rig and pose the cast, light the set, frame the shots, and cut the film. Meshy is optional: the included Standoff demo uses its own blocky cast and runs without a Meshy account or API key.

## Install

Needs Blender 5.x, Python 3, and ffmpeg. Tested on Blender 5.1.2 on macOS (Apple M4).

```bash
git clone https://github.com/aaksa/cinematicanimation.git
cd cinematicanimation
bash install.sh                 # Claude Code
# bash install.sh --antigravity # Antigravity instead
```

## Try it

The Sigajang project and its cast are not part of this repository. The included Standoff demo builds a four-shot scene with its own cast:

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
