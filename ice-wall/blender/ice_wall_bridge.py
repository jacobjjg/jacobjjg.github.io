"""Rough previz still: inside a naval ship's bridge, crew looking out at a vast ice wall with a cut entrance.

Blender 5.x (tested 5.3.0, Cycles CPU). Run with bpy as a module or inside Blender:
    python ice_wall_bridge.py --shot wide --res 1920x1080 --samples 96 --out ./renders
    blender -b -P ice_wall_bridge.py -- --shot ots
Shots: wide = from the back of the bridge (32 mm), ots = over an officer's shoulder (50 mm).
Scale is 1 unit = 1 m. The ship points along +Y; the bridge floor is at z = 0, the sea at z = -18.
"""
import argparse
import math
import os
import random
import sys

import bpy  # noqa: E402  (bpy must load before bmesh/mathutils when run as a module)
import bmesh
from mathutils import Matrix, Vector, noise


def get_args():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else argv[1:]
    p = argparse.ArgumentParser()
    p.add_argument("--out", default=os.path.join(os.getcwd(), "renders"))
    p.add_argument("--res", default="1920x1080")
    p.add_argument("--samples", type=int, default=96)
    p.add_argument("--shot", default="wide", help="wide, ots or all")
    p.add_argument("--save_blend", default="")
    return p.parse_known_args(argv)[0]


ARGS = get_args()
SEA_Z = -18.0
WALL_Y = 700.0
WALL_H = 160.0
GATE_W, GATE_H = 70.0, 90.0          # the cut entrance
FOG = (0.62, 0.68, 0.74)
FOG_DIST = 5500.0

bpy.ops.wm.read_factory_settings(use_empty=True)
SC = bpy.context.scene
COL = SC.collection
random.seed(4)


# ------------------------------------------------------------------ helpers
def node(nt, kind, **kw):
    n = nt.nodes.new(kind)
    for k, v in kw.items():
        setattr(n, k, v)
    return n


def link(nt, a, b):
    nt.links.new(a, b)


def make_haze():
    ng = bpy.data.node_groups.new("Haze", 'ShaderNodeTree')
    ng.interface.new_socket(name="Shader", in_out='INPUT', socket_type='NodeSocketShader')
    ng.interface.new_socket(name="Shader", in_out='OUTPUT', socket_type='NodeSocketShader')
    gi, go = node(ng, 'NodeGroupInput'), node(ng, 'NodeGroupOutput')
    cam = node(ng, 'ShaderNodeCameraData')
    m1 = node(ng, 'ShaderNodeMath', operation='MULTIPLY')
    link(ng, cam.outputs['View Distance'], m1.inputs[0])
    m1.inputs[1].default_value = -1.0 / FOG_DIST
    m2 = node(ng, 'ShaderNodeMath', operation='EXPONENT')
    link(ng, m1.outputs[0], m2.inputs[0])
    m3 = node(ng, 'ShaderNodeMath', operation='SUBTRACT')
    m3.inputs[0].default_value = 1.0
    link(ng, m2.outputs[0], m3.inputs[1])
    em = node(ng, 'ShaderNodeEmission')
    em.inputs['Color'].default_value = (*FOG, 1)
    em.inputs['Strength'].default_value = 1.0
    mix = node(ng, 'ShaderNodeMixShader')
    link(ng, m3.outputs[0], mix.inputs[0])
    link(ng, gi.outputs[0], mix.inputs[1])
    link(ng, em.outputs[0], mix.inputs[2])
    link(ng, mix.outputs[0], go.inputs[0])
    return ng


HAZE = make_haze()


