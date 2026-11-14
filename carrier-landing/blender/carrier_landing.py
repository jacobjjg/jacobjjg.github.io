"""Rough previz: a navy fighter traps aboard an aircraft carrier.

Blender 5.x (built and tested on 5.3.0, Cycles on CPU). Run it with bpy as a module or inside Blender:

    python carrier_landing.py --shot all --res 960x540 --samples 16 --out ./renders
    blender -b -P carrier_landing.py -- --shot 3 --frames 181,240 --res 1920x1080 --samples 64

Shots (24 fps):
    1  helicopter chase, 50mm   frames   1-96   jet on the glide slope, carrier ahead
    2  spine-mounted cam, 20mm  frames  97-168  over the canopy, deck rushing up
    3  deck-level, 35mm         frames 169-288  touchdown, hook catches the 3-wire, jet stops

Scale is 1 unit = 1 m. The carrier is static with its bow toward +Y. The angled landing
deck runs 9 degrees to port of the ship's centreline.
"""
import bpy
import bmesh
import math
import os
import random
import sys
import argparse
from mathutils import Vector, Matrix, Euler, Quaternion


# ------------------------------------------------------------------ arguments
def get_args():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else argv[1:]
    p = argparse.ArgumentParser()
    p.add_argument("--out", default=os.path.join(os.getcwd(), "renders"))
    p.add_argument("--res", default="960x540")
    p.add_argument("--samples", type=int, default=16)
    p.add_argument("--shot", default="all", help="1, 2, 3 or all")
    p.add_argument("--frames", default="", help="frame list instead of the shot range: 1-96 or 10,50,90")
    p.add_argument("--save_blend", default="")
    p.add_argument("--no_render", action="store_true")
    p.add_argument("--static_ocean", action="store_true", help="skip wave animation (faster)")
    return p.parse_known_args(argv)[0]


ARGS = get_args()

# ------------------------------------------------------------------ timeline and geometry
FPS = 24
N_FRAMES = 288
SHOTS = {1: (1, 96), 2: (97, 168), 3: (169, 288)}

DECK_Z = 20.0
TH = math.radians(9.0)                                  # angled-deck offset
DIR = Vector((-math.sin(TH), math.cos(TH), 0.0))        # landing direction along the angled deck
PORT = Vector((-math.cos(TH), -math.sin(TH), 0.0))      # unit vector to port of the landing line
RAMP = Vector((-4.0, -165.0, DECK_Z))                   # landing centreline at the stern ramp
GS = math.radians(3.5)                                  # glide slope
V_APP = 65.0                                            # closing speed on the deck, m/s
S_TD, T_TD = 72.0, 7.5                                  # main-gear touchdown: metres past ramp, seconds
WIRES = [55.0, 67.0, 79.0, 91.0]                        # arresting wires, metres past ramp
WIRE_HALF = 15.0
T_ARR = 2.4                                             # arrestment time (constant deceleration)
D_ARR = V_APP * T_ARR / 2.0
ROLLBACK, T_RB = 2.5, 0.9                               # wire pulls the jet back a little

HOOK_PIVOT = Vector((0.0, -5.4, 1.45))                  # jet-local hinge of the tailhook
HOOK_LEN = 2.9
HOOK_NAT = math.radians(52.0)                           # free-hanging hook angle

# Light: low sun behind the approach path (front-lights shots 1-2, back-lights shot 3)
SUN_AZ = Vector((-0.45, -0.89, 0.0)).normalized()
SUN_EL = math.radians(11.0)
SUN_VEC = Vector((SUN_AZ.x * math.cos(SUN_EL), SUN_AZ.y * math.cos(SUN_EL), math.sin(SUN_EL)))
SKY_STRENGTH = 0.30
SUN_STRENGTH = 3.2
EXPOSURE = -0.6
HAZE_DIST = 8000.0
HAZE_MAX = 0.97


def T(f):
    return (f - 1) / FPS


def lp(s, lat=0.0, z=None):
    """Landing-line coordinates (metres past ramp, metres to port) -> world point."""
    p = RAMP + DIR * s + PORT * lat
    if z is not None:
        p.z = z
    return p


def smooth(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3.0 - 2.0 * u)


# ------------------------------------------------------------------ scene reset
bpy.ops.wm.read_factory_settings(use_empty=True)
SC = bpy.context.scene
SC.unit_settings.system = 'METRIC'
SC.render.fps = FPS
SC.frame_start, SC.frame_end = 1, N_FRAMES
bpy.context.preferences.edit.keyframe_new_interpolation_type = 'LINEAR'
ROOT_COL = SC.collection


def new_col(name, parent=ROOT_COL):
    c = bpy.data.collections.new(name)
    if parent is not None:
        parent.children.link(c)
    return c


# ------------------------------------------------------------------ node helpers
def node(nt, kind, **props):
    n = nt.nodes.new(kind)
    for k, v in props.items():
        setattr(n, k, v)
    return n


def link(nt, a, b):
    nt.links.new(a, b)


def feed(nt, sock, val):
    """Connect a socket or set a constant."""
    if isinstance(val, bpy.types.NodeSocket):
        nt.links.new(val, sock)
    else:
        sock.default_value = val


def math_n(nt, op, a, b=None, clamp=False):
    n = node(nt, 'ShaderNodeMath', operation=op, use_clamp=clamp)
    feed(nt, n.inputs[0], a)
    if b is not None:
        feed(nt, n.inputs[1], b)
    return n.outputs[0]


def vmath(nt, op, a, b=None, scale=None):
    n = node(nt, 'ShaderNodeVectorMath', operation=op)
    feed(nt, n.inputs[0], a)
    if b is not None:
        feed(nt, n.inputs[1], b)
    if scale is not None:
        feed(nt, n.inputs['Scale'], scale)
    return n.outputs['Value'] if op in ('DOT_PRODUCT', 'LENGTH', 'DISTANCE') else n.outputs['Vector']


def sep_xyz(nt, v):
    n = node(nt, 'ShaderNodeSeparateXYZ')
    link(nt, v, n.inputs[0])
    return n.outputs['X'], n.outputs['Y'], n.outputs['Z']


def comb_xyz(nt, x, y, z):
    n = node(nt, 'ShaderNodeCombineXYZ')
    feed(nt, n.inputs['X'], x)
    feed(nt, n.inputs['Y'], y)
    feed(nt, n.inputs['Z'], z)
    return n.outputs[0]


def map_range(nt, v, a, b, c=0.0, d=1.0, smoothstep=True):
    n = node(nt, 'ShaderNodeMapRange', interpolation_type='SMOOTHSTEP' if smoothstep else 'LINEAR')
    feed(nt, n.inputs['Value'], v)
    n.inputs['From Min'].default_value = a
    n.inputs['From Max'].default_value = b
    n.inputs['To Min'].default_value = c
    n.inputs['To Max'].default_value = d
    return n.outputs['Result']


def mix_rgb(nt, fac, a, b, blend='MIX'):
    n = node(nt, 'ShaderNodeMix', data_type='RGBA', blend_type=blend)
    fs = next(s for s in n.inputs if s.name == 'Factor' and s.type == 'VALUE')
    sa = next(s for s in n.inputs if s.name == 'A' and s.type == 'RGBA')
    sb = next(s for s in n.inputs if s.name == 'B' and s.type == 'RGBA')
    feed(nt, fs, fac)
    feed(nt, sa, a)
    feed(nt, sb, b)
    return next(s for s in n.outputs if s.type == 'RGBA')


