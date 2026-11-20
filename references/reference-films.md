# The two reference films, measured

Two shorts by GibbsonTV, studied on 19 Nov 2026 from the 4K uploads. Both were animated in Blender and rendered in Cycles (the
creator says so in the descriptions; Fugitive adds Houdini for simulations). They are the standard this skill aims at. They are
references for craft only: **never copy their characters, story, sets, title or music.**

| | Liar's Bar - Roblox Animation | Fugitive - Roblox Animation |
|---|---|---|
| uploaded | 11 Dec 2024 | 1 Nov 2025 |
| views / likes (19 Nov 2026) | 13.7 M / 220 K | 3.4 M / 71 K |
| length | 66 s | 111 s |
| picture | 3840x2160, 24 fps, no letterbox | same |
| shots | about 48 | 35 |
| average shot | 1.4 s (median 1.0 s) | 3.2 s (median 2.4 s) |
| longest shot | 2.7 s (the opening) | 8.8 s (the car-door one-take) |
| words spoken | none | 33 words, one speaker, 25 s of the film |
| on-screen text | 12 tiny captions (game calls) | none until the end cards |
| music | one track, 100 BPM | two tracks, 110 BPM, plus a 25 s scene with no music |
| loudness | -6.4 LUFS, peak +1.0 dBTP (clipped) | -12.1 LUFS, range 17.7 LU |