def material(name, color, rough=0.5, metal=0.0, emit=None, strength=0.0, haze=False, var=0.0, var_scale=1.0):
    m = bpy.data.materials.new(name)
    if m.node_tree is None:
        m.use_nodes = True
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.bl_idname == 'ShaderNodeBsdfPrincipled')
    out = next(n for n in nt.nodes if n.bl_idname == 'ShaderNodeOutputMaterial')
    if var:
        tc = node(nt, 'ShaderNodeTexCoord')
        nz = node(nt, 'ShaderNodeTexNoise')
        nz.inputs['Scale'].default_value = var_scale
        nz.inputs['Detail'].default_value = 6.0
        link(nt, tc.outputs['Object'], nz.inputs['Vector'])
        mx = node(nt, 'ShaderNodeMix', data_type='RGBA')
        fs = next(s for s in mx.inputs if s.name == 'Factor' and s.type == 'VALUE')
        sa = next(s for s in mx.inputs if s.name == 'A' and s.type == 'RGBA')
        sb = next(s for s in mx.inputs if s.name == 'B' and s.type == 'RGBA')
        link(nt, nz.outputs['Fac'], fs)
        sa.default_value = (*[c * (1 - var) for c in color], 1)
        sb.default_value = (*[min(1, c * (1 + var)) for c in color], 1)
        link(nt, next(s for s in mx.outputs if s.type == 'RGBA'), b.inputs['Base Color'])
    else:
        b.inputs['Base Color'].default_value = (*color, 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    if emit:
        b.inputs['Emission Color'].default_value = (*emit, 1)
        b.inputs['Emission Strength'].default_value = strength
    if haze:
        g = node(nt, 'ShaderNodeGroup')
        g.node_tree = HAZE
        link(nt, b.outputs[0], g.inputs[0])
        link(nt, g.outputs[0], out.inputs['Surface'])
    return m


def mesh_obj(name, verts, faces, mat=None, smooth=False):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], faces)
    me.update()
    if smooth:
        me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    ob = bpy.data.objects.new(name, me)
    COL.objects.link(ob)
    if mat:
        me.materials.append(mat)
    return ob


BOX_F = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]


def box(name, center, size, mat, rot=(0, 0, 0)):
    sx, sy, sz = (s / 2 for s in size)
    v = [(-sx, -sy, -sz), (sx, -sy, -sz), (sx, sy, -sz), (-sx, sy, -sz),
         (-sx, -sy, sz), (sx, -sy, sz), (sx, sy, sz), (-sx, sy, sz)]
    ob = mesh_obj(name, v, BOX_F, mat)
    ob.location = center
    ob.rotation_euler = rot
    return ob


def cyl(name, p0, p1, r, mat, seg=12):
    p0, p1 = Vector(p0), Vector(p1)
    ax = p1 - p0
    v = [(r * math.cos(2 * math.pi * i / seg), r * math.sin(2 * math.pi * i / seg), 0) for i in range(seg)]
    v += [(x, y, ax.length) for (x, y, _) in v]
    f = [(i, (i + 1) % seg, seg + (i + 1) % seg, seg + i) for i in range(seg)]
    f += [tuple(range(seg - 1, -1, -1)), tuple(range(seg, 2 * seg))]
    ob = mesh_obj(name, v, f, mat, smooth=True)
    ob.location = p0
    ob.rotation_mode = 'QUATERNION'
    ob.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(ax.normalized())
    return ob


def sphere(name, c, r, mat, scale=(1, 1, 1)):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=10, radius=r)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    ob = bpy.data.objects.new(name, me)
    COL.objects.link(ob)
    me.materials.append(mat)
    ob.location = c
    ob.scale = scale
    return ob


