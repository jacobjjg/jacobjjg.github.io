#!/usr/bin/env python3
"""Measure the registration of every 1952-54 quad against the modern USGS 3DEP DEM.

World mapping under test: scan pixel -> polyconic -> Old Hawaiian lat/lon -> WGS84 with the
NGA 3-parameter shift for Oahu (58,-283,-182 m).  Two independent robust estimates of the
remaining translation are made per sheet, in scan-pixel space (2.03 m/px):

  coast   : DEM shoreline points (elev > 0.3 m boundary)  ->  nearest edge of the map's water tint
  contour : DEM contour points at 40 ft multiples          ->  nearest brown contour ink
            (only on 8-60 % slopes, search radius limited to a third of the contour spacing)

Both use point-to-line ICP with a Tukey biweight, so changed shoreline (fill, dredging,
beach movement) and unmatched contours are rejected as outliers.  The result is
"map content appears at truth + (dx east, dz south)" in metres.  3x3 block estimates give the
within-sheet scatter.  Output: topo_registration.json (applied by topo_common.Sheet).

  python3 topo_02_register.py            measure with no residual applied, write the JSON
  python3 topo_02_register.py --verify   re-measure with the JSON applied (report only)
Requires the cached class layers from topo_classify.py.
"""
import json
import sys
import numpy as np
import cv2
from scipy import ndimage as ndi

from topo_common import *
from topo_classify import dem_on_sheet, neat_mask, load_layer

PX = 2.032
FT40 = 12.192


def icp_translation(P, N, nearest, shape, max_d, c_tukey, iters=6):
    """P (n,2) float (row,col) model points, N unit normals.  nearest = (iy, ix) index maps of the
    nearest target pixel.  Returns t (drow, dcol), n_inliers, cov-based sigma, normal-matrix cond."""
    t = np.zeros(2)
    H, W = shape
    iy, ix = nearest
    for it in range(iters):
        q = np.rint(P + t).astype(np.int64)
        ok = (q[:, 0] >= 0) & (q[:, 0] < H) & (q[:, 1] >= 0) & (q[:, 1] < W)
        qq = q[ok]
        tgt = np.stack([iy[qq[:, 0], qq[:, 1]], ix[qq[:, 0], qq[:, 1]]], 1).astype(np.float64)
        d = tgt - P[ok]                       # displacement model -> target
        n = N[ok]
        near = np.hypot(*(d - t).T) < max_d
        d, n = d[near], n[near]
        if len(d) < 200:
            return None
        r = (n * (d - t)).sum(1)
        w = np.clip(1 - (r / c_tukey) ** 2, 0, None) ** 2
        A = (n[:, :, None] * n[:, None, :] * w[:, None, None]).sum(0)
        b = (n * (w * (n * d).sum(1))[:, None]).sum(0)
        ev = np.linalg.eigvalsh(A)
        if ev[0] < 1e-6 * ev[1] or ev[0] <= 0:
            return None
        t_new = np.linalg.solve(A, b)
        if np.hypot(*(t_new - t)) < 0.01:
            t = t_new
            break
        t = t_new
    r = (n * (d - t)).sum(1)
    w = np.clip(1 - (r / c_tukey) ** 2, 0, None) ** 2
    rms = np.sqrt((w * r * r).sum() / max(w.sum(), 1))
    return dict(t=t, n=int((w > 0).sum()), rms=float(rms * PX), cond=float(ev[1] / ev[0]))


def normals_from(field, pts):
    gy = cv2.Sobel(field, cv2.CV_32F, 0, 1, ksize=3)
    gx = cv2.Sobel(field, cv2.CV_32F, 1, 0, ksize=3)
    g = np.stack([gy[pts[:, 0], pts[:, 1]], gx[pts[:, 0], pts[:, 1]]], 1).astype(np.float64)
    m = np.hypot(g[:, 0], g[:, 1])
    ok = m > 1e-6
    g[ok] /= m[ok, None]
    return g, ok


def nearest_index(mask):
    """Index maps (iy, ix) of the nearest True pixel of mask."""
    _, (iy, ix) = ndi.distance_transform_edt(~mask, return_indices=True)
    return iy.astype(np.int32), ix.astype(np.int32)


def estimates(P, N, nearest, shape, max_d, c, blocks=3, min_block=1500):
    res = icp_translation(P, N, nearest, shape, max_d, c)
    out = dict(all=res, blocks=[])
    H, W = shape
    for bj in range(blocks):
        for bi in range(blocks):
            sel = (P[:, 0] >= bj * H / blocks) & (P[:, 0] < (bj + 1) * H / blocks) & \
                  (P[:, 1] >= bi * W / blocks) & (P[:, 1] < (bi + 1) * W / blocks)
            if sel.sum() < min_block:
                continue
            r = icp_translation(P[sel], N[sel], nearest, shape, max_d, c)
            if r is not None and r['cond'] < 8 and r['n'] >= min_block // 2:
                out['blocks'].append(dict(b=[bj, bi], dx=round(r['t'][1] * PX, 1), dz=round(r['t'][0] * PX, 1), n=r['n']))
    return out


