# Look: light, materials, lens, grade, render

Targets come from `reference-films.md`; recipes were tested on `examples/standoff` (Blender 5.1.2, Cycles, Apple M4).

## 1. Lighting: one lamp you can see

Order of work, every scene:
1. **World near black** (`K.world`, strength 0.15 or less). If the scene is readable with every lamp off, it is too bright.
2. **The key is a practical in the shot:** `K.pendant`, a street lamp, headlights, a torch, a door crack, a screen. Place it first
   and frame the master so the lamp or its cone is visible.
3. **Accent in a second colour, far back:** `K.neon`, `K.bokeh_lights`, a jukebox, an EXIT sign. Small and saturated.
4. **Edge:** one weak cold light from behind (`K.light(... 9000)`) so dark shoulders separate from a dark wall.
5. **Bounce instead of fill:** a warm, soft area light lying on the lit surface, pointing up (the table "bouncing" the lamp into
   the faces). It is the only fill allowed, because it has a reason.
6. **Haze** (`K.haze`, 0.006-0.012) so the lamp has a cone and the background lifts off black.
7. Run GATE L on a still from every camera. Fix lamps, not exposure.

Recipes (1 unit = 1 stud; watts are Blender light power at these distances):
| place | key | accent | edge / bounce | haze | finish look |
|---|---|---|---|---|---|
| back-room table | pendant 2600 W, 2700 K, cone 125, 3.5 studs above the table | amber neon ring + pink word + 26 bokeh points on the far wall | 500 W 9000 K area behind-left; 260 W 2300 K bounce on the table | 0.006 | amber |
| night street | sodium lamp: spot 4000-8000 W, 2200 K, high and to one side | neon sign on the building; car headlights (spots, 6500 K) | cold 9000 K area from behind as moonlight | 0.004 | noir |
| alley, a car's lights | two 6500 K spots at the camera, nothing else | tail lights `emit('#FF2010')` | none: silhouettes | 0.012 | noir |
| boss room | one overhead pendant, 3200 K, tight cone 80 | wall sconces 2400 K, weak | bounce off green felt (`#5A7A3A`) | 0.008 | sick |
| rain exterior | car lights passing (keyed spot sweep), a sign | wet asphalt (`K.asphalt(wet=0.8)`) reflecting them | hard back light so drops show | 0.010 | noir |
| hospital at night | corridor light through a door: area 800 W, 4000 K, from one side | monitor screen `emit('#40FFC0')`, coloured balloons | window: weak 12000 K | 0.003 | cold |
| the last object | a wedge of 3000 K light through a door on an empty floor | nothing | nothing | 0.004 | amber |

Rules:
- **Backlight skin.** `K.plastic` lets light through thin parts; a lamp behind a hand makes its edges glow. That glow is the
  signature of the look.