# ------------------------------------------------------------------ materials
M_FLOOR = material("Deck", (0.035, 0.038, 0.042), 0.6, var=0.2, var_scale=2)
M_WALL = material("BulkheadGrey", (0.16, 0.17, 0.18), 0.55, var=0.08, var_scale=3)
M_CEIL = material("Overhead", (0.12, 0.125, 0.13), 0.7)
M_FRAME = material("WindowFrame", (0.05, 0.052, 0.056), 0.45, metal=0.4)
M_CONSOLE = material("Console", (0.06, 0.065, 0.07), 0.45, metal=0.2)
M_SCREEN_G = material("ScreenGreen", (0, 0, 0), 0.3, emit=(0.25, 0.9, 0.55), strength=3.0)
M_SCREEN_B = material("ScreenBlue", (0, 0, 0), 0.3, emit=(0.35, 0.6, 1.0), strength=3.0)
M_SCREEN_A = material("ScreenAmber", (0, 0, 0), 0.3, emit=(1.0, 0.55, 0.15), strength=1.0)
M_SCREEN_DIM = material("ScreenDim", (0, 0, 0), 0.3, emit=(0.4, 0.6, 0.9), strength=0.6)
M_STRIP = material("CeilingLight", (0, 0, 0), 0.5, emit=(0.85, 0.9, 1.0), strength=0.5)
M_UNIFORM = material("Uniform", (0.025, 0.03, 0.045), 0.8)
M_SKIN = material("Hair", (0.04, 0.032, 0.028), 0.6)   # we only see the backs of heads
M_CHAIR = material("Chair", (0.03, 0.03, 0.03), 0.6)
M_SEA = material("Sea", (0.008, 0.014, 0.018), 0.07, haze=True)
M_ICE = material("IceWall", (0.62, 0.77, 0.87), 0.3, haze=True, var=0.25, var_scale=0.015)
M_ICE_DARK = material("IceShadow", (0.18, 0.26, 0.32), 0.4, haze=True)
M_TUNNEL = material("TunnelDark", (0.002, 0.003, 0.004), 1.0, haze=False)
M_FLOE = material("IceFloe", (0.80, 0.86, 0.90), 0.5, haze=True)
M_SHIP = material("ShipGrey", (0.13, 0.14, 0.15), 0.55, haze=True, var=0.1, var_scale=0.5)

# ice wall: a little subsurface glow so it reads as ice, not chalk
_b = next(n for n in M_ICE.node_tree.nodes if n.bl_idname == 'ShaderNodeBsdfPrincipled')
_b.inputs['Subsurface Weight'].default_value = 0.15
_b.inputs['Subsurface Radius'].default_value = (1.0, 2.0, 3.0)
_nt = M_ICE.node_tree
_ao = node(_nt, 'ShaderNodeAmbientOcclusion', samples=8)
_ao.inputs['Distance'].default_value = 10.0
_inv = node(_nt, 'ShaderNodeMath', operation='SUBTRACT')
_inv.inputs[0].default_value = 1.0
link(_nt, _ao.outputs['AO'], _inv.inputs[1])
_mx = node(_nt, 'ShaderNodeMix', data_type='RGBA')
link(_nt, _inv.outputs[0], next(x for x in _mx.inputs if x.name == 'Factor' and x.type == 'VALUE'))
link(_nt, _b.inputs['Base Color'].links[0].from_socket, next(x for x in _mx.inputs if x.name == 'A' and x.type == 'RGBA'))
next(x for x in _mx.inputs if x.name == 'B' and x.type == 'RGBA').default_value = (0.06, 0.2, 0.33, 1)
link(_nt, next(x for x in _mx.outputs if x.type == 'RGBA'), _b.inputs['Base Color'])

# ------------------------------------------------------------------ the bridge
W, D, H = 15.0, 9.0, 3.1                 # interior width, depth, height
FRONT = 2.0                              # front window line (y)
BACK = FRONT - D
box("Floor", (0, (FRONT + BACK) / 2, -0.05), (W, D, 0.1), M_FLOOR)
box("Overhead", (0, (FRONT + BACK) / 2, H + 0.05), (W, D + 1.2, 0.1), M_CEIL)
box("BackWall", (0, BACK - 0.05, H / 2), (W, 0.1, H), M_WALL)
for sx in (-1, 1):
    box(f"SideWall{sx}", (sx * (W / 2 + 0.05), (FRONT + BACK) / 2, H / 2), (0.1, D, H), M_WALL)
    # small side windows near the front
    box(f"SideWinFrame{sx}", (sx * (W / 2 - 0.02), FRONT - 1.6, 1.9), (0.06, 1.4, 1.1), M_FRAME)
box("BackDoor", (4.5, BACK + 0.02, 1.0), (1.0, 0.06, 2.0), M_FRAME)

