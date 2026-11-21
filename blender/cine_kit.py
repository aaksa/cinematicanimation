"""cine_kit - blocky toy characters in a photoreal, low-key miniature world, for Blender 5.x + Cycles.

1 Blender unit = 1 stud. A character is 5.2 studs tall, stands on z = 0 and faces -Y. Run headless:
    Blender -b --factory-startup -P build.py -- --out out
and in build.py:  import sys; sys.path.insert(0, SKILL + "/blender"); import cine_kit as K

Numbers (brightness targets, shot lengths, lens choices) come from references/reference-films.md.
"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Euler

TOY = 12.0          # depth of field is computed as if 1 stud were 1/12 of what Blender thinks: a 40 cm collectible, not a 5 m giant
_rng = random.Random(7)
D = math.radians


# ----------------------------------------------------------------------------------------------------------- scene
def setup(aspect="16:9", height=1080, fps=24, samples=192, preview=False, seed=7, engine="CYCLES"):
    """Empty scene. engine="CYCLES" (the reference look; 60-90 s a 1080p frame) or "EEVEE" (1-4 s a frame; see eevee_lights()).
    preview=True: half size, few samples (stills for checking, never the delivery)."""
    global _rng, ENGINE
    _rng = random.Random(seed); ENGINE = engine.upper()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    w, h = {"16:9": (16, 9), "9:16": (9, 16), "1:1": (1, 1), "4:5": (4, 5), "2.39:1": (2.39, 1)}[aspect]
    if w >= h: sc.render.resolution_y = height; sc.render.resolution_x = int(round(height * w / h / 2) * 2)
    else: sc.render.resolution_x = height; sc.render.resolution_y = int(round(height * h / w / 2) * 2)
    sc.render.resolution_percentage = 50 if preview else 100
    sc.render.fps = fps
    if ENGINE == "EEVEE": _setup_eevee(sc, 24 if preview else samples)
    else: _setup_cycles(sc, preview, samples)
    sc.render.use_motion_blur = True; sc.render.motion_blur_shutter = 0.5      # 180 degree shutter
    sc.view_settings.view_transform = "AgX"
    try: sc.view_settings.look = "AgX - Medium High Contrast"
    except TypeError: pass
    sc.render.image_settings.file_format = "PNG"; sc.render.image_settings.color_depth = "16"
    sc.render.film_transparent = False
    world((0.01, 0.012, 0.018), 0.15)
    return sc


def _setup_cycles(sc, preview, samples):
    sc.render.engine = "CYCLES"
    c = sc.cycles
    c.samples = 48 if preview else samples
    c.use_adaptive_sampling = True; c.adaptive_threshold = 0.03 if preview else 0.015
    c.use_denoising = True
    c.sample_clamp_indirect = 6.0          # kills fireflies from small bright practicals
    c.max_bounces = 8; c.diffuse_bounces = 3; c.glossy_bounces = 4; c.transmission_bounces = 6; c.volume_bounces = 1
    c.caustics_reflective = False; c.caustics_refractive = False
    try:
        p = bpy.context.preferences.addons["cycles"].preferences
        p.compute_device_type = "METAL"; p.get_devices()
        for d in p.devices: d.use = True
        c.device = "GPU"
    except Exception as e:
        print("cine_kit: GPU not enabled:", e)


def _setup_eevee(sc, samples):
    """EEVEE tuned for this look: ray-traced reflections/refraction, fast GI for the bounce, real volumetric haze, soft shadows.
    Tested on Blender 5.1 (Apple M4): 1080x1920 in 2-5 s a frame with haze. Call eevee_lights() after the scene is built."""
    try: sc.render.engine = "BLENDER_EEVEE"
    except TypeError: sc.render.engine = "BLENDER_EEVEE_NEXT"
    e = sc.eevee
    e.taa_render_samples = max(16, samples)
    e.use_raytracing = True
    try: e.ray_tracing_method = "SCREEN"
    except TypeError: pass
    e.ray_tracing_options.resolution_scale = "1"; e.ray_tracing_options.use_denoise = True
    e.use_fast_gi = True; e.fast_gi_method = "GLOBAL_ILLUMINATION"; e.fast_gi_distance = 6.0
    e.use_shadows = True; e.shadow_ray_count = 2; e.shadow_step_count = 8
    try: e.shadow_pool_size = "1024"                      # a full pool is what makes EEVEE shadows flicker frame to frame
    except TypeError: pass
    e.volumetric_tile_size = "4"; e.volumetric_samples = 96; e.use_volumetric_shadows = True
    e.volumetric_start = 0.1; e.volumetric_end = 150.0; e.volumetric_light_clamp = 0.0
    e.clamp_surface_indirect = 10.0
    e.motion_blur_steps = 1


ENGINE = "CYCLES"


def eevee_lights(keep=(), min_power=300.0):
    """EEVEE housekeeping after the scene is built (no-op under Cycles):
    - only the motivated, big lights cast shadows (names in `keep`, or power >= min_power): many small shadow lights overflow
      the shadow pool and flicker; phone glows, bounces, fills and bokeh points light without shadows.
    - glass casts no shadow (EEVEE treats it as opaque; window and jar light must pass), glass gets ray-traced refraction."""
    if ENGINE != "EEVEE": return
    for ob in bpy.data.objects:
        if ob.type == "LIGHT":
            ob.data.use_shadow = ob.name in keep or (ob.data.energy >= min_power and ob.data.type in ("SPOT", "POINT", "SUN"))
        elif ob.type in ("MESH", "FONT") and ob.active_material is not None:
            b = next((n for n in ob.active_material.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None) if ob.active_material.use_nodes else None
            if b is not None and b.inputs["Transmission Weight"].default_value > 0.5:
                ob.visible_shadow = False
                m = ob.active_material
                for attr, val in (("surface_render_method", "DITHERED"), ("use_raytrace_refraction", True)):
                    if hasattr(m, attr):
                        try: setattr(m, attr, val)
                        except TypeError: pass


def world(color=(0.01, 0.012, 0.018), strength=0.15):
    """A near-black world. Light comes from lamps you place, never from the sky."""
    w = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
    bpy.context.scene.world = w; w.use_nodes = True
    bg = next(n for n in w.node_tree.nodes if n.type == "BACKGROUND")
    bg.inputs[0].default_value = (*color, 1); bg.inputs[1].default_value = strength
    return w


def col(c):
    """'#RRGGBB' (sRGB) or a tuple -> linear RGBA."""
    if isinstance(c, str):
        c = c.lstrip("#"); c = tuple(int(c[i:i + 2], 16) / 255 for i in (0, 2, 4))
        c = tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)
    return (c[0], c[1], c[2], 1.0)


def kelvin(k):
    """Colour of a black body, good enough for lamps: 1900 candle, 2700 tungsten, 4000 fluorescent, 6500 day, 9000 moon."""
    t = k / 100.0
    r = 255 if t <= 66 else 329.698727446 * (t - 60) ** -0.1332047592
    g = 99.4708025861 * math.log(t) - 161.1195681661 if t <= 66 else 288.1221695283 * (t - 60) ** -0.0755148492
    b = 255 if t >= 66 else (0 if t <= 19 else 138.5177312231 * math.log(t - 10) - 305.0447927307)
    s = [max(0, min(255, x)) / 255 for x in (r, g, b)]
    return tuple(x ** 2.2 for x in s)


def _link(ob, parent=None):
    bpy.context.scene.collection.objects.link(ob)
    if parent is not None: ob.parent = parent
    return ob


def empty(name, loc=(0, 0, 0), parent=None):
    e = bpy.data.objects.new(name, None); e.empty_display_size = 0.3; e.location = loc
    return _link(e, parent)


# ------------------------------------------------------------------------------------------------------- materials
def _mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree
    return m, nt, next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")


def _set(b, **kw):
    for k, v in kw.items():
        key = k.replace("_", " ")
        if key in b.inputs: b.inputs[key].default_value = v


def _bump(nt, b, height_socket, strength=0.3, distance=0.05):
    n = nt.nodes.new("ShaderNodeBump"); n.inputs["Strength"].default_value = strength; n.inputs["Distance"].default_value = distance
    nt.links.new(height_socket, n.inputs["Height"]); nt.links.new(n.outputs[0], b.inputs["Normal"]); return n


def _obj_coord(nt, scale=1.0):
    tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (scale,) * 3 if not isinstance(scale, (tuple, list)) else scale
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"]); return mp.outputs[0]


def _noise(nt, vec, scale, detail=6, rough=0.6):
    n = nt.nodes.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = scale; n.inputs["Detail"].default_value = detail
    n.inputs["Roughness"].default_value = rough; nt.links.new(vec, n.inputs["Vector"]); return n


def _ramp(nt, fac, stops):
    r = nt.nodes.new("ShaderNodeValToRGB"); e = r.color_ramp.elements
    e[0].position, e[0].color = stops[0][0], stops[0][1]; e[1].position, e[1].color = stops[-1][0], stops[-1][1]
    for p, c in stops[1:-1]:
        x = e.new(p); x.color = c
    nt.links.new(fac, r.inputs[0]); return r


def plastic(color, rough=0.32, glow=0.35, name="Plastic"):
    """Toy plastic: soft highlight, light bleeding through thin edges (the backlit-hand glow), a thin clear coat."""
    m, nt, b = _mat(name); c = col(color)
    _set(b, Base_Color=c, Roughness=rough, Subsurface_Weight=glow, Subsurface_Scale=0.12, Coat_Weight=0.25, Coat_Roughness=0.15)
    if "Subsurface Radius" in b.inputs: b.inputs["Subsurface Radius"].default_value = (1.0, 0.6, 0.4)
    n = _noise(nt, _obj_coord(nt, 14), 1.0, 3)               # micro scuffs so highlights are not CG-clean
    r = _ramp(nt, n.outputs["Fac"], [(0.3, (rough - 0.06,) * 3 + (1,)), (0.8, (rough + 0.12,) * 3 + (1,))])
    nt.links.new(r.outputs[0], b.inputs["Roughness"])
    return m


def cloth(color, kind="weave", name="Cloth"):
    """Fabric with a real surface: weave (shirt, suit), knit (wool, balaclava), leather (creased)."""
    m, nt, b = _mat(name); c = col(color); _set(b, Base_Color=c, Roughness=0.85)
    if "Sheen Weight" in b.inputs: b.inputs["Sheen Weight"].default_value = 0.4
    v = _obj_coord(nt, 1.0)
    if kind == "leather":
        t = nt.nodes.new("ShaderNodeTexVoronoi"); t.inputs["Scale"].default_value = 38; t.feature = "DISTANCE_TO_EDGE"
        nt.links.new(v, t.inputs["Vector"]); _bump(nt, b, t.outputs["Distance"], 0.35, 0.012); _set(b, Roughness=0.42)
    else:
        w1 = nt.nodes.new("ShaderNodeTexWave"); w2 = nt.nodes.new("ShaderNodeTexWave")
        s = 55 if kind == "weave" else 22
        for w, d in ((w1, "X"), (w2, "Z")):
            w.bands_direction = d; w.inputs["Scale"].default_value = s; w.inputs["Distortion"].default_value = 0.6 if kind == "knit" else 0.1
            nt.links.new(v, w.inputs["Vector"])
        mx = nt.nodes.new("ShaderNodeMath"); mx.operation = "MULTIPLY" if kind == "weave" else "MAXIMUM"
        nt.links.new(w1.outputs["Fac"], mx.inputs[0]); nt.links.new(w2.outputs["Fac"], mx.inputs[1])
        _bump(nt, b, mx.outputs[0], 0.35 if kind == "weave" else 0.8, 0.02 if kind == "weave" else 0.04)
    return m


def wood(dark="#2A1408", light="#7A4A22", planks=0.0, gloss=0.35, name="Wood"):
    """Worn wood with uneven gloss. planks > 0 = plank width in studs (seams run along Y)."""
    m, nt, b = _mat(name); v = _obj_coord(nt, (1.0, 0.12, 1.0))
    grain = _noise(nt, v, 9, 8, 0.65)
    r = _ramp(nt, grain.outputs["Fac"], [(0.25, col(dark)), (0.75, col(light))])
    wear = _noise(nt, _obj_coord(nt, 0.6), 1.0, 5, 0.7)
    rr = _ramp(nt, wear.outputs["Fac"], [(0.35, (gloss - 0.15,) * 3 + (1,)), (0.7, (gloss + 0.35,) * 3 + (1,))])
    nt.links.new(rr.outputs[0], b.inputs["Roughness"])
    height = grain.outputs["Fac"]; base = r.outputs[0]
    if planks:
        br = nt.nodes.new("ShaderNodeTexBrick"); br.inputs["Scale"].default_value = 1.0
        br.inputs["Mortar Size"].default_value = 0.012; br.inputs["Brick Width"].default_value = 9.0; br.inputs["Row Height"].default_value = planks
        br.inputs["Color1"].default_value = (1, 1, 1, 1); br.inputs["Color2"].default_value = (0.72, 0.72, 0.72, 1); br.inputs["Mortar"].default_value = (0.03, 0.03, 0.03, 1)
        sw = nt.nodes.new("ShaderNodeMapping"); sw.inputs["Rotation"].default_value = (0, 0, D(90))      # rows run along Y
        tc = nt.nodes.new("ShaderNodeTexCoord"); nt.links.new(tc.outputs["Object"], sw.inputs["Vector"]); nt.links.new(sw.outputs[0], br.inputs["Vector"])
        mul = nt.nodes.new("ShaderNodeMixRGB"); mul.blend_type = "MULTIPLY"; mul.inputs[0].default_value = 1
        nt.links.new(base, mul.inputs[1]); nt.links.new(br.outputs["Color"], mul.inputs[2]); base = mul.outputs[0]
        add = nt.nodes.new("ShaderNodeMath"); add.operation = "MULTIPLY"
        nt.links.new(grain.outputs["Fac"], add.inputs[0]); nt.links.new(br.outputs["Fac"], add.inputs[1])
        inv = nt.nodes.new("ShaderNodeMath"); inv.operation = "SUBTRACT"; inv.inputs[0].default_value = 1.0
        nt.links.new(br.outputs["Fac"], inv.inputs[1])
        mix = nt.nodes.new("ShaderNodeMath"); mix.operation = "ADD"; mix.inputs[1].default_value = 0.0
        g2 = nt.nodes.new("ShaderNodeMath"); g2.operation = "MULTIPLY"; g2.inputs[1].default_value = 0.25
        nt.links.new(grain.outputs["Fac"], g2.inputs[0]); nt.links.new(inv.outputs[0], mix.inputs[0]); nt.links.new(g2.outputs[0], mix.inputs[1])
        height = mix.outputs[0]
    nt.links.new(base, b.inputs["Base Color"]); _bump(nt, b, height, 0.5, 0.04)
    return m


def brick(brick_a="#5A2A1C", brick_b="#7A3B26", mortar="#3A332C", name="Brick"):
    """Old brickwork with soot. For walls: the pattern lies in the object's X/Z plane."""
    m, nt, b = _mat(name)
    tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Rotation"].default_value = (D(90), 0, 0)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    br = nt.nodes.new("ShaderNodeTexBrick"); br.inputs["Scale"].default_value = 1.6; br.inputs["Mortar Size"].default_value = 0.025
    br.inputs["Color1"].default_value = col(brick_a); br.inputs["Color2"].default_value = col(brick_b); br.inputs["Mortar"].default_value = col(mortar)
    nt.links.new(mp.outputs[0], br.inputs["Vector"])
    dirt = _noise(nt, _obj_coord(nt, 0.35), 1.0, 7, 0.7)
    dr = _ramp(nt, dirt.outputs["Fac"], [(0.3, (0.25, 0.22, 0.2, 1)), (0.7, (1, 1, 1, 1))])
    mul = nt.nodes.new("ShaderNodeMixRGB"); mul.blend_type = "MULTIPLY"; mul.inputs[0].default_value = 1
    nt.links.new(br.outputs["Color"], mul.inputs[1]); nt.links.new(dr.outputs[0], mul.inputs[2]); nt.links.new(mul.outputs[0], b.inputs["Base Color"])
    fine = _noise(nt, _obj_coord(nt, 30), 1.0, 4)
    h = nt.nodes.new("ShaderNodeMath"); h.operation = "MULTIPLY_ADD"; h.inputs[1].default_value = 0.15
    inv = nt.nodes.new("ShaderNodeMath"); inv.operation = "SUBTRACT"; inv.inputs[0].default_value = 1
    nt.links.new(br.outputs["Fac"], inv.inputs[1]); nt.links.new(fine.outputs["Fac"], h.inputs[0]); nt.links.new(inv.outputs[0], h.inputs[2])
    _bump(nt, b, h.outputs[0], 0.9, 0.06); _set(b, Roughness=0.9)
    return m


