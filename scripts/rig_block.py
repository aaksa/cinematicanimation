"""Give a static, one-piece blocky character (a Meshy / Tripo / Roblox export) the rigid skeleton cine_kit expects.

  Blender -b source.blend -P rig_block.py -- --out characters/name.blend --name Name --neck 0.44 --hip -0.40
        --arm-x 0.372 --arm-slope -0.177 --arm-z -0.42 0.46 --shoulder 0.33 0.36 --rest-out 33 [--legs -0.69 0.17]

All numbers are in the source mesh's own units (measure them from slices of the mesh first). The parts stay rigid, as on a
toy: head, torso, two arms, the lower body (bends at the hip to sit) and, with --legs, two legs below a hem. The mesh is
really cut apart on the joint planes and every open end is capped, so nothing stretches when a part turns.
  neck / hip    heights where the head starts and where the lower body starts
  arm-x, slope  the torso/arm border: an arm is where |x| > arm-x + slope * z, between the two --arm-z heights
  shoulder      the arm's pivot (|x|, z)
  rest-out      degrees the arms are spread from hanging straight down in the source pose (A-pose about 30, arms down 0)
  legs          hem height and the legs' |x| pivot: only for trousers showing below a skirt or sarong
Result: armature <Name> (bones root, spine, head, arm.L, arm.R, lower, leg.L, leg.R; local axes = world axes, front = -Y,
feet on z = 0) with the mesh parented to it. cine_kit.Rigged loads it.
The neck is the one soft joint: neck_blend.py welds the head back onto the torso and blends head/spine weights through the collar,
so a nod bends a hijab or collar instead of tearing it (--no-neck-blend keeps the hard split).
"""
import bpy, sys, os, argparse
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("--out", required=True); ap.add_argument("--name", required=True); ap.add_argument("--neck", type=float, required=True)
ap.add_argument("--hip", type=float, required=True); ap.add_argument("--arm-x", type=float, required=True); ap.add_argument("--arm-slope", type=float, default=0.0)
ap.add_argument("--arm-z", type=float, nargs=2, required=True); ap.add_argument("--shoulder", type=float, nargs=2, required=True)
ap.add_argument("--rest-out", type=float, default=0.0); ap.add_argument("--legs", type=float, nargs=2); ap.add_argument("--soft", type=float, default=0.012)
ap.add_argument("--neck-soft", type=float, default=0.012)
ap.add_argument("--no-neck-blend", action="store_true", help="keep the hard head/torso split (pure block heads with nothing crossing the neck)")
a = ap.parse_args(sys.argv[sys.argv.index("--") + 1:])
o = [x for x in bpy.data.objects if x.type == "MESH"][0]
for x in list(bpy.data.objects):
    if x is not o: bpy.data.objects.remove(x)
bpy.context.view_layer.objects.active = o; o.select_set(True); bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
import bmesh, math
from mathutils import Vector
me = o.data
z0 = min(v.co.z for v in me.vertices)
for v in me.vertices: v.co.z -= z0                                                    # feet on z = 0
neck, hip = a.neck - z0, a.hip - z0; az = (a.arm_z[0] - z0, a.arm_z[1] - z0); sh_x, sh_z = a.shoulder[0], a.shoulder[1] - z0
hem = a.legs[0] - z0 if a.legs else None
bx0 = a.arm_x + a.arm_slope * z0                                                       # border: |x| = bx0 + slope * z (z from the feet)
border = lambda z: bx0 + a.arm_slope * z

# ---- 1. cut the one-piece mesh into real, separate parts. A fused mesh cannot be posed rigidly: the faces that bridge
#         an arm and the torso stretch into smears. So: slice on every joint plane, tear the parts apart, close the holes.
bm = bmesh.new(); bm.from_mesh(me)
bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-5)                              # close the texture seams so cuts form closed loops
def is_arm(c): return az[0] < c.z < az[1] and abs(c.x) > border(c.z)
def cut(co, no, keep):
    faces = [f for f in bm.faces if keep(f.calc_center_median())]
    geom = list({v for f in faces for v in f.verts}) + list({e for f in faces for e in f.edges}) + faces
    bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-6, plane_co=co, plane_no=no)
