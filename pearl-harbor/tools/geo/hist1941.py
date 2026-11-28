"""Hand-digitised geometry used for the 1941 corrections and the harbor depth model.
All coordinates are (lon, lat), digitised from the 3DEP DEM / Sentinel-2 composite."""
import numpy as np
from common import *

# --- Honolulu airport Reef Runway (built 1973-77 on the reef flat) -------------------
# bar (runway 8R/26L and its fill), west connector taxiway, enclosed lagoon.
REEF_RUNWAY_POLYS = [
    # the runway bar: everything south of the airport's southern shoreline
    [(-157.9520, 21.3020), (-157.9040, 21.3020), (-157.9040, 21.3104), (-157.9520, 21.3104)],
    # west connector + enclosed lagoon (the lagoon's N shore is found from the DEM, see build)
    [(-157.9490, 21.3104), (-157.9280, 21.3104), (-157.9280, 21.3166), (-157.9490, 21.3166)],
]
# inside the second polygon only these pixels are turned back into reef: the flattened
# lagoon (0.69 m in 3DEP) and the connector strip
REEF_RUNWAY_CONNECTOR = [(-157.9490, 21.3104), (-157.9452, 21.3104), (-157.9452, 21.3163), (-157.9490, 21.3163)]
REEF_RUNWAY_LAGOON_Z = 0.69

# --- Pearl Harbor Navy Yard dry docks -----------------------------------------------
# DD1 (1919) and DD2 (1941) existed on 7 Dec 1941 -> kept, as water basins.
# DD3 (1942) and DD4 (1943) did not -> filled back to yard level.
DRYDOCK_YARD_BOX = (-157.9640, -157.9565, 21.3490, 21.3536)      # lon_w, lon_e, lat_s, lat_n (DD1, DD2, DD3)
DRYDOCK_FILL_BOXES = [(-157.9680, -157.9632, 21.3452, 21.3488)]  # DD4 at Hospital Point

# --- Pearl Harbor depth model: (lon, lat, max depth m, ramp distance m) ---------------
# 1941: entrance channel and main channels dredged to ~40 ft, berths around Ford Island
# 35-45 ft, Middle Loch moorings ~30 ft, upper lochs natural mud flats.
HARBOR_DEPTH_CTRL = [
    (-157.9610, 21.3050, 14.0, 60),    # entrance channel through the reef
    (-157.9625, 21.3200, 14.0, 60),
    (-157.9650, 21.3300, 14.0, 60),    # mouth (Iroquois Pt / Fort Kamehameha)
    (-157.9670, 21.3400, 13.5, 60),
    (-157.9690, 21.3500, 13.5, 60),    # Hospital Point
    (-157.9720, 21.3580, 13.0, 60),    # west of Ford Island
    (-157.9700, 21.3680, 12.5, 60),
    (-157.9620, 21.3745, 12.0, 60),    # north channel (Ford Is - Pearl City)
    (-157.9500, 21.3700, 12.5, 60),    # NE of Ford Island
    (-157.9490, 21.3640, 13.0, 50),    # Battleship Row
    (-157.9540, 21.3590, 13.0, 50),    # channel SE of Ford Island
    (-157.9600, 21.3555, 13.5, 50),    # off the Navy Yard / 1010 dock
    (-157.9460, 21.3570, 12.5, 50),    # Southeast Loch entrance
    (-157.9420, 21.3545, 11.5, 50),    # Southeast Loch (sub base, Merry Point)
    (-157.9440, 21.3600, 11.0, 50),    # Magazine Loch / sub base piers
    (-157.9450, 21.3760, 11.0, 80),    # East Loch
    (-157.9550, 21.3830, 9.0, 120),    # East Loch north (off Pearl City / Aiea)
    (-157.9400, 21.3800, 6.0, 150),    # Aiea Bay
    (-157.9370, 21.3720, 7.0, 120),    # off Halawa / Makalapa shore
    (-157.9600, 21.3870, 4.0, 200),    # head of East Loch (Waimalu)
    (-157.9790, 21.3640, 11.0, 80),    # Middle Loch entrance (Ford Is NW / Waipio Pt)
    (-157.9850, 21.3720, 9.5, 100),    # Middle Loch
    (-157.9900, 21.3800, 7.0, 150),    # Middle Loch north
    (-157.9920, 21.3870, 3.0, 250),    # head of Middle Loch (Waiawa)
    (-157.9740, 21.3480, 12.0, 60),    # turn into West Loch channel
    (-157.9820, 21.3470, 10.5, 60),    # West Loch channel
    (-157.9900, 21.3520, 10.0, 70),
    (-157.9980, 21.3560, 9.5, 80),     # lower West Loch
    (-158.0070, 21.3600, 8.0, 120),    # West Loch (ammunition depot)
    (-158.0150, 21.3650, 5.0, 200),    # upper West Loch
    (-158.0190, 21.3720, 2.5, 300),    # head of West Loch (Honouliuli)
    (-158.0050, 21.3700, 3.0, 250),    # NE arm of West Loch
]
# the harbor model applies north of this latitude and fades out towards the sea
HARBOR_MOUTH_LAT = 21.3230
HARBOR_BOX = (-158.045, -157.925, 21.3230, 21.400)


def poly_mask(poly, rect=ISLAND, w=M8_W, h=M8_H, window=None):
    """Rasterise a lon/lat polygon on a world grid -> bool array (optionally a (r0,r1,c0,c1) window)."""
    from PIL import Image, ImageDraw
    pts = [tuple(float(v) + 0.5 for v in lonlat_to_px(rect, w, h, lon, lat)) for lon, lat in poly]
    img = Image.new('1', (w, h), 0)
    ImageDraw.Draw(img).polygon(pts, fill=1)
    return np.asarray(img, bool)


def box_slices(box, rect=ISLAND, w=M8_W, h=M8_H):
    lon_w, lon_e, lat_s, lat_n = box
    i0, j0 = lonlat_to_px(rect, w, h, lon_w, lat_n)
    i1, j1 = lonlat_to_px(rect, w, h, lon_e, lat_s)
    return slice(int(round(float(j0))), int(round(float(j1))) + 1), slice(int(round(float(i0))), int(round(float(i1))) + 1)