def asphalt(wet=0.6, color="#1A1B1C", name="Asphalt"):
    """Night street. wet 0-1: share of the surface that is a puddle mirror for neon and headlights."""
    m, nt, b = _mat(name); _set(b, Base_Color=col(color))
    grit = _noise(nt, _obj_coord(nt, 40), 1.0, 3); pud = _noise(nt, _obj_coord(nt, 0.35), 1.0, 4, 0.5)
    r = _ramp(nt, pud.outputs["Fac"], [(0.62 - 0.3 * wet, (0.04,) * 3 + (1,)), (0.7 - 0.2 * wet, (0.75,) * 3 + (1,))])
    nt.links.new(r.outputs[0], b.inputs["Roughness"])
    k = nt.nodes.new("ShaderNodeMath"); k.operation = "MULTIPLY"
    nt.links.new(grit.outputs["Fac"], k.inputs[0]); nt.links.new(r.outputs[0], k.inputs[1])
    _bump(nt, b, k.outputs[0], 0.7, 0.05)
    return m


def flat(color, rough=0.6, metal=0.0, name="Flat"):
    """Plain surface: felt (rough 1), plaster (0.9), painted metal (metal 1, rough 0.3), chrome (metal 1, rough 0.05)."""
    m, nt, b = _mat(name); _set(b, Base_Color=col(color), Roughness=rough, Metallic=metal)
    n = _noise(nt, _obj_coord(nt, 25), 1.0, 4); _bump(nt, b, n.outputs["Fac"], 0.15, 0.02)
    return m


def glass(color="#FFFFFF", rough=0.02, name="Glass"):
    m, nt, b = _mat(name); _set(b, Base_Color=col(color), Roughness=rough, Transmission_Weight=1.0, IOR=1.5); return m