# front: sill wall, slanted window band, header
box("SillWall", (0, FRONT, 0.55), (W, 0.25, 1.1), M_WALL)
box("Header", (0, FRONT + 0.25, H - 0.2), (W, 0.4, 0.4), M_WALL)
tilt = math.radians(14)                   # bridge windows lean outward at the top
win_bot, win_top = 1.1, H - 0.4
n_panes = 7
pane_w = W / n_panes
for i in range(n_panes + 1):
    x = -W / 2 + i * pane_w
    hgt = win_top - win_bot
    box(f"Mullion{i}", (x, FRONT + 0.06 + math.tan(tilt) * hgt / 2, (win_bot + win_top) / 2),
        (0.14, 0.12, hgt / math.cos(tilt)), M_FRAME, rot=(-tilt, 0, 0))
box("WindowSillFrame", (0, FRONT + 0.05, win_bot), (W, 0.25, 0.08), M_FRAME)
box("WindowTopFrame", (0, FRONT + 0.06 + math.tan(tilt) * (win_top - win_bot), win_top), (W, 0.25, 0.08), M_FRAME)
# wipers on two panes, a classic bridge detail
for x in (-pane_w * 0.5, pane_w * 1.5):
    cyl(f"Wiper{x:.0f}", (x - 0.35, FRONT + 0.1, win_bot + 0.1), (x + 0.15, FRONT + 0.2, win_bot + 0.75), 0.012, M_FRAME, 6)

# console row under the windows, angled screens
for i in range(6):
    x = -W / 2 + 1.4 + i * 2.45
    box(f"Console{i}", (x, FRONT - 0.55, 0.5), (2.2, 0.8, 1.0), M_CONSOLE)
    scr = [M_SCREEN_G, M_SCREEN_B, M_SCREEN_A][i % 3]
    for j, dx in enumerate((-0.5, 0.5)):
        box(f"Screen{i}{j}", (x + dx, FRONT - 0.72, 1.08), (0.8, 0.05, 0.42), scr, rot=(math.radians(-25), 0, 0))
# chart table, captain's chair, a pillar
box("ChartTable", (-3.5, BACK + 2.6, 0.48), (1.8, 1.2, 0.96), M_CONSOLE)
box("ChartGlow", (-3.5, BACK + 2.6, 0.97), (1.6, 1.0, 0.02), M_SCREEN_B)
box("ChairSeat", (0.6, -2.4, 0.55), (0.7, 0.7, 0.15), M_CHAIR)
box("ChairBack", (0.6, -2.72, 1.0), (0.7, 0.12, 0.85), M_CHAIR)
cyl("ChairPost", (0.6, -2.4, 0), (0.6, -2.4, 0.5), 0.07, M_FRAME)
for x in (-6.0, 6.0):
    box(f"Pillar{x:.0f}", (x, BACK + 3.0, H / 2), (0.3, 0.3, H), M_WALL)
# overhead light strips and cable trays
for x in (-4.5, 0.0, 4.5):
    box(f"LightStrip{x:.0f}", (x, (FRONT + BACK) / 2, H - 0.02), (0.18, 6.0, 0.03), M_STRIP)
box("CableTray", (0, FRONT - 1.4, H - 0.25), (W - 1.0, 0.3, 0.12), M_FRAME)
for i, x in enumerate((-3.0, 5.4)):
    box(f"OverheadMonitor{i}", (x, FRONT - 1.0, H - 0.6), (1.1, 0.08, 0.6), M_CONSOLE, rot=(math.radians(15), 0, 0))
    box(f"OverheadMonitorScr{i}", (x, FRONT - 1.05, H - 0.6), (1.0, 0.02, 0.52), M_SCREEN_DIM, rot=(math.radians(15), 0, 0))