def noise(nt, vec, scale, detail=4.0, rough=0.5):
    n = node(nt, 'ShaderNodeTexNoise')
    if vec is not None:
        link(nt, vec, n.inputs['Vector'])
    n.inputs['Scale'].default_value = scale
    n.inputs['Detail'].default_value = detail
    n.inputs['Roughness'].default_value = rough
    return n.outputs['Fac']


def setup_sky(sky):
    sky.sky_type = 'MULTIPLE_SCATTERING'
    sky.sun_disc = False
    sky.sun_elevation = SUN_EL
    sky.sun_rotation = math.atan2(SUN_AZ.x, SUN_AZ.y)    # probed: 0 = sun toward +Y, 90 deg = toward +X
    sky.altitude = 0.0
    sky.air_density = 1.0
    sky.aerosol_density = 1.4                          # some maritime haze
    sky.ozone_density = 1.0


# ------------------------------------------------------------------ aerial haze (shared by every material)
def make_haze_group():
    ng = bpy.data.node_groups.new("AerialHaze", 'ShaderNodeTree')
    ng.interface.new_socket(name="Shader", in_out='INPUT', socket_type='NodeSocketShader')
    ng.interface.new_socket(name="Shader", in_out='OUTPUT', socket_type='NodeSocketShader')
    gi = node(ng, 'NodeGroupInput')
    go = node(ng, 'NodeGroupOutput')
    cam = node(ng, 'ShaderNodeCameraData')
    e = math_n(ng, 'EXPONENT', math_n(ng, 'MULTIPLY', cam.outputs['View Distance'], -1.0 / HAZE_DIST))
    fac = math_n(ng, 'MULTIPLY', math_n(ng, 'SUBTRACT', 1.0, e), HAZE_MAX)
    geo = node(ng, 'ShaderNodeNewGeometry')
    view = vmath(ng, 'SCALE', geo.outputs['Incoming'], scale=-1.0)
    x, y, z = sep_xyz(ng, view)
    d = vmath(ng, 'NORMALIZE', comb_xyz(ng, x, y, math_n(ng, 'MAXIMUM', z, 0.004)))
    sky = node(ng, 'ShaderNodeTexSky')
    setup_sky(sky)
    link(ng, d, sky.inputs['Vector'])
    em = node(ng, 'ShaderNodeEmission')
    link(ng, sky.outputs['Color'], em.inputs['Color'])
    em.inputs['Strength'].default_value = SKY_STRENGTH
    mix = node(ng, 'ShaderNodeMixShader')
    link(ng, fac, mix.inputs[0])
    link(ng, gi.outputs[0], mix.inputs[1])
    link(ng, em.outputs[0], mix.inputs[2])
    link(ng, mix.outputs[0], go.inputs[0])
    return ng


HAZE = make_haze_group()


def material(name, color, rough=0.5, metal=0.0, emit=None, emit_strength=0.0, haze=True, var=0.0, var_scale=2.0):
    """Principled material with optional noise variation, emission and aerial haze."""
    m = bpy.data.materials.new(name)
    if m.node_tree is None:
        m.use_nodes = True
    nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.bl_idname == 'ShaderNodeBsdfPrincipled')
    out = next(n for n in nt.nodes if n.bl_idname == 'ShaderNodeOutputMaterial')
    col = (*color, 1.0)
    if var > 0:
        tc = node(nt, 'ShaderNodeTexCoord')
        f = noise(nt, tc.outputs['Object'], var_scale, 5.0, 0.6)
        dark = tuple(c * (1.0 - var) for c in color) + (1.0,)
        light = tuple(min(1.0, c * (1.0 + var)) for c in color) + (1.0,)
        link(nt, mix_rgb(nt, f, dark, light), bsdf.inputs['Base Color'])
    else:
        bsdf.inputs['Base Color'].default_value = col
    bsdf.inputs['Roughness'].default_value = rough
    bsdf.inputs['Metallic'].default_value = metal
    if emit is not None:
        bsdf.inputs['Emission Color'].default_value = (*emit, 1.0)
        bsdf.inputs['Emission Strength'].default_value = emit_strength
    if haze:
        g = node(nt, 'ShaderNodeGroup')
        g.node_tree = HAZE
        link(nt, bsdf.outputs[0], g.inputs[0])
        link(nt, g.outputs[0], out.inputs['Surface'])
    m["bsdf"] = bsdf.name
    return m


def bsdf_of(m):
    return m.node_tree.nodes[m["bsdf"]]


# ------------------------------------------------------------------ mesh helpers
def mesh_obj(name, verts, faces, col, mat=None, smooth_shade=False, recalc=True, xform=None):
    if xform is not None:
        verts = [xform @ Vector(v) for v in verts]
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], faces)
    if recalc:
        bm = bmesh.new()
        bm.from_mesh(me)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(me)
        bm.free()
    me.update()
    if smooth_shade:
        me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    ob = bpy.data.objects.new(name, me)
    col.objects.link(ob)
    if mat is not None:
        me.materials.append(mat)
    return ob


BOX_F = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]


def box(name, center, size, col, mat, rot_z=0.0):
    sx, sy, sz = (s / 2.0 for s in size)
    v = [(-sx, -sy, -sz), (sx, -sy, -sz), (sx, sy, -sz), (-sx, sy, -sz),
         (-sx, -sy, sz), (sx, -sy, sz), (sx, sy, sz), (-sx, sy, sz)]
    ob = mesh_obj(name, v, BOX_F, col, mat, recalc=False)
    ob.location = center
    ob.rotation_euler = (0.0, 0.0, rot_z)
    return ob


def cyl(name, p0, p1, r, col, mat, seg=16, cap=True):
    p0, p1 = Vector(p0), Vector(p1)
    axis = p1 - p0
    L = axis.length
    v = [(r * math.cos(2 * math.pi * i / seg), r * math.sin(2 * math.pi * i / seg), 0.0) for i in range(seg)]
    v += [(x, y, L) for (x, y, _) in v]
    f = [(i, (i + 1) % seg, seg + (i + 1) % seg, seg + i) for i in range(seg)]
    if cap:
        f += [tuple(range(seg - 1, -1, -1)), tuple(range(seg, 2 * seg))]
    ob = mesh_obj(name, v, f, col, mat, smooth_shade=True, recalc=False)
    ob.location = p0
    ob.rotation_mode = 'QUATERNION'
    ob.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(axis.normalized())
    return ob


def loft(name, stations, n, expo, col, mat):
    """Superellipse cross-sections (y, half-width, half-height, z-centre) lofted along Y."""
    v, f = [], []
    for (y, hw, hh, zc) in stations:
        for i in range(n):
            a = 2 * math.pi * i / n
            c, s = math.cos(a), math.sin(a)
            v.append((hw * math.copysign(abs(c) ** (2 / expo), c), y,
                      zc + hh * math.copysign(abs(s) ** (2 / expo), s)))
    ns = len(stations)
    for k in range(ns - 1):
        for i in range(n):
            j = (i + 1) % n
            f.append((k * n + i, k * n + j, (k + 1) * n + j, (k + 1) * n + i))
    f.append(tuple(range(n)))
    f.append(tuple(range((ns - 1) * n, ns * n)))
    return mesh_obj(name, v, f, col, mat, smooth_shade=True)


