#!/usr/bin/env python3
"""networks.py: real systems as network files the wafer draws with its own dust.

Each output is {"name","source","attribution","law","stations":[[x,y,name],...],"edges":[[i,j],...]} with x,y in
[-0.9, 0.9], north up, equirectangular scaled by cos(mean latitude), so the drawing keeps its shape. Lines are
simplified by Douglas-Peucker so a file stays small; the tolerance is printed with the counts. Nothing is invented:
every node is a vertex of the source geometry or a point in the source data.

Sources (all public): grid_400kv.geojson, grid_132kv.geojson, grid_substations.geojson at globalgrid2050.com
(OpenStreetMap-derived, ODbL); Natural Earth coastlines (public domain); a REPD project from Pipeline News.
"""
import argparse, json, math, os, sys

OSM = "© OpenStreetMap contributors, Open Database Licence (ODbL); published at globalgrid2050.com"
NE = "Natural Earth (naturalearthdata.com), public domain"


def dp(points, tol):
    """Douglas-Peucker on [x,y] points."""
    if len(points) < 3:
        return points
    if points[0] == points[-1]:                       # a closed ring (an island): split it, or it collapses to a line
        h = len(points) // 2
        return dp(points[:h + 1], tol)[:-1] + dp(points[h:], tol)
    (x1, y1), (x2, y2) = points[0], points[-1]
    dx, dy = x2 - x1, y2 - y1
    L = math.hypot(dx, dy) or 1e-12
    imax, dmax = 0, -1.0
    for i in range(1, len(points) - 1):
        px, py = points[i]
        d = abs(dy * px - dx * py + x2 * y1 - y2 * x1) / L
        if d > dmax:
            imax, dmax = i, d
    if dmax > tol:
        return dp(points[:imax + 1], tol)[:-1] + dp(points[imax:], tol)
    return [points[0], points[-1]]


def normalise(pts):
    lat0 = sum(p[1] for p in pts) / len(pts)
    c = math.cos(math.radians(lat0))
    xs = [p[0] * c for p in pts]; ys = [p[1] for p in pts]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    sc = max(x1 - x0, y1 - y0) or 1
    return [[round((x - x0) / sc * 1.8 - 0.9 * (x1 - x0) / sc, 4), round((y - y0) / sc * 1.8 - 0.9 * (y1 - y0) / sc, 4)] for x, y in zip(xs, ys)]


def from_lines(features, tol, name_key="name", bbox=None, min_pts=2):
    """LineString features -> nodes and edges, vertices shared by exact coordinate."""
    idx, nodes, edges, kept = {}, [], set(), 0
    for f in features:
        g = f["geometry"]
        parts = [g["coordinates"]] if g["type"] == "LineString" else (g["coordinates"] if g["type"] == "MultiLineString" else [])
        label = (f.get("properties") or {}).get(name_key, "") or ""
        for coords in parts:
            pts = [[float(c[0]), float(c[1])] for c in coords]
            if bbox:
                pts = [p for p in pts if bbox[0] <= p[0] <= bbox[2] and bbox[1] <= p[1] <= bbox[3]]
            if len(pts) < min_pts:
                continue
            pts = dp(pts, tol); kept += 1
            ids = []
            for p in pts:
                k = (round(p[0], 5), round(p[1], 5))
                if k not in idx:
                    idx[k] = len(nodes); nodes.append([p[0], p[1], label if len(nodes) == 0 or label else ""])
                ids.append(idx[k])
            for a, b in zip(ids, ids[1:]):
                if a != b:
                    edges.add((a, b) if a < b else (b, a))
    return nodes, sorted(edges), kept