# ------------------------------------------------------------------ crew
def person(name, x, y, heading_deg=0.0, pose="stand", height=1.78):
    """A simple mannequin. heading 0 = facing +Y (out of the windows)."""
    s = height / 1.78
    parts = []
    for side in (-1, 1):
        parts.append(cyl(f"{name}Leg{side}", (side * 0.1, 0, 0), (side * 0.1, 0, 0.86 * s), 0.075 * s, M_UNIFORM))
    parts.append(sphere(f"{name}Torso", (0, 0, 1.17 * s), 0.3 * s, M_UNIFORM, scale=(0.72, 0.45, 1.05)))
    parts.append(sphere(f"{name}Head", (0, 0.01, 1.63 * s), 0.11 * s, M_SKIN, scale=(0.9, 1.0, 1.15)))
    parts.append(cyl(f"{name}Cap", (0, 0.0, 1.71 * s), (0, 0.0, 1.78 * s), 0.12 * s, M_UNIFORM))
    sh = 1.43 * s
    for side in (-1, 1):
        start = (side * 0.22 * s, 0, sh)
        if pose == "binoculars":
            end = (side * 0.07 * s, 0.25 * s, 1.6 * s)
        elif pose == "point" and side == 1:
            end = (0.35 * s, 0.6 * s, 1.75 * s)
        elif pose == "lean":
            end = (side * 0.28 * s, 0.35 * s, 1.0 * s)
        else:
            end = (side * 0.26 * s, 0.04 * s, 0.86 * s)
        parts.append(cyl(f"{name}Arm{side}", start, end, 0.05 * s, M_UNIFORM))
    if pose == "binoculars":
        parts.append(box(f"{name}Binos", (0, 0.28 * s, 1.62 * s), (0.17 * s, 0.14 * s, 0.07 * s), M_CHAIR))
    root = bpy.data.objects.new(name, None)
    COL.objects.link(root)
    for p in parts:
        p.parent = root
    root.location = (x, y, 0)
    root.rotation_euler = (0, 0, math.radians(heading_deg))
    return root


person("Officer1", -2.2, FRONT - 1.35, 4, "binoculars", 1.80)
person("Officer2", 0.45, FRONT - 1.3, -3, "point", 1.76)
person("Officer3", 2.75, FRONT - 1.4, -6, "stand", 1.74)
person("Helmsman", -5.0, FRONT - 1.2, 0, "lean", 1.72)
person("Captain", 1.2, -1.6, 0, "stand", 1.82)

# ------------------------------------------------------------------ outside: bow, sea, floes, ice wall
bow = [(-9, 3, -2.5), (9, 3, -2.5), (6, 60, -6.5), (0, 78, -6.0), (-6, 60, -6.5)]
mesh_obj("Foredeck", bow, [(0, 1, 2, 3, 4)], M_SHIP)
box("Gun", (0, 30, -4.6), (3.0, 4.0, 2.0), M_SHIP)
cyl("GunBarrel", (0, 32, -4.3), (0, 40, -3.9), 0.18, M_SHIP)
mesh_obj("Sea", [(-30000, -30000, SEA_Z), (30000, -30000, SEA_Z), (30000, 30000, SEA_Z), (-30000, 30000, SEA_Z)],
         [(0, 1, 2, 3)], M_SEA)
_b = next(n for n in M_SEA.node_tree.nodes if n.bl_idname == 'ShaderNodeBsdfPrincipled')
_nt = M_SEA.node_tree
_tc = node(_nt, 'ShaderNodeTexCoord')
_nz = node(_nt, 'ShaderNodeTexNoise')
_nz.inputs['Scale'].default_value = 0.08
_nz.inputs['Detail'].default_value = 8.0
link(_nt, _tc.outputs['Object'], _nz.inputs['Vector'])
_bump = node(_nt, 'ShaderNodeBump')
_bump.inputs['Strength'].default_value = 0.35
link(_nt, _nz.outputs['Fac'], _bump.inputs['Height'])
link(_nt, _bump.outputs['Normal'], _b.inputs['Normal'])

for k in range(70):                                 # drifting ice floes between ship and wall
    y = random.uniform(120, WALL_Y - 40)
    x = random.uniform(-0.9, 0.9) * (y * 0.9)
    s = random.uniform(3, 18) * (0.5 + y / WALL_Y)
    box(f"Floe{k}", (x, y, SEA_Z + 0.3), (s, s * random.uniform(0.5, 1.2), random.uniform(0.6, 2.0)),
        M_FLOE, rot=(0, 0, random.uniform(0, 3.14)))