nrm = Vector((1, 0, -a.arm_slope)).normalized()
pad = 0.05
cut(Vector((bx0, 0, 0)), nrm, lambda c: c.x > 0 and az[0] - pad < c.z < az[1] + pad)                       # left arm / torso
cut(Vector((-bx0, 0, 0)), Vector((-nrm.x, 0, nrm.z)), lambda c: c.x < 0 and az[0] - pad < c.z < az[1] + pad)   # right arm / torso
cut(Vector((0, 0, neck)), Vector((0, 0, 1)), lambda c: not is_arm(c))                                      # head / torso
cut(Vector((0, 0, hip)), Vector((0, 0, 1)), lambda c: not is_arm(c))                                       # torso / lower body
if hem is not None:
    cut(Vector((0, 0, hem)), Vector((0, 0, 1)), lambda c: c.z < hip)                                       # skirt hem / legs
    cut(Vector((0, 0, 0)), Vector((1, 0, 0)), lambda c: c.z < hem)                                         # left leg / right leg
PARTS = ["spine", "head", "arm.L", "arm.R", "lower", "leg.L", "leg.R"]
def part_of(c):
    if is_arm(c): return 2 if c.x > 0 else 3
    if c.z > neck: return 1
    if c.z < hip:
        if hem is not None and c.z < hem: return 5 if c.x > 0 else 6
        return 4
    return 0
lab = bm.faces.layers.int.new("part")
for f in bm.faces: f[lab] = part_of(f.calc_center_median())
# cloth that only brushes past a limb (a veil tip beside a hand, a sliver of sleeve) must not ride on that limb: within each
# arm, head and leg keep the main solid and hand every small stray piece to the part it hangs from
bm.faces.ensure_lookup_table(); comp = {}; sizes = []
for f0 in bm.faces:
    if f0.index in comp: continue
    cid = len(sizes); comp[f0.index] = cid; stack = [f0]; cnt = 0
    while stack:
        f = stack.pop(); cnt += 1
        for e_ in f.edges:
            for g in e_.link_faces:
                if g.index not in comp and g[lab] == f[lab]: comp[g.index] = cid; stack.append(g)
    sizes.append((cnt, f0[lab]))
best = {}
for cid, (cnt, p_) in enumerate(sizes):
    if cnt > best.get(p_, (0, -1))[0]: best[p_] = (cnt, cid)
moved = 0
for f in bm.faces:
    p_ = f[lab]
    if p_ in (2, 3, 5, 6) and comp[f.index] != best[p_][1] and sizes[comp[f.index]][0] < 0.2 * best[p_][0]:
        f[lab] = 0 if p_ in (2, 3) else 4; moved += 1
print("stray faces handed back to the body:", moved)
tear = [e for e in bm.edges if len({f[lab] for f in e.link_faces}) > 1]
bmesh.ops.split_edges(bm, edges=tear)                                                   # the parts no longer share vertices
uv = bm.loops.layers.uv.active
def plane_of(v):
    """Which cut plane a vertex lies on (0 = none): 1/2 arm borders, 3 neck, 4 hip, 5 hem, 6 between the legs."""
    c = v.co; e = 2e-4
    if abs(abs(c.x) - border(c.z)) < e and az[0] - pad < c.z < az[1] + pad: return 1 if c.x > 0 else 2
    if abs(c.z - neck) < e: return 3
    if abs(c.z - hip) < e: return 4
    if hem is not None and abs(c.z - hem) < e: return 5
    if hem is not None and abs(c.x) < e and c.z < hem + e: return 6
    return 0
groups = {}
for e_ in bm.edges:
    if not e_.is_boundary: continue
    pa, pb_ = plane_of(e_.verts[0]), plane_of(e_.verts[1])
    if pa and pa == pb_: groups.setdefault((pa, e_.link_faces[0][lab]), []).append(e_)
old = set(bm.faces); caps = []; seen = set(old)
for (pl, part), edges in groups.items():                                               # one flat cap per open end of each part;
    try: bmesh.ops.triangle_fill(bm, use_beauty=True, use_dissolve=False, edges=edges)   # scan-fill copes with shells inside shells
    except Exception as ex: print("cap", pl, part, ex)
    mi = edges[0].link_faces[0].material_index
    for f in bm.faces:
        if f not in seen:
            seen.add(f); caps.append(f); f[lab] = part; f.material_index = mi; f.smooth = False     # every cap triangle belongs to ITS part
