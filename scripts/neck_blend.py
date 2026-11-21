"""Soften the neck of a character rigged by rig_block.py, so a head nod bends the collar instead of tearing it.

rig_block gives every vertex 100% to one bone and splits head from torso at the measured neck line (armature prop "neck"). A rigid
block head on a block torso is fine with that, but anything that crosses the line (a hijab, a collar, a beard, the chin of a face
whose mouth sits low, prep_mouth's head-skinned mouth plate) hinges there: any nod opens a striped gap under the lips and, past
about 10 degrees, a band of the body's colour between face and cloth. This does, once per character (proven on Sekar, Negara Angin):
  1. merge by distance among head + torso vertices only (Meshy / Tripo shells carry duplicates, and rig_block's neck cut is welded
     back so the neck is one surface again; the arm and hip cuts stay open, so arms and the lower body still turn rigidly),
     then recalculate normals outward;
  2. the chin and everything up to the neck pivot -> head 100%; below it a smootherstep head/spine gradient down through the
     collar (band neck - 0.16 to just under the mouth plate's bottom, or to the pivot without a plate), outer fabric folds lagging a
     little behind the throat; arm vertices are left alone;
  3. one vertex-group smoothing pass across the band, so neighbouring weights never step;
  4. no sharp edges inside the band + a Weighted Normal modifier after the armature (block edges elsewhere stay crisp).
Lengths are Sekar's (height 1.90) scaled by the character's height. Re-running is safe: the band is re-weighted from scratch.

  Blender -b characters/x.blend -P scripts/neck_blend.py -- [--out y.blend] [--no-backup]   (backup: x_preneck.blend)
  from neck_blend import blend_neck; blend_neck(armature, mesh, mouth=plate_or_None)          (rig_block / prep_mouth call it)
"""
import bpy, bmesh, os, sys, shutil
import numpy as np
from mathutils import Vector

REF_H = 1.90                                   # Sekar's height: the lengths below were tuned on her


def _smoother(x):
    x = np.clip(x, 0.0, 1.0); return x * x * x * (x * (x * 6 - 15) + 10)   # smootherstep: no kink at either end


def mouth_bottom(mesh, mouth):
    """Lowest point of a mouth plate, in the mesh's own space (None without a plate)."""
    if mouth is None: return None
    inv = mesh.matrix_world.inverted(); mw = mouth.matrix_world
    return min((inv @ (mw @ v.co)).z for v in mouth.data.vertices)