def emit(color, strength=10.0, name="Emit"):
    """A light you can see: neon tube, lamp bulb, screen, window. color = '#hex' or a kelvin number."""
    m, nt, b = _mat(name); c = (*kelvin(color), 1) if isinstance(color, (int, float)) else col(color)
    _set(b, Base_Color=(0, 0, 0, 1), Emission_Color=c, Emission_Strength=strength); return m


# -------------------------------------------------------------------------------------------------------- geometry
def box(name, size, loc=(0, 0, 0), mat=None, bevel=0.05, seg=3, rot=(0, 0, 0), parent=None):
    """A rounded box. Every edge is bevelled: sharp CG edges are the first thing that reads as cheap."""
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts: v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    bv = min(bevel, min(size) * 0.49)
    if bv > 0: bmesh.ops.bevel(bm, geom=bm.edges[:], offset=bv, segments=seg, profile=0.5, affect="EDGES")
    return _finish(bm, name, loc, rot, mat, parent)


def cyl(name, radius, depth, loc=(0, 0, 0), mat=None, bevel=0.03, verts=40, rot=(0, 0, 0), parent=None, radius2=None):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=verts, radius1=radius, radius2=radius if radius2 is None else radius2, depth=depth)
    if bevel > 0:
        rim = [e for e in bm.edges if abs(e.verts[0].co.z - e.verts[1].co.z) < 1e-6 and len(e.link_faces) == 2
               and any(len(f.verts) > 4 for f in e.link_faces)]
        if rim: bmesh.ops.bevel(bm, geom=rim, offset=min(bevel, depth * 0.45), segments=3, profile=0.5, affect="EDGES")
    return _finish(bm, name, loc, rot, mat, parent)


def torus(name, radius, tube, loc=(0, 0, 0), mat=None, rot=(0, 0, 0), arc=360.0, parent=None):
    """A ring or an arc of tube (neon). arc < 360 leaves a gap."""
    bm = bmesh.new(); seg = 96; ts = 12; n = max(2, int(seg * arc / 360))
    rings = []
    for i in range(n + (0 if arc >= 360 else 1)):
        a = D(arc) * i / n; c = Vector((math.cos(a) * radius, math.sin(a) * radius, 0)); out = Vector((math.cos(a), math.sin(a), 0))
        rings.append([bm.verts.new(c + out * tube * math.cos(2 * math.pi * j / ts) + Vector((0, 0, tube * math.sin(2 * math.pi * j / ts)))) for j in range(ts)])
    cnt = len(rings)
    for i in range(cnt if arc >= 360 else cnt - 1):
        a, b = rings[i], rings[(i + 1) % cnt]
        for j in range(ts): bm.faces.new((a[j], a[(j + 1) % ts], b[(j + 1) % ts], b[j]))
    return _finish(bm, name, loc, rot, mat, parent)


def _finish(bm, name, loc, rot, mat, parent):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    ob = bpy.data.objects.new(name, me); ob.location = loc; ob.rotation_euler = Euler([D(a) for a in rot])
    if mat is not None: me.materials.append(mat)
    return _link(ob, parent)


def text(name, body, size=0.5, loc=(0, 0, 0), rot=(90, 0, 0), mat=None, extrude=0.0, bevel=0.0, align="CENTER", parent=None):
    """3D letters: a neon sign (emit material + bevel), a number plate, the words on a poster. Stands up facing -Y by default."""
    cu = bpy.data.curves.new(name, "FONT"); cu.body = body; cu.size = size; cu.align_x = align; cu.align_y = "CENTER"
    cu.extrude = extrude; cu.bevel_depth = bevel; cu.bevel_resolution = 3
    ob = bpy.data.objects.new(name, cu); ob.location = loc; ob.rotation_euler = Euler([D(a) for a in rot])
    if mat is not None: cu.materials.append(mat)
    return _link(ob, parent)


def paper(name, lines, size=(0.8, 1.1), loc=(0, 0, 0), rot=(90, 0, 0), paper_col="#D8CDB4", ink="#1A1410", accent="#A01818"):
    """A readable prop: poster, bill, note, card. lines = [("WANTED", 0.16), ("$10.000", 0.12, True), ...] (text, height, accent?).
    Stakes belong on a prop the camera can push in on, not in a caption."""
    root = empty(name, loc); root.rotation_euler = Euler([D(a) for a in rot])
    box(name + "_sheet", (size[0], size[1], 0.006), (0, 0, 0), flat(paper_col, 0.8, name=name + "_paper"), bevel=0.002, parent=root)
    mi, ma = flat(ink, 0.7, name=name + "_ink"), flat(accent, 0.7, name=name + "_accent")
    y = size[1] / 2 - 0.12 * size[1]
    for ln in lines:
        t, hgt = ln[0], ln[1]
        text(name + "_t", t, hgt, (0, y - hgt / 2, 0.005), (0, 0, 0), ma if len(ln) > 2 and ln[2] else mi, parent=root)
        y -= hgt * 1.45
    return root


def room(w=24, d=24, h=10, floor=None, wall=None, ceiling=None, name="Room"):
    """A closed box to shoot inside (interior faces only matter). Centre of the floor at the origin."""
    root = empty(name); t = 0.4
    box(name + "_floor", (w, d, t), (0, 0, -t / 2), floor or wood(planks=0.9), bevel=0, parent=root)
    box(name + "_ceil", (w, d, t), (0, 0, h + t / 2), ceiling or flat("#14100C", 0.9), bevel=0, parent=root)
    wm = wall or brick()
    box(name + "_back", (w, t, h), (0, d / 2 + t / 2, h / 2), wm, bevel=0, parent=root)
    box(name + "_front", (w, t, h), (0, -d / 2 - t / 2, h / 2), wm, bevel=0, parent=root)
    box(name + "_left", (t, d, h), (-w / 2 - t / 2, 0, h / 2), wm, bevel=0, parent=root)
    box(name + "_right", (t, d, h), (w / 2 + t / 2, 0, h / 2), wm, bevel=0, parent=root)
    return root


def round_table(name="Table", radius=3.2, height=2.3, top=None, loc=(0, 0, 0)):
    root = empty(name, loc); m = top or wood("#3A1C0C", "#8A4E22", gloss=0.22)
    cyl(name + "_top", radius, 0.22, (0, 0, height - 0.11), m, bevel=0.05, verts=64, parent=root)
    cyl(name + "_stem", 0.3, height - 0.3, (0, 0, (height - 0.3) / 2), flat("#1A120C", 0.5), parent=root)
    cyl(name + "_foot", 1.3, 0.15, (0, 0, 0.075), flat("#1A120C", 0.5), parent=root)
    return root


def chair(name="Chair", loc=(0, 0, 0), yaw=0.0, seat=1.5, mat=None):
    """A plain wooden chair. Its back also makes a good out-of-focus foreground."""
    root = empty(name, loc); root.rotation_euler.z = D(yaw); m = mat or wood("#24120A", "#5A341A")
    box(name + "_seat", (1.6, 1.6, 0.14), (0, 0, seat), m, 0.04, parent=root)
    for x in (-0.7, 0.7):
        for y in (-0.7, 0.7): box(name + "_leg", (0.14, 0.14, seat), (x, y, seat / 2), m, 0.03, parent=root)
        box(name + "_post", (0.14, 0.14, 2.0), (x, 0.7, seat + 1.0), m, 0.03, parent=root)
    for z in (0.7, 1.25, 1.8): box(name + "_slat", (1.5, 0.08, 0.26), (0, 0.7, seat + z), m, 0.03, parent=root)
    return root


# ---------------------------------------------------------------------------------------------------------- lights
def aim(ob, target):
    """Point an object's -Z at a world position (lights, cameras)."""
    t = Cam._pos(target)
    ob.rotation_euler = (t - Vector(ob.location)).to_track_quat("-Z", "Y").to_euler(); return ob


def light(name, kind, loc, power, color=2700, target=None, size=1.0, spot=60.0, blend=0.3, parent=None):
    """kind: 'SPOT' | 'AREA' | 'POINT' | 'SUN'. color = kelvin or '#hex'. size = soft source size in studs (bigger = softer)."""
    L = bpy.data.lights.new(name, kind); L.energy = power
    L.color = kelvin(color) if isinstance(color, (int, float)) else col(color)[:3]
    if kind == "AREA": L.size = size
    elif kind == "SUN": L.angle = D(size)
    else: L.shadow_soft_size = size
    if kind == "SPOT": L.spot_size = D(spot); L.spot_blend = blend
    ob = bpy.data.objects.new(name, L); ob.location = loc; _link(ob, parent)
    ob.visible_camera = False                                   # a light lights; it is never seen (Cycles draws area lights as white cards)
    if kind == "AREA": ob.visible_glossy = False
    if target is not None: aim(ob, target)
    return ob


