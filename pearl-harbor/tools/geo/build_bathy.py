#!/usr/bin/env python3
"""Stage 2 - water optical classes and synthetic bathymetry on the 8 m master grid.

 * deep-water background reflectance (sun-glint / scene residue) estimated far offshore
   and subtracted -> "excess" green reflectance = bottom-visible signal
 * class 1 (shallow / reef flat, bottom visible) where the excess is clearly above noise;
   its depth (0.8..5 m) follows the brightness of the bottom signal
 * outside the reef the sea floor follows a distance profile calibrated on the open-ocean
   Mapzen/AWS terrain tiles, into which it blends 2.5..5 km from land (tiles are unusable
   near shore); clamped at -600 m
 * Pearl Harbor uses a control-point model of the 1941 dredged depths (hist1941.py)

Outputs (TMP/build/): depth8.npy float32 (positive metres below sea level, 0 on land),
   wclass8.npy uint8 (0 deep, 1 shallow; 255 on land), bg32_B0x.npy, exg8.npy float16,
   harborw8.npy float16 (0..1 weight of the Pearl Harbor model)
"""
import os, numpy as np
from scipy import ndimage as ndi
from common import *
from hist1941 import *

EX_T = 0.018          # green excess threshold for "bottom visible"
EX_BRIGHT = 0.14      # excess of ~1 m deep bright bottom
PROFILE_D = np.array([0, 100, 300, 750, 1250, 1750, 2500, 3500, 5000, 7000, 20000, 60000], float)
PROFILE_Z = np.array([5, 12, 22, 45, 85, 150, 260, 390, 520, 610, 650, 650], float)


