"""QA drawing helpers: labelled lat/lon graticule on world-frame rasters."""
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from common import *


def _font(size):
    for p in ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
              '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf'):
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            pass
    return ImageFont.load_default()


def graticule(img, x0, x1, z0, z1, step, color=(255, 255, 0), font=12, width=1, label_every=1):
    """Draw a lat/lon grid on a PIL image covering world rect [x0,x1]x[z0,z1]."""
    W, H = img.size
    d = ImageDraw.Draw(img)
    f = _font(font)
    lon_w, lat_n = world_to_lonlat(x0, z0)
    lon_e, lat_s = world_to_lonlat(x1, z1)
    nd = max(0, int(np.ceil(-np.log10(step) - 1e-9)))
    k = 0
    for lon in np.arange(np.ceil(lon_w / step) * step, lon_e + 1e-9, step):
        px = (lon - lon_w) / (lon_e - lon_w) * W
        d.line([(px, 0), (px, H)], fill=color, width=width)
        if k % label_every == 0:
            d.text((px + 3, 2), f'{lon:.{nd}f}', fill=color, font=f, stroke_width=2, stroke_fill=(0, 0, 0))
        k += 1
    k = 0
    for lat in np.arange(np.ceil(lat_s / step) * step, lat_n + 1e-9, step):
        py = (lat_n - lat) / (lat_n - lat_s) * H
        d.line([(0, py), (W, py)], fill=color, width=width)
        if k % label_every == 0:
            d.text((3, py + 2), f'{lat:.{nd}f}', fill=color, font=f, stroke_width=2, stroke_fill=(0, 0, 0))
        k += 1
    return img


def crop_m8(arr, lon_w, lon_e, lat_s, lat_n):
    """Crop an M8-grid array to a lon/lat box; returns (crop, x0, x1, z0, z1)."""
    i0, j0 = lonlat_to_px(ISLAND, M8_W, M8_H, lon_w, lat_n)
    i1, j1 = lonlat_to_px(ISLAND, M8_W, M8_H, lon_e, lat_s)
    i0, j0, i1, j1 = [int(round(float(v) + 0.5)) for v in (i0, j0, i1, j1)]
    i0, j0 = max(i0, 0), max(j0, 0)
    c = arr[j0:j1, i0:i1]
    return c, ISLAND['X0'] + i0 * 8.0, ISLAND['X0'] + i1 * 8.0, ISLAND['Z0'] + j0 * 8.0, ISLAND['Z0'] + j1 * 8.0


def mark(img, x0, x1, z0, z1, lon, lat, label=None, color=(255, 0, 255), r=5):
    W, H = img.size
    x, z = lonlat_to_world(lon, lat)
    px = (x - x0) / (x1 - x0) * W
    py = (z - z0) / (z1 - z0) * H
    d = ImageDraw.Draw(img)
    d.ellipse([px - r, py - r, px + r, py + r], outline=color, width=2)
    if label:
        d.text((px + r + 2, py - 6), label, fill=color, font=_font(12), stroke_width=2, stroke_fill=(0, 0, 0))
    return img


def depth_colormap(elev, water, px=8.0, contours=(2, 5, 10, 14, 20, 50, 100, 200, 400)):
    """RGB uint8 visualisation: hillshaded hypsometric land, colour-mapped depth with contours."""
    e = np.asarray(elev, np.float32)
    gy, gx = np.gradient(e, px)
    hs = np.clip(0.75 + 0.9 * (-gx * 0.7 - gy * 0.7) / np.sqrt(1 + gx * gx + gy * gy), 0.25, 1.25)
    t = np.clip(e / 1000.0, 0, 1) ** 0.5
    land = np.stack([110 + 120 * t, 140 + 60 * t - 40 * t * t, 80 + 60 * t], -1) * hs[..., None]
    d = np.clip(-e, 0, None)
    stops_d = np.array([0, 1, 2.5, 5, 10, 15, 30, 100, 300, 600], float)
    stops_c = np.array([[235, 250, 235], [170, 240, 220], [90, 220, 215], [40, 185, 215], [30, 135, 200], [30, 100, 180],
                        [25, 70, 150], [20, 45, 115], [12, 25, 80], [5, 10, 45]], float)
    wat = np.stack([np.interp(d, stops_d, stops_c[:, k]) for k in range(3)], -1)
    img = np.where(np.asarray(water)[..., None], wat, land)
    for c in contours:
        b = d >= c
        edge = (b ^ np.roll(b, 1, 0)) | (b ^ np.roll(b, 1, 1))
        img[edge & np.asarray(water)] = (255, 255, 255) if c in (10, 100) else (10, 10, 10)
    return np.clip(img, 0, 255).astype(np.uint8)
