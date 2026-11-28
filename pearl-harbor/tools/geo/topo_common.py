"""Shared helpers for the 1952-54 USGS topographic map reference pack ("topo" task).

Self-contained on purpose (does not import the terrain pipeline's common.py) so the
two pipelines can evolve independently; the world-frame constants are identical.

World frame
  origin lat0 = 21.3650, lon0 = -157.9600 (Ford Island)
  x east  (m) =  (lon - lon0) * 103715.50
  z south (m) = -(lat - lat0) * 110721.79      (north is -z)
Raster convention: a raster covering [X0,X1] x [Z0,Z1] has column 0 at X0 (west) and
row 0 at Z0 (north); pixel (i,j) centre is x = X0+(i+0.5)*(X1-X0)/W, z = Z0+(j+0.5)*(Z1-Z0)/H.

Georeferencing of the scans
  The HTMC GeoTIFFs are in a per-sheet polyconic projection (Clarke 1866) whose origin is
  the bottom-centre of the 7.5' quadrangle.  Their geographic coordinates are OLD HAWAIIAN
  DATUM values (most files are mislabelled "NAD27"; the map collar says Old Hawaiian datum).
  The Oahu quads of this edition are offset 1.5' in longitude from the modern 7.5' lattice
  (neat lines at 157d54', 158d01'30" ...).
  world (WGS84) -> Old Hawaiian uses the NGA 3-parameter shift for Oahu
  (dx,dy,dz = 58,-283,-182 m, EPSG:1525-family "Old Hawaiian to WGS 84 (7)") followed by an
  empirically measured residual translation (see topo_02_register.py / registration.json).
"""
import json
import os
import numpy as np

LAT0, LON0 = 21.3650, -157.9600
MX, MZ = 103715.50, 110721.79            # metres per degree of lon / lat

ISLAND = dict(X0=-40960.0, X1=40960.0, Z0=-45568.0, Z1=19968.0)
HARBOR = dict(X0=-8192.0, X1=8192.0, Z0=-5120.0, Z1=11264.0)

SCRATCH = os.environ.get(
    'PH_SCRATCH',
    '/tmp/claude-0/-home-user-jacobjjg-github-io/6c8bef42-c6d1-5e3f-b90c-54fd254d3e2e/scratchpad')
WORK = os.path.join(SCRATCH, 'geo-work', 'topo')
DL = os.path.join(WORK, 'dl')
TMP = os.path.join(WORK, 'tmp')
REF = os.path.join(SCRATCH, 'ref')
REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
ASSETS = os.path.join(REPO, 'assets', 'geo')
DEM8 = os.path.join(TMP, 'topo_dem8.npy')     # modern 3DEP DEM on the 8 m ISLAND grid (built by topo_01_download.py)
REG_JSON = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'topo_registration.json')

S3 = 'https://prd-tnm.s3.amazonaws.com/StagedProducts/Maps/HistoricalTopo/GeoTIFF/HI/'