CREVASSES = [random.uniform(-1000, 1000) for _ in range(40)]
CREVASSES = [c for c in CREVASSES if abs(c) > GATE_W / 2 + 15]


def ice_wall():
    """A 2 km cliff of ice across the horizon, displaced with noise, with a sharp rectangular cut."""
    nx, nz = 320, 90
    x0, x1 = -1100.0, 1100.0
    verts, faces, index = [], [], {}
    for j in range(nz + 1):
        for i in range(nx + 1):
            x = x0 + (x1 - x0) * i / nx
            top = WALL_H + 22 * noise.fractal(Vector((x / 180, 3.1, 0.0)), 1.0, 2.0, 4)
            z = SEA_Z + (top + 0) * (j / nz)
            p = Vector((x / 70, z / 30, 0.7))
            d = 12 * noise.fractal(p, 1.0, 2.0, 5) + 5 * noise.noise(Vector((x / 6, z / 60, 1.3)))
            d += 0.6 * math.sin(z / 3.5 + 2 * noise.noise(Vector((x / 90, z / 20, 4.0))))   # strata
            d += 5.0 * math.sin(x / 14.0 + 3 * noise.noise(Vector((x / 40, z / 80, 2.0))))   # vertical fluting
            for xk in CREVASSES:
                d -= 9.0 * math.exp(-((x - xk) / 2.5) ** 2)                                # crevasses
            y = WALL_Y + 0.00018 * x * x + d                                        # slight curve away
            gate = abs(x) < GATE_W / 2 and z < SEA_Z + GATE_H
            if abs(x) < GATE_W / 2 + 6 and z < SEA_Z + GATE_H + 6:
                y = WALL_Y + 0.00018 * x * x          # the cut face is planed smooth around the entrance
            index[(i, j)] = len(verts)
            verts.append((x, y, z))
    for j in range(nz):
        for i in range(nx):
            xc = x0 + (x1 - x0) * (i + 0.5) / nx
            zc = SEA_Z + (WALL_H) * (j + 0.5) / nz
            if abs(xc) < GATE_W / 2 and zc < SEA_Z + GATE_H:
                continue
            faces.append((index[(i, j)], index[(i + 1, j)], index[(i + 1, j + 1)], index[(i, j + 1)]))
    ob = mesh_obj("IceWall", verts, faces, M_ICE, smooth=True)
    # the tunnel behind the cut: dark, deep, straight-sided
    gx, gz0, gz1 = GATE_W / 2 + 0.4, SEA_Z, SEA_Z + GATE_H
    y0 = WALL_Y - 2
    y1 = WALL_Y + 220
    v = [(-gx, y0, gz0), (gx, y0, gz0), (gx, y1, gz0), (-gx, y1, gz0),
         (-gx, y0, gz1), (gx, y0, gz1), (gx, y1, gz1), (-gx, y1, gz1)]
    mesh_obj("Tunnel", v, [(0, 3, 7, 4), (1, 5, 6, 2), (4, 7, 6, 5), (3, 2, 6, 7), (0, 1, 2, 3)], M_TUNNEL)
    # crisp frame of the cut so it reads as made, not natural
    for side in (-1, 1):
        box(f"GateJamb{side}", (side * (GATE_W / 2 + 0.8), WALL_Y - 0.5, SEA_Z + GATE_H / 2), (1.6, 3.0, GATE_H), M_ICE_DARK)
    box("GateLintel", (0, WALL_Y - 0.5, SEA_Z + GATE_H + 0.8), (GATE_W + 3.2, 3.0, 1.6), M_ICE_DARK)
    return ob


ice_wall()

