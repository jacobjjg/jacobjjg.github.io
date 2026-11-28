#!/usr/bin/env python3
"""Stage 3 - cleaned natural-colour reflectance on the 8 m master grid.

 * sea: scene residue / sun-glint background removed (comp - background + global deep
   colour); ships, wakes, bridges, the Arizona Memorial, mixed shoreline pixels and the
   Reef Runway fill are in-painted from surrounding clean water; open ocean without any
   bottom signal fades to one constant deep-water colour
 * land: water-coloured fringe pixels at the shore and the filled dry docks are in-painted
   from neighbouring land

Outputs (TMP/build/): rgb8_R.npy, rgb8_G.npy, rgb8_B.npy  uint16 reflectance*10000
"""
import os, numpy as np
from scipy import ndimage as ndi
from common import *
from build_bathy import up4, smoothstep


def fill_multiscale(v, good, bad, sigmas=(1.5, 4, 12, 40)):
    """Replace v[bad] by normalised Gaussian means of v[good], coarser where needed."""
    out = v.copy()
    todo = bad.copy()
    goodf = good.astype(np.float32)
    vg = np.where(good, v, 0).astype(np.float32)
    for k, s in enumerate(sigmas):
        if not todo.any():
            break
        rs, cs = ndi.find_objects(todo.astype(np.uint8))[0]
        pad = int(4 * s) + 2
        rs = slice(max(0, rs.start - pad), min(v.shape[0], rs.stop + pad))
        cs = slice(max(0, cs.start - pad), min(v.shape[1], cs.stop + pad))
        num = ndi.gaussian_filter(vg[rs, cs], s)
        den = ndi.gaussian_filter(goodf[rs, cs], s)
        ok = todo[rs, cs] & (den > (0.12 if k < len(sigmas) - 1 else 1e-4))
        sub = out[rs, cs]
        sub[ok] = num[ok] / den[ok]
        t = todo[rs, cs]
        t[ok] = False
    if todo.any():
        idx = ndi.distance_transform_edt(~good, return_distances=False, return_indices=True)
        out[todo] = v[tuple(idx)][todo]
    return out


def main():
    sea = np.load(TMP + '/build/water8.npy')
    edit = np.load(TMP + '/build/edit8.npy')
    dirty = np.load(TMP + '/build/dirtywater8.npy')
    exs = np.load(TMP + '/build/exg8.npy').astype(np.float32)
    wet = np.load(TMP + '/m8/wetfreq.npy')
    inland = np.load(TMP + '/build/inland8.npy')
    cdeep = np.load(TMP + '/build/cdeep.npy')
    S8 = np.ones((3, 3), bool)

    nodata = np.load(TMP + '/m8/B03.npy', mmap_mode='r')[:] == 0
    clean_sea = sea & ~dirty & ~nodata
    bad_sea = sea & ~clean_sea
    near_sea = ndi.binary_dilation(sea, S8, iterations=3)
    # land that looks like water right at the shore (mixed pixels), plus filled docks
    bad_land = ~sea & ~inland & ((near_sea & (wet > 45)) | (edit == 2))
    # land pixels touching the sea are always mixed at 10 m: take them from one pixel inland
    bad_land |= ~sea & ~inland & ndi.binary_dilation(sea, S8) & (wet > 20)
    clean_land = ~sea & ~bad_land & ~nodata
    w_deep = (1 - smoothstep(ndi.gaussian_filter(exs, 6), 0.004, 0.013)).astype(np.float32)
    w_deep[~sea] = 0
    del exs
    print('bad sea px', bad_sea.sum(), 'bad land px', bad_land.sum(), flush=True)

    for name, band, k in (('R', 'B04', 2), ('G', 'B03', 1), ('B', 'B02', 0)):
        v = np.load(f'{TMP}/m8/{band}.npy').astype(np.float32) / 10000.0
        bg = up4(np.load(f'{TMP}/build/bg32_{band}.npy'))
        vs = v - bg + cdeep[k]
        del bg
        vs = fill_multiscale(vs, clean_sea, bad_sea)
        vs += w_deep * (cdeep[k] - vs)
        vl = fill_multiscale(v, clean_land, bad_land, sigmas=(1.2, 3, 8))
        out = np.where(sea, vs, vl)
        del vs, vl, v
        np.save(f'{TMP}/build/rgb8_{name}.npy', np.clip(np.rint(out * 10000), 0, 65535).astype(np.uint16))
        print(name, 'done', flush=True)


if __name__ == '__main__':
    main()
