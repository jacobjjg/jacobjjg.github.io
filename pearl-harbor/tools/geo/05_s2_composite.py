#!/usr/bin/env python3
"""Cloud-free Sentinel-2 composite on the 10 m UTM master grid.

Per pixel: observations flagged cloud / shadow / no-data by SCL (dilated) are
dropped; the remaining ones are ranked by blue reflectance and the mean of the
20th..60th percentile ranks is taken for every band (same dates for all bands,
so colours stay physically consistent; bright residual cloud/glint and dark
residual shadow are both rejected).  Where fewer than 3 clear observations
exist (bright roofs/sand/surf that SCL always calls cloud) all observations
are ranked instead.

Outputs (TMP/comp/): B02,B03,B04,B08,B11 .npy uint16 (reflectance*10000, 10 m),
  nclear.npy uint8, wetfreq.npy uint8 (percentage of clear obs with NDWI>0 & MNDWI>0)
"""
import os, json, numpy as np
from scipy import ndimage as ndi
from common import *

BANDS = ['B02', 'B03', 'B04', 'B08', 'B11']
STRIP = 250


def main():
    sel = json.load(open(TMP + '/s2_selected.json'))
    keys = [g['key'] for g in sel if os.path.exists(f"{DL}/s2/{g['key']}_B08.npy")]
    n = len(keys)
    print('scenes', n)
    os.makedirs(TMP + '/comp', exist_ok=True)
    # clear masks at 20 m
    clear20 = []
    for k in keys:
        scl = np.load(f'{DL}/s2/{k}_SCL.npy')
        cloud = ndi.binary_dilation(np.isin(scl, (8, 9, 10)), iterations=4)
        shadow = ndi.binary_dilation(scl == 3, iterations=2)
        clear20.append(~(cloud | shadow | (scl <= 1)))
    clear20 = np.stack(clear20)
    mm = {b: [np.load(f'{DL}/s2/{k}_{b}.npy', mmap_mode='r') for k in keys] for b in BANDS}
    out = {b: np.zeros((UTM_H, UTM_W), np.uint16) for b in BANDS}
    nclear = np.zeros((UTM_H, UTM_W), np.uint8)
    wet = np.zeros((UTM_H, UTM_W), np.uint8)
    ranks = np.arange(n, dtype=np.int16)[:, None, None]
    for r0 in range(0, UTM_H, STRIP):
        r1 = min(r0 + STRIP, UTM_H)
        st = {}
        for b in BANDS:
            if b == 'B11':
                a = np.stack([m[r0 // 2:(r1 + 1) // 2] for m in mm[b]])
                a = np.repeat(np.repeat(a, 2, axis=1), 2, axis=2)[:, :r1 - r0, :UTM_W]
            else:
                a = np.stack([m[r0:r1] for m in mm[b]])
            st[b] = a.astype(np.float32)
        c = clear20[:, r0 // 2:(r1 + 1) // 2]
        c = np.repeat(np.repeat(c, 2, axis=1), 2, axis=2)[:, :r1 - r0, :UTM_W]
        has = (st['B02'] > 0) & (st['B03'] > 0) & (st['B04'] > 0) & (st['B08'] > 0) & (st['B11'] > 0)
        c = c & has
        nc = c.sum(0)
        use = np.where(nc[None] >= 3, c, has)
        nu = use.sum(0)
        score = np.where(use, st['B02'], np.inf)
        order = np.argsort(score, axis=0)
        lo = np.floor(0.2 * nu).astype(np.int16)
        hi = np.maximum(lo + 1, np.rint(0.6 * nu).astype(np.int16))
        w = ((ranks >= lo[None]) & (ranks < hi[None])).astype(np.float32)
        wsum = np.maximum(w.sum(0), 1)
        for b in BANDS:
            s = np.take_along_axis(st[b], order, axis=0)
            v = (s * w).sum(0) / wsum
            v[nu == 0] = 0
            out[b][r0:r1] = np.clip(np.rint(v), 0, 65535).astype(np.uint16)
        ndwi = (st['B03'] - st['B08']) / np.maximum(st['B03'] + st['B08'], 1)
        mndwi = (st['B03'] - st['B11']) / np.maximum(st['B03'] + st['B11'], 1)
        isw = (ndwi > 0.0) & (mndwi > 0.0) & use
        wet[r0:r1] = np.rint(100.0 * isw.sum(0) / np.maximum(nu, 1)).astype(np.uint8)
        nclear[r0:r1] = nc.astype(np.uint8)
        print('rows', r0, r1, flush=True)
    for b in BANDS:
        np.save(f'{TMP}/comp/{b}.npy', out[b])
    np.save(TMP + '/comp/nclear.npy', nclear)
    np.save(TMP + '/comp/wetfreq.npy', wet)
    json.dump(keys, open(TMP + '/comp/scenes.json', 'w'))


if __name__ == '__main__':
    main()
