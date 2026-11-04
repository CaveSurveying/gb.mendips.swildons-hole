"""The 3D view: the cave in 3D beneath the ground surface, by cave-viewer.

    python3 -m tools.model3d      # after the main build; writes output/3d/

The page and its build are cave-viewer's
(https://github.com/CaveSurveying/cave-viewer, pinned in
tools/model3d/requirements.txt), configured by caves.json: the centreline
from output/Swildons.3d, the passage walls from output/Swildons-walls.lox,
the entrance's lat/long from output/Swildons-centreline.kml, and the
Environment Agency's 1 m LIDAR, fetched once and kept in surface/lidar/.
This step adds the passage names from the plan drawings (via
tools.routes.survey and output/Swildons.sql), each at the nearest station,
as output/cave-viewer/names.json, then runs cave-viewer. With CHROMIUM set
it also saves a preview.png for the index page.

The LIDAR failing (or cave-viewer) is only a warning: the 3D view is an
extra, and shouldn't stop the rest of the site being published.

The helpers below (the grid to lat/long, the entrance from the KML, PNG
cropping) are tools.webmap's too.
"""
import argparse
import json
import math
import os
import re
import struct
import subprocess
import sys
import zlib

from tools.model3d.formats import read_3d

# Swildons_Centreline.th puts the survey in OSGB:ST, the ST 100 km square
# of the National Grid: add these to get full grid references.
ST = (300000, 100000)
NAMES = 'output/cave-viewer/names.json'


# -- National Grid to lat/long ----------------------------------------------------------

def grid_to_ll(e, n):
    """OSGB36 National Grid to WGS84 lat/long (degrees), by the Ordnance
    Survey's formulae and a Helmert shift: good to a few metres, and the
    caller corrects what is left with the entrance's OSTN15 position."""
    a, b, f0 = 6377563.396, 6356256.909, 0.9996012717
    lat0, lon0, e0, n0 = math.radians(49), math.radians(-2), 400000, -100000
    e2 = 1 - b * b / (a * a)
    nn = (a - b) / (a + b)
    lat, m = lat0, 0
    while abs(n - n0 - m) >= 1e-5:
        lat += (n - n0 - m) / (a * f0)
        m = b * f0 * ((1 + nn + 1.25 * nn ** 2 + 1.25 * nn ** 3) * (lat - lat0)
                      - (3 * nn + 3 * nn ** 2 + 21 / 8 * nn ** 3) * math.sin(lat - lat0) * math.cos(lat + lat0)
                      + (15 / 8 * nn ** 2 + 15 / 8 * nn ** 3) * math.sin(2 * (lat - lat0)) * math.cos(2 * (lat + lat0))
                      - 35 / 24 * nn ** 3 * math.sin(3 * (lat - lat0)) * math.cos(3 * (lat + lat0)))
    s, c, t = math.sin(lat), math.cos(lat), math.tan(lat)
    nu = a * f0 / math.sqrt(1 - e2 * s * s)
    rho = a * f0 * (1 - e2) / (1 - e2 * s * s) ** 1.5
    eta2 = nu / rho - 1
    de = e - e0
    lat = (lat - t / (2 * rho * nu) * de ** 2
           + t / (24 * rho * nu ** 3) * (5 + 3 * t * t + eta2 - 9 * t * t * eta2) * de ** 4
           - t / (720 * rho * nu ** 5) * (61 + 90 * t * t + 45 * t ** 4) * de ** 6)
    lon = (lon0 + de / (c * nu)
           - de ** 3 / (6 * c * nu ** 3) * (nu / rho + 2 * t * t)
           + de ** 5 / (120 * c * nu ** 5) * (5 + 28 * t * t + 24 * t ** 4)
           - de ** 7 / (5040 * c * nu ** 7) * (61 + 662 * t * t + 1320 * t ** 4 + 720 * t ** 6))
    # Airy 1830 to GRS80 through Cartesian coordinates
    s, c = math.sin(lat), math.cos(lat)
    nu = a / math.sqrt(1 - e2 * s * s)
    x, y, z = nu * c * math.cos(lon), nu * c * math.sin(lon), nu * (1 - e2) * s
    tx, ty, tz, sc = 446.448, -125.157, 542.060, -20.4894e-6
    rx, ry, rz = (math.radians(v / 3600) for v in (0.1502, 0.2470, 0.8421))
    x, y, z = (tx + (1 + sc) * x - rz * y + ry * z,
               ty + rz * x + (1 + sc) * y - rx * z,
               tz - ry * x + rx * y + (1 + sc) * z)
    a2, b2 = 6378137.0, 6356752.3141
    e2 = 1 - b2 * b2 / (a2 * a2)
    p = math.hypot(x, y)
    lat = math.atan2(z, p * (1 - e2))
    for _ in range(10):
        lat = math.atan2(z + e2 * a2 / math.sqrt(1 - e2 * math.sin(lat) ** 2) * math.sin(lat), p)
    return math.degrees(lat), math.degrees(math.atan2(y, x))


def mercator(lat, lon):
    """Web Mercator, as a fraction of the world (0..1 across and down)."""
    s = math.sin(math.radians(lat))
    return (lon + 180) / 360, 0.5 - math.log((1 + s) / (1 - s)) / (4 * math.pi)


