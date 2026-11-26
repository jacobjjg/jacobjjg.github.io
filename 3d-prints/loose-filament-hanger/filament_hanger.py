#!/usr/bin/env python3
"""
Hanging holder for LOOSE filament  --  parametric generator.

A one-piece strap, shaped like a garden-hose hanger: the top curls over a closet
rod, the bottom is a trough with a rounded saddle that a loose coil of filament
drapes over.  A wall at the back and a taller-than-usual wall at the front keep
the loops from sliding off, and two small holes in the front wall park the
loose end.

    pip install numpy shapely mapbox-earcut manifold3d
    python3 filament_hanger.py                 # writes filament_hanger.stl next to this file
    python3 filament_hanger.py --rod-d 32      # any parameter below can be overridden

All dimensions are millimetres.  The part is modelled lying on its side, exactly
as it should be printed: the strap profile is in XY and the strap's width is
along Z.  In use, +Y is "up" and the closet rod runs along Z.
"""
import argparse
import math
import os
import struct

import numpy as np
import mapbox_earcut as earcut
import manifold3d as m3
from shapely.geometry import LineString, Polygon

PARAMS = dict(
    # --- what it has to fit -------------------------------------------------
    rod_d=35.0,           # largest closet-rod diameter it should hang on (1-3/8 in)
    rod_clear=5.0,        # the hook is rod_d + rod_clear across inside
    coil_thick=50.0,      # tallest stack of windings to leave room for (a full 1 kg coil)
    channel=72.0,         # room between the back and front walls (coil width + slack)
    saddle_r=40.0,        # radius of the hump the coil rests on (suits coils 80 mm+ inside)
    # --- the part itself ----------------------------------------------------
    width=50.0,           # width of the strap = how wide the saddle and the hook are
    wall=7.0,             # thickness of the strap
    front_h=42.0,         # height of the front wall above the trough floor
    front_lean_deg=8.0,   # front wall leans outward so a coil is easy to drop in
    floor_slope_deg=4.0,  # floor rises toward the front so the coil settles to the back
    hook_x=36.0,          # rod centre, measured from the back wall: over the coil's weight
    tip_deg=10.0,         # where the hook tip ends (0 = level with the hook centre)
    ridge_drop=11.5,      # how far the strap dips behind the rod, to keep the rod seated
    lift_clear=4.0,       # spare room for the rod to pass between hook tip and a full coil
    chamfer=1.2,          # 45-degree chamfer on both faces
    end_hole_d=2.8,       # holes in the front wall for the filament's loose end (0 = none)
    r_inside=6.0,         # inside corner radius of the trough
)

ARC_STEP = 0.5  # target facet length on curves, mm


def derive(p):
    """Everything that follows from the parameters."""
    d = dict(p)
    h = d["h"] = p["wall"] / 2.0
    d["ri"] = (p["rod_d"] + p["rod_clear"]) / 2.0            # inside radius of the hook
    d["rc"] = d["ri"] + h                                     # hook centreline radius
    d["slope"] = math.radians(p["floor_slope_deg"])
    d["lean"] = math.radians(p["front_lean_deg"])
    d["edge"] = p["chamfer"] + 0.3                            # saddle stops just short of the chamfer
    chord = p["width"] - 2 * d["edge"]
    d["phi"] = math.asin(min(1.0, chord / 2.0 / p["saddle_r"]))
    assert math.degrees(d["phi"]) <= 45.0, "saddle would overhang more than 45 deg; raise saddle_r"
    d["hump_h"] = p["saddle_r"] * (1 - math.cos(d["phi"]))
    # Top of a full coil sitting on the saddle ...
    d["coil_top"] = d["hump_h"] + p["coil_thick"] + math.tan(d["slope"]) * p["channel"] / 2.0
    # ... and the rod has to pass between that and the hook tip, so the holder can
    # be lifted on and off the rod with the filament still on it.
    tip_bottom = d["coil_top"] + p["rod_d"] + p["lift_clear"]
    d["hook_y"] = math.ceil(tip_bottom - d["rc"] * math.sin(math.radians(p["tip_deg"])) + h)
    d["arm_y"] = d["hook_y"] + d["ri"] - p["ridge_drop"] + h  # centreline of the top strap
    return d


