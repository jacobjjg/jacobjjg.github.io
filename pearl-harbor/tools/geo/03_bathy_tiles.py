#!/usr/bin/env python3
"""Mapzen/AWS terrarium terrain tiles (zoom 12) -> open-ocean sea floor on the
8 m world-frame master grid.  Near-shore values in these tiles are unusable
(interpolated shore heights); 05_build.py only uses them far from the coast.

Output: TMP/tiles8.npy float32 (10240 x 8192)
"""
import os, math, subprocess, numpy as np
from PIL import Image
from affine import Affine
from rasterio.warp import reproject, Resampling
from common import *

Z = 12
X_RANGE = range(246, 256)     # lon -158.379 .. -157.500
Y_RANGE = range(1794, 1802)   # lat  21.780 ..  21.126
URL = 'https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png'
R = 6378137.0


def main():
    d = DL + '/terr12'
    os.makedirs(d, exist_ok=True)
    mos = np.zeros((len(Y_RANGE) * 256, len(X_RANGE) * 256), np.float32)
    for yi, y in enumerate(Y_RANGE):
        for xi, x in enumerate(X_RANGE):
            p = f'{d}/{x}_{y}.png'
            pre = f'{DEMDIR}/{Z}/{x}_{y}.png'          # tiles fetched earlier by the orchestrator
            if not os.path.exists(p):
                if os.path.exists(pre):
                    subprocess.check_call(['cp', pre, p])
                else:
                    subprocess.check_call(['curl', '-sf', '--retry', '3', '-o', p, URL.format(z=Z, x=x, y=y)])
            a = np.asarray(Image.open(p).convert('RGB')).astype(np.float32)
            mos[yi * 256:(yi + 1) * 256, xi * 256:(xi + 1) * 256] = a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768
    world = 2 * math.pi * R
    res = world / (256 * 2 ** Z)
    src_tr = Affine(res, 0, -world / 2 + X_RANGE[0] * 256 * res, 0, -res, world / 2 - Y_RANGE[0] * 256 * res)
    out = np.zeros((M8_H, M8_W), np.float32)
    reproject(mos, out, src_transform=src_tr, src_crs='EPSG:3857',
              dst_transform=rect_transform(ISLAND, M8_W, M8_H), dst_crs='EPSG:4326',
              resampling=Resampling.cubic, num_threads=4)
    np.save(TMP + '/tiles8.npy', out)
    print('tiles8', out.shape, out.min(), out.max())


if __name__ == '__main__':
    main()