# name, file on S3, map date, quad SW-corner latitude (deg, Old Hawaiian), central meridian.
# Every quad spans 7.5' x 7.5': lat [lat0, lat0+0.125], lon [cm-0.0625, cm+0.0625].
SHEETS = [
    dict(name='Kaena',      file='HI_Kaena_349316_1954_24000_geo.tif',              year=1954, lat0=21.500, cm=-158.2125),
    dict(name='Waianae',    file='HI_Waianae_349773_1954_24000_geo.tif',            year=1954, lat0=21.375, cm=-158.2125),
    dict(name='Waimea',     file='HI_Waimea_349788_1952_24000_geo.tif',             year=1952, lat0=21.625, cm=-158.0875),
    dict(name='Haleiwa',    file='HI_Haleiwa_349240_1953_24000_geo.tif',            year=1953, lat0=21.500, cm=-158.0875),
    dict(name='Schofield Barracks', file='HI_Schofield Barracks_349746_1953_24000_geo.tif', year=1953, lat0=21.375, cm=-158.0875),
    dict(name='Ewa',        file='HI_Ewa_349219_1953_24000_geo.tif',                year=1953, lat0=21.250, cm=-158.0875),
    dict(name='Kahuku',     file='HI_Kahuku_349333_1954_24000_geo.tif',             year=1954, lat0=21.625, cm=-157.9625),
    dict(name='Hauula',     file='HI_Hauula_349263_1953_24000_geo.tif',             year=1953, lat0=21.500, cm=-157.9625),
    dict(name='Waipahu',    file='HI_Waipahu_349798_1954_24000_geo.tif',            year=1954, lat0=21.375, cm=-157.9625),
    dict(name='Puuloa',     file='HI_Puuloa_349733_1953_24000_geo.tif',             year=1953, lat0=21.250, cm=-157.9625),
    dict(name='Kahana',     file='HI_Kahana_349325_1954_24000_geo.tif',             year=1954, lat0=21.500, cm=-157.8375),
    dict(name='Kaneohe',    file='HI_Kaneohe_349371_1954_24000_geo.tif',            year=1954, lat0=21.375, cm=-157.8375),
    dict(name='Honolulu',   file='HI_Honolulu_349300_1953_24000_geo.tif',           year=1953, lat0=21.250, cm=-157.8375),
    dict(name='Mokapu',     file='HI_Mokapu_349586_1952_24000_geo.tif',             year=1952, lat0=21.375, cm=-157.7125),
    dict(name='Koko Head',  file='HI_Koko Head_349485_1952_24000_geo.tif',          year=1952, lat0=21.250, cm=-157.7125),
]
# duplicate scans of the same edition (kept only for comparison) and the small-scale sheet
EXTRA = [
    dict(name='Kahana (alt scan)', file='HI_Kahana_349324_1954_24000_geo.tif', year=1954),
    dict(name='Waimea (alt scan)', file='HI_Waimea_349787_1952_24000_geo.tif', year=1952),
    dict(name='Oahu 1:250,000 (AMS W532 NF 4-11)', file='HI_Oahu_349935_1954_250000_geo.tif', year=1954),
]
SEA_RGB = (203, 226, 214)      # flat fill for sea outside sheet coverage (close to the map's water tint)


def local_name(f):
    return f.replace(' ', '_')


def lonlat_to_world(lon, lat):
    return (np.asarray(lon, float) - LON0) * MX, -(np.asarray(lat, float) - LAT0) * MZ


def world_to_lonlat(x, z):
    return LON0 + np.asarray(x, float) / MX, LAT0 - np.asarray(z, float) / MZ


def rect_px_centres(rect, w, h):
    """1-D arrays of the world x of column centres and world z of row centres."""
    xs = rect['X0'] + (np.arange(w) + 0.5) * (rect['X1'] - rect['X0']) / w
    zs = rect['Z0'] + (np.arange(h) + 0.5) * (rect['Z1'] - rect['Z0']) / h
    return xs, zs


def world_to_px(rect, w, h, x, z):
    """World metres -> fractional pixel indices (pixel centre = integer index)."""
    i = (np.asarray(x, float) - rect['X0']) / (rect['X1'] - rect['X0']) * w - 0.5
    j = (np.asarray(z, float) - rect['Z0']) / (rect['Z1'] - rect['Z0']) * h - 0.5
    return i, j


# --------------------------------------------------------------------------- datum
_OHD2WGS = None


def _helmert():
    global _OHD2WGS
    if _OHD2WGS is None:
        import pyproj
        _OHD2WGS = pyproj.Transformer.from_pipeline(
            '+proj=pipeline +step +proj=unitconvert +xy_in=deg +xy_out=rad '
            '+step +proj=cart +ellps=clrk66 '
            '+step +proj=helmert +x=58 +y=-283 +z=-182 '
            '+step +inv +proj=cart +ellps=WGS84 '
            '+step +proj=unitconvert +xy_in=rad +xy_out=deg')
    return _OHD2WGS


def wgs_to_ohd(lon, lat):
    """WGS84 lon/lat -> Old Hawaiian lon/lat (3-parameter Oahu shift, no residual)."""
    lo, la, _ = _helmert().transform(np.asarray(lon, float), np.asarray(lat, float),
                                     np.zeros_like(np.asarray(lon, float)), direction='INVERSE')
    return lo, la


def ohd_to_wgs(lon, lat):
    lo, la, _ = _helmert().transform(np.asarray(lon, float), np.asarray(lat, float),
                                     np.zeros_like(np.asarray(lon, float)))
    return lo, la


def load_registration():
    """Residual translation (metres, world frame) of the map content relative to truth,
    measured against the modern DEM: content appears at truth + (dx, dz)."""
    if os.path.exists(REG_JSON):
        with open(REG_JSON) as f:
            return json.load(f)
    return dict(global_shift=[0.0, 0.0], sheets={})


# --------------------------------------------------------------------------- sheets
def _polyfit2(u, v, f, deg=3):
    terms = [(i, j) for i in range(deg + 1) for j in range(deg + 1 - i)]
    A = np.stack([u ** i * v ** j for i, j in terms], 1)
    c, *_ = np.linalg.lstsq(A, f, rcond=None)
    return terms, c, float(np.abs(A @ c - f).max())