def _arc(c, r, a0, a1):
    n = max(2, math.ceil(abs(a1 - a0) * r / ARC_STEP))
    a = np.linspace(a0, a1, n + 1)
    return np.column_stack([c[0] + r * np.cos(a), c[1] + r * np.sin(a)])


def fillet_polyline(verts, radii):
    """Polyline through `verts` with each interior corner replaced by a tangent arc."""
    verts = [np.asarray(v, float) for v in verts]
    out = [verts[0][None, :]]
    for i in range(1, len(verts) - 1):
        d1 = verts[i] - verts[i - 1]
        d2 = verts[i + 1] - verts[i]
        d1, d2 = d1 / np.linalg.norm(d1), d2 / np.linalg.norm(d2)
        cross = d1[0] * d2[1] - d1[1] * d2[0]
        turn = math.atan2(cross, float(np.dot(d1, d2)))
        r = radii[i - 1]
        t = r * math.tan(abs(turn) / 2)
        sgn = 1.0 if turn > 0 else -1.0
        centre = verts[i] - d1 * t + sgn * r * np.array([-d1[1], d1[0]])
        a0 = math.atan2(*(verts[i] - d1 * t - centre)[::-1])
        out.append(_arc(centre, r, a0, a0 + turn))
    out.append(verts[-1][None, :])
    return np.vstack(out)


def centreline(d):
    """Path the strap follows, from the top of the front wall round to the hook tip.
    x forward (away from the back wall), y up; origin = floor level at the back wall."""
    h, th, al = d["h"], d["slope"], d["lean"]
    u = np.array([math.cos(th), math.sin(th)])                 # along the floor, toward the front
    nfl = np.array([-math.sin(th), math.cos(th)])              # floor normal (up)
    f = np.array([math.sin(al), math.cos(al)])                 # up the front wall
    nf = np.array([math.cos(al), -math.sin(al)])               # out of the front wall
    base = u * (d["channel"] / math.cos(th))                   # floor meets front wall (inside face)
    q0 = base + h * nf                                         # a point on the front wall's centreline
    p0 = -h * nfl                                              # a point on the floor's centreline
    # corner 1: front wall / floor
    lam = np.linalg.solve(np.column_stack([u, -f]), q0 - p0)
    v1 = p0 + lam[0] * u
    tip_tau = (d["front_h"] - h - (q0[1] - base[1])) / math.cos(al)
    top = q0 + tip_tau * f
    # corner 2: floor / back wall, corner 3: back wall / top strap
    v2 = p0 + ((-h - p0[0]) / u[0]) * u
    v3 = np.array([-h, d["arm_y"]])
    # the dip behind the rod: an arc that turns the strap up into the hook
    H = np.array([d["hook_x"], d["hook_y"]])
    rf = d["r_inside"]
    fy = d["arm_y"] + rf
    F = np.array([H[0] - math.sqrt((d["rc"] + rf) ** 2 - (fy - H[1]) ** 2), fy])
    a1 = np.array([F[0], d["arm_y"]])
    assert a1[0] > v3[0] + 10.5, "hook is too close to the back wall"
    rin = d["r_inside"] + h
    path = fillet_polyline([top, v1, v2, v3, a1], [rin, rin, rin + 0.5])
    j = math.atan2(H[1] - F[1], H[0] - F[0])
    dip = _arc(F, rf, -math.pi / 2, j)
    hook = _arc(H, d["rc"], j + math.pi, math.radians(d["tip_deg"]))
    d["front_top"] = top
    d["front_base"] = base
    return np.vstack([path, dip[1:], hook[1:]])


