"""Shared constants and helpers for the Pearl Harbor geo raster pipeline.

World frame (shared by the whole project):
  origin lat0 = 21.3650, lon0 = -157.9600 (Ford Island)
  x east  (m) =  (lon - lon0) * 103715.50
  z south (m) = -(lat - lat0) * 110721.79
Because x is linear in lon and z linear in lat, every world-frame raster is an
ordinary north-up EPSG:4326 raster with a non-square pixel, which lets
rasterio/GDAL warp straight into it.
"""
import os
import numpy as np

LAT0, LON0 = 21.3650, -157.9600
MX, MZ = 103715.50, 110721.79          # metres per degree lon / lat

ISLAND = dict(X0=-40960.0, X1=40960.0, Z0=-45568.0, Z1=19968.0)
HARBOR = dict(X0=-8192.0, X1=8192.0, Z0=-5120.0, Z1=11264.0)

# master working grid: 8 m over the ISLAND rect (harbor grid is an exact crop,
# the 32 m island grid an exact 4x4 block reduction)
M8_W, M8_H = 10240, 8192
HARBOR_COL0 = int((HARBOR['X0'] - ISLAND['X0']) / 8)   # 4096
HARBOR_ROW0 = int((HARBOR['Z0'] - ISLAND['Z0']) / 8)   # 5056
HARBOR_N = 2048

SCRATCH = os.environ.get(
    'PH_SCRATCH',
    '/tmp/claude-0/-home-user-jacobjjg-github-io/6c8bef42-c6d1-5e3f-b90c-54fd254d3e2e/scratchpad')
WORK = os.path.join(SCRATCH, 'geo-work', 'terrain')
DL = os.path.join(WORK, 'dl')
TMP = os.path.join(WORK, 'tmp')
FINAL = os.path.join(WORK, 'final')
REF = os.path.join(SCRATCH, 'ref')
DEMDIR = os.path.join(SCRATCH, 'dem')
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
ASSETS = os.path.join(REPO, 'assets', 'geo')

# UTM zone 4N master mosaic grid for Sentinel-2 (all four MGRS tiles share the
# same 10 m lattice): covers the ISLAND rect with margin.
UTM_EPSG = 32604
UTM_E0, UTM_N1 = 566000.0, 2409500.0     # upper-left corner
UTM_W, UTM_H = 8350, 6750                # 10 m pixels -> E 566000..649500, N 2342000..2409500


def lonlat_to_world(lon, lat):
    return (np.asarray(lon) - LON0) * MX, -(np.asarray(lat) - LAT0) * MZ


def world_to_lonlat(x, z):
    return LON0 + np.asarray(x) / MX, LAT0 - np.asarray(z) / MZ


def rect_transform(rect, w, h):
    """Affine (EPSG:4326 degrees) for a world-frame raster of w x h pixels."""
    from affine import Affine
    lon_w, lat_n = world_to_lonlat(rect['X0'], rect['Z0'])
    dx = (rect['X1'] - rect['X0']) / w / MX
    dy = (rect['Z1'] - rect['Z0']) / h / MZ
    return Affine(dx, 0.0, float(lon_w), 0.0, -dy, float(lat_n))


def world_to_px(rect, w, h, x, z):
    """World metres -> fractional pixel indices (col, row); pixel centre = i+0.5."""
    i = (np.asarray(x) - rect['X0']) / (rect['X1'] - rect['X0']) * w - 0.5
    j = (np.asarray(z) - rect['Z0']) / (rect['Z1'] - rect['Z0']) * h - 0.5
    return i, j


def lonlat_to_px(rect, w, h, lon, lat):
    x, z = lonlat_to_world(lon, lat)
    return world_to_px(rect, w, h, x, z)


def utm_transform():
    from affine import Affine
    return Affine(10.0, 0.0, UTM_E0, 0.0, -10.0, UTM_N1)


def gdal_env():
    """Environment for remote COG range reads through the session proxy."""
    os.environ.setdefault('CURL_CA_BUNDLE', '/root/.ccr/ca-bundle.crt')
    os.environ.setdefault('GDAL_DISABLE_READDIR_ON_OPEN', 'EMPTY_DIR')
    os.environ.setdefault('CPL_VSIL_CURL_ALLOWED_EXTENSIONS', '.tif')
    os.environ.setdefault('GDAL_HTTP_MAX_RETRY', '5')
    os.environ.setdefault('GDAL_HTTP_RETRY_DELAY', '3')
    os.environ.setdefault('GDAL_HTTP_MULTIRANGE', 'YES')
    os.environ.setdefault('GDAL_HTTP_MERGE_CONSECUTIVE_RANGES', 'YES')
    os.environ.setdefault('AWS_NO_SIGN_REQUEST', 'YES')
    os.environ.setdefault('VSI_CACHE', 'TRUE')
    os.environ.setdefault('GDAL_CACHEMAX', '512')


def encode_height_png(elev, water, path):
    """8-bit RGB: v = R*256+G, elevation = v*0.05-600; B = 255 on water."""
    from PIL import Image
    v = np.clip(np.rint((elev.astype(np.float64) + 600.0) / 0.05), 0, 65535).astype(np.uint16)
    rgb = np.zeros(elev.shape + (3,), np.uint8)
    rgb[..., 0] = v >> 8
    rgb[..., 1] = v & 255
    rgb[..., 2] = np.where(water, 255, 0)
    Image.fromarray(rgb, 'RGB').save(path, optimize=True)   # Pillow writes no gAMA/iCCP unless asked
