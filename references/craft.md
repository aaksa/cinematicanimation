# Craft: story, shots, edit, animation, sound

Rules distilled from `reference-films.md`. Where a rule has a number, the number was measured there. Where it is craft with no
measurement behind it, it says so.

## 1. Story shapes that fit 30-110 seconds

**The loop that shortens** (Liar's Bar). One rule, shown once slowly, then repeated faster with one thing changed each time.
| part | share of the film | job |
|---|---|---|
| arrival | 25 % | place, opponents, the hero sits. Long shots. The music has not dropped yet |
| round 1 | 30 % | teach the rule by showing it; end on the penalty, withheld (cut to black) |
| the stake | 10 % | music out; one object says why this matters |
| round 2 | 25 % | the loudest character loses |
| round 3 | 10 % | five or six shots under a second; the last face; black |

**The chain** (Fugitive). Each scene ends on the object or fact that opens the next: evidence -> witness -> sketch -> the face ->
the chase -> the debt -> the threat -> the reason -> an unanswered object. End with "To Be Continued" only if a part 2 exists.

Rules for both:
- **Show the rule, never explain it.** If a caption is needed, it is two or three words naming what the viewer is looking at.
- **One stake object.** Small, readable, with a face or a number on it. It gets its own macro shot and the film's quietest moment.
- **One comic beat** in a dark film, early (a snack, a smug face). Tone needs a second colour.
- **Plant it three times.** Anything that pays off (a poster, a card, a key) is in the background twice before it matters.
- **Withhold the violent or decisive instant.** Black frame, or the camera on someone else's face. Show the result.
- **End on a face or an object, then under a second of black with one or two words.** No logo, no outro, no recap.
- **Colour can carry plot** (red = lie, green = true). Decide the code in the brief and never break it.

For a reel with a voice-over (the user's usual format): the VO takes the place of captions, not of pictures. Write the VO last,
after the film works silent, and leave the stake scene without it.

## 2. Shot grammar

**Coverage of one scene:** one wide master (once, early), then only closer shots. Never return to the master unless the room
itself changes.

| shot | lens | camera | use |
|---|---|---|---|
| establishing | 24-35 mm | moving: crane down, slow push | first shot; long (2.5-6 s) |
| master | 28-35 mm | table height, something soft in the foreground | once per scene |
| over-shoulder | 50-85 mm | near shoulder black and soft, a third of the frame | every exchange between two characters |
| close-up | 50-85 mm | slightly below eye line, bokeh behind the head | reactions; the face swap happens here |
| insert / macro | 24 mm a hand-width away, or 85-100 mm | on the table surface | hands, props, text. Half the film |
| top-down | 35 mm straight down | centred, symmetric | layout of a table; a body; 2-3 per film at most |
| high angle | 35-50 mm | above, looking down a street | someone alone |
| low hero | 28-35 mm | from the ground, looking up | the one moment the character decides |
| rolled (dutch) | any, 15-30 degrees | | once: the moment it goes wrong |

Rules:
- **Depth in every frame:** soft foreground, sharp subject, glowing background. If one layer is missing, add it before lighting.
- **Change size and angle on every cut.** Wide -> insert -> close is the default rhythm.
- **Moves are slow or instant.** Push-ins of 3-8 % of the distance over a whole shot; or a 6-10 frame whip. Nothing in between.
- **Handheld only when the character is not in control** (running, the chase). Still or slow for power (the boss shot is locked).
- **One rack focus, one match cut, one long take per film**, each used as a reveal. More than one and they stop being events.
- **Symmetry for power**, off-centre for doubt.
- **The title can be an object in the world** (letters on the road that the car breaks).

In 9:16: the same grammar. Masters at 24-28 mm; put the layers along the lens axis instead of side by side; over-shoulders work
better than two-shots; top-downs and inserts fill a tall frame well.

## 3. The edit

- Get the track first. `beatgrid.py track.mp3` gives BPM and beat frames. At 24 fps: 100 BPM = 14.4 frames per beat, 110 BPM = 13.1.
- **Write shot lengths in beats:** 4 (a held shot), 2.5 and 1.5 (a bar split unevenly, the Liar's Bar signature), 1, 0.5 (a flash,
  only in pairs). `K.cut_list` turns the list into frames and camera markers.
- **Cuts land within two frames of a hit.** Measured: both sides occur; do not chase a direction.
- **Pace follows the story:**
  | part | average shot |
  |---|---|
  | arrival / establishing | 2.3-6 s |
  | exchange | 1.2-2.2 s |
  | the quiet beat | 2-2.5 s, slow motion or stillness inside the shot |
  | climax | 0.6-0.9 s |
  | a speech | one take of 5-7 s, then a 1.5 s cutaway, then back |
- **The action starts before the cut and lands after it.** A slam is under way on the first frame of its shot and hits 3-5 frames in.
- **A black frame is a shot:** 14-16 frames with near-silence, once.

## 4. Animation

- **Pose to pose with holds.** `char.hit(frame, dur=3, ...)`: the move takes 2-4 frames and is a smear under motion blur; then the
  pose holds 10-40 frames. `char.life()` adds the slow drift that keeps a hold alive. Never ease everything evenly: that is the
  floaty "AI animation" look.
- **Hits on beats and half beats.** Key every `hit` and `face` with `B(n)`.
- **Faces swap, on the hit, and hold.** Neutral for a few beats, one swap exactly on the accent, hold. At most one swap per beat
  outside speech.
- **Speech is limited animation:** a mouth swap every 5-12 frames, an arm gesture on the stressed word, a head tilt between
  sentences, 1 s pauses. For the user's avatar use the real lip-sync rig instead.
- **Hands act.** Frame the arm without the face for the action, then cut to the face for the reaction.
- **Rigid, not rubbery.** No squash, no bend. Weight comes from speed and the stop.
- **Secondary motion gives scale:** smoke, a spinning card, sliding cash, a swinging door, rain, dust in a beam, flickering neon
  (ramped over 3+ frames, see the flash rule below).
- **On ones, 24 fps, 180-degree shutter.** (Both references; no doubled frames.) Do not animate on twos here: that is the
  brickfilm look and belongs to `brickmaxxing`.

## 5. Sound

- **Loudness:** master to -14 LUFS, -1 dBTP. Range 8-18 LU: let the quiet scene be quiet.
- **Structure:** a low build under the arrival -> the track drops in on a physical action (a slam, a door) -> music fully out for
  the stake scene (3-8 s short film, up to 25 s in a two-minute film) -> back in on a cut -> silence under the last face.
- **A sound for every on-screen action,** from the same frame numbers as the picture: slam, card flick, cloth, footsteps on wood,
  the lamp's hum, room tone under the silence (never digital zero until the end card).
- **Voice:** dry, close, 1-1.5 words per second, gaps of about a second. Music out or 12 dB under.
- **Bass carries it:** both references put most of their energy under 250 Hz. Check the mix on a phone speaker, where that is gone:
  the hits must still read (add a mid-range click to every low thump).
- For a sync error, late is safer than early (early is noticed at about 45 ms, late at about 125 ms).

## 6. Words on screen

- Captions for game calls or object names only: tiny (2.5-3 % of frame height), yellow with a thin black edge, bottom centre,
  two or three words, on for the length of the shot. Never a headline, never word-by-word chips: those belong to reelmaxxing.
- Story text lives on props (`K.paper`, `K.text`): poster, bill, plate, sign. The camera pushes in until it can be read on a phone.
- End card: one or two words, white on black, under a second (up to 3 s for "to be continued").

## 7. Safety and platform

- **Flashing light:** the references alternate full-frame red and blue once per beat. Keep any alternating light under three
  changes per second, ramp each change over 3+ frames and keep it to a part of the frame. The user's standing preference is stable
  light with no flashes; lightning or police lights are a deliberate, limited exception to ask about.
- **Violence:** withheld in the references, and still too strong for a general Reels audience in the gun-to-head form. Use a
  penalty that fits the platform (losing the stake, a trapdoor, lights out).
- **Originality:** new characters, a new place, a new game, a new title, licensed or CC0 music. Roblox-style blocks are a style;
  someone's film is not.
- No real person's likeness and no brand mascot as a character.

## 8. Mistakes this skill exists to prevent
| symptom | cause | fix |
|---|---|---|
| "looks like a game" | blocky world, flat colour, bright even light | real-world materials and props; one lamp; GATE L |
| "looks like a render" | sharp edges, clean surfaces, no grain, everything in focus | bevels, wear, `finish.py`, a shallow stop |
| flat, grey shadows | world light or a fill; haze too dense | world at 0.15 or less; haze 0.006-0.012; remove the fill |
| faces lost in the dark | key straight above, hat brims | a warm bounce from the table surface; turn the head to the lamp |
| floaty acting | even easing | `hit()` + holds + `life()` |
| the cut drags | lengths chosen by feel | lengths in beats; halve every shot after the midpoint |
| no emotion | no stake object, music never stops | one object, one silence |