def pendant(name, loc, power=900, color=2700, spot=95, shade="#0C0C0C"):
    """A hanging lamp you can see: shade, glowing bulb and the spot that does the lighting. The key light of an interior."""
    root = empty(name, loc)
    cyl(name + "_shade", 0.15, 0.55, (0, 0, 0.3), flat(shade, 0.35, 1.0, name=name + "_shade"), bevel=0, radius2=0.75, parent=root)
    cyl(name + "_cord", 0.02, 6, (0, 0, 3.6), flat("#050505", 0.6), bevel=0, verts=8, parent=root)
    b = cyl(name + "_bulb", 0.22, 0.08, (0, 0, 0.08), emit(color, 60, name=name + "_bulb"), bevel=0, parent=root)
    b.visible_shadow = False
    light(name + "_spot", "SPOT", (0, 0, 0.02), power, color, size=0.25, spot=spot, blend=0.45, parent=root)
    return root


def neon(name, loc, radius=1.4, color="#FFB020", strength=14, arc=300, rot=(90, 0, 0), tube=0.07, fill=0.35):
    """A neon ring/arc on a wall plus a weak area light of the same colour so it actually tints what is near it.
    For neon words use text(..., bevel=0.03, mat=emit(color, strength))."""
    root = empty(name, loc); root.rotation_euler = Euler([D(a) for a in rot])
    torus(name + "_tube", radius, tube, (0, 0, 0), emit(color, strength, name=name + "_glow"), arc=arc, parent=root)
    if fill > 0:
        l = light(name + "_fill", "AREA", (0, 0, 0.3), 60 * fill * strength, color, size=radius * 1.6, parent=root)
        l.rotation_euler = Euler((math.pi, 0, 0))
    return root


def bokeh_lights(name, bounds, n=18, colors=(2400, 2900, "#FF4070", "#40C0FF"), size=(0.05, 0.14), strength=40):
    """Small glowing points far behind the subject (bottles, fairy lights, a city). They exist to become bokeh."""
    root = empty(name); (x0, y0, z0), (x1, y1, z1) = bounds
    for i in range(n):
        r = _rng.uniform(*size); c = _rng.choice(colors)
        o = cyl(f"{name}_{i}", r, r, (_rng.uniform(x0, x1), _rng.uniform(y0, y1), _rng.uniform(z0, z1)),
                emit(c, strength * _rng.uniform(0.4, 1.3), name=f"{name}_m{i}"), bevel=0, verts=12, rot=(90, 0, 0), parent=root)
        o.visible_shadow = False
    return root


def haze(size=(30, 30, 12), loc=(0, 0, 6), density=0.012, anisotropy=0.55, color=(1, 1, 1)):
    """Air you can see: light cones, shafts, glow round lamps. 0.006 thin, 0.012 bar, 0.03 smoke-filled. Costs render time."""
    ob = box("Haze", size, loc, None, bevel=0); m = bpy.data.materials.new("Haze"); m.use_nodes = True; nt = m.node_tree
    for n in list(nt.nodes):
        if n.type != "OUTPUT_MATERIAL": nt.nodes.remove(n)
    out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
    v = nt.nodes.new("ShaderNodeVolumeScatter"); v.inputs["Density"].default_value = density
    v.inputs["Anisotropy"].default_value = anisotropy; v.inputs["Color"].default_value = (*color, 1)
    nt.links.new(v.outputs[0], out.inputs["Volume"]); ob.data.materials.append(m)
    ob.display_type = "WIRE"; ob.visible_shadow = False
    return ob


# ------------------------------------------------------------------------------------------------------- animation
def fcurves(idb):
    """All F-curves of an ID (Blender 5 layered actions)."""
    ad = getattr(idb, "animation_data", None)
    if not ad or not ad.action: return []
    out = []
    for layer in ad.action.layers:
        for strip in layer.strips:
            for cb in strip.channelbags: out.extend(cb.fcurves)
    return out


def key(ob, path, frame, value, interp="BEZIER", index=-1):
    """Key ob.path at frame. interp: BEZIER (ease), LINEAR, CONSTANT (a swap or a cut-safe jump)."""
    if index >= 0:
        v = list(getattr(ob, path)); v[index] = value; setattr(ob, path, v)
    else: setattr(ob, path, value)
    ob.keyframe_insert(path, frame=frame, index=index)
    for fc in fcurves(ob):
        if fc.data_path == path and (index < 0 or fc.array_index == index):
            for kp in fc.keyframe_points:
                if abs(kp.co.x - frame) < 0.01: kp.interpolation = interp
    return ob


def value_at(ob, path, frame):
    cur = list(getattr(ob, path))
    for fc in fcurves(ob):
        if fc.data_path == path: cur[fc.array_index] = fc.evaluate(frame)
    return cur


def move(ob, path, f0, f1, value, ease="BEZIER"):
    """Hold whatever ob.path is until f0, arrive at value on f1. The building block of pose-to-pose with holds."""
    key(ob, path, f0, value_at(ob, path, f0), ease); key(ob, path, f1, value, ease); return ob


def visible(ob, ranges):
    """Render-visible only in these frame ranges [(f0, f1), ...]. Only the hide_render curve is made constant: setting every curve
    of the object to CONSTANT (an easy mistake) turns its motion into steps."""
    ob.hide_render = True; ob.keyframe_insert("hide_render", frame=0)
    for f0, f1 in sorted(ranges):
        ob.hide_render = False; ob.keyframe_insert("hide_render", frame=f0)
        ob.hide_render = True; ob.keyframe_insert("hide_render", frame=f1 + 1)
    for fc in fcurves(ob):
        if fc.data_path == "hide_render":
            for kp in fc.keyframe_points: kp.interpolation = "CONSTANT"
    return ob


def drift(ob, paths=("rotation_euler",), amount=0.02, period=40):
    """A moving hold: slow noise on top of the keys, so nothing is ever frozen."""
    for fc in fcurves(ob):
        if fc.data_path in paths and not any(m.type == "NOISE" for m in fc.modifiers):
            m = fc.modifiers.new("NOISE"); m.strength = amount * 2; m.scale = period; m.phase = _rng.uniform(0, 1000); m.depth = 1


# ------------------------------------------------------------------------------------------------------- face atlas
EXPRESSIONS = ("neutral", "smirk", "grin", "angry", "shout", "shock", "sad", "shut", "talk_a", "talk_o", "talk_m", "side")


def _face_atlas(path, px=256):
    """Draws the expression atlas (one row, RGBA) with numpy. Original drawings: two eyes, brows, a mouth."""
    import numpy as np
    n = len(EXPRESSIONS); img = np.zeros((px, px * n, 4), np.float32)
    yy, xx = np.mgrid[0:px, 0:px].astype(np.float32) / px            # y up after flip below

    def put(tile, mask, rgb):
        a = np.clip(mask, 0, 1)
        for c in range(3): tile[..., c] = tile[..., c] * (1 - a) + rgb[c] * a
        tile[..., 3] = np.maximum(tile[..., 3], a)

    def ell(cx, cy, rx, ry): return np.clip((1 - np.sqrt(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2)) * px * min(rx, ry), 0, 1)

    def stroke(pts, w):
        m = np.zeros((px, px), np.float32)
        for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
            dx, dy = x1 - x0, y1 - y0; L = dx * dx + dy * dy + 1e-9
            t = np.clip(((xx - x0) * dx + (yy - y0) * dy) / L, 0, 1)
            d = np.sqrt((xx - x0 - t * dx) ** 2 + (yy - y0 - t * dy) ** 2)
            m = np.maximum(m, np.clip((w - d) * px, 0, 1))
        return m

    def curve(x0, x1, y, bend, k=14): return [(x0 + (x1 - x0) * i / k, y + bend * 4 * (i / k) * (1 - i / k)) for i in range(k + 1)]
    ink, white = (0.02, 0.02, 0.025), (0.95, 0.95, 0.93)
    for i, ex in enumerate(EXPRESSIONS):
        t = np.zeros((px, px, 4), np.float32); ey = 0.60; look = 0.035 if ex == "side" else 0.0
        for sx in (-1, 1):
            cx = 0.5 + sx * 0.17
            if ex == "shut" or ex == "grin": put(t, stroke(curve(cx - 0.07, cx + 0.07, ey, 0.03 if ex == "grin" else -0.02), 0.014), ink)
            elif ex == "shock":
                put(t, ell(cx, ey, 0.075, 0.10), white); put(t, ell(cx, ey, 0.028, 0.035), ink)
                put(t, stroke([(cx - 0.075, ey), (cx - 0.05, ey + 0.085), (cx + 0.05, ey + 0.085), (cx + 0.075, ey)], 0.008), ink)
            else:
                sq = 0.6 if ex in ("angry", "smirk", "side") else 1.0
                put(t, ell(cx + look, ey, 0.042, 0.085 * sq), ink)
                put(t, ell(cx + look + 0.012, ey + 0.03 * sq, 0.012, 0.02 * sq), white)
            b = {"angry": -0.07, "shout": -0.06, "sad": 0.06, "shock": 0.0, "smirk": -0.02 if sx > 0 else 0.03, "side": -0.02}.get(ex)
            if b is not None:
                by = ey + (0.17 if ex == "shock" else 0.125) + (0.03 if ex == "smirk" and sx < 0 else 0)
                put(t, stroke([(cx - sx * 0.08, by + b * 0.5), (cx + sx * 0.08, by - b * 0.5)], 0.017), ink)
        my = 0.30
        if ex in ("neutral", "side", "talk_m"): put(t, stroke(curve(0.40, 0.60, my, 0.0 if ex == "talk_m" else 0.012), 0.013), ink)
        elif ex == "smirk": put(t, stroke(curve(0.38, 0.66, my, -0.03) + [(0.68, my + 0.03)], 0.013), ink)
        elif ex == "grin":
            put(t, ell(0.5, my + 0.02, 0.15, 0.085) * (yy < my + 0.03), ink); put(t, ell(0.5, my + 0.02, 0.13, 0.03) * (yy < my + 0.03), white)
        elif ex == "angry": put(t, stroke(curve(0.39, 0.61, my - 0.01, 0.035), 0.014), ink)
        elif ex == "sad": put(t, stroke(curve(0.40, 0.60, my - 0.015, 0.03), 0.013), ink)
        elif ex in ("shout", "shock", "talk_a", "talk_o"):
            rx, ry = {"shout": (0.12, 0.10), "shock": (0.06, 0.08), "talk_a": (0.085, 0.05), "talk_o": (0.045, 0.055)}[ex]
            put(t, ell(0.5, my, rx, ry), ink)
            if ex in ("shout", "talk_a"): put(t, ell(0.5, my, rx * 0.85, ry * 0.8) * (yy > my + ry * 0.35), white)
            if ex == "shout": put(t, ell(0.5, my - ry * 0.55, rx * 0.55, ry * 0.4), (0.55, 0.12, 0.12))
        elif ex == "shut": put(t, stroke(curve(0.42, 0.58, my, 0.0), 0.013), ink)
        img[:, i * px:(i + 1) * px] = t
    im = bpy.data.images.new("face_atlas", px * n, px, alpha=True); im.pixels.foreach_set(img.ravel())
    im.filepath_raw = path; im.file_format = "PNG"; im.save(); im.pack()
    return im


