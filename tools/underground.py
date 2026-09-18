#!/usr/bin/env python3
"""underground.py: build B2. A network drawn from a typed command, with the same particles.

Topology is fact and comes from Transport for London's open Unified API (stations, lines, order
of stops). The artwork is ours: stations and edges become same-sized particles under a schematic
law that snaps edges towards the eight compass directions. No TfL map artwork is used.
Attribution required by the data terms: "Powered by TfL Open Data. Contains OS data (c) Crown
copyright and database rights 2016 and Geomni UK Map data (c) and database rights 2019."

Usage: python tools/underground.py --out out/b2 [--offline out/b2/tfl-raw.json]
Exit 3 if no topology could be fetched (examined nothing), 1 if the drawing failed.
"""
import argparse, json, math, os, sys, time, urllib.request
sys.path.insert(0, os.path.dirname(__file__))
from png import raster_to_png

API = "https://api.tfl.gov.uk"
SIZE = 1024
EDGE_SPACING = 0.004      # particles along an edge, in normalised units
STATION_DOTS = 9          # a station is a small dense cluster of the same particles


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "particle-physics-drawing-engine/0.1"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def topology(raw):
    """raw: {lineId: routeSequence json}. Returns stations {id: (name, lat, lon)}, edges {(a,b)}, per line."""
    stations, edges, lines = {}, set(), {}
    for line_id, seq in raw.items():
        points = list(seq.get("stations", []))
        for q in seq.get("stopPointSequences", []):       # some stops appear only here
            points += q.get("stopPoint", [])
        for sp in points:
            sid = sp.get("id") or sp.get("stationId")
            if sid and "lat" in sp:
                stations[sid] = (sp.get("name", sid), sp["lat"], sp["lon"])
        line_edges = set()
        for branch in seq.get("orderedLineRoutes", []):
            ids = branch.get("naptanIds", [])
            for a, b in zip(ids, ids[1:]):
                if a in stations and b in stations:
                    line_edges.add((a, b) if a < b else (b, a))
        lines[line_id] = sorted(line_edges)
        edges |= line_edges
    return stations, edges, lines


def schematic(stations, edges, passes=200, step=0.05):
    """Start from geography (equirectangular), then pull each edge towards the nearest of 8 directions."""
    lat0 = sum(s[1] for s in stations.values()) / len(stations)
    pos = {k: [(s[2]) * math.cos(math.radians(lat0)), s[1]] for k, s in stations.items()}
    xs = [p[0] for p in pos.values()]; ys = [p[1] for p in pos.values()]
    sx, sy = max(xs) - min(xs), max(ys) - min(ys); sc = max(sx, sy)
    for p in pos.values():
        p[0] = (p[0] - min(xs)) / sc * 1.8 - 0.9 * sx / sc
        p[1] = (p[1] - min(ys)) / sc * 1.8 - 0.9 * sy / sc
    for _ in range(passes):
        for a, b in edges:
            pa, pb = pos[a], pos[b]
            dx, dy = pb[0] - pa[0], pb[1] - pa[1]
            L = math.hypot(dx, dy) or 1e-9
            ang = math.atan2(dy, dx)
            snap = round(ang / (math.pi / 4)) * (math.pi / 4)
            tx, ty = math.cos(snap) * L, math.sin(snap) * L
            cx, cy = (pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2
            for p, sgn in ((pa, -1), (pb, 1)):
                gx, gy = cx + sgn * tx / 2, cy + sgn * ty / 2
                p[0] += (gx - p[0]) * step; p[1] += (gy - p[1]) * step
    return pos


def draw(pos, edges, out):
    raster = [0] * (SIZE * SIZE)
    n = 0
    def dot(x, y):
        nonlocal n
        if -1 <= x <= 1 and -1 <= y <= 1:
            raster[int((1 - y) * 0.5 * (SIZE - 1)) * SIZE + int((x + 1) * 0.5 * (SIZE - 1))] += 1; n += 1
    for a, b in edges:
        (x0, y0), (x1, y1) = pos[a], pos[b]
        k = max(1, int(math.hypot(x1 - x0, y1 - y0) / EDGE_SPACING))
        for i in range(k + 1):
            dot(x0 + (x1 - x0) * i / k, y0 + (y1 - y0) * i / k)
    for x, y in pos.values():
        for i in range(STATION_DOTS):
            th = i * 2.399963229728653
            r = 0.004 * math.sqrt(i)
            dot(x + r * math.cos(th), y + r * math.sin(th))
    raster_to_png(os.path.join(out, "underground.png"), SIZE, raster, gamma=0.35)
    return n


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--out", default="out/b2")
    p.add_argument("--offline", help="use a previously saved tfl-raw.json instead of the API")
    a = p.parse_args()
    os.makedirs(a.out, exist_ok=True)
    t0 = time.time()
    if a.offline:
        raw = json.load(open(a.offline))
    else:
        try:
            line_ids = [l["id"] for l in fetch(f"{API}/Line/Mode/tube")]
            raw = {lid: fetch(f"{API}/Line/{lid}/Route/Sequence/all") for lid in line_ids}
        except Exception as e:
            print(f"examined nothing: TfL fetch failed: {e}"); sys.exit(3)
        json.dump(raw, open(os.path.join(a.out, "tfl-raw.json"), "w"))
    stations, edges, lines = topology(raw)
    if not stations or not edges:
        print(f"examined nothing: {len(stations)} stations, {len(edges)} edges parsed"); sys.exit(3)
    pos = schematic(stations, edges)
    n = draw(pos, edges, a.out)
    facts = {
        "command": "draw underground", "source": f"{API}/Line/Mode/tube + /Line/<id>/Route/Sequence/all",
        "attribution": "Powered by TfL Open Data. Contains OS data (c) Crown copyright and database rights 2016 and Geomni UK Map data (c) and database rights 2019.",
        "lines": len(lines), "stations": len(stations), "edges": len(edges), "particles_drawn": n,
        "law": "geography then 200 passes of 8-direction edge snapping (step 0.05); edge particles every 0.004; 9 per station",
        "seconds": round(time.time() - t0, 1), "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    json.dump(facts, open(os.path.join(a.out, "underground.json"), "w"), indent=1)
    print(json.dumps(facts))


if __name__ == "__main__":
    main()