def profile(p):
    d = derive(p)
    line = LineString(centreline(d))
    body = line.buffer(d["h"], quad_segs=10, cap_style="round", join_style="round")
    assert body.geom_type == "Polygon" and not body.interiors, "strap profile overlaps itself"
    return body, d


def clean_ring(poly, min_seg=0.05):
    """Counter-clockwise vertex loop without duplicate or collinear points."""
    poly = poly.simplify(0.002, preserve_topology=True)
    pts = np.array(poly.exterior.coords)[:-1]
    if not Polygon(pts).exterior.is_ccw:
        pts = pts[::-1]
    keep = [pts[0]]
    for q in pts[1:]:
        if np.linalg.norm(q - keep[-1]) >= min_seg:
            keep.append(q)
    if np.linalg.norm(keep[0] - keep[-1]) < min_seg:
        keep.pop()
    return np.array(keep)


def inset_ring(pts, dist):
    """Offset every vertex inward by `dist` (exact parallel offset, mitred), keeping
    the vertex count so the chamfer can be meshed as a clean strip of quads."""
    prev, nxt = np.roll(pts, 1, axis=0), np.roll(pts, -1, axis=0)
    e1, e2 = pts - prev, nxt - pts
    e1 /= np.linalg.norm(e1, axis=1)[:, None]
    e2 /= np.linalg.norm(e2, axis=1)[:, None]
    n1 = np.stack([-e1[:, 1], e1[:, 0]], axis=1)       # inward normals of a CCW loop
    n2 = np.stack([-e2[:, 1], e2[:, 0]], axis=1)
    b = n1 + n2
    b /= np.linalg.norm(b, axis=1)[:, None]
    cos_half = np.einsum("ij,ij->i", b, n1)
    return pts + b * (dist / cos_half)[:, None]


def strap_mesh(ring, width, c):
    """The strap profile extruded to `width`, with a chamfer on both faces."""
    inner = inset_ring(ring, c)
    ip = Polygon(inner)
    assert ip.is_valid and ip.is_simple, "chamfer too large for the smallest radius"
    n = len(ring)
    lift = lambda xy, z: np.column_stack([xy, np.full(len(xy), z)])
    verts = np.vstack([lift(inner, 0.0), lift(ring, c), lift(ring, width - c), lift(inner, width)])
    tris = []
    cap = earcut.triangulate_float64(inner, np.array([n], dtype=np.uint32)).reshape(-1, 3)
    tris += [(a, cc, b) for a, b, cc in cap]                           # face on the bed
    tris += [(a + 3 * n, b + 3 * n, cc + 3 * n) for a, b, cc in cap]   # top face
    for lo, hi in ((0, n), (n, 2 * n), (2 * n, 3 * n)):                # chamfer, wall, chamfer
        for i in range(n):
            j = (i + 1) % n
            tris.append((lo + i, lo + j, hi + j))
            tris.append((lo + i, hi + j, hi + i))
    return verts, np.array(tris, dtype=np.int64)


def to_manifold(verts, tris):
    return m3.Manifold(m3.Mesh(np.ascontiguousarray(verts, dtype=np.float32),
                               np.ascontiguousarray(tris, dtype=np.uint32)))


def saddle(d):
    """The hump on the trough floor: a slice of a cylinder running front to back."""
    W, c, R, phi = d["width"], d["edge"], d["saddle_r"], d["phi"]
    embed = 1.0
    ang = np.linspace(math.pi / 2 - phi, math.pi / 2 + phi, max(8, math.ceil(2 * phi * R / ARC_STEP)) + 1)
    # cross-section in (height above floor, position across the strap)
    sink = 0.05                                                # arc ends just under the floor surface
    arc = np.column_stack([R * np.sin(ang) - R * math.cos(phi) - sink, W / 2 + R * np.cos(ang)])
    # below floor level the section tucks inward, so only the arc ever shows
    sec = np.vstack([[-embed, W - c - embed], arc, [-embed, c + embed]])
    if Polygon(sec).exterior.is_ccw is False:
        sec = sec[::-1]
    th = d["slope"]
    x0 = -1.0                                                  # start inside the back wall
    x1 = d["front_base"][0] + d["hump_h"] * math.tan(d["lean"]) + 1.0   # end inside the front wall
    body = m3.Manifold.extrude(m3.CrossSection([sec]), x1 - x0)
    # local (height, across, along)  ->  print (X along, Y up + floor slope, Z across)
    s = math.tan(th)
    return body.transform(np.array([[0.0, 0.0, 1.0, x0],
                                    [1.0, 0.0, s, s * x0],
                                    [0.0, 1.0, 0.0, 0.0]]))


