"""Head-pose test for a rig_block character: renders the head and collar in six head poses from a low front three-quarter and a back
three-quarter view, on a magenta world so any hole through the mesh shows. Fast (Workbench, textured).

  Blender -b characters/x.blend -P scripts/neck_test.py -- out/dir [--res 420]
writes out/dir/<view>_<pose>.png for poses neutral, nod+16, nod-16, turn30, tilt12, nod16_turn30_tilt12.
Tile them with ffmpeg (xstack) into a sheet, or look at them one by one. See SKILL.md, "Neck seam".
"""
import bpy, sys, os, math
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:]; OUT = os.path.abspath(args[0]); os.makedirs(OUT, exist_ok=True)
RES = int(args[args.index("--res") + 1]) if "--res" in args else 420
POSES = [("neutral", 0, 0, 0), ("nod+16", 16, 0, 0), ("nod-16", -16, 0, 0), ("turn30", 0, 30, 0), ("tilt12", 0, 0, 12),
         ("nod16_turn30_tilt12", 16, 30, 12)]                     # (name, nod down, turn, tilt) in degrees, as Rigged.pose(head=...)
arm = next(o for o in bpy.data.objects if o.type == "ARMATURE")
H = float(arm["height"]); neck = float(arm["neck"])
sc = bpy.context.scene
sc.render.engine = "BLENDER_WORKBENCH"; sc.display.shading.light = "STUDIO"; sc.display.shading.color_type = "TEXTURE"
sc.display.shading.show_cavity = False; sc.view_settings.view_transform = "Standard"; sc.render.film_transparent = False
for o in bpy.data.objects:                                       # a prep_mouth plate: Workbench ignores the mcell maths, so show cell 0
    if o.type == "MESH" and o.name.endswith("_mouth") and o.data.uv_layers:   # (the painted mouth) by squeezing its UVs (not saved)
        for d in o.data.uv_layers.active.data: d.uv.x /= 10
w = sc.world or bpy.data.worlds.new("w"); sc.world = w; w.color = (1.0, 0.0, 1.0)
sc.render.resolution_x = RES; sc.render.resolution_y = int(RES * 1.15); sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = "PNG"
cam = bpy.data.objects.new("neck_cam", bpy.data.cameras.new("neck_cam")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.lens = 85
aim = Vector((0, 0, neck + 0.12 * H / 1.9))
VIEWS = {"front": (-25, -0.06), "back": (155, 0.10)}               # yaw from the front (-Y), camera height offset from the aim
dist = 3.1 * H / 1.9
pb = arm.pose.bones["head"]; pb.rotation_mode = "XYZ"
for view, (yaw, dz) in VIEWS.items():
    a = math.radians(yaw); cam.location = aim + Vector((math.sin(a) * dist, -math.cos(a) * dist, dz * H / 1.9 * 4))
    cam.rotation_euler = (aim - cam.location).to_track_quat("-Z", "Y").to_euler()
    for name, nod, turn, tilt in POSES:
        pb.rotation_euler = (math.radians(nod), math.radians(tilt), math.radians(turn))
        bpy.context.view_layer.update()
        sc.render.filepath = os.path.join(OUT, f"{view}_{name}.png"); bpy.ops.render.render(write_still=True)
print("NECK TEST", OUT)