for f in caps:
    for l in f.loops:                                                                   # colour the cap from the texture at its rim
        src = next((m for m in l.vert.link_loops if m.face in old), None)
        if src is not None and uv is not None: l[uv].uv = src[uv].uv
bmesh.ops.recalc_face_normals(bm, faces=caps)
vpart = {}
for f in bm.faces:
    for v in f.verts: vpart[v.index] = f[lab]
bm.verts.index_update()
vpart = [0] * len(bm.verts)
for f in bm.faces:
    for v in f.verts: vpart[v.index] = f[lab]
mixed = sum(1 for v in bm.verts if len({f[lab] for f in v.link_faces}) > 1)
if mixed: print("WARNING:", mixed, "vertices are shared by two parts and will stretch")
print(f"cut: {len(tear)} torn edges, {len(caps)} caps, parts used {sorted(set(vpart))}")
bm.to_mesh(me); bm.free(); me.update()
for pl in me.polygons: pl.use_smooth = True
try: me.set_sharp_from_angle(angle=math.radians(42))                                    # keep the block edges crisp after the weld
except Exception as ex: print("sharp:", ex)
n = len(me.vertices); V = np.empty(n * 3); me.vertices.foreach_get("co", V); V = V.reshape(-1, 3); x, y, z = V.T
vp = np.array(vpart)
W = {k: (vp == i).astype(float) for i, k in enumerate(PARTS) if (vp == i).any() or k in ("spine", "head", "arm.L", "arm.R", "lower")}
J = {"root": (0, 0, hip), "spine": (0, 0, hip), "head": (0, 0, neck), "arm.L": (sh_x, 0, sh_z), "arm.R": (-sh_x, 0, sh_z), "lower": (0, 0, hip)}
PAR = {"spine": "root", "head": "spine", "arm.L": "spine", "arm.R": "spine", "lower": "root"}
if a.legs:
    J["leg.L"] = (a.legs[1], 0, hem + 0.06); J["leg.R"] = (-a.legs[1], 0, hem + 0.06); PAR["leg.L"] = PAR["leg.R"] = "lower"
arm_d = bpy.data.armatures.new(a.name + "_arm"); ao = bpy.data.objects.new(a.name, arm_d); bpy.context.collection.objects.link(ao)
bpy.context.view_layer.objects.active = ao; bpy.ops.object.mode_set(mode="EDIT")
for k, h in J.items():
    b = arm_d.edit_bones.new(k); b.head = h; b.tail = (h[0], h[1] + 0.06, h[2]); b.roll = 0
for k, p in PAR.items(): arm_d.edit_bones[k].parent = arm_d.edit_bones[p]
bpy.ops.object.mode_set(mode="OBJECT")
for b in ao.pose.bones: b.rotation_mode = "YXZ" if b.name.startswith("arm") else "XYZ"     # arms: un-spread first, then swing
for k, w in W.items():
    g = o.vertex_groups.new(name=k); full = np.nonzero(w > 0.999)[0]; part = np.nonzero((w > 1e-3) & (w <= 0.999))[0]
    if len(full): g.add(full.tolist(), 1.0, "REPLACE")
    for i in part: g.add([int(i)], float(w[i]), "REPLACE")
    print(f"  {k:6s} {len(full) + len(part):7d} verts ({len(part)} blended)")
m = o.modifiers.new("arm", "ARMATURE"); m.object = ao; o.parent = ao; o.name = a.name + "_mesh"
H = float(V[:, 2].max()); hy = float(y[z > neck].mean()) if (z > neck).any() else 0.0
ao["height"] = H; ao["rest_out"] = a.rest_out; ao["hip"] = float(hip); ao["neck"] = float(neck); ao["has_legs"] = bool(a.legs)
ao["thick"] = float(y[z < hip].max() - y[z < hip].min()); ao["head_mid"] = (0.0, hy, float((neck + H) / 2 - neck))
if not a.no_neck_blend:                                                                # a hard 100% split at the neck tears anything that
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))                      # crosses it (hijab, collar, a low chin) on any nod:
    from neck_blend import blend_neck                                                   # weld it back and blend head/spine through the collar
    blend_neck(ao, o)                                                                   # (prep_mouth re-blends under its plate)
for im in bpy.data.images:
    if im.source == "FILE" and not im.packed_file and im.filepath: im.pack()
bpy.ops.wm.save_as_mainfile(filepath=a.out, compress=True)
print("RIGGED", a.out, "height", round(H, 3))
