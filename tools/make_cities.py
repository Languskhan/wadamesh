#!/usr/bin/env python3
"""Build cities.bin (WadaMesh city locator) from Census TIGER/Line place boundaries.

Usage: make_cities.py <tl_YYYY_SS_place.shp basename> <out.bin> [minlon minlat maxlon maxlat] [tolerance_deg]

File format v1 (little-endian):
  "WCTY" u8 version=1 u8 reserved u16 count
  count x record:
    u8 kind (0 = incorporated city/town, 1 = census-designated place)
    u8 name_len, name bytes (UTF-8, no terminator)
    i32 min_lat_e6, i32 min_lon_e6, i32 max_lat_e6, i32 max_lon_e6
    u16 ring_count
    ring_count x ( u16 point_count, point_count x (i32 lat_e6, i32 lon_e6) )
Point-in-place uses even-odd over ALL rings, so holes and multi-part places work.
"""
import struct, sys
import shapefile
from shapely.geometry import shape, box

src, out = sys.argv[1], sys.argv[2]
bb = [float(x) for x in sys.argv[3:7]] if len(sys.argv) >= 7 else [-122.3, 38.0, -120.0, 40.0]  # SMF area
tol = float(sys.argv[7]) if len(sys.argv) >= 8 else 0.00005  # ~5 m
area = box(*bb)
recs = []
for sr in shapefile.Reader(src).iterShapeRecords():
    g = shape(sr.shape.__geo_interface__)
    if not g.intersects(area):
        continue
    d = sr.record.as_dict()
    g = g.simplify(tol, preserve_topology=True)
    polys = [g] if g.geom_type == "Polygon" else list(g.geoms)
    rings = []
    for p in polys:
        rings.append(list(p.exterior.coords))
        rings += [list(i.coords) for i in p.interiors]
    kind = 1 if d["LSAD"] == "57" else 0
    recs.append((d["NAME"], kind, g.bounds, rings))
recs.sort(key=lambda r: (r[1], r[0]))  # cities first, then CDPs
e6 = lambda v: int(round(v * 1e6))
buf = bytearray(b"WCTY" + struct.pack("<BBH", 1, 0, len(recs)))
for name, kind, (x0, y0, x1, y1), rings in recs:
    nb = name.encode("utf-8")[:63]
    buf += struct.pack("<BB", kind, len(nb)) + nb
    buf += struct.pack("<iiiiH", e6(y0), e6(x0), e6(y1), e6(x1), len(rings))
    for ring in rings:
        assert len(ring) < 65536
        buf += struct.pack("<H", len(ring))
        for x, y in ring:
            buf += struct.pack("<ii", e6(y), e6(x))
open(out, "wb").write(buf)
print(f"{len(recs)} places, {len(buf)} bytes -> {out}")