def blend_neck(arm, mesh, mouth=None, z_mouth=None, merge=0.0006, verbose=True):
    """Re-weight the neck band of `mesh` (skinned to rig_block bones head / spine) in place. Returns (lo, hi)."""
    say = print if verbose else (lambda *a: None)
    k = float(arm.get("height", REF_H)) / REF_H
    neck = float(arm["neck"])
    if z_mouth is None: z_mouth = mouth_bottom(mesh, mouth)
    G = {g.name: g for g in mesh.vertex_groups}; H, S = G["head"], G["spine"]
    ok_groups = {H.index, S.index}

    # ---- 1. merge by distance among head + torso vertices, normals outward
    me = mesh.data
    bm = bmesh.new(); bm.from_mesh(me)
    dl = bm.verts.layers.deform.verify()
    sub = [v for v in bm.verts if v[dl] and set(v[dl].keys()) <= ok_groups]
    n0 = len(bm.verts)
    # rig_block's flat caps on the neck plane: the weld closes the neck, and a cap left inside would take blended weights at its
    # corners and poke out through the cloth as thin dark slivers
    bm.normal_update(); subs = set(sub); e = 3e-4 * k
    caps = [f for f in bm.faces if abs(f.normal.z) > 0.99 and all(v in subs and abs(v.co.z - neck) < e for v in f.verts)]
    bmesh.ops.delete(bm, geom=caps, context="FACES_ONLY")
    sub = [v for v in sub if v.is_valid]
    bmesh.ops.remove_doubles(bm, verts=sub, dist=merge * k)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    for f in bm.faces: f.smooth = True
    bm.to_mesh(me); bm.free(); me.update()
    say("neck_blend: removed", len(caps), "neck cap faces, merged", n0 - len(me.vertices), "vertices")

    # ---- 2. the band, in the mesh's own space (rig_block: head pivot at x = y = 0, z = neck)
    lo = max(neck - 0.16 * k, float(arm.get("hip", 0.0)) + 0.05 * k)    # collar bottom: still all body
    hi = neck if z_mouth is None else min(neck, z_mouth - 0.012 * k)     # the pivot, or just under the plate: all head above
    top = neck + 0.02 * k                                                # re-weight up to here
    pad = 0.02 * k                                                       # smoothing reaches this far past the band
    n = len(me.vertices)
    co = np.empty(n * 3, np.float32); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
    z = co[:, 2]; r = np.hypot(co[:, 0], co[:, 1])
    elig = np.zeros(n, bool)
    for v in me.vertices:                                                # only head / torso vertices; arms keep their weights
        gs = [g.group for g in v.groups if g.weight > 0]
        elig[v.index] = bool(gs) and all(g in ok_groups for g in gs)
    zone = elig & (z >= lo - pad) & (z <= top)
    # the blend reaches only as far out as the neck itself: the rim where rig_block cut it (90th percentile radius), fading to
    # nothing 0.05 further out. Block shoulders and small loose pieces hidden inside the arms stay on the body (a stray shard
    # at |x| 0.43 on the Bugis woman swung out of her arm on a head tilt before this)
    rim = elig & (np.abs(z - neck) < 0.004 * k)
    r_rim = float(np.percentile(r[rim], 90)) if rim.sum() > 20 else float(np.percentile(r[elig & (z > neck) & (z < neck + 0.04 * k)], 90))
    reach = 1.0 - _smoother((r - r_rim) / (0.05 * k))
    bias = np.clip((r - 0.10 * k) / k * 0.5, 0.0, 0.12)                  # outer folds hang: they follow the head a little later
    w = np.where(z >= hi, 1.0, np.where(z < lo, 0.0, _smoother((z - lo) / max(hi - lo, 1e-6) - bias))) * reach
    # ---- 3. smoothing across the band (edge neighbours, 3 passes at 0.5, like Blender's vertex_group_smooth)
    ev = np.empty(len(me.edges) * 2, np.int64); me.edges.foreach_get("vertices", ev); ev = ev.reshape(-1, 2)
    hw = np.zeros(n)                                                     # current head weight of every vertex
    for v in me.vertices:
        for g in v.groups:
            if g.group == H.index: hw[v.index] = g.weight
    was_head = (hw > 0.999) & (z >= neck)                                # rig_block's own head part above the pivot stays whole
    hw[zone] = w[zone]
    sm = elig & (z >= lo - pad) & (z <= hi + pad)
    a_, b_ = ev[:, 0], ev[:, 1]
    for _ in range(3):
        acc = np.zeros(n); cnt = np.zeros(n)
        np.add.at(acc, a_, hw[b_]); np.add.at(cnt, a_, 1); np.add.at(acc, b_, hw[a_]); np.add.at(cnt, b_, 1)
        avg = np.where(cnt > 0, acc / np.maximum(cnt, 1), hw)
        hw = np.where(sm, 0.5 * hw + 0.5 * avg, hw)
    force = elig & (z >= hi) & (z <= top)                                # the chin and lower lip stay on the head, no matter what
    hw[force] = np.where(was_head, 1.0, reach)[force]
    idx = np.nonzero(elig & (z >= lo - pad) & (z <= max(top, hi + pad)))[0]
    for i in idx:
        h = float(np.clip(hw[i], 0.0, 1.0)); i = int(i)
        H.add([i], h, "REPLACE"); S.add([i], 1.0 - h, "REPLACE")
    say(f"neck_blend: neck {neck:.3f} band {lo:.3f} -> {hi:.3f}, rim radius {r_rim:.3f} (mouth bottom {z_mouth if z_mouth is None else round(z_mouth, 3)}),"
        f" re-weighted {len(idx)} vertices")

    # ---- 4. shading: no hard line left at the old split
    if "sharp_edge" in me.attributes:
        band = (z >= lo - pad) & (z <= top + pad) & (r <= r_rim + 0.05 * k)
        sh = np.zeros(len(me.edges), bool); me.attributes["sharp_edge"].data.foreach_get("value", sh)
        sh[band[a_] & band[b_]] = False; me.attributes["sharp_edge"].data.foreach_set("value", sh)
    if not any(m.type == "WEIGHTED_NORMAL" for m in mesh.modifiers):
        wn = mesh.modifiers.new("WeightedNormal", "WEIGHTED_NORMAL"); wn.keep_sharp = True; wn.weight = 50; wn.mode = "FACE_AREA"
    arm["neck_blend"] = (float(lo), float(hi), r_rim)
    me.update()
    return lo, hi


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    out = os.path.abspath(args[args.index("--out") + 1]) if "--out" in args else bpy.data.filepath
    if "--no-backup" not in args and out == bpy.data.filepath:
        bak = bpy.data.filepath.replace(".blend", "_preneck.blend")
        if not os.path.exists(bak): shutil.copy2(bpy.data.filepath, bak); print("backup", bak)
    arm = next(o for o in bpy.data.objects if o.type == "ARMATURE")
    mesh = next(o for o in bpy.data.objects if o.type == "MESH" and not o.name.endswith("_mouth"))
    plate = next((o for o in bpy.data.objects if o.type == "MESH" and o.name.endswith("_mouth")), None)
    blend_neck(arm, mesh, plate)
    bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
    print("SAVED", out)
