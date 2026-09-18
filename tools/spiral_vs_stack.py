#!/usr/bin/env python3
"""spiral_vs_stack.py: build B1. The same addresses under two laws, drawn side by side.

  spiral  one endless disc: r = sqrt(address), theta = address * golden angle (64-bit)
  stack   one disc per layer of 2^18 slots, tiled; theta by the whole-number law (exact per layer)

Same particles, same size, same count. Only the law differs. Decision 1 is taken by looking.
Every number printed is measured; the script exits non-zero if a raster examined nothing.
"""
import argparse, json, math, os, sys, time
sys.path.insert(0, os.path.dirname(__file__))
from png import raster_to_png
from particles import SLOTS, GOLDEN, theta_int

SIZE = 1024


def run(layers, per_layer, out):
    os.makedirs(out, exist_ok=True)
    n = layers * per_layer
    t0 = time.time()
    # ---- spiral: one disc over every address
    spiral = [0] * (SIZE * SIZE)
    R = math.sqrt(n)
    for a in range(n):
        r = math.sqrt(a) / R
        th = a * GOLDEN
        x = int((r * math.cos(th) + 1) * 0.5 * (SIZE - 1))
        y = int((r * math.sin(th) + 1) * 0.5 * (SIZE - 1))
        spiral[y * SIZE + x] += 1
    t1 = time.time()
    # ---- stack: one disc per layer, tiled in a square grid
    cols = math.ceil(math.sqrt(layers))
    tile = SIZE // cols
    stack = [0] * (SIZE * SIZE)
    Rl = math.sqrt(per_layer)
    for L in range(layers):
        ox, oy = (L % cols) * tile, (L // cols) * tile
        for s in range(per_layer):
            r = math.sqrt(s) / Rl
            th = theta_int(s)
            x = ox + int((r * math.cos(th) + 1) * 0.5 * (tile - 1))
            y = oy + int((r * math.sin(th) + 1) * 0.5 * (tile - 1))
            stack[y * SIZE + x] += 1
    t2 = time.time()
    raster_to_png(os.path.join(out, "spiral.png"), SIZE, spiral)
    raster_to_png(os.path.join(out, "stack.png"), SIZE, stack)
    # side by side
    both = []
    for y in range(SIZE):
        both += spiral[y * SIZE:(y + 1) * SIZE] + [0] * 16 + stack[y * SIZE:(y + 1) * SIZE]
    from png import write_grey
    peak = max(max(spiral), max(stack)) or 1
    write_grey(os.path.join(out, "spiral-vs-stack.png"), SIZE * 2 + 16, SIZE,
               bytes(int(255 * (c / peak) ** 0.5) if c else 0 for c in both))
    stats = {
        "layers": layers, "particles_per_layer": per_layer, "particles": n,
        "spiral": {"cells_lit": sum(1 for c in spiral if c), "peak_per_cell": max(spiral), "seconds": round(t1 - t0, 2)},
        "stack": {"cells_lit": sum(1 for c in stack if c), "peak_per_cell": max(stack), "tile_px": tile, "seconds": round(t2 - t1, 2)},
        "raster_px": SIZE, "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    json.dump(stats, open(os.path.join(out, "spiral-vs-stack.json"), "w"), indent=1)
    print(json.dumps(stats))
    if not stats["spiral"]["cells_lit"] or not stats["stack"]["cells_lit"]:
        sys.exit(3)  # examined nothing


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--layers", type=int, default=4)
    p.add_argument("--per-layer", type=int, default=SLOTS)
    p.add_argument("--out", default="out/b1")
    a = p.parse_args()
    run(a.layers, a.per_layer, a.out)