def fit_affine(pairs):
    """Least-squares (u, v) = A (1, x, y) over (x, y) -> (u, v) pairs."""
    m = [[0.0] * 3 for _ in range(3)]
    ru, rv = [0.0] * 3, [0.0] * 3
    for (x, y), (u, v) in pairs:
        r = (1.0, x, y)
        for i in range(3):
            ru[i] += r[i] * u
            rv[i] += r[i] * v
            for j in range(3):
                m[i][j] += r[i] * r[j]

    def solve(rhs):
        a = [row[:] + [rhs[i]] for i, row in enumerate(m)]
        for i in range(3):
            p = max(range(i, 3), key=lambda k: abs(a[k][i]))
            a[i], a[p] = a[p], a[i]
            for k in range(3):
                if k != i:
                    f = a[k][i] / a[i][i]
                    a[k] = [x - f * y for x, y in zip(a[k], a[i])]
        return [a[i][3] / a[i][i] for i in range(3)]
    return solve(ru) + solve(rv)


def kml_entrance(kml='output/Swildons-centreline.kml'):
    if not os.path.exists(kml):
        return None
    t = open(kml, encoding='utf-8').read()
    m = re.search(r'#ThEntranceIcon</styleUrl>.*?<coordinates>\s*([-\d.]+),([-\d.]+)', t, re.S)
    return (float(m.group(2)), float(m.group(1))) if m else None


# -- the names ------------------------------------------------------------------------

def place_names():
    """Passage names from the plan drawings, each at the height of the
    nearest station, or [] if the database export isn't there."""
    try:
        from tools.routes.survey import Survey
        s = Survey()
        labels = s.load_labels()
    except (OSError, ImportError) as e:
        print(f'no passage names: {e}', file=sys.stderr)
        return []
    # only stations on a leg: Swildons_Centreline.th fixes a fake station,
    # 'bottom', at 140 m beside the entrance to pin the altitude colours
    real = [k for k in s.pos if s.adj.get(k)]
    seen, out = set(), []
    for t, x, y in labels:
        t = re.sub(r'\s*\(.*?\)', '', t).strip()
        if len(t) < 4 or t in seen or re.match(r'^C[\d.]+$', t):
            continue
        k = min(real, key=lambda k: math.hypot(s.pos[k][0] - x, s.pos[k][1] - y))
        if math.hypot(s.pos[k][0] - x, s.pos[k][1] - y) > 20:
            continue
        seen.add(t)
        out.append((t, x, y, s.pos[k][2]))
    return out


def write_names(path=NAMES):
    """names.json for cave-viewer: the entrance, and each name from the plan
    drawings at the nearest station on a leg (by its name in Swildons.3d)."""
    legs, stations = read_3d('output/Swildons.3d')
    on_leg = {tuple(p) for a, b, f in legs if not f & 1 for p in (a, b)}
    named = [(n, p) for n, p, f in stations if n and tuple(p) in on_leg]
    ents = {n: 'Entrance' for n, p, f in stations if f & 4}
    places = {}
    for t, x, y, z in place_names():
        n = min(named, key=lambda s: math.hypot(s[1][0] - x, s[1][1] - y))[0]
        places.setdefault(t, n)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    json.dump({'entrances': ents, 'places': places}, open(path, 'w'), indent=2, ensure_ascii=False)
    print(f'{len(places)} passage names for the 3D view', file=sys.stderr)



# -- PNGs ---------------------------------------------------------------------------

def crop_png(path, height):
    """Keep the top rows of an 8-bit PNG. Each row's filter refers only to
    the row above, so the rows can be cut without decoding them."""
    d = open(path, 'rb').read()
    i, chunks = 8, []
    while i < len(d):
        n = struct.unpack('>I', d[i:i + 4])[0]
        chunks.append((d[i + 4:i + 8], d[i + 8:i + 8 + n]))
        i += 12 + n
    ihdr = chunks[0][1]
    w, h, depth, colour = struct.unpack('>IIBB', ihdr[:10])
    if height >= h or depth != 8 or ihdr[12] != 0:
        return
    row = 1 + w * {0: 1, 2: 3, 4: 2, 6: 4}[colour]
    pixels = zlib.decompress(b''.join(c for t, c in chunks if t == b'IDAT'))[:row * height]

    def chunk(t, c):
        return struct.pack('>I', len(c)) + t + c + struct.pack('>I', zlib.crc32(t + c))
    out = d[:8] + chunk(b'IHDR', ihdr[:4] + struct.pack('>I', height) + ihdr[8:])
    out += b''.join(chunk(t, c) for t, c in chunks[1:] if t not in (b'IDAT', b'IEND'))
    out += chunk(b'IDAT', zlib.compress(pixels, 9)) + chunk(b'IEND', b'')
    open(path, 'wb').write(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.parse_args()
    write_names()
    r = subprocess.run([sys.executable, '-m', 'caveviewer', 'build', 'caves.json', '--out', 'output', '--steps', 'survey,model'])
    if r.returncode:
        # an extra, so it shouldn't stop the rest of the site being published
        print('::warning::no 3D view: cave-viewer failed (see above)', file=sys.stderr)


if __name__ == '__main__':
    main()