def write(out, name, source, attribution, law, nodes, edges):
    xy = normalise([[n[0], n[1]] for n in nodes]) if nodes else []
    net = {"name": name, "source": source, "attribution": attribution, "law": law,
           "stations": [[p[0], p[1], n[2]] for p, n in zip(xy, nodes)], "edges": edges}
    p = os.path.join(out, f"{name}-network.json")
    json.dump(net, open(p, "w", encoding="utf-8"), separators=(",", ":"), ensure_ascii=False)
    print(f"{name}: {len(nodes)} nodes, {len(edges)} edges, {os.path.getsize(p):,} bytes -> {p}")
    return p


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--gg", default=r"C:\Users\vikra\Documents\GitHub\globalgrid2050", help="globalgrid2050 clone")
    ap.add_argument("--ne", default=r"E:\particles-runs\data", help="folder with ne_10m_coastline.geojson and ne_110m_coastline.geojson")
    ap.add_argument("--shotwick", default="", help="lon,lat of Shotwick Solar Farm from Pipeline News")
    ap.add_argument("--out", default="out/networks")
    ap.add_argument("--tol", type=float, default=0.002, help="simplification tolerance in degrees")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    gj = lambda f: json.load(open(f, encoding="utf-8"))["features"]

    f400 = gj(os.path.join(a.gg, "grid_400kv.geojson")); n, e, k = from_lines(f400, a.tol)
    write(a.out, "grid400", "globalgrid2050.com/grid_400kv.geojson, 400 kV overhead lines and cables", OSM, f"vertices of {k} lines simplified at {a.tol} deg, edges between consecutive vertices", n, e)
    f132 = gj(os.path.join(a.gg, "grid_132kv.geojson")); n, e, k = from_lines(f132, a.tol)
    write(a.out, "grid132", "globalgrid2050.com/grid_132kv.geojson, 132 kV lines", OSM, f"vertices of {k} lines simplified at {a.tol} deg", n, e)
    subs = gj(os.path.join(a.gg, "grid_substations.geojson"))
    n = [[float(f["geometry"]["coordinates"][0]), float(f["geometry"]["coordinates"][1]), (f.get("properties") or {}).get("name", "") or ""] for f in subs if f["geometry"]["type"] == "Point"]
    write(a.out, "substations", "globalgrid2050.com/grid_substations.geojson, substations", OSM, "one node per substation, no edges: the particles cluster at each", n, [])
    uk = gj(os.path.join(a.ne, "ne_10m_coastline.geojson")); n, e, k = from_lines(uk, a.tol * 2, bbox=(-11.0, 49.5, 2.5, 61.0), min_pts=3)
    write(a.out, "uk", "Natural Earth 10 m coastline, clipped to the British Isles", NE, f"coastline vertices simplified at {a.tol * 2} deg", n, e)
    world = gj(os.path.join(a.ne, "ne_110m_coastline.geojson")); n, e, k = from_lines(world, 0.0, min_pts=3)
    write(a.out, "world", "Natural Earth 110 m coastline", NE, "coastline vertices, unsimplified", n, e)
    # the grid as one picture: 400 kV and 132 kV lines with every substation, the transmission and sub-transmission system
    n1, e1, k1 = from_lines(f400, a.tol); n2, e2, k2 = from_lines(f132, a.tol)
    subs_nodes = [[float(f["geometry"]["coordinates"][0]), float(f["geometry"]["coordinates"][1]), (f.get("properties") or {}).get("name", "") or ""] for f in subs if f["geometry"]["type"] == "Point"]
    o1 = len(n1); o2 = o1 + len(n2)
    write(a.out, "grid", "globalgrid2050.com: grid_400kv.geojson, grid_132kv.geojson and grid_substations.geojson together", OSM,
          f"{k1} 400 kV lines and {k2} 132 kV lines as edges, simplified at {a.tol} deg; {len(subs_nodes)} substations as nodes without edges", n1 + n2 + subs_nodes, e1 + [[i + o1, j + o1] for i, j in e2])
    if a.shotwick:
        lon, lat = (float(v) for v in a.shotwick.split(","))
        box = (lon - 0.6, lat - 0.4, lon + 0.6, lat + 0.4)
        n1, e1, k1 = from_lines(f400, a.tol / 2, bbox=box); n2, e2, k2 = from_lines(f132, a.tol / 2, bbox=box)
        off = len(n1); nodes = n1 + n2 + [[lon, lat, "Shotwick Solar Farm (REPD, Pipeline News)"]]
        edges = e1 + [[i + off, j + off] for i, j in e2]
        write(a.out, "shotwick", "Shotwick Solar Farm from Pipeline News (REPD), with the 400 kV and 132 kV lines within about 60 x 80 km from globalgrid2050.com", OSM + "; REPD via Pipeline News", f"{k1} 400 kV and {k2} 132 kV lines around the site, simplified at {a.tol / 2} deg; the site is the last node", nodes, edges)


if __name__ == "__main__":
    main()
