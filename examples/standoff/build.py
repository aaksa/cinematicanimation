"""STANDOFF - the kit's proof scene. Two figures, one table, one lamp, one small bright thing they both want.
Four shots on a 100 BPM grid (12 beats, 7.2 s): master -> insert -> the rival's face -> the hero's face.

ART BRIEF
- world: a night back room. Worn planks, soot-dark brick, one pendant lamp, a neon arc on the far wall, haze.
- light: the pendant is the only key (2700 K). Neon is the accent (amber + a pink word). A weak cold edge from behind-left.
- palette: amber light, brown-black shadow, one cyan gem as the only cold saturated thing in frame (the eye goes there).
- lens: table height. 28 mm master, 24 mm insert a hand-width from the table, 85 mm faces. Shallow focus everywhere.
- exclusions: no fill light, no bright walls, no sharp CG edges, nobody standing in empty space.

Run:  Blender -b --factory-startup -P build.py -- --out out [--stills | --frames] [--final] [--aspect 9:16]
"""
import sys, os, argparse
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "blender"))
import cine_kit as K

ap = argparse.ArgumentParser()
ap.add_argument("--out", default=os.path.join(HERE, "out")); ap.add_argument("--stills", action="store_true")
ap.add_argument("--frames", action="store_true"); ap.add_argument("--final", action="store_true"); ap.add_argument("--aspect", default="16:9")
ap.add_argument("--range", default=""); ap.add_argument("--blend", action="store_true")
ap.add_argument("--avatar", action="store_true", help="the hero is Aksa's own Roblox avatar instead of the generic figure")
ap.add_argument("--bugis", action="store_true", help="the cast is the Bugis man (hero) and the Bugis woman (rival)")
a = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
K.setup(aspect=a.aspect, height=1080, samples=160, preview=not a.final)
BPM = 100

# ---- world ---------------------------------------------------------------------------------------------------
K.room(26, 22, 10)
K.round_table("Table", 3.2, 2.9)
K.chair("ChairA", (-4.7, 0, 0), 90); K.chair("ChairB", (4.7, 0, 0), -90)
K.chair("ChairFg", (-1.2, -5.6, 0), 200)                                    # soft foreground for the master
K.pendant("Lamp", (0, 0, 6.5), power=2600, spot=125)
K.neon("Ring", (0, 10.8, 5.6), radius=1.7, color="#FFB020", strength=16, arc=300)
K.text("Sign", "OPEN", 0.9, (0, 10.75, 5.6), mat=K.emit("#FF3050", 14, "SignGlow"), extrude=0.02, bevel=0.035)
K.bokeh_lights("Shelf", ((-11, 10.2, 2.5), (11, 10.6, 8.0)), n=26)
K.light("Edge", "AREA", (-9, 8, 7), 500, 9000, target=(0, 0, 3.5), size=3)   # cold rim so dark shoulders separate from a dark wall
K.light("TableBounce", "AREA", (0, 0, 3.05), 260, 2300, target=(0, 0, 9), size=4)   # the lit table throws warm light up into the faces: the only "fill"
K.haze((26, 22, 10), (0, 0, 5), density=0.006)
for i, (x, y, r) in enumerate([(-0.9, 0.5, 20), (-0.5, -0.7, -35), (0.8, 0.9, 70)]):   # small things on the table: scale + something to defocus
    K.box(f"Chip{i}", (0.5, 0.34, 0.05), (x, y, 2.93), K.flat("#B8322A", 0.5), 0.015, rot=(0, 0, r))
K.cyl("Mug", 0.28, 0.6, (1.7, -1.2, 3.2), K.flat("#C9C2B4", 0.25), 0.05)
gem = K.box("Gem", (0.26, 0.26, 0.26), (0, 0, 3.12), K.emit("#30E0FF", 5, "GemGlow"), 0.07, rot=(45, 35, 0))
K.light("GemLight", "POINT", (0, 0, 3.25), 6, "#30E0FF", size=0.2)