_ATLAS = None


def _head_material(skin, name, size):
    """Skin plastic with the face atlas projected on the -Y side of the head. The 'expr' Value node picks the column."""
    global _ATLAS
    if _ATLAS is None: _ATLAS = _face_atlas(os.path.join(bpy.app.tempdir, "cine_face_atlas.png"))
    m = plastic(skin, name=name); nt = m.node_tree; b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Object"], sep.inputs[0])
    val = nt.nodes.new("ShaderNodeValue"); val.name = val.label = "expr"; val.outputs[0].default_value = 0
    n = len(EXPRESSIONS)

    def m2(op, a, bb):
        x = nt.nodes.new("ShaderNodeMath"); x.operation = op
        for i, s in enumerate((a, bb)):
            if hasattr(s, "is_linked"): nt.links.new(s, x.inputs[i])
            else: x.inputs[i].default_value = s
        return x.outputs[0]
    u = m2("ADD", m2("DIVIDE", sep.outputs["X"], size[0] * 0.84), 0.5)                 # the face covers 84 % of the head's width
    v = m2("ADD", m2("DIVIDE", m2("ADD", sep.outputs["Z"], 0.03), size[2] * 0.84), 0.5)
    inside = m2("MULTIPLY", m2("GREATER_THAN", u, 0.0), m2("LESS_THAN", u, 1.0))
    ua = m2("DIVIDE", m2("ADD", u, val.outputs[0]), float(n))
    comb = nt.nodes.new("ShaderNodeCombineXYZ"); nt.links.new(ua, comb.inputs[0]); nt.links.new(v, comb.inputs[1])
    tex = nt.nodes.new("ShaderNodeTexImage"); tex.image = _ATLAS; tex.extension = "CLIP"; nt.links.new(comb.outputs[0], tex.inputs[0])
    nsep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Normal"], nsep.inputs[0])
    front = m2("GREATER_THAN", m2("MULTIPLY", nsep.outputs["Y"], -1.0), 0.25)
    fac = m2("MULTIPLY", m2("MULTIPLY", tex.outputs["Alpha"], front), inside)
    mix = nt.nodes.new("ShaderNodeMixRGB"); mix.inputs[1].default_value = b.inputs["Base Color"].default_value
    nt.links.new(fac, mix.inputs[0]); nt.links.new(tex.outputs["Color"], mix.inputs[2]); nt.links.new(mix.outputs[0], b.inputs["Base Color"])
    ks = nt.nodes.new("ShaderNodeMath"); ks.operation = "SUBTRACT"; ks.inputs[0].default_value = b.inputs["Subsurface Weight"].default_value
    nt.links.new(fac, ks.inputs[1]); ks.use_clamp = True; nt.links.new(ks.outputs[0], b.inputs["Subsurface Weight"])     # ink does not glow
    return m, val


# ------------------------------------------------------------------------------------------------------- character
class Char:
    """A blocky toy figure: rigid parts on joints, a drawn face that swaps. Stands on z=0 at `at`, faces -Y (yaw turns it).

    Pose channels (degrees): arm_l / arm_r = (forward, out, twist), leg_l / leg_r = forward, head = (nod down, turn, tilt),
    torso = (lean forward, turn, tilt), at = (x, y, z), yaw. Turn: + = toward its own left. Its left arm is on world +X at yaw 0.
    """
    HEAD = (1.3, 1.3, 1.2)

    def __init__(self, name, skin="#F2C230", shirt="#1B1B1F", pants="#22252B", hat=None, hat_color="#3A3A3A", hair_color="#5A3A1A",
                 shirt_kind="weave", at=(0, 0, 0), yaw=0.0):
        self.name = name; self.root = empty(name, at); self.root.rotation_euler.z = D(yaw)
        ms, mp_ = cloth(shirt, shirt_kind, name + "_shirt"), cloth(pants, "weave", name + "_pants"); sk = plastic(skin, name=name + "_skin")
        J = self.j = {}
        J["waist"] = empty(name + "_waist", (0, 0, 2.0), self.root)
        box(name + "_torso", (2.0, 1.0, 2.0), (0, 0, 1.0), ms, 0.12, parent=J["waist"])
        J["head"] = empty(name + "_neck", (0, 0, 2.0), J["waist"])
        hm, self._expr = _head_material(skin, name + "_head", self.HEAD)
        self.head = box(name + "_head", self.HEAD, (0, 0, self.HEAD[2] / 2), hm, 0.34, 6, parent=J["head"])
        cyl(name + "_neckpin", 0.3, 0.2, (0, 0, 0.0), sk, 0.02, parent=J["head"])
        for side, sx in (("l", 1), ("r", -1)):
            a = J["arm_" + side] = empty(f"{name}_shoulder_{side}", (sx * 1.5, 0, 1.75), J["waist"])
            box(f"{name}_sleeve_{side}", (1.0, 1.0, 1.25), (0, 0, -0.375), ms, 0.14, parent=a)
            box(f"{name}_hand_{side}", (0.96, 0.96, 0.85), (0, 0, -1.32), sk, 0.2, 5, parent=a)
            g = J["leg_" + side] = empty(f"{name}_hip_{side}", (sx * 0.5, 0, 2.0), self.root)
            box(f"{name}_leg_{side}", (0.98, 0.98, 2.0), (0, 0, -1.0), mp_, 0.12, parent=g)
        if hat: self._hat(hat, hat_color, hair_color)
        self.mats = dict(shirt=ms, pants=mp_, skin=sk, head=hm)

    def _hat(self, kind, hc, hair):
        n, top, P = self.name, self.HEAD[2], self.j["head"]
        if kind == "hair":
            m = cloth(hair, "knit", n + "_hair")
            box(n + "_hair", (1.42, 1.42, 0.62), (0, 0.03, top - 0.1), m, 0.26, 5, parent=P)
            box(n + "_hairback", (1.42, 0.5, 0.9), (0, 0.5, top - 0.55), m, 0.2, 4, parent=P)
            for i, (x, z, ry, w) in enumerate(((-0.42, 0.12, -14, 0.5), (0.0, 0.2, 6, 0.56), (0.42, 0.1, 18, 0.5))):   # tufts break the helmet shape
                box(f"{n}_tuft{i}", (w, 0.62, 0.34), (x, -0.42, top + z), m, 0.15, 4, rot=(-18, ry, 0), parent=P)
        elif kind == "cap":
            m = cloth(hc, "weave", n + "_cap")
            cyl(n + "_cap", 0.74, 0.42, (0, 0.02, top + 0.12), m, 0.16, parent=P)
            cyl(n + "_brim", 0.6, 0.07, (0, -0.55, top - 0.02), m, 0.03, rot=(8, 0, 0), parent=P)
        elif kind == "fedora":
            m = cloth(hc, "weave", n + "_hat")
            cyl(n + "_crown", 0.66, 0.62, (0, 0, top + 0.28), m, 0.18, radius2=0.58, parent=P)
            cyl(n + "_brim", 1.12, 0.07, (0, 0, top + 0.0), m, 0.03, parent=P)
            cyl(n + "_band", 0.68, 0.14, (0, 0, top + 0.1), flat("#0A0A0A", 0.5), 0.0, parent=P)
        elif kind == "beanie":
            m = cloth(hc, "knit", n + "_beanie")
            box(n + "_beanie", (1.4, 1.4, 0.75), (0, 0, top - 0.12), m, 0.34, 6, parent=P)
            cyl(n + "_cuff", 0.74, 0.26, (0, 0, top - 0.4), m, 0.06, parent=P)

    # --- posing ---
    def pose(self, frame, ease="BEZIER", **ch):
        """Key the given channels at `frame`. Only what you pass is keyed."""
        for k, v in ch.items():
            if k == "at": key(self.root, "location", frame, tuple(v), ease)
            elif k == "yaw": key(self.root, "rotation_euler", frame, D(v), ease, index=2)
            elif k in ("arm_l", "arm_r"):
                sx = 1 if k.endswith("l") else -1; f, o, t = v
                key(self.j[k], "rotation_euler", frame, (D(-f), D(-o * sx), D(t * sx)), ease)
            elif k in ("leg_l", "leg_r"): key(self.j[k], "rotation_euler", frame, (D(-v), 0, 0), ease)
            elif k == "head": key(self.j["head"], "rotation_euler", frame, (D(v[0]), D(v[2]), D(v[1])), ease)
            elif k == "torso": key(self.j["waist"], "rotation_euler", frame, (D(v[0]), D(v[2]), D(v[1])), ease)
            else: raise KeyError(k)
        return self

    def hit(self, frame, dur=3, **ch):
        """A snap: hold the current pose until `frame - dur`, arrive on `frame` (2-4 frames, a blur on screen), then hold.
        This is how the reference films animate: fast move, long hold."""
        for k, v in ch.items():
            ob, path = (self.root, "location") if k == "at" else (self.root, "rotation_euler") if k == "yaw" else \
                (self.j["head" if k == "head" else "waist" if k == "torso" else k], "rotation_euler")
            ob.rotation_euler = value_at(ob, "rotation_euler", frame - dur); ob.location = value_at(ob, "location", frame - dur)
            ob.keyframe_insert(path, frame=frame - dur)
        return self.pose(frame, **ch)

    def face(self, frame, expr):
        """Swap the drawn face on this exact frame (never a morph). Swap on the hit, hold, swap back."""
        s = self._expr.outputs[0]; s.default_value = EXPRESSIONS.index(expr); s.keyframe_insert("default_value", frame=frame)
        for fc in fcurves(self.mats["head"].node_tree):
            for kp in fc.keyframe_points: kp.interpolation = "CONSTANT"
        return self

    def talk(self, f0, f1, step=6, shapes=("talk_a", "talk_m", "talk_o", "talk_a", "talk_m"), rest="neutral"):
        """Limited-animation speech: a mouth swap every `step` frames between f0 and f1, back to `rest` after.
        For word-accurate lip sync use the face rig in ~/Ngonten/Maxxing/Roblox/blender/face instead."""
        i = 0
        for f in range(int(f0), int(f1), step):
            self.face(f, shapes[i % len(shapes)]); i += 1
        return self.face(int(f1), rest)

    def sit(self, frame, seat=1.5, ease="BEZIER"):
        """Sit on a seat of that height: thighs forward, hips on the seat."""
        x, y, _ = value_at(self.root, "location", frame)
        return self.pose(frame, ease, at=(x, y, seat + 0.07 - 2.0 + 0.49), leg_l=88, leg_r=88)

    def walk(self, f0, f1, a, b, stride=14, swing=32):
        """Walk from a to b (x, y) between f0 and f1, limbs swinging. stride = frames per step."""
        a, b = Vector((*a, 0)), Vector((*b, 0))
        yaw = math.degrees(math.atan2((b - a).x, -(b - a).y))
        self.pose(f0, "LINEAR", at=a, yaw=yaw); self.pose(f1, "LINEAR", at=b, yaw=yaw)
        f, s = f0, 1
        while f <= f1:
            last = f + stride > f1
            sw = 0 if last else swing * s
            self.pose(f, leg_l=sw, leg_r=-sw, arm_l=(-sw * 0.8, 4, 0), arm_r=(sw * 0.8, 4, 0)); f += stride; s = -s
        return self

    def life(self, amount=1.0):
        """Moving holds on every joint so held poses breathe. Call after all pose keys exist."""
        for k, ob in self.j.items(): drift(ob, amount=0.012 * amount, period=_rng.uniform(30, 55))
        return self