def end_holes(d):
    """Two small holes through the front wall, near its top corners."""
    if d["end_hole_d"] <= 0:
        return []
    al = d["lean"]
    f = np.array([math.sin(al), math.cos(al), 0.0])            # up the wall
    nf = np.array([math.cos(al), -math.sin(al), 0.0])          # through the wall
    ez = np.array([0.0, 0.0, 1.0])
    e2 = np.cross(nf, ez)
    centre = np.append(d["front_top"], 0.0) - f * 6.0
    out = []
    for z in (10.0, d["width"] - 10.0):
        cyl = m3.Manifold.cylinder(d["wall"] + 6.0, d["end_hole_d"] / 2.0, circular_segments=24, center=True)
        o = centre + ez * z
        out.append(cyl.transform(np.column_stack([ez, e2, nf, o])))
    return out


def build(p):
    """Returns (manifold solid, outline ring, derived dims).  Solid is in print
    orientation, shifted so it sits in the +X +Y quadrant on Z = 0."""
    poly, d = profile(p)
    ring = clean_ring(poly)
    solid = to_manifold(*strap_mesh(ring, d["width"], d["chamfer"]))
    assert solid.status() == m3.Error.NoError, solid.status()
    solid = solid + saddle(d)
    for hole in end_holes(d):
        solid = solid - hole
    d["origin"] = (float(ring[:, 0].min()), float(ring[:, 1].min()))
    solid = solid.translate([-d["origin"][0], -d["origin"][1], 0.0])
    return solid, ring, d


def write_stl(path, verts, tris, name=b"loose filament hanger"):
    v = verts[tris].astype(np.float32)
    nrm = np.cross(v[:, 1] - v[:, 0], v[:, 2] - v[:, 0])
    ln = np.linalg.norm(nrm, axis=1)
    nrm = (nrm / np.where(ln == 0, 1, ln)[:, None]).astype(np.float32)
    rec = np.zeros(len(tris), dtype=[("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
    rec["n"], rec["v"] = nrm, v
    with open(path, "wb") as fh:
        fh.write(name.ljust(80, b" "))
        fh.write(struct.pack("<I", len(tris)))
        fh.write(rec.tobytes())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    for k, v in PARAMS.items():
        ap.add_argument("--" + k.replace("_", "-"), type=float, default=v, help=f"(default {v:g})")
    ap.add_argument("-o", "--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                         "filament_hanger.stl"))
    a = vars(ap.parse_args())
    out = a.pop("out")
    solid, ring, d = build(a)
    mesh = solid.to_mesh()
    verts, tris = np.asarray(mesh.vert_properties)[:, :3], np.asarray(mesh.tri_verts)
    write_stl(out, verts, tris)
    size = verts.max(axis=0) - verts.min(axis=0)
    print(f"wrote {out}")
    print(f"  size on the bed : {size[0]:.1f} x {size[1]:.1f} mm, {size[2]:.1f} mm tall")
    print(f"  hook opening    : {2 * d['ri']:.0f} mm (rods up to {d['rod_d']:.0f} mm)")
    print(f"  trough          : {d['channel']:.0f} mm between walls, {d['width']:.0f} mm wide, "
          f"front wall {d['front_h']:.0f} mm")
    print(f"  solid volume    : {solid.volume() / 1000:.1f} cm3, {len(tris)} triangles")


if __name__ == "__main__":
    main()
