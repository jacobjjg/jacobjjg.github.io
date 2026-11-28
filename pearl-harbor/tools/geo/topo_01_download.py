#!/usr/bin/env python3
"""Download the 1952-54 USGS 1:24,000 quadrangles of Oahu (Historical Topographic Map
Collection GeoTIFFs) plus the modern 3DEP 1/3 arc-second DEM used as registration control,
and warp the DEM into an 8 m world-frame grid (ISLAND rect, 10240 x 8192).

Sheet selection (from the bucket listing of StagedProducts/Maps/HistoricalTopo/GeoTIFF/HI/):
every Oahu 7.5' quadrangle has exactly one pre-1955 edition (1952, 1953 or 1954); two of them
(Kahana, Waimea) exist as two scans of the same edition - the cleaner scan is used.  The
bucket holds no 1:62,500 (1928-43) sheet of Oahu: all 68 1:62,500 files are Hawaii Island,
Lanai or Kahoolawe.  The only other pre-1955 Oahu sheet is the AMS 1:250,000 (1954).

Outputs: DL/*.tif, TMP/topo_dem8.npy (float32 elevation; hydro-flattened water and no-data = 0).
"""
import os
import subprocess
import urllib.parse
import numpy as np

from topo_common import *

DEM_BASE = 'https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/13/TIFF/current'
DEM_TILES = ['n22w158', 'n22w159']


def fetch(url, path):
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return
    print('GET', url, flush=True)
    subprocess.check_call(['curl', '-sS', '--fail', '--retry', '3', '-o', path + '.part', url])
    os.replace(path + '.part', path)


def main():
    os.makedirs(DL, exist_ok=True)
    os.makedirs(TMP, exist_ok=True)
    for rec in SHEETS + EXTRA:
        fetch(S3 + urllib.parse.quote(rec['file']), os.path.join(DL, local_name(rec['file'])))
    os.makedirs(os.path.join(DL, 'dem'), exist_ok=True)
    import rasterio
    from rasterio.warp import reproject, Resampling
    from affine import Affine
    W, H = 10240, 8192
    lon_w, lat_n = world_to_lonlat(ISLAND['X0'], ISLAND['Z0'])
    tr = Affine(8.0 / MX, 0, float(lon_w), 0, -8.0 / MZ, float(lat_n))
    dem = np.zeros((H, W), np.float32)
    for t in DEM_TILES:
        p = os.path.join(DL, 'dem', f'USGS_13_{t}.tif')
        fetch(f'{DEM_BASE}/{t}/USGS_13_{t}.tif', p)
        with rasterio.open(p) as ds:
            a = ds.read(1)
            a[(a == ds.nodata) | ~np.isfinite(a)] = 0.0
            tmp = np.full((H, W), -9999, np.float32)
            reproject(a, tmp, src_transform=ds.transform, src_crs=ds.crs, dst_transform=tr,
                      dst_crs='EPSG:4326', dst_nodata=-9999, resampling=Resampling.bilinear, num_threads=4)
            ok = tmp > -9000
            dem[ok] = np.where(np.abs(dem[ok]) > np.abs(tmp[ok]), dem[ok], tmp[ok])
    np.save(DEM8, dem)
    print('dem8', dem.shape, 'land frac', float((dem > 0.3).mean()), 'max', float(dem.max()))


if __name__ == '__main__':
    main()