# ---------------------------------------------------------------------------------------------- the user's avatar
AVATAR_BLEND = os.path.expanduser("~/Ngonten/Maxxing/Roblox/blender/hero_face.blend")
AVATAR_POSES = {  # degrees per bone; the model is modelled arms-out, so "arms down" is +-78 on the arm's Y
    "stand": {"arm.L": (0, 78, 0), "arm.R": (0, -78, 0), "fore.L": (0, 0, -8), "fore.R": (0, 0, 8)},
    "relax": {"arm.L": (6, 72, 0), "arm.R": (-6, -72, 0), "fore.L": (0, 0, -18), "fore.R": (0, 0, 18), "spine": (2, 0, 0)},
    "table": {"arm.L": (-52, 70, 0), "arm.R": (-52, -70, 0), "fore.L": (0, 0, -46), "fore.R": (0, 0, 46), "spine": (7, 0, 0), "head": (6, 0, 0)},
    "reach": {"arm.L": (0, 78, 0), "arm.R": (-74, -72, 4), "fore.L": (0, 0, -22), "fore.R": (0, 0, 14), "head": (10, 0, 0), "spine": (10, 0, -6)},
    "chin": {"arm.L": (0, 78, 0), "arm.R": (-40, -70, -10), "fore.L": (0, 0, -10), "fore.R": (0, 0, 118), "head": (-4, -9, 12)},
    "hips": {"arm.L": (0, 58, 0), "arm.R": (0, -58, 0), "fore.L": (0, 0, -100), "fore.R": (0, 0, 100)},
    "sit": {"thigh.L": (-88, 0, 0), "thigh.R": (-88, 0, 0), "shin.L": (88, 0, 0), "shin.R": (88, 0, 0)},
}
AVATAR_BONES = ("spine", "head", "arm.L", "fore.L", "arm.R", "fore.R", "thigh.L", "shin.L", "thigh.R", "shin.R")


class Avatar:
    """Aksa's own Roblox avatar (the rigged model in Roblox/blender/hero_face.blend) inside a cine_kit scene: same height as a
    Char (5.2 studs), stands on z = 0, faces -Y. It keeps its own texture, outfit and painted face rig.

    av.pose(frame, "table", head=(4, 0, 30))   named pose and/or bones (arm_L, fore_R, head, spine, thigh_L, shin_R; degrees)
    av.hit(frame, 3, head=(0, 0, -40))         snap and hold, like Char.hit
    av.face.expr(f, eyes="happy", brows="one_up", mouth="smile"); av.face.blink(f); av.face.dart(f, "look_l")
    av.face.lipsync(words, vo_frame, fps=24)   word-accurate Indonesian lip sync
    av.finish(f0, f1)                          REQUIRED once at the end: bakes the face (constant keys)
    Head: (nod down, tilt, turn) with turn + = toward his own left. av.head is an empty at the head for Cam target / focus.
    """
    HEIGHT = 5.2

    def __init__(self, at=(0, 0, 0), yaw=0.0, pose="stand", name="Aksa", glow=0.12):
        if not os.path.exists(AVATAR_BLEND): raise FileNotFoundError(AVATAR_BLEND)
        with bpy.data.libraries.load(AVATAR_BLEND, link=False) as (src, dst): dst.objects = [n for n in src.objects if n in ("hero", "hero_mesh")]
        for o in dst.objects: _link(o)
        self.ob = bpy.data.objects["hero"]; self.mesh = bpy.data.objects["hero_mesh"]
        bpy.context.view_layer.update()
        s = self.HEIGHT / max(self.mesh.dimensions.z, 1e-6); self.scale = s
        self.root = empty(name, at); self.root.rotation_euler.z = D(yaw)
        self.ob.parent = self.root; self.ob.scale = (s, s, s); self.ob.location = (0, 0, 0)
        m = self.mesh.active_material; nt = m.node_tree; b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
        lk = b.inputs["Base Color"].links[0]; g = nt.nodes.new("ShaderNodeGamma"); g.inputs[1].default_value = 0.72   # same lift the reels use
        src_s = lk.from_socket; nt.links.remove(lk); nt.links.new(src_s, g.inputs[0]); nt.links.new(g.outputs[0], b.inputs["Base Color"])
        _set(b, Roughness=0.42, Subsurface_Weight=glow, Subsurface_Scale=0.1, Coat_Weight=0.2, Coat_Roughness=0.2)   # toy plastic, like the cast
        self.head = empty(name + "_head", (0, 0, 0)); self.head.parent = self.ob; self.head.parent_type = "BONE"; self.head.parent_bone = "head"
        self.head.location = (0, -0.06, 0.16)                       # bone space: the middle of the head
        self._face = None
        self.pose(1, pose)

    @property
    def face(self):
        """The painted face rig (eyes, brows, mouth atlases). Loaded on first use."""
        if self._face is None:
            d = os.path.dirname(AVATAR_BLEND)
            for p in (d, os.path.join(d, "face")):
                if p not in sys.path: sys.path.insert(0, p)
            import face_rig as FR
            self._face = FR.Face()
        return self._face

    def _bone(self, k): return self.ob.pose.bones[k.replace("_", ".")]

    def pose(self, frame, name=None, ease="BEZIER", **ch):
        vals = dict(AVATAR_POSES.get(name, {})) if name else {}
        if name and name not in AVATAR_POSES: raise KeyError(name)
        for k, v in ch.items():
            if k == "at": key(self.root, "location", frame, tuple(v), ease)
            elif k == "yaw": key(self.root, "rotation_euler", frame, D(v), ease, index=2)
            else: vals[k.replace("_", ".")] = v
        for k, v in vals.items():
            pb = self._bone(k); pb.rotation_euler = [D(x) for x in v]; pb.keyframe_insert("rotation_euler", frame=frame)
            path = pb.path_from_id("rotation_euler")
            for fc in fcurves(self.ob):
                if fc.data_path == path:
                    for kp in fc.keyframe_points:
                        if abs(kp.co.x - frame) < 0.01: kp.interpolation = ease
        return self

    def hit(self, frame, dur=3, name=None, **ch):
        """Hold the current pose until frame - dur, arrive on frame."""
        bones = set(AVATAR_POSES.get(name, {})) | {k.replace("_", ".") for k in ch if k not in ("at", "yaw")}
        for k in bones:
            pb = self._bone(k); path = pb.path_from_id("rotation_euler"); cur = list(pb.rotation_euler)
            for fc in fcurves(self.ob):
                if fc.data_path == path: cur[fc.array_index] = fc.evaluate(frame - dur)
            pb.rotation_euler = cur; pb.keyframe_insert("rotation_euler", frame=frame - dur)
        for k in ("at", "yaw"):
            if k in ch:
                self.root.location = value_at(self.root, "location", frame - dur); self.root.rotation_euler = value_at(self.root, "rotation_euler", frame - dur)
                self.root.keyframe_insert("location" if k == "at" else "rotation_euler", frame=frame - dur)
        return self.pose(frame, name, **ch)

    def sit(self, frame, seat=1.5):
        """Sit on a seat of that height (thighs forward, shins down)."""
        x, y, _ = value_at(self.root, "location", frame)
        hip = 0.335 * self.scale; thigh = 0.11 * self.scale
        return self.pose(frame, "sit", at=(x, y, seat + 0.07 + thigh - hip))

    def life(self, amount=1.0):
        drift(self.ob, paths=tuple(self._bone(b).path_from_id("rotation_euler") for b in AVATAR_BONES), amount=0.012 * amount, period=_rng.uniform(30, 55))
        return self

    def finish(self, f0=None, f1=None, blinks=True):
        """Bake the face for the frame range (auto blinks unless told otherwise). Call once, after all face calls."""
        sc = bpy.context.scene; f0 = f0 or sc.frame_start; f1 = f1 or sc.frame_end
        if blinks and not self.face.blinks: self.face.auto_blinks(f0, f1)
        self.face.bake(f0, f1); return self


