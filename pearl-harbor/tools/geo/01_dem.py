#!/usr/bin/env python3
"""Download USGS 3DEP 1/3 arc-second DEM tiles and warp them into the 8 m
world-frame master grid (ISLAND rect, 10240 x 8192).

The 3DEP tiles are lidar-derived and hydro-flattened: sea / harbor water is
exactly 0.0 m, open ocean beyond the lidar swath is no-data.  To keep the
shoreline crisp the water flag is warped separately (as a fraction) and the
land heights are warped with water masked out, so coastal land pixels are not
dragged towards 0 by interpolation.

Outputs (TMP/): dem8.npy      float32 land elevation, NaN on DEM water / no-data
                demwater8.npy float32 0..1 fraction of DEM water (1 = water or no-data)
"""
import os, subprocess, numpy as np, rasterio
from rasterio.warp import reproject, Resampling
from common import *

BASE = 'https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/13/TIFF/current'
TILES = ['n22w158', 'n22w159']


def main():
    os.makedirs(DL + '/dem', exist_ok=True)
    os.makedirs(TMP, exist_ok=True)
    tr = rect_transform(ISLAND, M8_W, M8_H)
    dem = np.full((M8_H, M8_W), np.nan, np.float32)
    wat = np.ones((M8_H, M8_W), np.float32)
    for t in TILES:
        p = f'{DL}/dem/USGS_13_{t}.tif'
        if not os.path.exists(p):
            subprocess.check_call(['curl', '-sf', '-o', p, f'{BASE}/{t}/USGS_13_{t}.tif'])
            subprocess.call(['curl', '-sf', '-o', p[:-4] + '.xml', f'{BASE}/{t}/USGS_13_{t}.xml'])
        with rasterio.open(p) as ds:
            a = ds.read(1)
            nod = (a == ds.nodata) | ~np.isfinite(a)
            water = nod | (a == 0.0)
            print(t, 'native: nodata %.3f, exactly 0: %.3f, |z|<0.02 & !=0: %.5f' % (
                nod.mean(), (a == 0).mean(), ((np.abs(a) < 0.02) & (a != 0)).mean()))
            land = np.where(water, np.nan, a).astype(np.float32)
            tmp = np.full((M8_H, M8_W), np.nan, np.float32)
            reproject(land, tmp, src_transform=ds.transform, src_crs=ds.crs, src_nodata=np.nan,
                      dst_transform=tr, dst_crs='EPSG:4326', dst_nodata=np.nan,
                      resampling=Resampling.cubic, num_threads=4)
            ok = np.isfinite(tmp)
            dem[ok] = tmp[ok]
            # water fraction; outside this tile's footprint -> -1 (unknown)
            wf = np.full((M8_H, M8_W), -1, np.float32)
            reproject(water.astype(np.float32), wf, src_transform=ds.transform, src_crs=ds.crs,
                      dst_transform=tr, dst_crs='EPSG:4326', dst_nodata=-1, src_nodata=None,
                      resampling=Resampling.bilinear, num_threads=4)
            cov = wf >= 0
            wat[cov] = np.minimum(wat[cov], wf[cov]) if t != TILES[0] else wf[cov]
    np.save(TMP + '/dem8.npy', dem)
    np.save(TMP + '/demwater8.npy', wat)
    print('dem8 land frac', np.isfinite(dem).mean(), 'water frac (>0.5)', (wat > 0.5).mean(),
          'land min/max', np.nanmin(dem), np.nanmax(dem))


if __name__ == '__main__':
    main()
