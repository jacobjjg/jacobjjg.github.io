#!/usr/bin/env python3
"""Warp the UTM cloud-free composite into the 8 m world-frame master grid.

Outputs (TMP/m8/): B02,B03,B04,B08,B11 .npy uint16 (reflectance*10000, 0 = no data),
                   wetfreq.npy uint8 (% of clear dates classified water), nclear.npy uint8
"""
import os, numpy as np
from rasterio.warp import reproject, Resampling
from common import *


def main():
    os.makedirs(TMP + '/m8', exist_ok=True)
    dst_tr = rect_transform(ISLAND, M8_W, M8_H)
    for b in ['B02', 'B03', 'B04', 'B08', 'B11', 'wetfreq', 'nclear']:
        src = np.load(f'{TMP}/comp/{b}.npy')
        is_band = b.startswith('B')
        out = np.zeros((M8_H, M8_W), np.float32)
        if b == 'B11':     # native 20 m, stored nearest-upsampled: soften the 2x2 blocks first
            from scipy import ndimage as ndi
            src = ndi.uniform_filter(src.astype(np.float32), 2, mode='nearest')
        reproject(src.astype(np.float32), out, src_transform=utm_transform(), src_crs=f'EPSG:{UTM_EPSG}',
                  src_nodata=0 if is_band else None, dst_transform=dst_tr, dst_crs='EPSG:4326',
                  dst_nodata=0 if is_band else None,
                  resampling=Resampling.cubic if is_band else Resampling.bilinear, num_threads=4)
        if is_band:
            out = np.clip(np.rint(out), 0, 65535).astype(np.uint16)
        else:
            out = np.clip(np.rint(out), 0, 255).astype(np.uint8)
        np.save(f'{TMP}/m8/{b}.npy', out)
        print(b, out.dtype, out.shape, 'zero frac', (out == 0).mean())


if __name__ == '__main__':
    main()
