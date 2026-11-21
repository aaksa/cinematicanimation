"""Give a rigged character with a PAINTED face a mouth that sings: a thin plate that hugs the face over the painted mouth, skinned
to the head bone, showing one cell of a mouth atlas drawn in the character's own style. Cell 0 is the painted mouth itself (copied
pixel for pixel), so at rest the plate is invisible; the others are lip-sync shapes over the character's own skin.

  Blender -b cast/her.blend -P film/prep_mouth.py -- cast/her_sing.blend [--cz 1.52]

In the scene: the plate is <Mesh name minus _mesh>_mouth with a custom property "mcell" (0-9, constant keys), see MOUTHS.
"""
import bpy, sys, os, math
import numpy as np
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:]; OUT = os.path.abspath(args[0])
MOUTHS = ["rest", "mbp", "a", "a_mid", "e", "i", "o", "u", "fv", "cons"]
arm = next(o for o in bpy.data.objects if o.type == "ARMATURE"); mesh = next(o for o in bpy.data.objects if o.type == "MESH")
H = arm["height"]; cz_guess = float(args[args.index("--cz") + 1]) if "--cz" in args else H * 0.80

# ---- 1. a flat, unlit orthographic picture of the front of the head (the painting, exactly as textured)
sc = bpy.context.scene
sc.render.engine = "BLENDER_WORKBENCH"; sc.display.shading.light = "FLAT"; sc.display.shading.color_type = "TEXTURE"
sc.view_settings.view_transform = "Standard"; sc.render.film_transparent = True
SIZE = 0.6; RES = 1024
cam = bpy.data.objects.new("ortho", bpy.data.cameras.new("ortho")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = "ORTHO"; cam.data.ortho_scale = SIZE; cam.location = (0, -3, cz_guess); cam.rotation_euler = (math.pi / 2, 0, 0)
sc.render.resolution_x = sc.render.resolution_y = RES; sc.render.resolution_percentage = 100
shot = os.path.splitext(OUT)[0] + "_face.png"; sc.render.filepath = shot; bpy.ops.render.render(write_still=True)
img = bpy.data.images.load(shot); px = np.array(img.pixels[:], np.float32).reshape(RES, RES, 4)[::-1]   # row 0 = top
rgb = px[..., :3]; al = px[..., 3]


def to_img(x, z):                                                    # model x,z -> pixel col,row
    return (x / SIZE + 0.5) * RES, (0.5 - (z - cz_guess) / SIZE) * RES


def to_mod(c, r): return (c / RES - 0.5) * SIZE, cz_guess + (0.5 - r / RES) * SIZE


# ---- 2. find the painted mouth: the darkest / pinkest blob in the lower middle of the face, against the median skin
yy, xx = np.mgrid[0:RES, 0:RES]
cheeks = (np.abs(xx - RES / 2) < RES * 0.2) & (yy > RES * 0.37) & (yy < RES * 0.46) & (al > 0.5)
skin = np.median(rgb[cheeks], axis=0)
centre = (np.abs(xx - RES / 2) < RES * 0.15) & (yy > RES * 0.45) & (yy < RES * 0.57) & (al > 0.5)
d = np.linalg.norm(rgb - skin, axis=2)
cand = centre & (d > 0.16) & (rgb.sum(2) < skin.sum() * 0.98)
rows, cols = np.nonzero(cand)
if len(rows) < 20: raise SystemExit("mouth not found: pass --cz")
r0, r1 = np.percentile(rows, [3, 97]); c0, c1 = np.percentile(cols, [3, 97])
mcx, mcz = to_mod((c0 + c1) / 2, (r0 + r1) / 2); mw = (c1 - c0) / RES * SIZE; mh = (r1 - r0) / RES * SIZE
lum = rgb[cand].sum(1); line = np.median(rgb[cand][lum < np.percentile(lum, 20)], axis=0)       # the painted stroke colour
lipc = np.median(rgb[cand][lum > np.percentile(lum, 55)], axis=0)                                    # the painted lips
print("MOUTH centre x %.4f z %.4f  w %.4f h %.4f  skin %s line %s" % (mcx, mcz, mw, mh, np.round(skin, 3), np.round(line, 3)))

# ---- 3. the atlas: 10 cells, each the plate's area; skin with a feathered edge, then a mouth
PW, PH = mw * 1.75, min(0.085, mw * 0.75)
CW, CH = 384, int(384 * PH / PW)
ys, xs = np.mgrid[0:CH, 0:CW].astype(np.float32)
U = (xs + 0.5) / CW - 0.5; V = 0.5 - (ys + 0.5) / CH                 # plate coords, -0.5..0.5 (V up)
X = U * PW; Z = V * PH                                               # model units from the mouth centre
feather = np.clip((1 - np.sqrt((U / 0.5) ** 2 + (V / 0.5) ** 2)) / 0.22, 0, 1)
dark = np.array([0.16, 0.05, 0.07]); lip = lipc; teeth = np.array([0.93, 0.9, 0.86])
tongue = np.array([0.55, 0.22, 0.26])


def ell(cx, cz, rx, rz, soft=0.004):
    return np.clip((1 - np.sqrt(((X - cx) / rx) ** 2 + ((Z - cz) / rz) ** 2)) * min(rx, rz) / soft, 0, 1)


def curve(w, bend, thick, dz=0.0):
    """A stroke across the mouth: bend > 0 = smile."""
    t = np.clip(X / (w / 2), -1, 1); zc = dz + bend * (t ** 2 - 1) * -1 * 0 + bend * (t ** 2)
    inside = np.abs(X) < w / 2
    return np.clip((thick / 2 - np.abs(Z - (dz - bend + bend * t ** 2))) / 0.0012, 0, 1) * inside


def paint(cell, m, col):
    for k in range(3): cell[..., k] = cell[..., k] * (1 - m) + col[k] * m


def open_mouth(cell, w, h, teeth_top=True, teeth_bot=False, round_=False):
    rx, rz = w / 2, h / 2
    outer = ell(0, 0, rx + 0.007, rz + 0.007); inner = ell(0, 0, rx, rz)
    paint(cell, outer, lip); paint(cell, inner, dark)
    paint(cell, outer * (1 - inner) * np.clip((Z - rz * 0.2) / 0.002, 0, 1) * 0.6, line)                # a darker upper lip line, as painted
    if not round_:
        paint(cell, inner * np.clip((Z + rz * 0.35) / 0.002, 0, 1) * 0 + inner * np.clip((-Z - rz * 0.35) / 0.003, 0, 1) * 0.0, tongue)
        paint(cell, inner * ell(0, -rz * 0.75, rx * 0.6, rz * 0.45), tongue)
    if teeth_top: paint(cell, inner * np.clip((Z - (rz * 0.55)) / 0.0015, 0, 1), teeth)
    if teeth_bot: paint(cell, inner * np.clip((-(rz * 0.6) - Z) / 0.0015, 0, 1), teeth)


cells = []
for name in MOUTHS:
    cell = np.zeros((CH, CW, 3), np.float32); cell[...] = skin
    if name == "rest":                                               # the painting itself, copied pixel for pixel
        ci, ri = to_img(mcx + X, mcz + Z); ci = np.clip(ci.astype(int), 0, RES - 1); ri = np.clip(ri.astype(int), 0, RES - 1)
        cell = rgb[ri, ci].copy()
    elif name == "mbp":  paint(cell, curve(mw * 0.85, 0.0, max(0.0035, mh * 0.35)), line)
    elif name == "a":    open_mouth(cell, mw * 0.72, PH * 0.6)
    elif name == "a_mid": open_mouth(cell, mw * 0.66, PH * 0.38)
    elif name == "e":    open_mouth(cell, mw * 0.86, PH * 0.28, teeth_bot=True)
    elif name == "i":    open_mouth(cell, mw * 0.74, PH * 0.17, teeth_bot=True)
    elif name == "o":    open_mouth(cell, mw * 0.44, PH * 0.5, teeth_top=False, round_=True)
    elif name == "u":    open_mouth(cell, mw * 0.28, PH * 0.32, teeth_top=False, round_=True)
    elif name == "fv":   open_mouth(cell, mw * 0.66, PH * 0.15); paint(cell, curve(mw * 0.6, 0.0, 0.004, dz=-0.004), lip)
    elif name == "cons": open_mouth(cell, mw * 0.52, PH * 0.24)
    a = feather if name != "rest" else feather
    cells.append(np.dstack([cell, a]))
atlas = np.concatenate(cells, axis=1)
apath = os.path.splitext(OUT)[0] + "_mouths.png"
im = bpy.data.images.new("mouth_atlas", atlas.shape[1], atlas.shape[0], alpha=True)
im.pixels.foreach_set(atlas[::-1].astype(np.float32).ravel()); im.filepath_raw = apath; im.file_format = "PNG"; im.save()
print("ATLAS", apath, atlas.shape)

# ---- 4. the plate: a grid over the mouth, every vertex dropped onto the face surface (ray cast from the front), a hair in front
NX, NZ = 14, 8; verts = []; faces = []; uvs = []
mi = mesh.matrix_world.inverted()
dg = bpy.context.evaluated_depsgraph_get(); mesh_e = mesh.evaluated_get(dg)
for j in range(NZ + 1):
    for i in range(NX + 1):
        u, v = i / NX, j / NZ; x = mcx + (u - 0.5) * PW; z = mcz + (v - 0.5) * PH
        o = mi @ Vector((x, -3, z)); dvec = (mi.to_3x3() @ Vector((0, 1, 0))).normalized()
        hit, loc, nrm, _ = mesh_e.ray_cast(o, dvec)
        y = (mesh.matrix_world @ loc).y if hit else -0.2
        verts.append((x, y - 0.0018, z)); uvs.append((u, v))
for j in range(NZ):
    for i in range(NX):
        a_ = j * (NX + 1) + i; faces.append((a_, a_ + 1, a_ + NX + 2, a_ + NX + 1))
me = bpy.data.meshes.new(mesh.name.replace("_mesh", "") + "_mouth"); me.from_pydata([tuple(mesh.matrix_world.inverted() @ Vector(v)) for v in verts], [], faces)
uvl = me.uv_layers.new(name="UVMap")
for p in me.polygons:
    p.use_smooth = True
    for li in p.loop_indices: uvl.data[li].uv = uvs[me.loops[li].vertex_index]
plate = bpy.data.objects.new(me.name, me); sc.collection.objects.link(plate)
plate.parent = mesh.parent; plate.matrix_parent_inverse = mesh.matrix_parent_inverse.copy(); plate.matrix_basis = mesh.matrix_basis.copy()
vg = plate.vertex_groups.new(name="head"); vg.add(list(range(len(verts))), 1.0, "REPLACE")
md = plate.modifiers.new("Armature", "ARMATURE"); md.object = arm
plate["mcell"] = 0.0; plate.visible_shadow = False

# ---- 5. its material: the atlas cell picked by the object's "mcell", lit like her skin
src = mesh.data.materials[0]; sb = next((n for n in src.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
m = bpy.data.materials.new(me.name + "_m"); m.use_nodes = True; nt = m.node_tree; b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
uvn = nt.nodes.new("ShaderNodeUVMap"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(uvn.outputs[0], sep.inputs[0])
at = nt.nodes.new("ShaderNodeAttribute"); at.attribute_type = "OBJECT"; at.attribute_name = "mcell"
add = nt.nodes.new("ShaderNodeMath"); add.operation = "ADD"; nt.links.new(sep.outputs["X"], add.inputs[0]); nt.links.new(at.outputs["Fac"], add.inputs[1])
div = nt.nodes.new("ShaderNodeMath"); div.operation = "DIVIDE"; div.inputs[1].default_value = len(MOUTHS); nt.links.new(add.outputs[0], div.inputs[0])
cmb = nt.nodes.new("ShaderNodeCombineXYZ"); nt.links.new(div.outputs[0], cmb.inputs[0]); nt.links.new(sep.outputs["Y"], cmb.inputs[1])
tex = nt.nodes.new("ShaderNodeTexImage"); tex.image = bpy.data.images.load(apath); tex.interpolation = "Closest" if False else "Linear"; tex.extension = "CLIP"
nt.links.new(cmb.outputs[0], tex.inputs[0]); nt.links.new(tex.outputs["Color"], b.inputs["Base Color"]); nt.links.new(tex.outputs["Alpha"], b.inputs["Alpha"])
b.inputs["Roughness"].default_value = sb.inputs["Roughness"].default_value if sb else 0.5
if "Subsurface Weight" in b.inputs: b.inputs["Subsurface Weight"].default_value = 0.1
for attr, val in (("surface_render_method", "DITHERED"), ("blend_method", "HASHED")):
    if hasattr(m, attr):
        try: setattr(m, attr, val)
        except TypeError: pass
me.materials.append(m)
bpy.data.objects.remove(cam)
tex.image.pack()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("SAVED", OUT, "plate", plate.name, "cells", MOUTHS)
