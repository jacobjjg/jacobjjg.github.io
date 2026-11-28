#!/usr/bin/env python3
"""Catalogue Sentinel-2 L2A COG scenes over Oahu (MGRS 4QFJ/4QEJ/4QFK/4QEK) and
score each acquisition date by its SCL cloud/shadow fraction over Oahu's land.

Output: TMP/s2_catalog.json  (list of per-date records sorted by land-cloud fraction)
"""
import os, re, json, sys, urllib.request, concurrent.futures as cf
import numpy as np
from common import *
gdal_env()
import rasterio
from rasterio.windows import from_bounds
from rasterio.warp import reproject, Resampling

BUCKET = 'https://sentinel-cogs.s3.us-west-2.amazonaws.com'
TILES = ['FJ', 'EJ', 'FK', 'EK']
YEARS = range(2019, 2026)


def get(url, tries=4):
    for k in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                return r.read()
        except Exception as e:      # noqa
            err = e
    raise err


def list_scenes(tile, year, month):
    url = f'{BUCKET}/?list-type=2&prefix=sentinel-s2-l2a-cogs/4/Q/{tile}/{year}/{month}/&delimiter=/'
    t = get(url).decode()
    return re.findall(r'<Prefix>(sentinel-s2-l2a-cogs/4/Q/\w\w/\d+/\d+/[^<]+)/</Prefix>', t)


def fetch_meta(prefix):
    name = prefix.rsplit('/', 1)[1]
    try:
        d = json.loads(get(f'{BUCKET}/{prefix}/{name}.json'))
    except Exception as e:
        return None
    p = d['properties']
    return dict(prefix=prefix, name=name, tile=p.get('mgrs:grid_square'), datetime=p['datetime'],
                cloud=p.get('eo:cloud_cover'), nodata=p.get('s2:nodata_pixel_percentage'),
                baseline=p.get('s2:processing_baseline'), boa_applied=p.get('earthsearch:boa_offset_applied'),
                sun_el=p.get('view:sun_elevation'), sun_az=p.get('view:sun_azimuth'),
                product=p.get('s2:product_uri'), seq=p.get('s2:sequence'))


def land_mask_utm160():
    """Coarse (160 m) land mask on the UTM master grid from the 3DEP DEM."""
    dem = np.load(TMP + '/dem8.npy')
    land = (np.nan_to_num(dem, nan=0.0) > 0.5).astype(np.float32)
    h, w = UTM_H // 16, UTM_W // 16
    out = np.zeros((h, w), np.float32)
    from affine import Affine
    tr = Affine(160, 0, UTM_E0, 0, -160, UTM_N1)
    reproject(land, out, src_transform=rect_transform(ISLAND, M8_W, M8_H), src_crs='EPSG:4326',
              dst_transform=tr, dst_crs=f'EPSG:{UTM_EPSG}', resampling=Resampling.average)
    return out > 0.5, tr


def scl_coarse(prefix, tr, shape):
    """Read SCL overview (160 m) and paste on the coarse UTM master grid."""
    out = np.zeros(shape, np.uint8)
    with rasterio.open(f'{BUCKET}/{prefix}/SCL.tif') as ds:
        reproject(rasterio.band(ds, 1), out, dst_transform=tr, dst_crs=f'EPSG:{UTM_EPSG}',
                  resampling=Resampling.nearest, src_nodata=0, dst_nodata=0)
    return out


def main():
    os.makedirs(TMP, exist_ok=True)
    cache = TMP + '/s2_meta_raw.json'
    if os.path.exists(cache):
        metas = json.load(open(cache))
    else:
        jobs = [(t, y, m) for t in TILES for y in YEARS for m in range(1, 13)]
        with cf.ThreadPoolExecutor(6) as ex:
            prefixes = [p for lst in ex.map(lambda a: list_scenes(*a), jobs) for p in lst]
        print('scene prefixes', len(prefixes), flush=True)
        with cf.ThreadPoolExecutor(6) as ex:
            metas = [m for m in ex.map(fetch_meta, prefixes) if m]
        json.dump(metas, open(cache, 'w'))
    print('metas', len(metas), flush=True)

    # group by acquisition (date + relative orbit); keep the newest processing per tile
    groups = {}
    for m in metas:
        mo = re.search(r'_R(\d{3})_', m['product'] or '')
        orbit = mo.group(1) if mo else '000'
        key = m['datetime'][:10] + '_R' + orbit
        g = groups.setdefault(key, dict(key=key, date=m['datetime'][:10], orbit=orbit, tiles={}))
        prev = g['tiles'].get(m['tile'])
        if prev is None or (m['baseline'] or '') > (prev['baseline'] or ''):
            g['tiles'][m['tile']] = m
    print('acquisitions', len(groups), 'orbits', sorted({g['orbit'] for g in groups.values()}), flush=True)

    land, tr = land_mask_utm160()
    cand = [g for g in groups.values() if 'FJ' in g['tiles'] and (g['tiles']['FJ']['cloud'] or 100) < 45]
    print('candidates for SCL scoring', len(cand), flush=True)

    def score(g):
        try:
            scl = np.zeros(land.shape, np.uint8)
            for t in ('FK', 'EK', 'EJ', 'FJ'):
                if t in g['tiles']:
                    s = scl_coarse(g['tiles'][t]['prefix'], tr, land.shape)
                    scl = np.where(s > 0, s, scl)
            v = scl[land]
            g['land_nodata'] = float((v == 0).mean())
            bad = np.isin(v, (0, 1, 3, 8, 9, 10))
            g['land_bad'] = float(bad.mean())
            g['land_cloud'] = float(np.isin(v, (8, 9, 10)).mean())
            np.save(f"{TMP}/scl160/{g['key']}.npy", scl)
        except Exception as e:
            g['error'] = str(e)
        return g

    os.makedirs(TMP + '/scl160', exist_ok=True)
    with cf.ThreadPoolExecutor(6) as ex:
        res = list(ex.map(score, cand))
    res = [g for g in res if 'land_bad' in g]
    res.sort(key=lambda g: g['land_bad'])
    json.dump(res, open(TMP + '/s2_catalog.json', 'w'), indent=1)
    np.save(TMP + '/land160.npy', land)
    for g in res[:60]:
        fj = g['tiles']['FJ']
        print(g['key'], 'bad %.3f cloud %.3f nodata %.3f' % (g['land_bad'], g['land_cloud'], g['land_nodata']),
              'tiles', ''.join(sorted(g['tiles'])), 'sun_el %.0f' % fj['sun_el'], 'bl', fj['baseline'], fj['boa_applied'])


if __name__ == '__main__':
    main()