def measure(sheet, corrected):
    name = sheet.name
    e = dem_on_sheet(sheet, 1, corrected=corrected)
    body = neat_mask(sheet, 40)
    k3 = np.ones((3, 3), np.uint8)
    shape = e.shape
    out = {}
    # ---------------- coast
    wm = load_layer(name, 'water_raw')
    wm = cv2.morphologyEx(wm, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    wm = cv2.morphologyEx(wm, cv2.MORPH_OPEN, np.ones((7, 7), np.uint8))
    map_edge = (cv2.morphologyEx(wm, cv2.MORPH_GRADIENT, k3) > 0) & body
    land = (e > 0.3).astype(np.uint8)
    dem_edge = (cv2.morphologyEx(land, cv2.MORPH_GRADIENT, k3) > 0) & body
    out['coast_px'] = int(dem_edge.sum())
    if dem_edge.sum() > 3000 and map_edge.sum() > 3000:
        P = np.argwhere(dem_edge)
        N, ok = normals_from(cv2.GaussianBlur(land.astype(np.float32), (0, 0), 2.0), P)
        P, N = P[ok].astype(np.float64), N[ok]
        near = nearest_index(map_edge)
        out['coast'] = estimates(P, N, near, shape, max_d=30, c=8)
        del near
    # ---------------- contours
    br = (load_layer(name, 'brown') > 0) & body
    es = cv2.GaussianBlur(e, (0, 0), 2.0)
    q = np.floor(es / FT40)
    cont = np.zeros(shape, bool)
    cont[:, 1:] |= q[:, 1:] != q[:, :-1]
    cont[1:, :] |= q[1:, :] != q[:-1, :]
    gy = cv2.Sobel(es, cv2.CV_32F, 0, 1, ksize=3) / 8 / PX
    gx = cv2.Sobel(es, cv2.CV_32F, 1, 0, ksize=3) / 8 / PX
    slope = np.hypot(gx, gy)
    cont &= body & (es > 3) & (slope > 0.08) & (slope < 0.60)
    if cont.sum() > 20000 and br.sum() > 20000:
        P = np.argwhere(cont)
        P = P[::3]
        g = np.stack([gy[P[:, 0], P[:, 1]], gx[P[:, 0], P[:, 1]]], 1).astype(np.float64)
        sl = np.hypot(g[:, 0], g[:, 1])
        N = g / sl[:, None]
        # search radius: a third of the 40 ft contour spacing, 6..14 px
        rad = np.clip(FT40 / sl / PX / 3.0, 6, 14)
        near = nearest_index(br)
        keep = rad >= 6
        out['contour'] = estimates(P[keep].astype(np.float64), N[keep], near, shape, max_d=12, c=6, min_block=6000)
        del near
    return out


def fmt(r):
    if not r or r.get('all') is None:
        return 'n/a'
    a = r['all']
    bl = r['blocks']
    s = f"dx={a['t'][1]*PX:+6.1f} dz={a['t'][0]*PX:+6.1f} m (n={a['n']}, rms {a['rms']:.1f}, cond {a['cond']:.1f})"
    if bl:
        bx = np.array([b['dx'] for b in bl])
        bz = np.array([b['dz'] for b in bl])
        s += f" blocks[{len(bl)}] med dx={np.median(bx):+.1f} dz={np.median(bz):+.1f} sd=({bx.std():.1f},{bz.std():.1f})"
    return s


def clean(r):
    if not r or r.get('all') is None:
        return None
    a = r['all']
    return dict(dx=round(a['t'][1] * PX, 2), dz=round(a['t'][0] * PX, 2), n=a['n'], rms=round(a['rms'], 2),
                cond=round(a['cond'], 2), blocks=r['blocks'])


def main():
    verify = '--verify' in sys.argv
    reg = load_registration() if verify else dict(global_shift=[0.0, 0.0], sheets={})
    report = {}
    for rec in SHEETS:
        s = Sheet(rec, reg)
        r = measure(s, corrected=verify)
        s.free()
        report[s.name] = dict(coast_px=r['coast_px'], coast=clean(r.get('coast')), contour=clean(r.get('contour')))
        print(f"{s.name:20s} coast[{r['coast_px']:6d}] {fmt(r.get('coast'))}\n{'':20s} contour       {fmt(r.get('contour'))}", flush=True)
    os.makedirs(TMP, exist_ok=True)
    if verify:
        with open(os.path.join(TMP, 'registration_verify.json'), 'w') as f:
            json.dump(report, f, indent=1)
        return
    with open(os.path.join(TMP, 'registration_raw.json'), 'w') as f:
        json.dump(report, f, indent=1)
    print('raw measurements ->', os.path.join(TMP, 'registration_raw.json'))


if __name__ == '__main__':
    main()
