#!/usr/bin/env python3
"""Fetch the selected Sentinel-2 L2A acquisitions (window reads of the public
COGs) and mosaic the MGRS tiles of each date onto the 10 m UTM master grid.

Selection: greedy over the catalogue (02_s2_catalog.py) - start from the dates
with the least cloud over Oahu's land and keep adding dates until every land
cell (160 m) has been seen clear at least MIN_CLEAR times (or MAX_SCENES).

Output per date: DL/s2/<key>_{B02,B03,B04,B08}.npy (uint16, 10 m),
                 DL/s2/<key>_{B11,SCL}.npy (20 m), TMP/s2_selected.json
"""
import os, sys, json, numpy as np, concurrent.futures as cf
from common import *
gdal_env()
import rasterio
from rasterio.windows import from_bounds, Window

BUCKET = 'https://sentinel-cogs.s3.us-west-2.amazonaws.com'
MIN_CLEAR, MAX_SCENES, FIRST_N = 8, 26, 10
BANDS10 = ['B02', 'B03', 'B04', 'B08']
BANDS20 = ['B11', 'SCL']
TILE_ORDER = ['EK', 'FK', 'EJ', 'FJ']       # later tiles overwrite earlier ones (identical data in overlaps)


def select():
    cat = json.load(open(TMP + '/s2_catalog.json'))
    land = np.load(TMP + '/land160.npy')
    cat = [g for g in cat if g['land_nodata'] < 0.02 and 'EJ' in g['tiles'] and 'FJ' in g['tiles'] and 'FK' in g['tiles']]
    clear = {g['key']: np.isin(np.load(f"{TMP}/scl160/{g['key']}.npy"), (2, 4, 5, 6, 7, 11)) & land for g in cat}
    chosen = [g['key'] for g in cat[:FIRST_N]]
    count = sum(clear[k].astype(np.int16) for k in chosen)
    pool = [g['key'] for g in cat[FIRST_N:160]]
    while len(chosen) < MAX_SCENES and pool:
        need = land & (count < MIN_CLEAR)
        if need.sum() < 0.002 * land.sum():
            break
        gains = [(clear[k] & need).sum() for k in pool]
        b = int(np.argmax(gains))
        if gains[b] == 0:
            break
        k = pool.pop(b)
        chosen.append(k)
        count += clear[k]
    by = {g['key']: g for g in cat}
    sel = [by[k] for k in chosen]
    print('selected', len(sel), 'land cells with <%d clear obs: %.4f, with <3: %.4f, zero: %.5f' % (
        MIN_CLEAR, (land & (count < MIN_CLEAR)).sum() / land.sum(), (land & (count < 3)).sum() / land.sum(),
        (land & (count == 0)).sum() / land.sum()))
    json.dump(sel, open(TMP + '/s2_selected.json', 'w'), indent=1)
    np.save(TMP + '/clearcount160.npy', count)
    return sel


def read_band(g, band):
    res = 10 if band in BANDS10 else 20
    out_path = f"{DL}/s2/{g['key']}_{band}.npy"
    if os.path.exists(out_path):
        return out_path
    W, H = UTM_W * 10 // res, UTM_H * 10 // res
    out = np.zeros((H, W), np.uint8 if band == 'SCL' else np.uint16)
    e0, n1 = UTM_E0, UTM_N1
    e1, n0 = e0 + UTM_W * 10, n1 - UTM_H * 10
    for t in TILE_ORDER:
        m = g['tiles'].get(t)
        if not m:
            continue
        for attempt in range(4):
            try:
                with rasterio.open(f"{BUCKET}/{m['prefix']}/{band}.tif") as ds:
                    b = ds.bounds
                    le, ri = max(e0, b.left), min(e1, b.right)
                    bo, to = max(n0, b.bottom), min(n1, b.top)
                    if ri <= le or to <= bo:
                        break
                    win = from_bounds(le, bo, ri, to, ds.transform).round_offsets().round_lengths()
                    a = ds.read(1, window=win)
                    c0 = int(round((le - e0) / res)); r0 = int(round((n1 - to) / res))
                    sub = out[r0:r0 + a.shape[0], c0:c0 + a.shape[1]]
                    if not m.get('boa_applied') and (m.get('baseline') or '00') >= '04.00' and band != 'SCL':
                        a = np.where(a > 0, np.maximum(a.astype(np.int32) - 1000, 1), 0).astype(np.uint16)
                    np.copyto(sub, a, where=a > 0)
                break
            except Exception as e:
                print('retry', g['key'], t, band, e, flush=True)
        else:
            raise RuntimeError(f"failed {g['key']} {t} {band}")
    np.save(out_path, out)
    return out_path


def main():
    os.makedirs(DL + '/s2', exist_ok=True)
    sel = select()
    for g in sel:
        print(g['key'], 'land_bad %.3f' % g['land_bad'], ''.join(sorted(g['tiles'])), flush=True)
    if '--select-only' in sys.argv:
        return
    jobs = [(g, b) for g in sel for b in BANDS20 + BANDS10]
    with cf.ThreadPoolExecutor(5) as ex:
        for i, p in enumerate(ex.map(lambda a: read_band(*a), jobs)):
            if i % 6 == 5:
                print('done', i + 1, '/', len(jobs), flush=True)


if __name__ == '__main__':
    main()