- **Colour per location, decided in the brief.** One dominant, one shadow tone, one accent. A film in one place changes colour
  only for the stake scene (Liar's Bar goes orange/purple for six seconds).
- **Contrast between neighbours:** put a cold shot before the warm room, a dark shot before the bright insert.
- **Moving light = life:** headlights sweeping a face, a torch beam crossing haze, a swinging lamp. Ramp every change over 3+
  frames; see the flash rule in `craft.md`.
- **Every frame keeps one real highlight** (GATE L peak over 0.85): the bulb, a glint on metal, a neon tube. A frame without it
  looks under-exposed instead of moody.

## 2. Materials: the world is real, the cast is toys

| thing | call | why |
|---|---|---|
| skin, bare parts | `K.plastic(color, rough=0.32, glow=0.35)` | soft highlight, subsurface glow, scuffed roughness |
| clothes | `K.cloth(color, 'weave' / 'knit' / 'leather')` | the flat shirt colour gains a surface the light can rake |
| table, floor, chairs | `K.wood(dark, light, planks=0.9, gloss=0.3)` | uneven gloss is what catches the lamp |
| walls | `K.brick()`, `K.flat('#3A3630', 0.9)` | soot and mortar; keep walls dark so they fall away |
| street | `K.asphalt(wet=0.6)` | puddles mirror neon and headlights |
| metal, chrome, glass | `K.flat(c, 0.25, metal=1)`, `K.flat(c, 0.05, 1)`, `K.glass()` | glints: a revolver, a cloche, bottles, a watch |
| anything glowing | `K.emit(color or kelvin, strength)` | 5 = a soft screen, 15 = neon, 60 = a bare bulb |

- **Bevel everything** (`K.box` does). Limbs 0.12-0.14 studs, hands 0.2, heads 0.34. A sharp edge is a CG edge.
- **Clutter at three sizes:** furniture, hand props, and specks (chips, coins, litter, bottles). Small things give the scale.
- **Hero props are realistic,** not blocky: the more real the prop in the toy hand, the better. Poly Haven and Meshy assets belong
  here; scale them to the hand (a hand is about 1 stud wide).
- **Procedural materials are fine:** nothing here is exported to Roblox.
- **Readable props** with `K.paper` / `K.text`: at most six words, one number, large enough to read at 9:16 on a phone.

## 3. Lens

`K.Cam(..., lens, stop)`. `stop` is the f-number as if the figure were a 40 cm collectible (the kit divides by 12 internally,
because Blender takes 1 stud as 1 metre and a 5 m giant has no depth-of-field blur).

| shot | lens | stop | distance | note |
|---|---|---|---|---|
| master | 28-35 mm | 5.6-8 | 9-12 studs | lamp in frame; a chair back or shoulder soft in front |
| over-shoulder | 50-85 mm | 4 | 6-8 | the shoulder is a black shape |
| close-up | 50-65 mm | 4 | 6-7 | bokeh points behind the head; never a bare wall |
| insert, wide and close | 24 mm | 2.8-4 | 2-3 | near hand as large as a head |
| macro | 85-100 mm | 2-2.8 | 3-4 | a watch, a card, text |
| top-down | 35 mm | 8 | 9 above | keep it sharp: it is a diagram |

Camera height: prop level (3-3.5 studs at a 2.9-stud table) for most shots; eye level (4.5) only for close-ups.

## 4. Finish (`scripts/finish.py`)

Render raw (AgX, "Medium High Contrast", 16-bit PNG), then:
1. **Glow:** highlights above 55 % blurred wide and screened back at 0.5 (lamps and neon bloom).
2. **Grade** by look: `amber` (saturation 1.12, warm shadows), `noir` (saturation 0.55, teal shadows, warm highlights), `sick`
   (green-yellow), `cold` (blue), `clean`.
3. **Film curve:** black lifted to 0.018, shoulder at 0.975.
4. **Lens:** 0.45 px blur at 1080p, one pixel of red/blue fringing, vignette.
5. **Grain:** temporal noise, strength 6.

A different look is a new `finish.py` run of a few seconds, never a re-render. One look per location: finish each scene's frames
with its own look and join them.

## 5. Render budget (measured, M4, Cycles Metal, haze on)

| setting | size | samples | time per frame | 60 s film (1,440 frames) |
|---|---|---|---|---|
| `preview=True` | 960x540 | 48 | 14 s (7 s effective with two processes) | about 3 h |
| `preview=False` | 1920x1080 | 160 | 70-90 s, one process | 28-36 h |

Full quality is an overnight-and-a-day render for one minute. Decide before starting:
- A 30-40 s reel at 1080p is 14-20 h. Start it only after the whole film has been approved at preview size.
- `K.setup(samples=96)` roughly halves the time; grain from `finish.py` hides the difference in dark frames.
- Shots without a visible beam do not need haze: build them without `K.haze` and they render several times faster.

- **Check with stills, not runs.** One still per camera after every change (10 s each), finished and gated, before any range.
- **Split the range** across 2-3 Blender processes started with the same command: frames are claimed and skipped.
- **Re-render only the shot that changed** (`--range` with the shot's frames from `cut_list`).
- Haze is the largest single cost. For a wide exterior shot that does not need a visible beam, lower the density or cut the box
  down to where the light is.
- 4K is what the references uploaded. 1080p with this finish holds up on phones; go to 4K only for a YouTube release.

## 6. Mistakes that cost a render here
- `Cam(target=some_object)` reads the object's world position when the camera is made. Pose and seat the cast before creating
  cameras that aim at their heads.
- Head turn: `+` is toward the character's own left. A character facing +X with the camera on the -Y side turns its head
  negative to face the lens.
- A close-up from table height with a long lens ends up under the chin and against a bare wall. Raise it to 4 studs and aim it
  so the far wall with the bokeh points is behind the head.
- A pendant straight above leaves faces black under hair and hats: add the table bounce.
- Haze at 0.01 with a cold edge light turns the back wall grey. 0.006 keeps the cone and the blacks.
- GATE L "peak under 0.85" on a close-up means the frame has no light source in it. It was right both times it fired.
