#!/usr/bin/env python3
"""geometry.py: the translator's second input. Geometry (sections, not routes) into the wafer's network language.

Rules, fixed: a circle becomes a ring of N nodes joined in a loop (N from its circumference at a stated node
spacing); a rectangle becomes its four corners joined; everything is in millimetres in the plane of the section,
then fitted to the unit square like every other layer. Nothing is invented: the shapes come from stated inputs,
and the inputs are written into the file.

First geometry: a buried cable trench in flat formation, the inputs of the estate's cable-trench-or-drill
calculator (circuit quantity, cables per row, cable outer diameter, horizontal and vertical spacing, burial
depth). This is a picture of a stated arrangement; it is not a design, and it says so.
"""
import argparse, json, math, os


def circle(cx, cy, r, spacing_mm):
    n = max(12, int(2 * math.pi * r / spacing_mm))
    pts = [[cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n)] for i in range(n)]
    return pts, [[i, (i + 1) % n] for i in range(n)]


def rect(x0, y0, x1, y1):
    return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]], [[0, 1], [1, 2], [2, 3], [3, 0]]


def trench(circuits, per_row, cable_od, spacing_h, spacing_v, depth, cables_per_circuit=3, node_spacing=6.0):
    """Flat formation: each circuit's cables side by side; rows of `per_row` circuits; the trench outline around them."""
    nodes, edges, shapes = [], [], []
    def add(pts, eds, label):
        o = len(nodes); nodes.extend([[p[0], p[1], label if i == 0 else ""] for i, p in enumerate(pts)]); edges.extend([[a + o, b + o] for a, b in eds])
    pitch = cable_od + spacing_h
    rows = math.ceil(circuits / per_row)
    row_w = per_row * cables_per_circuit * pitch + (per_row - 1) * spacing_h
    for c in range(circuits):
        row, col = divmod(c, per_row)
        y = -(depth + row * (cable_od + spacing_v))
        x0 = -row_w / 2 + col * (cables_per_circuit * pitch + spacing_h) + cable_od / 2
        for k in range(cables_per_circuit):
            pts, eds = circle(x0 + k * pitch, y, cable_od / 2, node_spacing)
            add(pts, eds, f"circuit {c + 1} cable {k + 1}")
    margin = cable_od
    top, bottom = 0.0, -(depth + (rows - 1) * (cable_od + spacing_v) + cable_od / 2 + margin)
    pts, eds = rect(-row_w / 2 - margin, bottom, row_w / 2 + margin, top)
    add(pts, eds, "trench outline, ground level at the top")
    return nodes, edges


def fit(nodes):
    xs = [n[0] for n in nodes]; ys = [n[1] for n in nodes]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys); sc = max(x1 - x0, y1 - y0) or 1
    return [[round((n[0] - x0) / sc * 1.8 - 0.9 * (x1 - x0) / sc, 4), round((n[1] - y0) / sc * 1.8 - 0.9 * (y1 - y0) / sc, 4), n[2]] for n in nodes]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--circuits", type=int, default=4)
    ap.add_argument("--per-row", type=int, default=2)
    ap.add_argument("--cable-od", type=float, default=90.0, help="cable outer diameter, mm")
    ap.add_argument("--spacing-h", type=float, default=150.0, help="clear horizontal spacing between cables, mm")
    ap.add_argument("--spacing-v", type=float, default=300.0, help="clear vertical spacing between rows, mm")
    ap.add_argument("--depth", type=float, default=900.0, help="depth to the first row's centre, mm")
    ap.add_argument("--out", default="out/networks")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    nodes, edges = trench(a.circuits, a.per_row, a.cable_od, a.spacing_h, a.spacing_v, a.depth)
    inputs = {"circuits": a.circuits, "per_row": a.per_row, "cable_od_mm": a.cable_od, "spacing_h_mm": a.spacing_h, "spacing_v_mm": a.spacing_v, "depth_mm": a.depth, "cables_per_circuit": 3, "node_spacing_mm": 6.0}
    net = {"name": "trench", "source": f"a stated trench arrangement: {json.dumps(inputs)}", "attribution": "inputs as used by Ventusltd/cable-trench-or-drill; a picture of an arrangement, not a design; a chartered engineer signs",
           "law": "flat formation; each cable a ring of nodes at 6 mm spacing; rows below one another; the trench outline around them", "inputs": inputs, "stations": fit(nodes), "edges": edges}
    p = os.path.join(a.out, "trench-network.json"); json.dump(net, open(p, "w"), separators=(",", ":"))
    print(f"trench: {a.circuits} circuits x 3 cables, {len(nodes)} nodes, {len(edges)} edges, {os.path.getsize(p):,} bytes -> {p}")


if __name__ == "__main__":
    main()