def ellipsoid(name, center, radii, col, mat, nu=24, nv=12):
    v, f = [], []
    for j in range(1, nv):
        th = math.pi * j / nv
        for i in range(nu):
            ph = 2 * math.pi * i / nu
            v.append((radii[0] * math.sin(th) * math.cos(ph), radii[1] * math.sin(th) * math.sin(ph),
                      radii[2] * math.cos(th)))
    top = len(v)
    v.append((0, 0, radii[2]))
    bot = len(v)
    v.append((0, 0, -radii[2]))
    for j in range(nv - 2):
        for i in range(nu):
            a, b = j * nu + i, j * nu + (i + 1) % nu
            f.append((a, b, b + nu, a + nu))
    for i in range(nu):
        f.append((top, (i + 1) % nu, i))
        a, b = (nv - 2) * nu + i, (nv - 2) * nu + (i + 1) % nu
        f.append((a, b, bot))
    ob = mesh_obj(name, v, f, col, mat, smooth_shade=True)
    ob.location = center
    return ob


def wing(name, root, tip, col, mat, up=(0, 0, 1), xform=None):
    """Lens-section surface. root/tip = (x, y_leading_edge, z, chord, thickness)."""
    up = Vector(up)

    def sec(x, yle, z, c, th):
        le = Vector((x, yle, z))
        mid = Vector((x, yle - 0.38 * c, z))
        return [le, mid + up * th / 2, Vector((x, yle - c, z)), mid - up * th / 2]

    v = sec(*root) + sec(*tip)
    f = [(0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7), (3, 2, 1, 0), (4, 5, 6, 7)]
    return mesh_obj(name, v, f, col, mat, xform=xform)


def parent(child, par):
    child.parent = par
    child.matrix_parent_inverse = Matrix.Identity(4)


# ------------------------------------------------------------------ materials
M_OCEAN = None  # built below (procedural)
M_HULL = material("HullGrey", (0.105, 0.112, 0.12), 0.55, var=0.18, var_scale=0.08)
M_ISLAND = material("IslandGrey", (0.125, 0.133, 0.142), 0.5, var=0.10, var_scale=0.2)
M_DECK = material("DeckNonSkid", (0.058, 0.060, 0.064), 0.9, var=0.30, var_scale=0.05)
M_WHITE = material("DeckWhite", (0.62, 0.62, 0.60), 0.7, var=0.15, var_scale=0.5)
M_YELLOW = material("DeckYellow", (0.62, 0.42, 0.04), 0.7)
M_WIRE = material("WireSteel", (0.05, 0.05, 0.05), 0.35, metal=0.8)
M_GLASS = material("BridgeGlass", (0.008, 0.010, 0.012), 0.06)
M_BALL = material("MeatballAmber", (0.0, 0.0, 0.0), 0.5, emit=(1.0, 0.42, 0.05), emit_strength=40.0)
M_DATUM = material("DatumGreen", (0.0, 0.0, 0.0), 0.5, emit=(0.15, 1.0, 0.25), emit_strength=25.0)
M_PAINT = material("JetPaint", (0.13, 0.14, 0.15), 0.42, var=0.08, var_scale=0.7)
M_RADOME = material("JetRadome", (0.11, 0.115, 0.12), 0.5)
M_CANOPY = material("Canopy", (0.015, 0.02, 0.025), 0.03)
M_NOZZLE = material("Nozzle", (0.07, 0.065, 0.06), 0.45, metal=1.0)
M_GLOW = material("ExhaustGlow", (0.0, 0.0, 0.0), 0.5, emit=(1.0, 0.36, 0.08), emit_strength=1.5)
M_HANGAR = material("HangarOpening", (0.006, 0.006, 0.007), 0.9)
M_COLD = material("ExhaustCold", (0.02, 0.02, 0.02), 0.6)
M_GEAR = material("GearWhite", (0.62, 0.62, 0.60), 0.5)
M_TIRE = material("Tire", (0.015, 0.015, 0.015), 0.85)
M_HOOK = material("Hook", (0.55, 0.55, 0.52), 0.4, metal=0.5)
M_HELMET = material("Helmet", (0.5, 0.5, 0.48), 0.4)
M_INTAKE = material("IntakeDark", (0.01, 0.01, 0.01), 0.8)


