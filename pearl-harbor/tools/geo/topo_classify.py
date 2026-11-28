"""Per-sheet colour calibration and symbol/tint classification of the 1952-54 USGS quads.

All classification is done in scan-pixel space (2.03 m/px) with a calibration that is
specific to each scan, because the 15 scans differ a lot in ink density and colour cast
(the water tint ranges from saturated cyan to a 3 % grey).  The class layers are later
warped into the world frame by topo_common.Mosaic exactly like the RGB.

Layers (uint8, 255 = yes):
  water : blue water tint (sea, harbour, ponds, reservoirs)
  wood  : green woodland / scrub tint
  pink  : red-dot "urban area" tint (areas where only landmark buildings are shown)
  black : solid black building symbols (dense black blobs, not line work / lettering)
  brown : brown contour ink (used for registration only)
  marsh : blue marsh/swamp pattern on land (tufts) - reported separately, not water
"""
import os
import numpy as np
import cv2
from scipy import ndimage as ndi

from topo_common import (ISLAND, DEM8, TMP, Sheet, world_to_px)

CAL_JSON = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'topo_colour_calibration.json')


def dem_on_sheet(sheet, step=1, corrected=True, dem=None):
    """Modern DEM (8 m ISLAND grid from topo_01_download.py) resampled onto the scan pixel lattice
    (every `step`-th pixel).  Water / no data = 0."""
    dem = np.load(DEM8, mmap_mode='r') if dem is None else dem
    H, W = dem.shape
    cols = np.arange(0, sheet.width, step, dtype=np.float64)
    rows = np.arange(0, sheet.height, step, dtype=np.float64)
    # px -> world is smooth: evaluate on a coarse lattice and interpolate bilinearly
    cc = np.linspace(0, sheet.width - 1, 33)
    rr = np.linspace(0, sheet.height - 1, 33)
    CX, CZ = sheet.px_to_world(*np.meshgrid(cc, rr), corrected=corrected)
    di, dj = world_to_px(ISLAND, W, H, CX, CZ)
    fx = (cols / (sheet.width - 1) * 32).astype(np.float32)
    fy = (rows / (sheet.height - 1) * 32).astype(np.float32)
    FX, FY = np.meshgrid(fx, fy)
    mi = cv2.remap(di.astype(np.float32), FX, FY, cv2.INTER_LINEAR)
    mj = cv2.remap(dj.astype(np.float32), FX, FY, cv2.INTER_LINEAR)
    j0, j1 = max(0, int(mj.min()) - 3), min(H, int(mj.max()) + 4)
    i0, i1 = max(0, int(mi.min()) - 3), min(W, int(mi.max()) + 4)
    sub = np.array(dem[j0:j1, i0:i1])
    return cv2.remap(sub, mi - i0, mj - j0, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0.0)


def neat_mask(sheet, inset=4):
    """Boolean scan-pixel mask of the map body (inside the neat line)."""
    lo = np.linspace(sheet.lon_w, sheet.lon_e, 50)
    la = np.linspace(sheet.lat_s, sheet.lat_n, 50)
    ring = np.concatenate([
        np.stack(sheet.ohd_to_px(lo, np.full(50, sheet.lat_n)), 1),
        np.stack(sheet.ohd_to_px(np.full(50, sheet.lon_e), la[::-1]), 1),
        np.stack(sheet.ohd_to_px(lo[::-1], np.full(50, sheet.lat_s)), 1),
        np.stack(sheet.ohd_to_px(np.full(50, sheet.lon_w), la), 1)])
    m = np.zeros((sheet.height, sheet.width), np.uint8)
    cv2.fillPoly(m, [np.round(ring).astype(np.int32)], 1)
    if inset:
        m = cv2.erode(m, np.ones((2 * inset + 1, 2 * inset + 1), np.uint8))
    return m.astype(bool)