def _polyval2(terms, c, u, v):
    out = np.zeros(np.broadcast(u, v).shape, np.float64)
    for (i, j), k in zip(terms, c):
        out += k * (u ** i) * (v ** j)
    return out


class Sheet:
    """One scanned quadrangle: pixel access plus world <-> scan-pixel mapping."""

    def __init__(self, rec, reg=None):
        import pyproj
        self.rec = rec
        self.name = rec['name']
        self.path = os.path.join(DL, local_name(rec['file']))
        self.lat0, self.cm = rec['lat0'], rec['cm']
        self.lon_w, self.lon_e = self.cm - 0.0625, self.cm + 0.0625
        self.lat_s, self.lat_n = self.lat0, self.lat0 + 0.125
        self.proj = pyproj.Proj(proj='poly', lat_0=self.lat0, lon_0=self.cm, ellps='clrk66')
        import rasterio
        with rasterio.open(self.path) as ds:
            self.transform = ds.transform
            self.width, self.height = ds.width, ds.height
        reg = reg or load_registration()
        g = reg.get('global_shift', [0.0, 0.0])
        s = reg.get('sheets', {}).get(self.name, g)
        self.shift = (float(s[0]), float(s[1]))        # content = truth + shift
        self._img = None
        self._fit()

    # world -> scan pixel as a cubic polynomial (the exact mapping is smooth; fit error << 0.01 px)
    def _fit(self):
        lo = np.linspace(self.lon_w - 0.03, self.lon_e + 0.03, 25)
        la = np.linspace(self.lat_s - 0.02, self.lat_n + 0.02, 25)
        LO, LA = np.meshgrid(lo, la)
        col, row = self.ohd_to_px(LO.ravel(), LA.ravel())
        wlo, wla = ohd_to_wgs(LO.ravel(), LA.ravel())
        x, z = lonlat_to_world(wlo, wla)
        self._x0, self._z0 = x.mean(), z.mean()
        u, v = (x - self._x0) / 1e4, (z - self._z0) / 1e4
        self._tc, self._cc, e1 = _polyfit2(u, v, col)
        self._tr, self._cr, e2 = _polyfit2(u, v, row)
        self._tlo, self._clo, e3 = _polyfit2(u, v, LO.ravel() - self.cm)
        self._tla, self._cla, e4 = _polyfit2(u, v, LA.ravel() - self.lat0)
        self.fit_err = (e1, e2, e3 * MX, e4 * MZ)

    def ohd_to_px(self, lon, lat):
        """Old Hawaiian lon/lat -> scan pixel (col,row), integer = pixel centre."""
        X, Y = self.proj(lon, lat)
        t = self.transform
        col = (np.asarray(X) - t.c) / t.a - 0.5
        row = (np.asarray(Y) - t.f) / t.e - 0.5
        return col, row

    def world_to_px(self, x, z, corrected=True):
        """World metres -> scan pixel (col,row).  x, z broadcastable arrays."""
        sx, sz = self.shift if corrected else (0.0, 0.0)
        u = (np.asarray(x, float) - sx - self._x0) / 1e4
        v = (np.asarray(z, float) - sz - self._z0) / 1e4
        return _polyval2(self._tc, self._cc, u, v), _polyval2(self._tr, self._cr, u, v)

    def world_to_quad(self, x, z, shift):
        """World metres -> (fractional position across the quad) using a given content shift.
        Returns (fx, fy) with 0..1 inside the neat line (fx west->east, fy south->north)."""
        u = (np.asarray(x, float) - shift[0] - self._x0) / 1e4
        v = (np.asarray(z, float) - shift[1] - self._z0) / 1e4
        dlo = _polyval2(self._tlo, self._clo, u, v)
        dla = _polyval2(self._tla, self._cla, u, v)
        return (dlo + 0.0625) / 0.125, dla / 0.125

    def px_to_world(self, col, row, corrected=True):
        t = self.transform
        X = t.c + (np.asarray(col, float) + 0.5) * t.a
        Y = t.f + (np.asarray(row, float) + 0.5) * t.e
        lo, la = self.proj(X, Y, inverse=True)
        wlo, wla = ohd_to_wgs(lo, la)
        x, z = lonlat_to_world(wlo, wla)
        if corrected:
            x, z = x + self.shift[0], z + self.shift[1]
        return x, z

    @property
    def img(self):
        if self._img is None:
            import rasterio
            with rasterio.open(self.path) as ds:
                self._img = np.ascontiguousarray(np.moveaxis(ds.read(), 0, 2))
        return self._img

    def free(self):
        self._img = None