How it was measured: `scripts/shotlist.py` (ffmpeg scene score + signalstats per frame), `scripts/beatgrid.py` (spectral-flux
onsets and tempo), 2 fps contact sheets, full-size stills and 100 % crops. Shot contents below are my reading of the frames. Cut
detection misses a few cuts between two dark frames (the Liar's Bar count was corrected by eye from 46 to about 48). Raw data:
`liarsbar_shots.json`, `fugitive_shots.json`. Frames: `frames/` (kept out of git; they are someone else's film).

## 1. Why they work (the short version)

1. **Toy characters in a photoreal miniature world.** The characters stay simple blocks with flat 2D faces. Everything around
   them is real: worn brick, plank floors with uneven gloss, wet asphalt, engraved revolvers, knitted fabric, haze in the air.
   The contrast is the look. A blocky world with blocky characters reads as a game; this reads as a film shot on a tabletop.
2. **It is lit like a night film, and it is dark.** The median frame sits at 17-20 % brightness. Light comes from things you
   can see in the shot: a pendant lamp, a neon sign, headlights, a torch, police lights, a door crack.
3. **The camera is at prop height.** Most shots sit at table level or lower, close to a hand, a card, a gun, a wheel, with a
   very shallow focus. That is what makes a 5-stud character feel like a photographed miniature.
4. **The story is told without language.** Faces swap between drawn expressions, hands do the acting, props carry readable text
   (a wanted poster, a medical bill, a number plate). Liar's Bar has no dialogue at all and 13.7 M views across every country.
5. **The cut follows the music.** Shot lengths are whole numbers of beats and almost every cut sits within two frames of a hit.
6. **Loud and quiet are both used.** Each film removes the music completely at the emotional turn, then brings it back.

## 2. Picture, measured

Values are fractions of full video range (0 = black, 1 = white), from every frame at 320 px.

| measure | Liar's Bar | Fugitive | what it means |
|---|---|---|---|
| median frame brightness | 0.20 | 0.17 | a dark film; never "fix" this by adding fill |
| darkest 10 % of frames | below 0.14 | below 0.09 | |
| brightest 10 % of frames | above 0.32 | above 0.30 | even the bright shots are under a third |
| shadow level inside a frame (10th percentile pixel) | 0.06 | 0.04 | deep, but not crushed |
| bright level inside a frame (90th percentile pixel) | 0.46 | 0.36 | 90 % of the picture is under half brightness |
| darkest pixel (median over frames) | 0.02 | 0.02 | blacks lifted a touch above zero (film print feel) |
| brightest pixel (median over frames) | 0.91 | 0.98 | a small true highlight in nearly every frame: a lamp, a glint, a neon tube |
| average saturation (0-1) | 0.18 | 0.07 | Liar's Bar is warm and rich; Fugitive is almost monochrome with small colour accents |

Colour scripts:
- **Liar's Bar:** one palette for the whole film. Amber-orange light, brown-black shadows, red + yellow neon. Small cool or
  magenta accents far in the background (a jukebox, an EXIT sign) keep it from turning into a brown smear. Only two departures:
  a cold blue corridor before the door opens (so the bar feels warm by contrast) and an orange/purple backlit look for the
  "about to die" beat. **Colour also carries the plot:** cards revealed as a lie glow red-pink, cards revealed as true glow green.
- **Fugitive:** a palette per location. Street: sodium orange + police red/blue on grey-green. Bar: amber. Alley: black with
  red/blue alternation. Mob den: sick green-yellow under one overhead lamp. Rain: teal-green and black. Hospital: blue-violet with
  magenta balloons. Final shot: warm cream light wedge on the floor. The location is recognisable from colour alone.

Lens and finish (seen in stills and 100 % crops):
- Shallow depth of field in almost every shot; foreground objects out of focus between lens and subject (a shoulder, a chair
  back, a car body, a hand). Round bokeh from lamps and bottles.
- Wide lens very close to hands and props (the near hand is as large as a head) alternating with long-lens portraits.
- Visible haze: light cones under pendant lamps, a torch beam, headlight glow, tyre smoke, rain.
- Glow around neon and headlights; fine film grain over everything; soft corners; no sharpening halos.
- Heavy motion blur on fast moves (a hand slam covers its distance in about 3 frames and is a smear on each).
- Animated on ones: no duplicated frames in either film (26 of 1,583 and 0 of 2,659 frame pairs were near-identical).

Materials:
- Skin and bare plastic: soft, slightly translucent. Backlit hands glow at the edges like a real toy. Large rounded edges.
- Clothes: the flat Roblox shirt texture, but with a real surface (knit on a balaclava, embossed creases on sleeves, studs on a suit).
- Faces: 2D drawn decals. Expression changes are instant swaps, never morphs.
- World: PBR surfaces with wear, dirt, roughness variation, and many small props (bottles, posters, litter, ashtrays).

## 3. Camera and staging

- **Opening shots are long and moving, then the cutting starts.** Liar's Bar spends its first 11.4 s on 5 shots (sign tilt-down,
  profile walk, hand on the door, over-shoulder reveal, wide master) before its first sub-second shot. Fugitive opens with a
  6.3 s wide and an 8.8 s one-take.
- **Every scene gets one wide master, once.** The table under the lamp; the three men behind the green table; the street with
  two police cars. After it, the scene is covered in close shots only.
- **Inserts are the main event.** Hands, cards, the gun, a pocket watch with a photo, a fist tightening, a bill with a number
  on it, a card on the floor. In Liar's Bar roughly half of all shots have no face in them.
- **Angles:** table-level low angle (default), straight top-down on the table (three times in Liar's Bar, once in Fugitive),
  over-the-shoulder with the near shoulder black and soft, high angle for a lonely figure (rain walk), a rolled/dutch camera for
  a death, a low angle up at a face for the hero moment in the rain.
- **Moves:** slow push-ins on faces and on the final object; a crane down from the sign; a low dolly along the table; handheld
  shake during the run to the car and the chase; whip pans inside the chase; one rack focus per film used as a reveal.
- **Symmetry for power:** the boss sits dead centre under the lamp with a goon each side; the top-down card fan is radial.
- **Match cut:** the sketch of the suspect on a notepad cuts to the suspect's face in his car (Fugitive 43.5 s).
- **Title as an object:** "Animated By ..." stands on the road as 3D letters and the car drifts through it and shatters it.

## 4. Story mechanics

Liar's Bar is a **loop that gets shorter**: claim -> accusation -> reveal -> penalty.
| round | time | length | what changes |
|---|---|---|---|
| arrival | 0-17 s | 17 s | sign, corridor, door, opponents, sit down (no music hit yet) |
| 1 | 17-36 s | 19 s | rules taught by showing: table card, claims, "LIAR!", reveal, gun, black frame |
| stakes | 36-42 s | 6 s | music out, slow, the pocket watch with a child's photo |
| 2 | 42-58 s | 16 s | the loudest character loses; rolled camera, overhead |
| 3 | 58-65 s | 7 s | five inserts under a second each, then the last face |
| end | 65.5 s | 0.5 s | black, one word |

It teaches its rules visually in the first round (a caption names the table card, a caption names each claim), so later rounds
can be seven seconds long and still be understood. The final shot answers the question the opening posed (will he win?) with a
face, not a caption.

Fugitive is a **chain of consequences**: crime scene -> witness -> sketch -> chase -> debt -> threat -> daughter -> a card on the
floor. Each scene ends on the object or fact that starts the next. It ends on an unanswered object (a cliff-hanger) and a
"To Be Continued" card. The only speech in the film is the threat, and it gets the quietest, longest scene.

Shared devices:
- A comic beat inside a dark film (the cop and his donut; the smug pipe smoker) so the tone is not flat.
- Stakes shown by one small object with a face or a number on it (photo in a watch; "YOU OWE $2,432,344").
- Foreshadowing with posters in the background (a wanted poster appears three times before it matters).
- Continuity between films: Fugitive opens on the aftermath of Liar's Bar (blood-spotted cards on the same table).
- The violent moment itself is withheld (cut to black, or the camera looks away); the reaction is shown.

## 5. Editing, measured

- Liar's Bar: shot lengths cluster at 22, 36 and 58 frames (0.92 s, 1.5 s, 2.42 s). At 100 BPM a beat is 14.4 frames, so these
  are 1.5, 2.5 and 4 beats: a 4-beat bar split 1.5 + 2.5. The fastest shots are 7 frames (half a beat) and come in pairs.
- Fugitive: seven shots are exactly 52 frames (2.17 s) = 4 beats at 110 BPM; the alley shot flips the whole frame between red
  and blue once per beat.
- Cut-to-hit timing: 29 of 45 cuts in Liar's Bar and 12 of 34 in Fugitive sit within three frames (125 ms) of an audio hit, with
  no consistent side (the median offset is under half a frame). The rule is "on the grid, within two or three frames", not
  "before" or "after" the beat. Fugitive's lower share is its long dialogue scene, which has no beat to cut to.
- Speed follows the story, not a constant: Liar's Bar averages 2.3 s per shot in the arrival, 1.2 s in round 1, 2.0 s in the
  quiet beat and 0.8 s in the last round.
- A 0.67 s black frame with 0.34 s of near-silence stands in for the first gunshot.
- Both films end in under a second of black with one or two words. No logo, no outro.

## 6. Animation

- Bodies are rigid blocks rotating at shoulders, hips, neck and waist. No bending, no squash. Life comes from timing.
- Pose-to-pose with holds: a move takes 2-4 frames (blurred), then the pose is held with a slow drift for 10-40 frames.
- Hands are the actors: slamming, fanning cards, cocking a hammer, pointing, clenching. Arms are often framed without the face.
- Faces change on the hit: a neutral face for a few beats, one swap to a shout exactly on the caption/word, hold.
- In the one dialogue scene the mouth swaps roughly every 5-12 frames between a handful of shapes while the arms gesture on the
  stressed words; the head tilts between lines. It is limited animation and it is enough.
- Secondary motion sells the scale: smoke from a pipe, cards flipping in the air, cash sliding, tyre smoke, rain, a swinging
  car door, lightning in a window.

## 7. Sound

| | Liar's Bar | Fugitive |
|---|---|---|
| integrated loudness | -6.4 LUFS (too hot: clipped, do not copy) | -12.1 LUFS |
| loudness range | 8.2 LU | 17.7 LU |
| stereo width (side vs mid) | -19.6 dB (nearly mono) | -7.6 dB (wide) |
| where the energy is | below 250 Hz | 60-250 Hz and low mids |

- Liar's Bar: 17 s of low, quiet build (-22 to -9 dB), then the track drops in on the cloche slam at 17.1 s (+12 dB in one
  frame). Music is removed for the watch scene (36-42 s, about 17 dB down) and returns on the fall.
- Fugitive: music from the start, louder for the chase, then **nothing but room tone and a voice for 25 s** (62-87 s) with gaps
  of about a second between sentences. Music returns on the first rain shot.
- Every on-screen action has its own sound (slam, card flick, hammer click, door, tyre squeal, rain).
- Speech (transcribed by YouTube, checked against the picture; the last word is unclear): "Is that it? Now, you know what happens
  if you don't come back here with around 10 times what you just brought me, your daughter will die. But, I believe in you. Take
  this car(d)." 33 words in 25 s, about 1.3 words per second, with long pauses.

## 8. What to take, and what not to

Take: the dark motivated lighting, the toy-in-a-real-world contrast, prop-height lenses, inserts, beat-length shots, the loop
that shortens, the silence before the turn, stakes in one object, an ending that is a face or an object and then black.

Do not take: the characters, the game it is based on, the bar and its sign, the story beats, the music, the -6 LUFS master, or
the gun-to-head imagery for an audience that includes children (Instagram and TikTok both limit it; choose a penalty that fits
the platform).

## Shot lists

### Liar's Bar (times in seconds)
| # | start | len | shot |
|---|---|---|---|
| 1 | 0.0 | 2.7 | EXT, hard low sun. Crane down from the neon sign to the hero's back and a bouncer at the door |
| 2 | 2.7 | 2.3 | Cold blue corridor, profile tracking shot of the walk past a painting and a wanted poster |
| 3 | 5.0 | 2.5 | Insert: hand to the door, door swings, a warm sliver of the bar |
| 4 | 7.5 | 2.4 | Over the hero's black shoulder: a horned gold skull helmet at a table, lamp bokeh |
| 5 | 9.9 | 1.5 | Wide master: four players under a pendant lamp, neon on the back wall, a light shaft, a bottle on the floor |
| 6 | 11.4 | 0.9 | Close-up: flat cap, pipe, smirk, smoke, neon ring behind |
| 7 | 12.3 | 2.4 | Top-down: the hero crosses the plank floor |
| 8 | 14.7 | 2.4 | Table level: revolvers and a deck sharp in front, the hero sits down soft behind |
| 9 | 17.1 | 1.0 | A cloche slams over a tray of cash (the music drop) |
| 10 | 18.1 | 2.4 | Macro: a hand takes a revolver; a thumb lifts the deck: "King's Table" |
| 11 | 20.5 | 0.9 | Top-down: four hands fan their cards around the table |
| 12 | 21.5 | 2.4 | Low: the masked player leans in and plays: "2x Kings" |
| 13 | 23.8 | 1.5 | Wide lens: a hand slaps three cards down: "3x Kings" |
| 14 | 25.3 | 2.4 | Medium: the general studies his cards, then the face swaps to a shout: "LIAR!" |
| 15 | 27.8 | 0.9 | Insert: three cards face up, tinted red (a lie) |
| 16 | 28.6 | 1.5 | The hero lifts the revolver to his own head, very soft focus |
| 17-20 | 30.1 | 4.4 | Round 2 in four shots: deck "Queen's Table", worried mask, "1x Queen", fist "LIAR!" |
| 21 | 34.5 | 0.9 | A card spins through the air and lands: an ace |
| 22 | 35.4 | 0.7 | Black, near-silence |
| 23 | 36.1 | 2.4 | Orange backlight, slow: the masked player, gun to his head, eyes shut. No music |
| 24 | 38.5 | 2.4 | Macro: a pocket watch opens on a photo of a girl |
| 25-26 | 40.9 | 2.0 | Wider; he falls back. Music returns |
| 27-29 | 43.0 | 3.3 | Reactions: the general winces, the pipe droops, a wide from behind the hero |
| 30-31 | 46.3 | 0.6 | Two 7-frame shots: the deck ("Ace's Table"), a gun |
| 32-33 | 46.9 | 1.8 | The flat cap puts the gun to his head and lives; someone in the bar holds the wanted poster |
| 34 | 48.7 | 1.5 | Wide lens: the hero plays "3x Aces" |
| 35 | 50.2 | 1.4 | The general slams the table: "LIAR!" |
| 36 | 51.5 | 2.4 | Slow low dolly along the table past the cloche (the breath before the reveal) |
| 37 | 53.9 | 1.5 | Insert: three aces, tinted green (true). Then the general tips off his chair, camera rolled |
| 38 | 55.4 | 0.9 | Close-up: the flat cap, eyes wide |
| 39-40 | 56.3 | 2.1 | Overhead, camera rotating over the body; wider |
| 41-46 | 58.4 | 5.1 | Last round in six shots under a second: "2x Kings", "3x Kings", a green king, the flat cap closes his eyes |
| 47 | 63.5 | 2.0 | Close-up: the hero, blood-spotted, one eyebrow up. Silence |
| 48 | 65.5 | 0.5 | Black: "SUBSCRIBE :)" |

### Fugitive (times in seconds)
| # | start | len | shot |
|---|---|---|---|
| 1 | 0.0 | 6.3 | Wide, slow push: three officers with torches at the bar door, a police car crossing the foreground, red/blue wash |
| 2 | 6.3 | 2.4 | An officer by his car eating a doughnut (the comic beat) |
| 3 | 8.7 | 8.8 | One take at wheel height: car stops, door opens, a man in a fedora steps out as a silhouette, focus pulls to the sign, camera rises behind his head |
| 4 | 17.5 | 2.2 | INT: blood-spotted cards on the table, a torch beam coming through the haze |
| 5-6 | 19.6 | 4.3 | Officer with torch and pistol; the barman, hands up, eyes white in the beam |
| 7 | 24.0 | 5.0 | A body at the card table; then black: two headlights in an alley, the frame flipping red/blue each beat, plate "RBLX MAN" |
| 8 | 28.9 | 6.0 | The car leaves in tyre smoke; the doughnut officer reacts, drops it and runs (handheld) |
| 9-11 | 34.9 | 6.5 | Fedora and barman, three over-shoulders; the barman points |
| 12 | 41.4 | 2.1 | Push in and roll onto a notepad on the rug: a sketch of a face |
| 13 | 43.5 | 4.5 | Match cut: the same face driving, streetlights sweeping across him; a case on the seat |
| 14 | 48.0 | 3.3 | High wide: officers scramble to two cars |
| 15-16 | 51.2 | 5.5 | The chase: a drift through 3D title letters that shatter, whip pans, a mirror shot |
| 17 | 56.7 | 3.3 | Static wide: a house at night, the car pulls in (the stillest shot of the film) |
| 18 | 60.0 | 2.3 | Low angle: he gets out |
| 19 | 62.3 | 2.9 | A case is emptied; cash on green felt. Music has stopped |
| 20 | 65.2 | 2.1 | Wide master: the boss under the lamp, a man either side, weapons on the table |
| 21 | 67.3 | 2.1 | The hero, standing, small smile |
| 22 | 69.4 | 6.6 | The boss talks, one take, face swapping per syllable group, arm on the stressed words |
| 23 | 76.0 | 1.5 | Top-down: the money on the table |
| 24 | 77.5 | 2.4 | Over the hero's shoulder at the boss |
| 25 | 79.8 | 1.5 | Insert: the hero's hand closes into a fist |
| 26 | 81.4 | 5.4 | The boss drives a knife through his own hand, smiling; pan to a man with a drum-magazine gun |
| 27 | 86.8 | 3.2 | Rain, high angle: he walks past a hospital sign; a car's lights pass. Music returns |
| 28 | 90.0 | 5.1 | Low angle close-up in the rain; he looks up |
| 29-30 | 95.1 | 4.0 | Hospital room from behind: a child in bed, birthday balloons, lightning in the window |
| 31-33 | 99.2 | 3.2 | Insert: a bill, "YOU OWE $2,432,344 FINAL NOTICE"; his profile |
| 34 | 102.4 | 5.0 | Slow push: a card with three symbols on the floor in a wedge of light from the door |
| 35 | 107.4 | 3.5 | Black: "To Be Continued", then "Subscribe" |