def _mode_colour(px):
    """Robust dominant colour of an (N,3) sample."""
    q = (px // 6).astype(np.int32)
    key = q[:, 0] * 4096 + q[:, 1] * 64 + q[:, 2]
    u, c = np.unique(key, return_counts=True)
    k = u[np.argmax(c)]
    sel = px[key == k]
    cen = sel.mean(0)
    near = px[(np.abs(px - cen) < 7).all(1)]
    return near.mean(0)


def calibrate(sheet, dem_s4=None):
    """Reference colours of one scan: paper (unprinted land), water tint, green tint."""
    img = sheet.img
    nm = neat_mask(sheet, 12)[::4, ::4]
    small = cv2.blur(img, (5, 5))[::4, ::4].astype(np.float32)
    e = dem_on_sheet(sheet, 4, corrected=False) if dem_s4 is None else dem_s4
    sea = e <= 0.3
    d_sea = ndi.distance_transform_edt(sea) * 8.1
    d_land = ndi.distance_transform_edt(~sea) * 8.1
    land_px = small[nm & (d_land > 80)]
    # paper = brightest dominant land colour
    bright = land_px[land_px.min(1) > 190]
    paper = _mode_colour(bright if len(bright) > 2000 else land_px)
    cal = dict(paper=[float(v) for v in paper])
    sea_px = small[nm & (d_sea > 250)]
    if len(sea_px) > 800:
        cal['water'] = [float(v) for v in _mode_colour(sea_px)]
    else:
        cal['water'] = None
    # green tint: dominant saturated yellow-green on land
    n = land_px / paper
    g = land_px[(n[:, 2] < 0.75) & (n[:, 1] > 0.72) & (n[:, 1] - n[:, 0] > -0.06) & (n[:, 0] < 0.97)]
    cal['green'] = [float(v) for v in _mode_colour(g)] if len(g) > 3000 else None
    cal['n_sea'] = int(len(sea_px))
    return cal


def tint_axis(norm, ref_n):
    """Project (norm-1) on the paper->tint axis.  Returns (t, resid): t=0 paper, t=1 tint."""
    w = np.asarray(ref_n, np.float32) - 1.0
    d = norm - 1.0
    t = (d @ w) / float(w @ w)
    r = np.linalg.norm(d - t[..., None] * w, axis=-1)
    return t, r


def classify_sheet(sheet, cal):
    """Return dict of uint8 layers (scan-pixel space) for one sheet."""
    img = sheet.img
    H, W = img.shape[:2]
    paper = np.array(cal['paper'], np.float32)
    body = neat_mask(sheet, 3)
    out = {}
    f = cv2.GaussianBlur(img, (0, 0), 0.8).astype(np.float32) / paper      # light de-noise
    R, G, B = f[..., 0], f[..., 1], f[..., 2]
    mx = f.max(-1)
    mn = f.min(-1)
    sat = (mx - mn) / np.maximum(mx, 1e-3)

    # ---- black (solid building symbols): dark, unsaturated, and survives an opening
    dark = (mx < 0.45)
    blk = cv2.morphologyEx(dark.astype(np.uint8), cv2.MORPH_OPEN,
                           cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))
    out['black'] = (blk.astype(bool) & body).astype(np.uint8) * 255
    out['dark'] = (dark & body).astype(np.uint8) * 255

    # ---- brown contour ink
    hsv = cv2.cvtColor(np.clip(f, 0, 1).astype(np.float32), cv2.COLOR_RGB2HSV)
    hue = hsv[..., 0]
    brown = (hue > 10) & (hue < 38) & (sat > 0.30) & (mx > 0.45) & (mx < 0.97) & (G < 0.86) & (R - G > 0.10) & (G - B > 0.04)
    out['brown'] = (brown & body).astype(np.uint8) * 255

    # ---- red ink (roads, urban-tint dots)
    red = ((hue < 12) | (hue > 340)) & (sat > 0.25) & (R > 0.7) & (R - G > 0.14) & (np.abs(G - B) < 0.16)

    # ---- water tint -------------------------------------------------------------
    if cal.get('water') is not None:
        wn = np.array(cal['water'], np.float32) / paper
        wlen = float(np.linalg.norm(wn - 1))
        t, r = tint_axis(f, wn)
        rthr = max(0.030, 0.40 * wlen)
        onaxis = (r < rthr) & (t > -0.8) & (t < 2.2)
        # keep clear of any ink: anti-aliased edges of black line work are grey and would
        # otherwise fall on the paper->tint axis of the faint-tint scans
        ink = cv2.dilate((~onaxis).astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool)
        clean = onaxis & ~ink
        # normalised convolution of t over "clean" (paper..tint axis) pixels
        sig = 3.0 if wlen > 0.10 else 4.5
        wgt = cv2.GaussianBlur(clean.astype(np.float32), (0, 0), sig)
        ts = cv2.GaussianBlur(np.where(clean, t, 0).astype(np.float32), (0, 0), sig) / np.maximum(wgt, 1e-3)
        ok = (wgt > 0.06) & body
        # threshold at the valley between the land (t~0) and water (t~1) modes of this scan
        hist = np.bincount(np.clip((ts[ok][::7] * 50 + 50), 0, 149).astype(np.int32), minlength=150).astype(np.float64)
        hist = np.convolve(hist, np.ones(5) / 5, mode='same')
        lo, hi = 50 + int(0.22 * 50), 50 + int(0.72 * 50)
        thr = (lo + int(np.argmin(hist[lo:hi + 1])) - 50) / 50.0
        cal['t_thr'] = float(thr)
        # land mode and its spread -> generous lower threshold for hysteresis
        land_bins = hist[:lo + 1]
        pk = int(np.argmax(land_bins))
        half = np.nonzero(land_bins[pk:] < 0.5 * land_bins[pk])[0]
        sig_land = (half[0] if len(half) else 5) / 50.0 / 1.18
        t_low = float(np.clip((pk - 50) / 50.0 + 3.5 * sig_land, 0.12, thr))
        cal['t_low'] = t_low
        core = (ts > thr) & ok
        cand = ((ts > t_low) & ok).astype(np.uint8)
        n, lab = cv2.connectedComponents(cand, connectivity=4)
        keep = np.zeros(n, bool)
        keep[np.unique(lab[core])] = True
        keep[0] = False
        hyst = keep[lab]
        k = int(round(2 * sig)) * 2 + 1
        water = core | cv2.erode(hyst.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))).astype(bool)
        out['water_raw'] = (water & body).astype(np.uint8) * 255
        out['t_water'] = np.clip(ts * 100 + 50, 0, 255).astype(np.uint8)
    else:
        out['water_raw'] = np.zeros((H, W), np.uint8)

    # ---- green woodland tint ------------------------------------------------------
    # yellow-green: blue strongly absorbed, green high, red moderately high
    fb = cv2.GaussianBlur(f, (0, 0), 2.0)
    Rb, Gb, Bb = fb[..., 0], fb[..., 1], fb[..., 2]
    green = (Bb < 0.80 * np.minimum(Gb, 1.0)) & (Gb > 0.62) & (Gb - Rb > -0.07) & (Gb - Bb > 0.16) & (Rb < 0.99)
    out['wood_raw'] = (green & body).astype(np.uint8) * 255

    # ---- pink urban tint: red dot screen => local red-ink density moderate, on light ground
    fb6 = cv2.GaussianBlur(f, (0, 0), 5.0)
    brown_d = cv2.GaussianBlur(brown.astype(np.float32), (0, 0), 8.0)
    pinkish = (fb6[..., 0] > 0.80) & (fb6[..., 0] - fb6[..., 1] > 0.05) & (fb6[..., 0] - fb6[..., 2] > 0.04) & \
              (np.abs(fb6[..., 1] - fb6[..., 2]) < 0.10) & (brown_d < 0.14)
    out['pink_raw'] = (pinkish & body).astype(np.uint8) * 255
    out['red'] = (red & body).astype(np.uint8) * 255
    return out