def ocean_material():
    m = bpy.data.materials.new("Ocean")
    if m.node_tree is None:
        m.use_nodes = True
    nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.bl_idname == 'ShaderNodeBsdfPrincipled')
    out = next(n for n in nt.nodes if n.bl_idname == 'ShaderNodeOutputMaterial')
    geo = node(nt, 'ShaderNodeNewGeometry')
    px, py, pz = sep_xyz(nt, geo.outputs['Position'])
    # wake behind the stern: widening, fading, streaky foam
    along = math_n(nt, 'MULTIPLY', math_n(nt, 'ADD', py, 160.0), -1.0)          # metres behind stern
    halfw = math_n(nt, 'ADD', 18.0, math_n(nt, 'MULTIPLY', along, 0.10))
    lat = math_n(nt, 'ABSOLUTE', math_n(nt, 'SUBTRACT', px, 0.0))
    core = map_range(nt, math_n(nt, 'DIVIDE', lat, halfw), 1.0, 0.25)
    fade = math_n(nt, 'EXPONENT', math_n(nt, 'MULTIPLY', along, -1.0 / 700.0))
    behind = map_range(nt, along, -5.0, 25.0)
    streak_v = comb_xyz(nt, math_n(nt, 'MULTIPLY', px, 0.09), math_n(nt, 'MULTIPLY', py, 0.012), 0.0)
    streak = map_range(nt, noise(nt, streak_v, 1.1, 5.0, 0.55), 0.30, 0.78)
    wake = math_n(nt, 'MULTIPLY', math_n(nt, 'MULTIPLY', core, fade), math_n(nt, 'MULTIPLY', behind, streak), clamp=True)
    # a little foam where the hull meets the water
    hull_band = math_n(nt, 'MULTIPLY', map_range(nt, math_n(nt, 'ABSOLUTE', px), 24.0, 20.5),
                       map_range(nt, math_n(nt, 'ABSOLUTE', math_n(nt, 'SUBTRACT', py, 2.0)), 168.0, 150.0))
    foam = math_n(nt, 'MAXIMUM', wake, math_n(nt, 'MULTIPLY', hull_band, streak), clamp=True)
    water = (0.004, 0.014, 0.019, 1.0)
    aerated = mix_rgb(nt, map_range(nt, foam, 0.0, 0.5), water, (0.05, 0.16, 0.15, 1.0))
    link(nt, mix_rgb(nt, map_range(nt, foam, 0.35, 1.0), aerated, (0.50, 0.54, 0.55, 1.0)), bsdf.inputs['Base Color'])
    link(nt, map_range(nt, foam, 0.0, 1.0, 0.045, 0.6, smoothstep=False), bsdf.inputs['Roughness'])
    bsdf.inputs['IOR'].default_value = 1.33
    # fine ripples on top of the displaced swell
    rip_v = vmath(nt, 'MULTIPLY', geo.outputs['Position'], (1.0, 1.6, 1.0))
    bump = node(nt, 'ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.25
    bump.inputs['Distance'].default_value = 0.4
    link(nt, noise(nt, rip_v, 0.35, 8.0, 0.55), bump.inputs['Height'])
    link(nt, bump.outputs['Normal'], bsdf.inputs['Normal'])
    g = node(nt, 'ShaderNodeGroup')
    g.node_tree = HAZE
    link(nt, bsdf.outputs[0], g.inputs[0])
    link(nt, g.outputs[0], out.inputs['Surface'])
    return m


M_OCEAN = ocean_material()


# tyre marks and wear down the landing area
_bs = bsdf_of(M_DECK)
_nt = M_DECK.node_tree
_geo = node(_nt, 'ShaderNodeNewGeometry')
_rel = vmath(_nt, 'SUBTRACT', _geo.outputs['Position'], tuple(RAMP))
_u = vmath(_nt, 'DOT_PRODUCT', _rel, tuple(DIR))
_v = vmath(_nt, 'DOT_PRODUCT', _rel, tuple(PORT))
_band = math_n(_nt, 'MULTIPLY', map_range(_nt, math_n(_nt, 'ABSOLUTE', _v), 9.0, 2.0), map_range(_nt, _u, 25.0, 60.0))
_band = math_n(_nt, 'MULTIPLY', _band, map_range(_nt, _u, 230.0, 150.0))
_streaks = map_range(_nt, noise(_nt, comb_xyz(_nt, math_n(_nt, 'MULTIPLY', _u, 0.015), math_n(_nt, 'MULTIPLY', _v, 0.9), 0.0), 3.0, 6.0, 0.6), 0.45, 0.75)
_marks = math_n(_nt, 'MULTIPLY', _band, _streaks, clamp=True)
_old = _bs.inputs['Base Color'].links[0].from_socket
link(_nt, mix_rgb(_nt, math_n(_nt, 'MULTIPLY', _marks, 0.85), _old, (0.012, 0.012, 0.013, 1.0)), _bs.inputs['Base Color'])

# hull boot-topping: dark band at and below the waterline
_bs = bsdf_of(M_HULL)
_nt = M_HULL.node_tree
_geo = node(_nt, 'ShaderNodeNewGeometry')
_, _, _hz = sep_xyz(_nt, _geo.outputs['Position'])
_band = map_range(_nt, _hz, 1.6, 1.2)
_old = _bs.inputs['Base Color'].links[0].from_socket
link(_nt, mix_rgb(_nt, _band, _old, (0.012, 0.012, 0.014, 1.0)), _bs.inputs['Base Color'])


# ------------------------------------------------------------------ world: hazy low-sun sky with a cloud deck
def make_world():
    w = bpy.data.worlds.new("Sky")
    SC.world = w
    if w.node_tree is None:
        w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    out = node(nt, 'ShaderNodeOutputWorld')
    bg = node(nt, 'ShaderNodeBackground')
    bg.inputs['Strength'].default_value = SKY_STRENGTH
    tc = node(nt, 'ShaderNodeTexCoord')
    x, y, z = sep_xyz(nt, tc.outputs['Generated'])
    d = vmath(nt, 'NORMALIZE', comb_xyz(nt, x, y, math_n(nt, 'MAXIMUM', z, 0.0015)))
    sky = node(nt, 'ShaderNodeTexSky')
    setup_sky(sky)
    link(nt, d, sky.inputs['Vector'])
    # cloud deck projected onto a plane overhead
    zc = math_n(nt, 'MAXIMUM', z, 0.03)
    uv = comb_xyz(nt, math_n(nt, 'DIVIDE', x, zc), math_n(nt, 'DIVIDE', y, zc), 0.0)
    uv = vmath(nt, 'ADD', vmath(nt, 'MULTIPLY', uv, (1.0, 2.2, 1.0)), (3.7, 1.3, 0.0))
    c1 = map_range(nt, noise(nt, uv, 0.55, 8.0, 0.62), 0.38, 0.62)
    breaks = map_range(nt, noise(nt, uv, 0.12, 2.0, 0.5), 0.36, 0.56)
    fade = map_range(nt, z, 0.012, 0.16)
    mask = math_n(nt, 'MULTIPLY', math_n(nt, 'MULTIPLY', c1, fade), math_n(nt, 'MULTIPLY', breaks, 0.97), clamp=True)
    bw = node(nt, 'ShaderNodeRGBToBW')
    link(nt, sky.outputs['Color'], bw.inputs['Color'])
    grey = mix_rgb(nt, 0.85, sky.outputs['Color'], bw.outputs['Val'])
    cloud = mix_rgb(nt, 1.0, grey, (0.52, 0.53, 0.56, 1.0), blend='MULTIPLY')
    link(nt, mix_rgb(nt, mask, sky.outputs['Color'], cloud), bg.inputs['Color'])
    link(nt, bg.outputs[0], out.inputs['Surface'])


make_world()

sun_data = bpy.data.lights.new("Sun", 'SUN')
sun_data.energy = SUN_STRENGTH
sun_data.angle = math.radians(1.2)
sun_data.color = (1.0, 0.86, 0.72)
sun = bpy.data.objects.new("Sun", sun_data)
ROOT_COL.objects.link(sun)
sun.rotation_mode = 'QUATERNION'
sun.rotation_quaternion = (-SUN_VEC).to_track_quat('-Z', 'Y')

# ------------------------------------------------------------------ ocean
C_SEA = new_col("Sea")


def make_ocean():
    me = bpy.data.meshes.new("OceanPatch")
    ob = bpy.data.objects.new("OceanPatch", me)
    C_SEA.objects.link(ob)
    mod = ob.modifiers.new("Ocean", 'OCEAN')
    mod.geometry_mode = 'GENERATE'
    mod.resolution = 10
    mod.viewport_resolution = 6
    mod.spatial_size = 250
    mod.repeat_x, mod.repeat_y = 7, 12
    mod.wind_velocity = 11.0
    mod.wave_scale = 1.1
    mod.choppiness = 0.9
    mod.wave_alignment = 0.35
    mod.wave_direction = math.radians(80.0)
    mod.random_seed = 7
    mod.use_normals = True
    me.materials.append(M_OCEAN)
    me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    if ARGS.static_ocean:
        mod.time = 2.0
    else:
        mod.time = 0.0
        mod.keyframe_insert("time", frame=1)
        mod.time = N_FRAMES / FPS
        mod.keyframe_insert("time", frame=N_FRAMES + 1)
    # centre the tiled patch over the action
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    ev = ob.evaluated_get(dg)
    bb = [ev.matrix_world @ Vector(c) for c in ev.bound_box]
    cx = (min(b.x for b in bb) + max(b.x for b in bb)) / 2
    cy = (min(b.y for b in bb) + max(b.y for b in bb)) / 2
    w = max(b.x for b in bb) - min(b.x for b in bb)
    h = max(b.y for b in bb) - min(b.y for b in bb)
    target = Vector((-150.0, -650.0))
    ob.location = (target.x - cx, target.y - cy, 0.0)
    for p in ob.data.polygons:
        p.use_smooth = True
    # far sea: a flat ring out to 60 km around the patch
    hx, hy = w / 2 - 6.0, h / 2 - 6.0
    R = 60000.0
    tx, ty = target
    v = [(tx - hx, ty - hy, -0.25), (tx + hx, ty - hy, -0.25), (tx + hx, ty + hy, -0.25), (tx - hx, ty + hy, -0.25),
         (-R, -R, -0.25), (R, -R, -0.25), (R, R, -0.25), (-R, R, -0.25)]
    f = [(4, 5, 1, 0), (5, 6, 2, 1), (6, 7, 3, 2), (7, 4, 0, 3)]
    mesh_obj("FarSea", v, f, C_SEA, M_OCEAN, recalc=False)
    return ob, mod


OCEAN, OCEAN_MOD = make_ocean()

# ------------------------------------------------------------------ the jet
def build_jet(col, prefix, hero):
    root = bpy.data.objects.new(prefix + "Root", None)
    root.empty_display_size = 3.0
    col.objects.link(root)
    parts = []
    st = [(10.6, 0.03, 0.03, 2.42), (10.0, 0.22, 0.22, 2.42), (9.2, 0.42, 0.42, 2.44), (8.0, 0.62, 0.60, 2.47),
          (6.6, 0.76, 0.74, 2.52), (5.2, 0.86, 0.80, 2.52), (4.2, 1.30, 0.84, 2.45), (3.0, 1.80, 0.88, 2.40),
          (1.0, 1.92, 0.90, 2.38), (-1.0, 1.90, 0.86, 2.36), (-3.2, 1.70, 0.80, 2.36), (-5.2, 1.42, 0.68, 2.36),
          (-6.6, 1.22, 0.58, 2.36), (-7.0, 1.16, 0.55, 2.36)]
    parts.append(loft(prefix + "Fuselage", st, 28, 2.6, col, M_PAINT))
    parts.append(loft(prefix + "Radome", [(11.2, 0.02, 0.02, 2.42), (10.55, 0.10, 0.10, 2.42), (10.0, 0.24, 0.24, 2.42)],
                      20, 2.0, col, M_RADOME))
    parts.append(ellipsoid(prefix + "Canopy", (0, 6.0, 3.05), (0.52, 1.9, 0.58), col, M_CANOPY))
    parts.append(ellipsoid(prefix + "Helmet", (0, 6.1, 3.25), (0.17, 0.2, 0.19), col, M_HELMET, 12, 8))
    for sx in (-1, 1):
        parts.append(wing(prefix + f"Wing{sx}", (sx * 1.85, 1.6, 2.42, 4.8, 0.32), (sx * 6.3, -1.4, 2.40, 1.7, 0.10), col, M_PAINT))
        parts.append(wing(prefix + f"Lex{sx}", (sx * 0.7, 7.2, 2.62, 5.6, 0.12), (sx * 1.9, 3.2, 2.55, 1.7, 0.08), col, M_PAINT))
        parts.append(wing(prefix + f"Stab{sx}", (sx * 1.2, -4.3, 2.30, 2.6, 0.14), (sx * 3.7, -5.9, 2.12, 1.1, 0.06), col, M_PAINT))
        pivot = Vector((sx * 1.0, -2.4, 3.0))
        xf = Matrix.Translation(pivot) @ Matrix.Rotation(sx * math.radians(20), 4, 'Y') @ Matrix.Translation(-pivot)
        parts.append(wing(prefix + f"Tail{sx}", (sx * 1.0, -2.4, 3.0, 3.6, 0.14), (sx * 1.0, -4.9, 5.1, 1.3, 0.07),
                          col, M_PAINT, up=(1, 0, 0), xform=xf))
        parts.append(cyl(prefix + f"Rail{sx}", (sx * 6.35, 0.2, 2.38), (sx * 6.35, -2.6, 2.38), 0.07, col, M_PAINT, 8))
        parts.append(box(prefix + f"Intake{sx}", (sx * 1.25, 3.3, 1.78), (0.62, 0.3, 0.72), col, M_INTAKE))
        parts.append(cyl(prefix + f"Nozzle{sx}", (sx * 0.56, -6.6, 2.36), (sx * 0.56, -7.45, 2.36), 0.47, col, M_NOZZLE, 20))
        parts.append(cyl(prefix + f"Burner{sx}", (sx * 0.56, -7.2, 2.36), (sx * 0.56, -7.47, 2.36), 0.36, col,
                         M_GLOW if hero else M_COLD, 20))
        # main gear
        parts.append(cyl(prefix + f"MainStrut{sx}", (sx * 1.62, 0.0, 0.42), (sx * 1.45, 0.25, 1.75), 0.13, col, M_GEAR, 12))
        parts.append(cyl(prefix + f"MainWheel{sx}", (sx * 1.48, 0.0, 0.42), (sx * 1.80, 0.0, 0.42), 0.42, col, M_TIRE, 20))
        parts.append(cyl(prefix + f"NoseWheel{sx}", (sx * 0.06, 6.8, 0.36), (sx * 0.26, 6.8, 0.36), 0.36, col, M_TIRE, 16))
    parts.append(cyl(prefix + "NoseStrut", (0, 6.8, 0.36), (0, 6.6, 1.80), 0.11, col, M_GEAR, 12))
    for p in parts:
        parent(p, root)
    # tailhook on a hinge
    hinge = bpy.data.objects.new(prefix + "HookHinge", None)
    hinge.empty_display_size = 0.3
    col.objects.link(hinge)
    parent(hinge, root)
    hinge.location = HOOK_PIVOT
    hinge.rotation_euler = (HOOK_NAT if hero else math.radians(6), 0, 0)
    arm = box(prefix + "HookArm", (0, -HOOK_LEN / 2, 0), (0.12, HOOK_LEN, 0.12), col, M_HOOK)
    shoe = box(prefix + "HookShoe", (0, -HOOK_LEN, -0.04), (0.20, 0.32, 0.18), col, M_HOOK)
    parent(arm, hinge)
    parent(shoe, hinge)
    return root, hinge


C_JET = new_col("HeroJet")
JET, HOOK = build_jet(C_JET, "Hero", hero=True)
JET.rotation_mode = 'YXZ'

C_ASSET = bpy.data.collections.new("ParkedJetAsset")     # not linked to the scene: instanced below
build_jet(C_ASSET, "Parked", hero=False)

# ------------------------------------------------------------------ the carrier
C_SHIP = new_col("Carrier")


def build_carrier():
    # hull lofted through stations (y, half-beam at waterline, half-beam at hangar-deck level)
    stations = [(-160, 18.5, 19.5), (-140, 20.0, 21.0), (-100, 20.5, 21.5), (0, 20.5, 22.0), (60, 20.3, 22.0),
                (100, 18.5, 21.0), (125, 14.5, 19.0), (145, 9.0, 16.0), (158, 4.0, 12.0), (165, 0.8, 8.0)]
    v, f = [], []
    for (y, ww, wt) in stations:
        sec = [(-wt, 17.5), (-ww, 0.0), (-ww * 0.92, -7.0), (-ww * 0.55, -10.5), (0.0, -11.0),
               (ww * 0.55, -10.5), (ww * 0.92, -7.0), (ww, 0.0), (wt, 17.5)]
        v += [(x, y, z) for (x, z) in sec]
    n = 9
    for k in range(len(stations) - 1):
        for i in range(n - 1):
            f.append((k * n + i, k * n + i + 1, (k + 1) * n + i + 1, (k + 1) * n + i))
    f.append(tuple(range(n)))
    f.append(tuple(range((len(stations) - 1) * n, len(stations) * n)))
    mesh_obj("Hull", v, f, C_SHIP, M_HULL, recalc=False)

    # flight deck slab
    outline = [(18, -165), (-24, -165), (-30, -140), (-40, -60), (-47, 0), (-53, 50), (-56, 72), (-56, 80),
               (-34, 94), (-28, 118), (-21, 142), (-12, 160), (-5, 168), (5, 168), (14, 158), (22, 140),
               (27, 110), (30, 70), (31, 20), (31, -40), (30, -90), (27, -130), (22, -155)]
    area = sum(outline[i][0] * outline[(i + 1) % len(outline)][1] - outline[(i + 1) % len(outline)][0] * outline[i][1]
               for i in range(len(outline)))
    if area < 0:
        outline.reverse()
    m = len(outline)
    v = [(x, y, DECK_Z) for (x, y) in outline] + [(x, y, 17.5) for (x, y) in outline]
    f = [tuple(range(m)), tuple(range(2 * m - 1, m - 1, -1))]
    f += [(i, m + i, m + (i + 1) % m, (i + 1) % m) for i in range(m)]
    deck = mesh_obj("FlightDeck", v, f, C_SHIP, M_DECK, recalc=False)
    deck.data.materials.append(M_HULL)
    for p in deck.data.polygons[2:]:
        p.material_index = 1

    # hangar-deck openings on the hull sides
    for (x, y, ln) in ((22.15, 45.0, 22.0), (22.15, -72.0, 18.0), (-22.15, -15.0, 20.0)):
        box(f"Hangar{y:+.0f}", (x, y, 11.0), (0.25, ln, 7.0), C_SHIP, M_HANGAR)
    # dark catwalk / sponson recess under the flight-deck edge, and openings in the stern
    for x in (-22.2, 22.2):
        box(f"Catwalk{x:+.0f}", (x, -20.0, 16.6), (0.3, 270.0, 1.5), C_SHIP, M_HANGAR)
    box("SternCatwalk", (0.0, -160.2, 16.6), (40.0, 0.3, 1.5), C_SHIP, M_HANGAR)
    for x in (-11.0, 0.0, 11.0):
        box(f"Fantail{x:+.0f}", (x, -160.2, 11.5), (7.0, 0.3, 4.0), C_SHIP, M_HANGAR)

    # island superstructure
    box("IslandBase", (20.0, -25.0, 27.0), (11, 32, 14), C_SHIP, M_ISLAND)
    box("IslandUpper", (19.5, -21.0, 37.5), (10, 20, 7), C_SHIP, M_ISLAND)
    box("BridgeWindows", (19.5, -21.0, 38.9), (10.3, 20.3, 1.3), C_SHIP, M_GLASS)
    box("PriFly", (19.0, -27.0, 42.8), (8, 9, 3.6), C_SHIP, M_ISLAND)
    box("PriFlyWindows", (19.0, -27.0, 43.4), (8.3, 9.3, 1.2), C_SHIP, M_GLASS)
    box("RadarPanelA", (14.2, -14.0, 36.0), (0.4, 5.0, 4.0), C_SHIP, M_ISLAND)
    box("RadarPanelB", (14.2, -33.0, 36.0), (0.4, 5.0, 4.0), C_SHIP, M_ISLAND)
    cyl("Mast", (19.0, -24.0, 44.6), (19.0, -24.0, 62.0), 0.6, C_SHIP, M_ISLAND, 12)
    box("Yardarm", (19.0, -24.0, 56.0), (9.0, 0.35, 0.35), C_SHIP, M_ISLAND)
    cyl("RadarDish", (19.0, -24.0, 59.0), (19.0, -24.0, 59.5), 2.2, C_SHIP, M_ISLAND, 20)
    cyl("Mast2", (19.5, -12.0, 41.0), (19.5, -12.0, 52.0), 0.35, C_SHIP, M_ISLAND, 8)

    # deck markings along the angled deck
    rz = TH
    L_LAND = 236.0
    for lat in (11.5, -11.5):
        box(f"EdgeLine{lat:+.0f}", lp(L_LAND / 2, lat, DECK_Z + 0.015), (0.45, L_LAND, 0.03), C_SHIP, M_WHITE, rz)
    s = 3.0
    k = 0
    while s < L_LAND - 4:
        box(f"CentreDash{k}", lp(s + 3.0, 0.0, DECK_Z + 0.015), (0.5, 6.0, 0.03), C_SHIP, M_WHITE, rz)
        s += 12.0
        k += 1
    box("RampStripe", lp(1.0, 0.0, DECK_Z + 0.015), (24.0, 0.8, 0.03), C_SHIP, M_WHITE, rz)
    # ship centreline + bow catapult tracks
    for k, y in enumerate(range(70, 166, 12)):
        box(f"ShipCL{k}", (0.0, y + 3.0, DECK_Z + 0.015), (0.45, 6.0, 0.03), C_SHIP, M_WHITE)
    for x in (-7.0, 7.0):
        box(f"Catapult{x:+.0f}", (x, 118.0, DECK_Z + 0.012), (0.35, 92.0, 0.025), C_SHIP, M_WIRE)
    box("FoulLine", lp(150.0, -14.5, DECK_Z + 0.015), (0.35, 150.0, 0.03), C_SHIP, M_YELLOW, rz)

    # arresting wires: 1, 2 and 4 are static; 3 is two animated segments
    wire_objs = {}
    for i, sw in enumerate(WIRES):
        a = lp(sw, -WIRE_HALF, DECK_Z + 0.12)
        b = lp(sw, WIRE_HALF, DECK_Z + 0.12)
        for e, pnt in (("S", a), ("P", b)):
            box(f"Sheave{i + 1}{e}", (pnt.x, pnt.y, DECK_Z + 0.15), (0.7, 0.7, 0.3), C_SHIP, M_WIRE, rz)
        if i == 2:
            continue
        cyl(f"Wire{i + 1}", a, b, 0.07, C_SHIP, M_WIRE, 8, cap=False)
    for side, sgn in (("S", -1.0), ("P", 1.0)):
        vv = [(0.07 * math.cos(2 * math.pi * j / 8), 0.0, 0.07 * math.sin(2 * math.pi * j / 8)) for j in range(8)]
        vv += [(x, 1.0, z) for (x, _, z) in vv]
        ff = [(j, (j + 1) % 8, 8 + (j + 1) % 8, 8 + j) for j in range(8)]
        ob = mesh_obj(f"Wire3{side}", vv, ff, C_SHIP, M_WIRE, smooth_shade=True, recalc=False)
        ob.rotation_mode = 'QUATERNION'
        wire_objs[side] = (ob, lp(WIRES[2], sgn * WIRE_HALF, DECK_Z + 0.12))

    # optical landing aid on the port deck edge, facing the approach
    ball = lp(125.0, 16.0, DECK_Z + 1.9)
    box("LensHousing", ball, (5.0, 1.0, 3.8), C_SHIP, M_ISLAND, rz)
    box("LensBall", ball - DIR * 0.52 + Vector((0, 0, 0.3)), (0.8, 0.06, 0.8), C_SHIP, M_BALL, rz)
    for o in (-1.6, 1.6):
        box(f"Datum{o:+.0f}", ball - DIR * 0.52 + PORT * o + Vector((0, 0, 0.3)), (1.6, 0.06, 0.25), C_SHIP, M_DATUM, rz)

    # parked aircraft, a tug or two
    spots = [(23.0, 22.0, 250), (23.0, 40.0, 250), (23.0, 58.0, 250), (-14.0, 126.0, 170), (-4.0, 146.0, 175),
             (10.0, 150.0, 190), (16.0, 92.0, 215), (-18.0, 104.0, 160)]
    for k, (x, y, hdg) in enumerate(spots):
        inst = bpy.data.objects.new(f"Parked{k}", None)
        inst.instance_type = 'COLLECTION'
        inst.instance_collection = C_ASSET
        inst.location = (x, y, DECK_Z)
        inst.rotation_euler = (0, 0, math.radians(hdg))
        C_SHIP.objects.link(inst)
    box("Tug1", (12.0, 70.0, DECK_Z + 0.6), (1.6, 3.0, 1.2), C_SHIP, M_YELLOW, math.radians(30))
    box("Tug2", (24.0, -60.0, DECK_Z + 0.6), (1.6, 3.0, 1.2), C_SHIP, M_GEAR, math.radians(-10))
    return wire_objs


WIRE3 = build_carrier()


# escort ships on the horizon
def escort(name, x, y, hdg):
    c = new_col(name)
    box(name + "Hull", (x, y, 2.0), (18, 150, 10), c, M_HULL, math.radians(hdg))
    box(name + "Super", (x, y + 10, 10.0), (12, 40, 8), c, M_ISLAND, math.radians(hdg))
    cyl(name + "Mast", (x, y + 12, 14.0), (x, y + 12, 34.0), 0.8, c, M_ISLAND, 8)


escort("EscortAhead", -1300.0, 2600.0, 0.0)
escort("EscortAstern", -1500.0, -3800.0, 0.0)


# ------------------------------------------------------------------ motion
def jet_s_precatch(t):
    return S_TD - V_APP * (T_TD - t)


def jet_pose(t, t_catch=None, s_catch=None):
    """World position, (pitch, roll, yaw), exhaust glow, and distance past ramp at time t."""
    if t_catch is None or t <= t_catch:
        s = jet_s_precatch(t)
    elif t <= t_catch + T_ARR:
        u = (t - t_catch) / T_ARR
        s = s_catch + D_ARR * (1 - (1 - u) ** 2)
    else:
        s = s_catch + D_ARR - ROLLBACK * smooth((t - t_catch - T_ARR) / T_RB)
    fade = max(0.0, (T_TD - t) / T_TD)
    if t < T_TD:
        w = 2 * math.pi / 5.2
        lat = 2.2 * math.sin(w * t + 0.8) * fade ** 1.3
        dlat = 2.2 * w * math.cos(w * t + 0.8) * fade ** 1.3
        z = DECK_Z + (S_TD - s) * math.tan(GS) + 0.35 * math.sin(2 * math.pi * t / 2.3 + 0.4) * fade
        pitch = 4.6 + 0.6 * math.sin(2 * math.pi * t / 3.1) * fade
        roll = (-3.0 * math.cos(w * t + 0.8) + 0.5 * math.sin(2 * math.pi * t / 0.9 + 1.3)) * fade
        yaw = TH + math.atan2(dlat, V_APP) * 0.6
        glow = 1.5
    else:
        tau = t - T_TD
        lat = 0.25 * smooth(tau / 2.0)
        yaw = TH + math.radians(0.4) * smooth(tau / 2.0)
        z = DECK_Z - 0.35 * math.exp(-tau / 0.22) * math.sin(math.pi * tau / 0.2)
        if tau < 0.35:
            pitch = 4.6 - 5.0 * (tau / 0.35) ** 2
        else:
            pitch = -0.4 + 0.4 * (1 - math.exp(-(tau - 0.35) / 0.25))
        if t_catch is not None and t_catch <= t <= t_catch + T_ARR:
            pitch -= 1.6 * max(0.0, math.sin(math.pi * (t - t_catch) / T_ARR)) ** 0.7
        if t_catch is not None and t > t_catch + T_ARR:
            ts = t - t_catch - T_ARR
            pitch += 0.7 * math.exp(-ts / 0.35) * math.sin(2 * math.pi * ts / 0.7)
        roll = 1.0 * math.exp(-tau / 0.3) * math.sin(2 * math.pi * tau / 0.5)
        glow = 1.5 + 6.5 * smooth(tau / 0.3)
        if t_catch is not None and t > t_catch + T_ARR + 0.3:
            glow = 8.0 - 7.2 * smooth((t - t_catch - T_ARR - 0.3) / 1.0)
    pos = lp(s, lat, z)
    return pos, (math.radians(pitch), math.radians(roll), yaw), glow, s


def jet_matrix(pos, rot):
    return Matrix.Translation(pos) @ Euler(rot, 'YXZ').to_matrix().to_4x4()


def hook_tip(M, a):
    return M @ (HOOK_PIVOT + Vector((0.0, -HOOK_LEN * math.cos(a), -HOOK_LEN * math.sin(a))))


def hook_angle(M):
    """Free-hanging angle, or the angle that keeps the hook riding on the deck."""
    floor = DECK_Z + 0.06
    tip = hook_tip(M, HOOK_NAT)
    s_tip = (tip - RAMP).dot(DIR)
    if tip.z >= floor or s_tip < -0.5:
        return HOOK_NAT
    lo, hi = math.radians(-25.0), HOOK_NAT
    for _ in range(40):
        mid = 0.5 * (lo + hi)
        if hook_tip(M, mid).z < floor:
            hi = mid
        else:
            lo = mid
    return 0.5 * (lo + hi)


def solve_catch():
    """First moment the deck-riding hook reaches the 3-wire."""
    t = T_TD
    while t < T_TD + 1.0:
        pos, rot, _, s = jet_pose(t)
        M = jet_matrix(pos, rot)
        tip = hook_tip(M, hook_angle(M))
        if (tip - RAMP).dot(DIR) >= WIRES[2]:
            return t, s
        t += 0.0005
    raise RuntimeError("hook never reached the wire")


T_CATCH, S_CATCH = solve_catch()
T_STOP = T_CATCH + T_ARR
print(f"[previz] touchdown t={T_TD:.2f}s (f{T_TD * FPS + 1:.0f}), 3-wire t={T_CATCH:.3f}s "
      f"(f{T_CATCH * FPS + 1:.1f}), stop t={T_STOP:.2f}s (f{T_STOP * FPS + 1:.0f}) at s={S_CATCH + D_ARR:.1f} m")

glow_sock = bsdf_of(M_GLOW).inputs['Emission Strength']
tips = {}
for f in range(1, N_FRAMES + 2):
    t = T(f)
    pos, rot, glow, s = jet_pose(t, T_CATCH, S_CATCH)
    JET.location = pos
    JET.rotation_euler = rot
    JET.keyframe_insert("location", frame=f)
    JET.keyframe_insert("rotation_euler", frame=f)
    M = jet_matrix(pos, rot)
    a = hook_angle(M)
    HOOK.rotation_euler = (a, 0.0, 0.0)
    HOOK.keyframe_insert("rotation_euler", frame=f)
    tips[f] = hook_tip(M, a)
    glow_sock.default_value = glow
    glow_sock.keyframe_insert("default_value", frame=f)

# the 3-wire: straight until the hook catches it, then a V to the hook
mid0 = lp(WIRES[2], 0.0, DECK_Z + 0.12)
for f in range(1, N_FRAMES + 2):
    t = T(f)
    mid = mid0 if t < T_CATCH else Vector((tips[f].x, tips[f].y, max(tips[f].z, DECK_Z + 0.08)))
    for side, (ob, anchor) in WIRE3.items():
        d = mid - anchor
        ob.location = anchor
        ob.rotation_quaternion = Vector((0, 1, 0)).rotation_difference(d.normalized())
        ob.scale = (1.0, d.length, 1.0)
        ob.keyframe_insert("location", frame=f)
        ob.keyframe_insert("rotation_quaternion", frame=f)
        ob.keyframe_insert("scale", frame=f)


# ------------------------------------------------------------------ cameras
def make_cam(name, lens):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.sensor_width = 36.0
    cd.clip_start = 0.05
    cd.clip_end = 90000.0
    ob = bpy.data.objects.new(name, cd)
    ROOT_COL.objects.link(ob)
    ob.rotation_mode = 'QUATERNION'
    return ob


def wobble(t, seed, amp, freqs=(0.31, 0.53, 0.87, 1.37, 2.9, 4.7)):
    r = random.Random(seed)
    tot = 0.0
    for i, fr in enumerate(freqs):
        tot += math.sin(2 * math.pi * fr * t + r.uniform(0, 6.283)) / (1 + i)
    return amp * tot / 2.45


def look(cam_pos, target, roll=0.0, tilt=0.0, pan=0.0):
    q = (target - cam_pos).normalized().to_track_quat('-Z', 'Y')
    return q @ Euler((tilt, pan, roll), 'XYZ').to_quaternion()


CAM1 = make_cam("Cam1_HeloChase", 45.0)
CAM2 = make_cam("Cam2_SpineMount", 22.0)
CAM3 = make_cam("Cam3_DeckLevel", 40.0)

# shot 1: helicopter chase, slower than the jet so it pulls away toward the ship
s_jet0 = jet_s_precatch(0.0)
for f in range(1, SHOTS[1][1] + 6):
    t = T(f)
    sc = s_jet0 - 65.0 + 42.0 * t
    p = lp(sc, -12.0, DECK_Z + (S_TD - sc) * math.tan(GS) + 6.0)
    p += Vector((wobble(t, 1, 0.5), wobble(t, 2, 0.4), wobble(t, 3, 0.45)))
    jp = jet_pose(t, T_CATCH, S_CATCH)[0]
    tgt = jp.lerp(lp(S_TD, 0.0, DECK_Z), 0.20)
    CAM1.location = p
    CAM1.rotation_quaternion = look(p, tgt, roll=math.radians(wobble(t, 4, 0.8)),
                                    tilt=math.radians(wobble(t, 5, 0.25)), pan=math.radians(wobble(t, 6, 0.3)))
    CAM1.keyframe_insert("location", frame=f)
    CAM1.keyframe_insert("rotation_quaternion", frame=f)

# shot 2: rigidly mounted above the spine, looking over the canopy
parent(CAM2, JET)
CAM2.location = (0.0, -3.0, 4.9)
CAM2.rotation_mode = 'XYZ'
base = Euler((math.radians(82.0), 0.0, 0.0))
for f in range(SHOTS[2][0] - 5, SHOTS[2][1] + 6):
    t = T(f)
    jit = random.Random(f * 7919)
    CAM2.rotation_euler = (base.x + math.radians(jit.uniform(-0.12, 0.12) + wobble(t, 7, 0.2, (3.1, 5.3, 8.9))),
                           math.radians(jit.uniform(-0.1, 0.1)), math.radians(wobble(t, 8, 0.15, (2.7, 6.1, 9.7))))
    CAM2.keyframe_insert("rotation_euler", frame=f)

# shot 3: operator crouched at the deck edge, panning with the jet
p3 = lp(190.0, -12.0, DECK_Z + 2.6)
aim = None
for f in range(SHOTS[3][0] - 12, N_FRAMES + 2):
    t = T(f)
    jp = jet_pose(t, T_CATCH, S_CATCH)[0] + Vector((0, 0, 1.5))
    aim = jp if aim is None else aim.lerp(jp, 0.35)
    shake = 0.0
    for t0, amp in ((T_TD, 0.9), (T_CATCH, 0.6)):
        if t >= t0:
            shake += amp * math.exp(-(t - t0) / 0.25) * math.sin(2 * math.pi * 11.0 * (t - t0))
    pos = p3 + Vector((wobble(t, 9, 0.03), wobble(t, 10, 0.03), wobble(t, 11, 0.04)))
    if f >= SHOTS[3][0]:
        CAM3.location = pos
        CAM3.rotation_quaternion = look(pos, aim, roll=math.radians(wobble(t, 12, 0.5) + 0.3 * shake),
                                        tilt=math.radians(wobble(t, 13, 0.25) + shake),
                                        pan=math.radians(wobble(t, 14, 0.3) + 0.5 * shake))
        CAM3.keyframe_insert("location", frame=f)
        CAM3.keyframe_insert("rotation_quaternion", frame=f)

SHOT_CAMS = {1: CAM1, 2: CAM2, 3: CAM3}

# ------------------------------------------------------------------ render settings
rx, ry = (int(v) for v in ARGS.res.lower().split("x"))
SC.render.resolution_x, SC.render.resolution_y = rx, ry
SC.render.resolution_percentage = 100
SC.render.engine = 'CYCLES'
cy = SC.cycles
cy.device = 'CPU'
cy.samples = ARGS.samples
cy.use_adaptive_sampling = True
cy.adaptive_threshold = 0.04
cy.use_denoising = True
try:
    cy.denoiser = 'OPENIMAGEDENOISE'
except TypeError:
    pass
cy.max_bounces = 4
cy.diffuse_bounces = 2
cy.glossy_bounces = 2
cy.transmission_bounces = 2
cy.volume_bounces = 0
cy.transparent_max_bounces = 4
cy.caustics_reflective = False
cy.caustics_refractive = False
cy.sample_clamp_indirect = 4.0
SC.render.use_persistent_data = True
SC.render.film_transparent = False
vs = SC.view_settings
vs.view_transform = 'AgX'
for look_name in ('AgX - Medium High Contrast', 'Medium High Contrast'):
    try:
        vs.look = look_name
        break
    except TypeError:
        pass
vs.exposure = EXPOSURE
SC.render.image_settings.file_format = 'PNG'
SC.render.image_settings.color_mode = 'RGB'

if ARGS.save_blend:
    os.makedirs(os.path.dirname(os.path.abspath(ARGS.save_blend)), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(ARGS.save_blend))
    print("[previz] saved", ARGS.save_blend)


# ------------------------------------------------------------------ render
def shot_of(f):
    for k, (a, b) in SHOTS.items():
        if a <= f <= b:
            return k
    return 3


def frame_list():
    if ARGS.frames:
        out = []
        for part in ARGS.frames.split(","):
            if "-" in part:
                a, b = part.split("-")
                out += list(range(int(a), int(b) + 1))
            else:
                out.append(int(part))
        return out
    if ARGS.shot == "all":
        return list(range(1, N_FRAMES + 1))
    a, b = SHOTS[int(ARGS.shot)]
    return list(range(a, b + 1))


if not ARGS.no_render:
    import time
    os.makedirs(ARGS.out, exist_ok=True)
    for f in frame_list():
        k = shot_of(f)
        SC.camera = SHOT_CAMS[k]
        SC.frame_set(f)
        SC.render.filepath = os.path.join(ARGS.out, f"shot{k}", f"f{f:04d}.png")
        t0 = time.time()
        bpy.ops.render.render(write_still=True)
        print(f"[previz] frame {f} shot {k} rendered in {time.time() - t0:.1f}s", flush=True)
