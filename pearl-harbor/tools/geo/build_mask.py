#!/usr/bin/env python3
"""Stage 1 - sea/harbor water mask and land heights on the 8 m master grid.

Water = the hydro-flattened (0.0 m) / no-data part of the lidar-derived 3DEP DEM,
cross-checked against the Sentinel-2 water frequency (NDWI & MNDWI), then
  * Reef Runway (1970s fill) turned back into reef water (1941 correction)
  * dry docks 3 and 4 (1942/43) filled, dry docks 1 and 2 kept as water basins
  * only water connected to the open sea through openings >= 3 px (24 m) wide is
    kept (streams, canals < 24 m, land-locked ponds are land), tiny land specks removed

Outputs (TMP/build/): water8.npy bool, land8.npy float32 (land elevation, NaN on sea),
                      inland8.npy bool (inland water bodies, kept as 'land' in the mask),
                      edit8.npy uint8 (1 = reef runway -> water, 2 = dry dock filled, 3 = dry dock basin)
"""
import os, numpy as np
from scipy import ndimage as ndi
from common import *
from hist1941 import *

S8 = np.ones((3, 3), bool)


def fill_nearest(a, invalid):
    """Fill invalid cells with the nearest valid value."""
    idx = ndi.distance_transform_edt(invalid, return_distances=False, return_indices=True)
    return a[tuple(idx)]


def main():
    os.makedirs(TMP + '/build', exist_ok=True)
    dem = np.load(TMP + '/dem8.npy')
    wd = np.load(TMP + '/demwater8.npy') > 0.5
    wet = np.load(TMP + '/m8/wetfreq.npy')
    edit = np.zeros(dem.shape, np.uint8)

    # ---- 1941: reef runway -> water -------------------------------------------------
    bar = poly_mask(REEF_RUNWAY_POLYS[0])
    lag_box = poly_mask(REEF_RUNWAY_POLYS[1])
    conn = poly_mask(REEF_RUNWAY_CONNECTOR)
    lagoon = lag_box & (np.abs(np.nan_to_num(dem, nan=-99) - REEF_RUNWAY_LAGOON_Z) < 0.02)
    lagoon = ndi.binary_dilation(ndi.binary_opening(lagoon, S8), S8, iterations=2) & lag_box
    rr = (bar | lagoon | conn) & ~wd
    # islets of fill left between lagoon and bar / connector
    rr |= ndi.binary_closing(bar | lagoon | conn, S8, iterations=3) & (lag_box | bar) & ~wd
    edit[rr] = 1
    W = wd | rr

    # ---- dry docks -----------------------------------------------------------------
    demz = np.nan_to_num(dem, nan=0.0)
    for box in DRYDOCK_FILL_BOXES:
        sl = box_slices(box)
        pit = np.zeros(dem.shape, bool)
        pit[sl] = (demz[sl] < 1.0) & ~wd[sl]          # below yard level, not harbor water
        lab, n = ndi.label(pit, S8)
        deep_ids = np.unique(lab[sl][(demz[sl] < -1.0) & ~wd[sl]])   # components holding the dock floor
        dock = np.isin(lab, deep_ids[deep_ids > 0])
        dock = ndi.binary_dilation(dock, S8, iterations=1) & ~wd
        edit[dock] = 2
    # yard docks: the two largest below-sea-level slots are DD1/DD2 (kept as basins), a third
    # smaller one is DD3 (1942) -> filled
    dsl = box_slices(DRYDOCK_YARD_BOX)
    slot = np.zeros(dem.shape, bool)
    slot[dsl] = (demz[dsl] < -0.5) & ~wd[dsl]
    slot = ndi.binary_opening(slot, S8)
    lab, n = ndi.label(slot, S8)
    sizes = ndi.sum(slot, lab, np.arange(1, n + 1))
    order = np.argsort(-sizes)
    basin = ndi.binary_dilation(np.isin(lab, 1 + order[:2]), S8) & ~wd
    extra = ndi.binary_dilation(np.isin(lab, 1 + order[2:]), S8, iterations=2) & ~wd & ~basin
    print('yard dock slots (px):', sizes[order].astype(int))
    edit[extra] = 2
    edit[basin] = 3

    W[edit == 2] = False

    # ---- sea connectivity (opening by reconstruction, 3x3) ----------------------------
    core = ndi.binary_erosion(W, S8, border_value=1)
    lab, n = ndi.label(core, S8)
    sea_id = lab[5, 5]                       # NW corner of the rect is open ocean
    assert sea_id > 0
    sea = ndi.binary_dilation(lab == sea_id, S8) & W
    # second pass lets 2-px-wide basins that hang off wide water survive (pier slips)
    sea = ndi.binary_dilation(sea, S8) & W & ndi.binary_dilation(ndi.binary_erosion(W, np.ones((2, 2), bool)), np.ones((2, 2), bool))
    sea |= basin
    # inland water bodies (reservoirs, ponds, land-locked lagoons): DEM water that is not sea,
    # or flat DEM surface that Sentinel-2 sees as water on most dates (roof false-positives are small)
    flat = (ndi.maximum_filter(demz, 5) - ndi.minimum_filter(demz, 5)) < 0.15
    s2w = ndi.binary_opening((wet > 75) & flat & ~wd, S8)
    lab, n = ndi.label(s2w, S8)
    sizes = ndi.sum(np.ones_like(lab, np.uint8), lab, np.arange(1, n + 1))
    s2w = np.isin(lab, 1 + np.flatnonzero(sizes >= 60))
    inland = ((W & ~sea) | s2w) & ~rr
    # ---- remove land specks (< 8 px = 512 m2) and pin-hole water ------------------------
    lab, n = ndi.label(~sea, S8)
    sizes = ndi.sum(np.ones_like(lab, np.uint8), lab, np.arange(1, n + 1))
    small = np.isin(lab, 1 + np.flatnonzero(sizes < 8))
    sea |= small
    lab, n = ndi.label(sea, S8)
    sizes = ndi.sum(np.ones_like(lab, np.uint8), lab, np.arange(1, n + 1))
    keep = np.isin(lab, 1 + np.flatnonzero(sizes >= 12))
    sea &= keep
    print('sea frac', sea.mean(), 'land km2', (~sea).sum() * 64e-6, 'removed specks', small.sum(),
          'reef-runway px', rr.sum(), 'basin px', basin.sum(), 'filled dock px', (edit == 2).sum())

    # ---- land heights -------------------------------------------------------------------
    land = dem.copy()
    land[edit == 2] = np.nan                         # dry docks 3/4: refill from the rim
    land[basin] = np.nan
    need = ~sea & ~np.isfinite(land)                 # land in the mask without a DEM height
    if need.any():
        src = np.where(np.isfinite(land) & ~sea, land, np.nan)
        filled = fill_nearest(np.nan_to_num(src, nan=0.0), ~np.isfinite(src))
        # shoreline cells / former DEM water (ponds, stream mouths): low and flat
        land[need] = np.where(edit[need] == 2, filled[need], np.minimum(filled[need], 0.6))
    land[sea] = np.nan
    lmin = np.nanmin(land)
    land = np.where(sea, np.nan, np.maximum(land, 0.5)).astype(np.float32)
    print('land min before clamp', lmin, 'cells raised to 0.5:', int((dem < 0.5).sum()))
    inland &= ~sea
    np.save(TMP + '/build/water8.npy', sea)
    np.save(TMP + '/build/land8.npy', land)
    np.save(TMP + '/build/inland8.npy', inland)
    np.save(TMP + '/build/edit8.npy', edit)


if __name__ == '__main__':
    main()