def open_sheets(reg=None):
    reg = reg or load_registration()
    return [Sheet(r, reg) for r in SHEETS]


# Kaena sheet: the map body bleeds west of the neat line to show Kaena Point.  Polygon in scan
# pixels (col,row) of that tab, measured on the scan (inset 3 px from the tint edge).
KAENA_TAB_PX = None   # filled by kaena_tab() on first use


def kaena_tab(sheet):
    """Boolean mask (scan pixels) of the printed tab west of the Kaena neat line."""
    import cv2
    img = sheet.img
    col_nl, _ = sheet.ohd_to_px(sheet.lon_w, sheet.lat0 + 0.0625)
    c1 = int(col_nl) + 1
    r0, r1 = 2400, 3600
    sub = img[r0:r1, :c1].astype(np.int16)
    # paper is yellowish-white (B clearly below R); the tab is blue-green water tint / map ink
    paper = (sub[..., 0] > 225) & (sub[..., 1] > 225) & (sub[..., 0] - sub[..., 2] > 12)
    m = (~paper).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((25, 25), np.uint8))
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((41, 41), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
    k = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
    m = (lab == k).astype(np.uint8)
    m = cv2.erode(m, np.ones((9, 9), np.uint8))
    out = np.zeros(img.shape[:2], bool)
    out[r0:r1, :c1] = m.astype(bool)
    return out


# --------------------------------------------------------------------------- rendering
class Mosaic:
    """Samples the 15-sheet mosaic into arbitrary world-frame rasters."""

    SEAM_M = 7.0          # half-width (m) of the band around neat lines that is re-filled

    def __init__(self, reg=None, corrected=True):
        self.reg = reg or load_registration()
        self.sheets = open_sheets(self.reg)
        self.corrected = corrected
        self.gshift = tuple(self.reg.get('global_shift', [0.0, 0.0])) if corrected else (0.0, 0.0)
        self._tab = None

    def _kaena_tab_map(self):
        if self._tab is None:
            s = self.sheets[0]
            self._tab = kaena_tab(s).astype(np.uint8) * 255
        return self._tab

    def render(self, rect, w, h, fill=SEA_RGB, interp=None, return_index=False, fill_seams=True):
        """RGB uint8 (h,w,3) for the world rect sampled at pixel centres (no anti-aliasing:
        call with a pixel size close to the scan's 2.03 m and box-reduce afterwards)."""
        import cv2
        interp = cv2.INTER_LINEAR if interp is None else interp
        xs, zs = rect_px_centres(rect, w, h)
        X = xs[None, :]
        Z = zs[:, None]
        out = np.empty((h, w, 3), np.uint8)
        out[:] = np.array(fill, np.uint8)
        idx = np.full((h, w), -1, np.int8)
        seam = np.zeros((h, w), bool)
        px = (rect['X1'] - rect['X0']) / w
        for k, s in enumerate(self.sheets):
            # quick reject with the quad's world bounding box
            cx, cz = lonlat_to_world(*ohd_to_wgs(np.array([s.lon_w, s.lon_e]), np.array([s.lat_n, s.lat_s])))
            ext_w = 1500.0 if s.name == 'Kaena' else 0.0
            if cx[1] + 600 < rect['X0'] or cx[0] - 600 - ext_w > rect['X1'] or cz[1] + 600 < rect['Z0'] or cz[0] - 600 > rect['Z1']:
                continue
            i0 = max(0, int(np.searchsorted(xs, cx[0] - 600 - ext_w)))
            i1 = min(w, int(np.searchsorted(xs, cx[1] + 600)))
            j0 = max(0, int(np.searchsorted(zs, cz[0] - 600)))
            j1 = min(h, int(np.searchsorted(zs, cz[1] + 600)))
            if i1 <= i0 or j1 <= j0:
                continue
            Xs, Zs = X[:, i0:i1], Z[j0:j1]
            fx, fy = s.world_to_quad(Xs, Zs, self.gshift)
            inside = (fx >= 0) & (fx < 1) & (fy >= 0) & (fy < 1)
            sm = self.SEAM_M
            ex = sm / (0.125 * MX)
            ey = sm / (0.125 * MZ)
            near = inside & ((fx < ex) | (fx > 1 - ex) | (fy < ey) | (fy > 1 - ey))
            col, row = s.world_to_px(Xs, Zs, self.corrected)
            col = col.astype(np.float32)
            row = row.astype(np.float32)
            if s.name == 'Kaena':
                tab = cv2.remap(self._kaena_tab_map(), col, row, cv2.INTER_NEAREST,
                                borderMode=cv2.BORDER_CONSTANT, borderValue=0) > 0
                tab &= (fx < 0)
                tab_near = tab & (fx > -ex)
                inside = inside | tab
                near = near | tab_near
            if not inside.any():
                continue
            samp = cv2.remap(s.img, col, row, interp, borderMode=cv2.BORDER_REPLICATE)
            o = out[j0:j1, i0:i1]
            o[inside] = samp[inside]
            idx[j0:j1, i0:i1][inside] = k
            seam[j0:j1, i0:i1] |= near
        if fill_seams and seam.any():
            # replace the printed neat line by the nearest pixel that is clear of it
            from scipy import ndimage as ndi
            ys, xs_ = np.nonzero(seam)
            pad = int(np.ceil(4 * self.SEAM_M / px)) + 2
            # work per connected block to keep the distance transform small
            lab, n = ndi.label(cv2.dilate(seam.astype(np.uint8), np.ones((3, 3), np.uint8)))
            for sl in ndi.find_objects(lab):
                a0, a1 = max(0, sl[0].start - pad), min(h, sl[0].stop + pad)
                b0, b1 = max(0, sl[1].start - pad), min(w, sl[1].stop + pad)
                sub_seam = seam[a0:a1, b0:b1]
                if sub_seam.all():
                    continue
                _, (iy, ix) = ndi.distance_transform_edt(sub_seam, return_indices=True)
                sub = out[a0:a1, b0:b1]
                sub[sub_seam] = sub[iy[sub_seam], ix[sub_seam]]
        if return_index:
            return out, idx
        return out


def box_reduce(a, f):
    """Average f x f blocks of an (H,W[,C]) uint8/float array."""
    h, w = a.shape[0] // f, a.shape[1] // f
    b = a[:h * f, :w * f].reshape((h, f, w, f) + a.shape[2:]).astype(np.float32).mean(axis=(1, 3))
    return b


def draw_graticule(im, rect, step=0.005, label_every=1, color=(0, 90, 200), font_size=None):
    """Draw a labelled WGS84 lat/lon graticule on a PIL image covering the world rect."""
    from PIL import ImageDraw, ImageFont
    w, h = im.size
    d = ImageDraw.Draw(im, 'RGBA')
    fs = font_size or max(12, int(min(w, h) / 90))
    try:
        font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', fs)
    except Exception:
        font = ImageFont.load_default()
    lon_w, lat_n = world_to_lonlat(rect['X0'], rect['Z0'])
    lon_e, lat_s = world_to_lonlat(rect['X1'], rect['Z1'])
    nd = max(0, int(np.ceil(-np.log10(step) - 1e-9)))
    if step < 10 ** (-nd) * 0.99:
        nd += 1
    col = tuple(color) + (150,)
    k0, k1 = int(np.ceil(lon_w / step - 1e-9)), int(np.floor(lon_e / step + 1e-9))
    for n, k in enumerate(range(k0, k1 + 1)):
        lon = k * step
        i, _ = world_to_px(rect, w, h, *lonlat_to_world(lon, lat_n))
        d.line([(i, 0), (i, h)], fill=col, width=1)
        if k % label_every == 0:
            t = f'{lon:.{nd}f}'
            for yy in (2, h - fs - 4):
                bb = d.textbbox((i + 3, yy), t, font=font)
                d.rectangle(bb, fill=(255, 255, 255, 200))
                d.text((i + 3, yy), t, fill=tuple(color) + (255,), font=font)
    k0, k1 = int(np.ceil(lat_s / step - 1e-9)), int(np.floor(lat_n / step + 1e-9))
    for k in range(k0, k1 + 1):
        lat = k * step
        _, j = world_to_px(rect, w, h, *lonlat_to_world(lon_w, lat))
        d.line([(0, j), (w, j)], fill=col, width=1)
        if k % label_every == 0:
            t = f'{lat:.{nd}f}'
            tw = d.textlength(t, font=font)
            for xx in (2, w - tw - 4):
                bb = d.textbbox((xx, j - fs - 3), t, font=font)
                d.rectangle(bb, fill=(255, 255, 255, 200))
                d.text((xx, j - fs - 3), t, fill=tuple(color) + (255,), font=font)
    return im