# ------------------------------------------------------------------------------------- characters from a file
CHARACTERS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "characters")
CAST = {"bugis_man": "bugis_man.blend", "bugis_woman": "bugis_woman.blend"}      # rigged with scripts/rig_block.py


class Rigged:
    """A supplied character model (rigged by scripts/rig_block.py) acting in a cine_kit scene. Same height as a Char (5.2 studs),
    stands on z = 0, faces -Y, and takes the SAME pose channels as Char:
      arm_l / arm_r = (forward, out, twist), head = (nod down, turn, tilt), torso = (lean forward, turn, tilt),
      leg_l / leg_r = forward (only if it has legs below a hem), at, yaw.  out = 0 means the arm hangs straight down.
    .hit(), .sit(), .walk(), .life() as on Char; .head is an empty at the head for Cam target / focus.
    Its face is painted in its texture: .face() does nothing (give emotion with the head, the arms and the cut).

      man = K.Rigged("bugis_man", at=(-4.5, 0, 0), yaw=90); woman = K.Rigged("bugis_woman", at=(4.5, 0, 0), yaw=-90)
    """
    HEIGHT = 5.2

    def __init__(self, which, at=(0, 0, 0), yaw=0.0, name=None, glow=0.1, arms_down=True):
        path = which if os.path.isabs(which) else os.path.join(CHARACTERS, CAST.get(which, which))
        if not os.path.exists(path): raise FileNotFoundError(path)
        before = set(bpy.data.objects)
        with bpy.data.libraries.load(path, link=False) as (src, dst): dst.objects = list(src.objects)
        new = [o for o in dst.objects if o is not None and o not in before]
        for o in new: _link(o)
        self.ob = next(o for o in new if o.type == "ARMATURE")
        self.mesh = next(o for o in new if o.type == "MESH" and not o.name.endswith("_mouth"))
        self.mouth = next((o for o in new if o.type == "MESH" and o.name.endswith("_mouth")), None)   # scripts/prep_mouth.py adds it
        self.name = name or self.ob.name; P = self.ob
        self.scale = s = self.HEIGHT / P["height"]; self.rest_out = P["rest_out"]; self.has_legs = bool(P["has_legs"])
        self.root = empty(self.name + "_root", at); self.root.rotation_euler.z = D(yaw)
        P.parent = self.root; P.scale = (s, s, s); P.location = (0, 0, 0)
        for m in self.mesh.data.materials:                                  # a little toy translucency, like the rest of the cast
            b = next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
            if b: _set(b, Subsurface_Weight=glow, Subsurface_Scale=0.1)
        self.head = empty(self.name + "_head"); self.head.parent = P; self.head.parent_type = "BONE"; self.head.parent_bone = "head"
        hm = P["head_mid"]; self.head.location = (hm[0], hm[1] - 0.06, hm[2])       # bone-parented empties sit at the bone's tail (0.06 along Y)
        if arms_down: self.pose(1, arm_l=(0, 4, 0), arm_r=(0, 4, 0))

    _MAP = {"arm_l": "arm.L", "arm_r": "arm.R", "leg_l": "leg.L", "leg_r": "leg.R", "head": "head", "torso": "spine", "lower": "lower"}

    def _rot(self, k, v):
        if k in ("arm_l", "arm_r"):
            sx = 1 if k.endswith("l") else -1; f, o, t = v
            return (D(-f), D(-(o - self.rest_out) * sx), D(t * sx))
        if k in ("leg_l", "leg_r", "lower"): return (D(-v), 0, 0)
        return (D(v[0]), D(v[2]), D(v[1]))                                      # head / torso: (nod, turn, tilt)

    def pose(self, frame, ease="BEZIER", **ch):
        for k, v in ch.items():
            if k == "at": key(self.root, "location", frame, tuple(v), ease); continue
            if k == "yaw": key(self.root, "rotation_euler", frame, D(v), ease, index=2); continue
            if k in ("leg_l", "leg_r") and not self.has_legs: continue          # a long skirt: no separate legs
            pb = self.ob.pose.bones[self._MAP[k]]; pb.rotation_euler = self._rot(k, v); pb.keyframe_insert("rotation_euler", frame=frame)
            path = pb.path_from_id("rotation_euler")
            for fc in fcurves(self.ob):
                if fc.data_path == path:
                    for kp in fc.keyframe_points:
                        if abs(kp.co.x - frame) < 0.01: kp.interpolation = ease
        return self

    def hit(self, frame, dur=3, **ch):
        """A snap: hold the current pose until frame - dur, arrive on frame, then hold."""
        for k in ch:
            if k in ("at", "yaw"):
                self.root.location = value_at(self.root, "location", frame - dur); self.root.rotation_euler = value_at(self.root, "rotation_euler", frame - dur)
                self.root.keyframe_insert("location" if k == "at" else "rotation_euler", frame=frame - dur); continue
            if k in ("leg_l", "leg_r") and not self.has_legs: continue
            pb = self.ob.pose.bones[self._MAP[k]]; path = pb.path_from_id("rotation_euler"); cur = list(pb.rotation_euler)
            for fc in fcurves(self.ob):
                if fc.data_path == path: cur[fc.array_index] = fc.evaluate(frame - dur)
            pb.rotation_euler = cur; pb.keyframe_insert("rotation_euler", frame=frame - dur)
        return self.pose(frame, **ch)

    def face(self, frame, expr):
        return self                                                             # painted face: nothing to swap

    MOUTHS = ("rest", "mbp", "a", "a_mid", "e", "i", "o", "u", "fv", "cons")
    V2M = {"PP": "mbp", "FF": "fv", "TH": "cons", "DD": "cons", "kk": "cons", "CH": "i", "SS": "i", "nn": "cons", "RR": "cons",
           "aa": "a", "E": "e", "ih": "i", "oh": "o", "ou": "u"}

    def sing(self, words, f0, f1, song_frame=1, fps=24, lead=2):
        """Lip sync (singing or speech) on a painted face that has a mouth plate (scripts/prep_mouth.py): words = [{"word", "start",
        "end"}] in seconds of the track, song_frame = scene frame of the track's t=0. Mouth on twos, leads the sound by `lead` frames,
        rests between words. Uses the Aksa Indonesian engine (lipsync_id); Javanese and Malay read close enough."""
        if self.mouth is None: raise RuntimeError("no mouth plate: run scripts/prep_mouth.py on the character first")
        LSD = os.path.expanduser("~/Ngonten/Workflow/Podcast talking-head shot/Aksa_LipSync/scripts")
        if LSD not in sys.path: sys.path.insert(0, LSD)
        import lipsync_id as LS
        t0, t1 = (f0 - song_frame) / fps, (f1 - song_frame) / fps
        ws = [w for w in words if w["end"] > t0 and w["start"] < t1]
        if not ws: return self
        n = f1 - f0 + 1; Wt, _ = LS.curves(ws, n, fps, offset_frames=song_frame - f0 + 1, lead=lead)
        seq = []
        for i in range(n):
            best = max(LS.VISEMES, key=lambda v: Wt[v][i]); w = Wt[best][i]
            st = "rest" if w < 0.2 else self.V2M[best]
            if st == "a" and w < 0.6: st = "a_mid"
            if st == "o" and w < 0.45: st = "u"
            seq.append(st)
        for i in range(1, n - 1, 2):
            if seq[i] != "mbp": seq[i] = seq[i - 1]                            # on twos; a b/p/m closure may stay one frame
        m = self.mouth; last = None
        if not fcurves(m): m["mcell"] = 0.0; m.keyframe_insert('["mcell"]', frame=1)
        for i, st in enumerate(seq):
            if st != last: m["mcell"] = float(self.MOUTHS.index(st)); m.keyframe_insert('["mcell"]', frame=f0 + i); last = st
        m["mcell"] = 0.0; m.keyframe_insert('["mcell"]', frame=f1 + 1)
        for fc in fcurves(m):
            for kp in fc.keyframe_points: kp.interpolation = "CONSTANT"
        return self

    def sit(self, frame, seat=1.5, ease="BEZIER"):
        """Sit: the whole lower body swings forward at the hip (a sarong or skirt stays one block, as on a toy)."""
        x, y, _ = value_at(self.root, "location", frame); P = self.ob
        return self.pose(frame, ease, lower=88, at=(x, y, seat + 0.07 + (P["thick"] / 2 - P["hip"]) * self.scale))

    def walk(self, f0, f1, a, b, stride=14, swing=24):
        """Walk from a to b. With legs: they swing. In a long skirt: a glide with a small sway of the body."""
        a, b = Vector((*a, 0)), Vector((*b, 0)); yaw = math.degrees(math.atan2((b - a).x, -(b - a).y))
        self.pose(f0, "LINEAR", at=a, yaw=yaw); self.pose(f1, "LINEAR", at=b, yaw=yaw)
        f, sg = f0, 1
        while f <= f1:
            sw = 0 if f + stride > f1 else swing * sg
            self.pose(f, leg_l=sw, leg_r=-sw, arm_l=(-sw * 0.7, 4, 0), arm_r=(sw * 0.7, 4, 0), torso=(2, 0, sw * 0.08)); f += stride; sg = -sg
        return self

    def life(self, amount=1.0):
        drift(self.ob, paths=tuple(b.path_from_id("rotation_euler") for b in self.ob.pose.bones), amount=0.012 * amount, period=_rng.uniform(30, 55))
        return self