# ---- cast ----------------------------------------------------------------------------------------------------
AV = a.avatar; BG = a.bugis
hero = K.Avatar(at=(-4.5, 0, 0), yaw=90, pose="table") if AV else K.Rigged("bugis_man", at=(-4.5, 0, 0), yaw=90) if BG else \
    K.Char("Hero", skin="#F2C230", shirt="#20242C", pants="#1A2A44", hat="hair", hair_color="#8A5A1E", at=(-4.5, 0, 0), yaw=90)
rival = K.Rigged("bugis_woman", at=(4.5, 0, 0), yaw=-90) if BG else \
    K.Char("Rival", skin="#E8A070", shirt="#3A2A26", pants="#16161A", hat="fedora", hat_color="#2A2A30", shirt_kind="leather", at=(4.5, 0, 0), yaw=-90)
for c in (hero, rival): c.sit(1)
if not AV: hero.pose(1, arm_l=(62, 6, 0), arm_r=(20, 4, 0), head=(4, 0, 0), torso=(6, 0, 0)).face(1, "neutral")
rival.pose(1, arm_l=(58, 8, 0), arm_r=(58, 8, 0), head=(6, 40, 0), torso=(10, 0, 0)).face(1, "side")

# ---- cameras -------------------------------------------------------------------------------------------------
master = K.Cam("Master", (-2.2, -9.6, 3.1), (0.2, 0, 4.3), lens=28, stop=5.6, focus=(0, 0, 3.2))
insert = K.Cam("Insert", (1.5, -2.4, 3.5), (-1.5, 0.2, 3.1), lens=24, stop=4, focus=(0, 0, 3.1))
rivalcu = K.Cam("RivalCU", (1.6, -6.2, 4.1), (4.4, 0, 4.4), lens=50, stop=4, focus=rival.head)
herocu = K.Cam("HeroCU", (-1.6, -6.2, 4.1), (-4.4, 0, 4.4), lens=50, stop=4, focus=hero.head)
S = K.cut_list([("master", master, 4), ("insert", insert, 1.5), ("rival", rivalcu, 2.5), ("hero", herocu, 4)], BPM)
B = K.beats(BPM)

# ---- performance (every move lands on a beat or a half beat) -------------------------------------------------
master.push(*S["master"], 0.07).handheld(0.5)
if AV:                                                                     # the avatar: bone names, and its own painted face
    hero.hit(B(2), 4, head=(10, 0, 0)); hero.face.dart(B(2), "look_l", 20)
    hero.hit(B(4) + 4, 3, "reach")
    hero.pose(S["hero"][0], head=(6, 0, -40)); hero.hit(B(9.5), 3, head=(2, -5, -64))
    hero.face.expr(B(9.5), eyes="happy", brows="one_up", mouth="smile")
else:
    hero.hit(B(2), 4, head=(8, 0, 0)).face(B(2), "side")                  # he looks at the gem on beat 2
    hero.hit(B(4) + 4, 3, arm_r=(78, 10, 0), torso=(14, 0, 0))               # the slam: 3 frames, lands 4 frames into the insert
insert.at(S["insert"][0], roll=-4).handheld(0.8)
rival.hit(B(6.5), 2, head=(-8, 62, 0), torso=(2, 0, 0)).face(B(6.5), "shock")  # the swap is ON the half beat, then held
rivalcu.push(*S["rival"], 0.05).handheld(0.4)
if not AV:
    hero.pose(S["hero"][0], head=(6, -40, 0)).face(S["hero"][0], "neutral")
    hero.hit(B(9.5), 3, head=(2, -64, -5)).face(B(9.5), "smirk")
herocu.push(*S["hero"], 0.08).handheld(0.3)
hero.life(); rival.life()
if AV: hero.finish()

# ---- output --------------------------------------------------------------------------------------------------
os.makedirs(a.out, exist_ok=True)
if a.blend:
    import bpy; bpy.ops.wm.save_as_mainfile(filepath=os.path.join(a.out, "standoff.blend"))
if a.stills:
    for name, (f0, f1) in S.items(): K.still(os.path.join(a.out, f"still_{name}.png"), (f0 + f1) // 2 + (6 if name != "master" else 0))
if a.frames:
    r = [int(x) for x in a.range.split("-")] if a.range else [None, None]
    K.render_range(os.path.join(a.out, "frames"), r[0], r[1])
print("SHOTS", S)