def smoothstep(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def r4(a):
    a = np.asarray(a, dtype=np.float32)
    return a.reshape(M8_H // 4, 4, M8_W // 4, 4).mean((1, 3))


def up4(a):
    """32 m field -> 8 m (bilinear, pixel-centre aligned)."""
    return ndi.zoom(a, 4, order=1, mode='nearest', grid_mode=True).astype(np.float32)


def nconv(v, m, sig, min_den=0.02):
    """Normalised Gaussian convolution of v over mask m, nearest-extrapolated elsewhere."""
    num = ndi.gaussian_filter(np.where(m, v, 0).astype(np.float32), sig)
    den = ndi.gaussian_filter(m.astype(np.float32), sig)
    out = num / np.maximum(den, 1e-6)
    bad = den < min_den
    if bad.any():
        idx = ndi.distance_transform_edt(bad, return_distances=False, return_indices=True)
        out = out[tuple(idx)]
    return out


def edt_m(mask, px=8.0):
    """Distance (m) of True cells to the nearest False cell, float32."""
    return (ndi.distance_transform_edt(mask) * px).astype(np.float32)


def main():
    sea = np.load(TMP + '/build/water8.npy')
    edit = np.load(TMP + '/build/edit8.npy')
    B = {b: np.load(f'{TMP}/m8/{b}.npy', mmap_mode='r') for b in ('B02', 'B03', 'B04', 'B08')}

    # ---------- deep-water background at 32 m ----------
    sea4 = r4(sea) > 0.5
    d4 = ndi.distance_transform_edt(sea4) * 32.0
    t4 = r4(np.load(TMP + '/tiles8.npy', mmap_mode='r'))
    valid4 = r4(np.asarray(B['B03']) > 0) > 0.99
    deep4 = sea4 & (d4 > 2500) & (t4 < -100) & valid4
    cdeep = {}
    for b in ('B02', 'B03', 'B04', 'B08'):
        v4 = r4(B[b]) / 10000.0
        cdeep[b] = float(np.median(v4[deep4]))
        bg = nconv(v4, deep4, 40)
        np.save(f'{TMP}/build/bg32_{b}.npy', bg.astype(np.float32))
        if b == 'B03':
            bg3 = bg
    print('deep-water reflectance', cdeep, flush=True)
    np.save(TMP + '/build/cdeep.npy', np.array([cdeep[b] for b in ('B02', 'B03', 'B04', 'B08')], np.float32))

    # ---------- bottom-visible excess (green) ----------
    g = np.asarray(B['B03'], np.float32) / 10000.0
    # clean water pixels only: mixed shore pixels / ships / runway fill must not drive the reef map
    rr = edit == 1
    dirty = sea & ((np.load(TMP + '/m8/wetfreq.npy', mmap_mode='r') < 70) | rr | (g <= 0)
                   | (np.asarray(B['B08'], np.float32) / 10000.0 > g + 0.01))
    dirty = ndi.binary_dilation(dirty, np.ones((3, 3), bool)) & sea
    np.save(TMP + '/build/dirtywater8.npy', dirty)
    clean = sea & ~dirty
    del dirty
    g -= up4(bg3)                                        # g is now the green excess
    exs = nconv(g, clean, 1.5, min_den=0.05)             # light smoothing + fill of dirty cells
    big = ndi.binary_dilation(rr, iterations=3)
    if big.any():                                        # reef runway: fill from the reef around it
        rs, cs = [slice(max(0, a.start - 400), a.stop + 400) for a in ndi.find_objects(big.astype(np.uint8))[0]]
        wide = nconv(g[rs, cs], clean[rs, cs], 25, min_den=0.01)
        wgt = ndi.gaussian_filter(big[rs, cs].astype(np.float32), 4)
        exs[rs, cs] = exs[rs, cs] * (1 - wgt) + wide * wgt
    del g, clean, big
    exs = np.where(sea, exs, 0).astype(np.float32)
    np.save(TMP + '/build/exg8.npy', exs.astype(np.float16))

    d_land = edt_m(sea)

    # ---------- Pearl Harbor region + model ----------
    lon_w, lon_e, lat_s, lat_n = HARBOR_BOX
    sl = box_slices((lon_w, lon_e, lat_s - 0.03, lat_n))
    jj, ii = np.mgrid[sl[0], sl[1]]
    X = (ISLAND['X0'] + (ii + 0.5) * 8.0).astype(np.float32)
    Z = (ISLAND['Z0'] + (jj + 0.5) * 8.0).astype(np.float32)
    lon, lat = world_to_lonlat(X, Z)
    inner = sea[sl] & (lat > HARBOR_MOUTH_LAT) & (lon > lon_w) & (lon < lon_e)
    lab, n = ndi.label(inner)
    fi, fj = lonlat_to_px(ISLAND, M8_W, M8_H, -157.9720, 21.3580)      # channel west of Ford Island
    seed = lab[int(round(float(fj))) - sl[0].start, int(round(float(fi))) - sl[1].start]
    assert seed > 0
    hreg = lab == seed
    # weight of the harbor model: 1 inside (right up to the shore), fading over ~400 m at the mouth
    hwb = ndi.gaussian_filter(hreg.astype(np.float32), 20) / np.maximum(ndi.gaussian_filter(sea[sl].astype(np.float32), 20), 1e-3)
    hwb = np.where(sea[sl], smoothstep(hwb, 0.1, 0.9), 0).astype(np.float32)
    hw = np.zeros(sea.shape, np.float32)
    hw[sl] = hwb
    cx, cz = lonlat_to_world(np.array([c[0] for c in HARBOR_DEPTH_CTRL]), np.array([c[1] for c in HARBOR_DEPTH_CTRL]))
    wsum = np.zeros(X.shape, np.float32); dm = np.zeros(X.shape, np.float32); dr = np.zeros(X.shape, np.float32)
    for (lo, la, zmax, ramp), x0, z0 in zip(HARBOR_DEPTH_CTRL, cx, cz):
        w = 1.0 / (((X - x0) ** 2 + (Z - z0) ** 2) / 250.0 ** 2 + 0.05) ** 1.5
        wsum += w; dm += w * zmax; dr += w * ramp
    dm /= wsum; dr /= wsum
    hdepth = np.zeros(sea.shape, np.float32)
    hdepth[sl] = 0.5 + (dm - 0.5) * smoothstep(d_land[sl] / dr, 0, 1)
    del X, Z, lon, lat, jj, ii, wsum, dm, dr, lab, inner

    # ---------- class 1 (shallow, bottom visible) ----------
    c1 = sea & (exs > EX_T) & (d_land < 6000) & (hw < 0.5)
    c1 = ndi.binary_opening(c1, np.ones((3, 3), bool)) | (c1 & (d_land <= 16))
    lab, n = ndi.label(c1)
    sz = ndi.sum(c1, lab, np.arange(1, n + 1))
    c1 = np.isin(lab, 1 + np.flatnonzero(sz >= 40))
    lab, n = ndi.label(sea & ~c1 & (hw < 0.5))
    sz = np.bincount(lab.ravel())[1:]
    c1 |= np.isin(lab, 1 + np.flatnonzero(sz < 40))
    del lab
    c1 |= (edit == 1)                                   # the restored reef under the Reef Runway
    c1 &= sea

    # ---------- open-coast depth ----------
    depth = np.clip(np.log(EX_BRIGHT / np.maximum(exs, 1e-4)) / np.log(EX_BRIGHT / EX_T), 0, 1)
    depth *= 4.2
    depth += 0.8                                        # reef depth 0.8..5 m from bottom brightness
    del exs
    d2 = edt_m(sea & ~c1)
    # local steepness calibration against the tiles 3.5-7 km offshore (32 m grid)
    c14 = r4(c1) > 0.5
    d24 = ndi.distance_transform_edt(sea4 & ~c14) * 32.0
    ring = sea4 & (d4 > 3500) & (d4 < 7000)
    ratio = np.clip(-t4 / np.interp(d24, PROFILE_D, PROFILE_Z), 0.1, 4.0)
    s4 = np.clip(nconv(ratio, ring, 60, min_den=0.01), 0.25, 2.5)
    s = up4(ndi.gaussian_filter(s4, 15))
    s -= 1
    s *= smoothstep(d2, 300, 1500)
    s += 1
    prof = np.interp(d2, PROFILE_D, PROFILE_Z).astype(np.float32)
    prof -= 5
    prof *= s
    prof += 5
    del s
    np.copyto(depth, prof, where=~c1)
    del prof
    # terrain tiles far out
    ts = -up4(ndi.gaussian_filter(t4, 6))               # ~190 m smoothing, positive depth
    np.maximum(ts, 0.4 * depth, out=ts)
    wt = smoothstep(d_land, 2500, 5000)
    depth += wt * (ts - depth)
    del ts, wt
    np.minimum(depth, 0.5 + 0.12 * d_land, out=depth)   # beach ramp everywhere
    depth += hw * (hdepth - depth)                      # Pearl Harbor model
    del hdepth
    depth[edit == 3] = 10.0                             # dry docks 1 and 2 (flooded basins)
    depth[~sea] = 0

    # ---------- smoothing (sea only), stronger offshore ----------
    seaf = sea.astype(np.float32)
    b1 = ndi.gaussian_filter(depth, 2.0) / np.maximum(ndi.gaussian_filter(seaf, 2.0), 1e-3)   # 16 m
    w1 = np.maximum(smoothstep(d_land, 16, 60), 0.35) * (1 - 0.6 * hw)
    depth += w1 * (b1 - depth)
    del b1, w1, seaf
    dl4 = up4(nconv(r4(depth), sea4, 5))                # ~160 m
    w2 = smoothstep(d2, 400, 1600) * (1 - hw)
    depth += w2 * (dl4 - depth)
    del dl4, w2, d2
    depth = np.where(sea, np.clip(depth, 0.6, 600.0), 0).astype(np.float32)
    depth[edit == 3] = 10.0

    wclass = np.full(sea.shape, 255, np.uint8)
    wclass[sea] = 0
    wclass[c1] = 1
    wclass[sea & (hw >= 0.5) & (depth < 2.5)] = 1
    wclass[sea & (hw >= 0.5) & (depth >= 2.5)] = 0
    np.save(TMP + '/build/depth8.npy', depth)
    np.save(TMP + '/build/wclass8.npy', wclass)
    np.save(TMP + '/build/harborw8.npy', hw.astype(np.float16))
    np.save(TMP + '/build/dland8.npy', np.minimum(d_land, 65000).astype(np.float32))
    print('class1 km2', (wclass == 1).sum() * 64e-6, 'depth pct', np.percentile(depth[sea][::50], [1, 25, 50, 75, 99]))


if __name__ == '__main__':
    main()