# ------------------------------------------------------------------ world and light: overcast polar day
w = bpy.data.worlds.new("Overcast")
SC.world = w
nt = w.node_tree
nt.nodes.clear()
out = node(nt, 'ShaderNodeOutputWorld')
bg = node(nt, 'ShaderNodeBackground')
tc = node(nt, 'ShaderNodeTexCoord')
sep = node(nt, 'ShaderNodeSeparateXYZ')
link(nt, tc.outputs['Generated'], sep.inputs[0])
ramp = node(nt, 'ShaderNodeValToRGB')
ramp.color_ramp.elements[0].position = 0.0
ramp.color_ramp.elements[0].color = (*FOG, 1)
ramp.color_ramp.elements[1].position = 0.45
ramp.color_ramp.elements[1].color = (0.42, 0.47, 0.53, 1)
link(nt, sep.outputs['Z'], ramp.inputs['Fac'])
link(nt, ramp.outputs['Color'], bg.inputs['Color'])
bg.inputs['Strength'].default_value = 1.0
link(nt, bg.outputs[0], out.inputs['Surface'])

sun_d = bpy.data.lights.new("SoftSun", 'SUN')
sun_d.energy = 2.2
sun_d.angle = math.radians(12)
sun_d.color = (0.92, 0.95, 1.0)
sun = bpy.data.objects.new("SoftSun", sun_d)
COL.objects.link(sun)
sun.rotation_euler = (math.radians(58), 0, math.radians(25))
fill_d = bpy.data.lights.new("BridgeFill", 'AREA')
fill_d.energy = 40
fill_d.size = 6
fill_d.color = (0.8, 0.88, 1.0)
fill = bpy.data.objects.new("BridgeFill", fill_d)
COL.objects.link(fill)
fill.location = (0, -2.5, H - 0.15)

# ------------------------------------------------------------------ cameras
def camera(name, loc, target, lens):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.sensor_width = 36
    cd.clip_start = 0.05
    cd.clip_end = 60000
    cd.dof.use_dof = True
    cd.dof.aperture_fstop = 4.0
    ob = bpy.data.objects.new(name, cd)
    COL.objects.link(ob)
    ob.location = loc
    ob.rotation_mode = 'QUATERNION'
    ob.rotation_quaternion = (Vector(target) - Vector(loc)).normalized().to_track_quat('-Z', 'Y')
    return ob


CAMS = {
    "wide": camera("CamWide", (1.6, BACK + 0.9, 1.75), (-0.6, 60.0, 3.5), 28),
    "ots": camera("CamOTS", (2.1, -1.6, 1.70), (-0.4, 300.0, 15.0), 35),
}
CAMS["wide"].data.dof.focus_distance = 7.5
CAMS["ots"].data.dof.focus_distance = 600.0
CAMS["ots"].data.dof.aperture_fstop = 2.8

# ------------------------------------------------------------------ render
rx, ry = (int(v) for v in ARGS.res.lower().split("x"))
SC.render.resolution_x, SC.render.resolution_y = rx, ry
SC.render.engine = 'CYCLES'
cy = SC.cycles
cy.device = 'CPU'
cy.samples = ARGS.samples
cy.use_adaptive_sampling = True
cy.adaptive_threshold = 0.03
cy.use_denoising = True
try:
    cy.denoiser = 'OPENIMAGEDENOISE'
except TypeError:
    pass
cy.max_bounces = 6
cy.diffuse_bounces = 3
cy.glossy_bounces = 3
cy.transmission_bounces = 2
cy.sample_clamp_indirect = 3.0
SC.view_settings.view_transform = 'AgX'
try:
    SC.view_settings.look = 'AgX - Medium High Contrast'
except TypeError:
    pass
SC.view_settings.exposure = 0.0
SC.render.image_settings.file_format = 'PNG'
SC.camera = CAMS["wide"]

if ARGS.save_blend:
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(ARGS.save_blend))

os.makedirs(ARGS.out, exist_ok=True)
for name in (CAMS if ARGS.shot == "all" else [ARGS.shot]):
    SC.camera = CAMS[name]
    SC.render.filepath = os.path.join(ARGS.out, f"bridge_{name}.png")
    bpy.ops.render.render(write_still=True)
    print("[icewall] rendered", name, flush=True)