# ---------------------------------------------------------------------------------------------------------- camera
class Cam:
    """A camera that always looks at its target empty. Move either, key either. lens in mm; stop = f-number as if the
    figure were a 40 cm collectible (2 = dreamy insert, 4 = portrait, 8 = wide master, 16 = everything sharp)."""

    def __init__(self, name, loc, target, lens=50, stop=4.0, focus=None, roll=0.0):
        cd = bpy.data.cameras.new(name); cd.lens = lens; cd.sensor_width = 36; cd.clip_start = 0.05; cd.clip_end = 2000
        self.rig = empty(name + "_rig", loc)                       # the rig is what moves and aims; the camera rides it
        self.ob = _link(bpy.data.objects.new(name, cd), self.rig)
        self.target = empty(name + "_aim", self._pos(target))
        c = self.rig.constraints.new("TRACK_TO"); c.target = self.target; c.track_axis = "TRACK_NEGATIVE_Z"; c.up_axis = "UP_Y"
        cd.dof.use_dof = True; cd.dof.aperture_fstop = stop / TOY; cd.dof.aperture_blades = 0
        self.focus_ob = empty(name + "_focus", self._pos(focus if focus is not None else target)); cd.dof.focus_object = self.focus_ob
        self.ob.rotation_euler = (0, 0, D(roll))                   # roll = dutch angle: once, for the moment things go wrong
        if bpy.context.scene.camera is None: bpy.context.scene.camera = self.ob

    @staticmethod
    def _pos(t):
        if not hasattr(t, "matrix_world"): return Vector(t)
        bpy.context.view_layer.update(); return t.matrix_world.translation.copy()      # world position of an object, now

    def at(self, frame, loc=None, target=None, focus=None, lens=None, stop=None, roll=None, ease="BEZIER"):
        """Key the camera at a frame. Two calls make a move; a slow push-in is 3-8 % closer over the whole shot."""
        if loc is not None: key(self.rig, "location", frame, tuple(loc), ease)
        if target is not None: key(self.target, "location", frame, tuple(self._pos(target)), ease)
        if focus is not None: key(self.focus_ob, "location", frame, tuple(self._pos(focus)), ease)       # rack focus = two of these
        if roll is not None: key(self.ob, "rotation_euler", frame, D(roll), ease, index=2)
        if lens is not None: self.ob.data.lens = lens; self.ob.data.keyframe_insert("lens", frame=frame)
        if stop is not None: self.ob.data.dof.aperture_fstop = stop / TOY; self.ob.data.dof.keyframe_insert("aperture_fstop", frame=frame)
        return self

    def push(self, f0, f1, amount=0.06):
        """Slow push-in toward the target by a fraction of the distance (0.03-0.08 reads as intent, not as a zoom)."""
        a = Vector(value_at(self.rig, "location", f0)); t = Vector(value_at(self.target, "location", f0))
        key(self.rig, "location", f0, tuple(a), "LINEAR"); key(self.rig, "location", f1, tuple(a + (t - a) * amount), "LINEAR"); return self

    @staticmethod
    def distance_for(lens, height):
        """How far from a subject `height` studs tall it must be to fill the frame's height (9:16: sensor on the long side)."""
        return (height / 2) / math.tan(math.atan(18.0 / lens))

    def clip_follow(self, f0, f1, subject, margin=0.45, step=2):
        """Near clip that follows the subject: everything nearer than (distance - margin) is cut away. Dive over a character's head
        into the phone in their hands without the camera passing through the head (it is clipped, not hidden)."""
        for fr in range(f0, f1 + 1, step):
            d = (Vector(value_at(self.rig, "location", fr)) - self._pos(subject)).length
            self.ob.data.clip_start = max(0.05, d - margin); self.ob.data.keyframe_insert("clip_start", frame=fr)
        return self

    def handheld(self, amount=1.0):
        """Operator breathing: noise on the aim point. 0.5 = held on a tripod by a nervous hand, 1 = handheld, 3 = running."""
        for ob, s in ((self.target, 0.035), (self.rig, 0.02)):
            if not fcurves(ob): ob.keyframe_insert("location", frame=1)
            for fc in fcurves(ob):
                if fc.data_path == "location" and not fc.modifiers:
                    m = fc.modifiers.new("NOISE"); m.strength = s * amount * 2; m.scale = _rng.uniform(14, 26); m.phase = _rng.uniform(0, 999); m.depth = 2
        return self


def beats(bpm, fps=24, start=1, lead=0):
    """Returns f(n) -> the frame of beat n (0-based) at this tempo. lead = frames to cut ahead of the beat (0-2)."""
    return lambda n: int(round(start + n * 60.0 / bpm * fps)) - lead


def cut_list(shots, bpm, fps=24, start=1, lead=0):
    """shots = [("name", cam, length_in_beats), ...]. Binds each camera to a timeline marker (one render, real cuts),
    sets the frame range, returns {name: (first_frame, last_frame)}. Shot lengths in whole or half beats: that is the edit."""
    sc = bpy.context.scene; f = beats(bpm, fps, start, lead); n = 0.0; out = {}
    for m in list(sc.timeline_markers): sc.timeline_markers.remove(m)
    for name, cam, length in shots:
        a, b = f(n), f(n + length) - 1
        mk = sc.timeline_markers.new(name, frame=a); mk.camera = cam.ob if isinstance(cam, Cam) else cam
        out[name] = (a, b); n += length
    sc.frame_start = start; sc.frame_end = f(n) - 1
    return out


# ---------------------------------------------------------------------------------------------------------- render
def _cam_at(frame):
    sc = bpy.context.scene; cam = None
    for m in sorted(sc.timeline_markers, key=lambda m: m.frame):
        if m.frame <= frame and m.camera: cam = m.camera
    if cam: sc.camera = cam


def still(path, frame, pct=None):
    """Render one frame to a PNG. Look at it, describe it in one sentence, run scripts/look_gate.py on it."""
    sc = bpy.context.scene; old = sc.render.resolution_percentage
    if pct: sc.render.resolution_percentage = pct
    sc.frame_set(int(frame)); _cam_at(frame); sc.render.filepath = path
    bpy.ops.render.render(write_still=True); sc.render.resolution_percentage = old
    return path


def render_range(out_dir, f0=None, f1=None, step=1):
    """Numbered PNGs, skipping frames that exist (a crash resumes; run 2-3 processes on split ranges)."""
    sc = bpy.context.scene; os.makedirs(out_dir, exist_ok=True)
    for f in range(f0 or sc.frame_start, (f1 or sc.frame_end) + 1, step):
        p = os.path.join(out_dir, f"f_{f:05d}.png"); lock = p + ".lock"
        if os.path.exists(p): continue
        try: os.close(os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY))      # atomic claim: two processes never take one frame
        except FileExistsError: continue
        try:
            still(p + ".part.png", f); os.replace(p + ".part.png", p)           # the frame appears only when it is complete
        finally: os.remove(lock)