LAYER_DIR = os.path.join(TMP, 'layers')


def layer_path(sheet_name, layer):
    return os.path.join(LAYER_DIR, f"{sheet_name.replace(' ', '_')}_{layer}.png")


def load_layer(sheet_name, layer):
    return cv2.imread(layer_path(sheet_name, layer), cv2.IMREAD_UNCHANGED)


def main():
    """Calibrate + classify every sheet; cache the raw layers as PNG in TMP/layers."""
    import json
    import sys
    from topo_common import SHEETS, load_registration
    os.makedirs(LAYER_DIR, exist_ok=True)
    only = [a for a in sys.argv[1:] if not a.startswith('-')]
    cals = json.load(open(CAL_JSON)) if os.path.exists(CAL_JSON) else {}
    reg = load_registration()
    for rec in SHEETS:
        if only and rec['name'] not in only:
            continue
        s = Sheet(rec, reg)
        cal = calibrate(s)
        cals[s.name] = cal
        lay = classify_sheet(s, cal)
        for k, v in lay.items():
            cv2.imwrite(layer_path(s.name, k), v)
        print(s.name, {k: (round(x) if isinstance(x, float) else x) for k, x in
                       dict(paper=cal['paper'], water=cal['water'], green=cal['green']).items()},
              {k: round(float((v > 0).mean()), 3) for k, v in lay.items() if k != 't_water'}, flush=True)
        s.free()
    with open(CAL_JSON, 'w') as f:
        json.dump(cals, f, indent=1)


if __name__ == '__main__':
    main()
