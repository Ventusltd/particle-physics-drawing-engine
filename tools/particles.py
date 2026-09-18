#!/usr/bin/env python3
"""particles.py: procedural layers, the DNA test and the exactness test.

The laws it implements (see README, "The plan"):
  Law 1  a layer is 2^18 = 262,144 slots; address = layer * 2^18 + slot.
  Law 2  the angle within a layer is exact whole-number arithmetic:
         frac = (slot * 2654435769) mod 2^32 / 2^32,  theta = 2*pi*(1 - frac),
         which is the golden angle to 7.3e-10 rad per slot, the same bits on every machine.
  Law 3  a generated layer stores no lines: recipe + seed + slot regenerate every line,
         and the DNA test regenerates and compares hashes, or fails.
  Density: same-sized particles, r = sqrt(sum of bounded weights), weight from line length,
         bounded to [0.25, 1] and taken by rank, which measured zero overlaps on 250,174 real lines.

House rules: no random module; every number printed is measured; exit non-zero on failure;
positions are computed, never stored.
"""
import argparse, hashlib, json, math, os, platform, struct, sys, time

SLOTS = 1 << 18
C32 = 2654435769                      # floor(2^32 / phi)
GOLDEN = math.pi * (3 - math.sqrt(5)) # the golden angle, 2.39996... rad
RASTER = 512


def digest(recipe, seed, slot):
    return hashlib.sha256(f"{recipe}|{seed}|{slot}".encode()).digest()


def line_for(recipe, seed, slot):
    """One generated line of code. Deterministic in (recipe, seed, slot)."""
    d = digest(recipe, seed, slot)
    u = int.from_bytes(d[:8], "big")
    if recipe == "grid-feeder":
        kv = (11, 33, 66, 132, 275, 400)[u % 6]
        kw = 50 + (u >> 8) % 20000
        fed = (u >> 32) % slot if slot else 0
        return f"bus[{slot}] = Bus(kv={kv}, load_kw={kw}, fed_from=bus[{fed}])"
    if recipe == "prose":
        n = 8 + (u >> 8) % 120
        return "x" * n
    sys.exit(f"FAIL: unknown recipe {recipe!r}")


def weight(chars):
    return min(1.0, max(0.25, chars / 80.0))


def theta_int(slot):
    frac = ((slot * C32) & 0xFFFFFFFF) / 4294967296.0
    return 2 * math.pi * (1 - frac)


def f32(x):
    return struct.unpack("f", struct.pack("f", x))[0]


# ---------------------------------------------------------------- layer
def cmd_layer(a):
    os.makedirs(a.out, exist_ok=True)
    t0 = time.time()
    raster = [0] * (RASTER * RASTER)
    chain = hashlib.sha256()
    cum = 0.0
    chars_sum = 0
    sample = {}
    for slot in range(SLOTS):
        line = line_for(a.recipe, a.seed, slot)
        chain.update(hashlib.sha256(line.encode()).digest())
        n = len(line)
        chars_sum += n
        cum += weight(n)
        r = math.sqrt(cum)
        th = theta_int(slot)
        if slot in (0, 1, 39885, SLOTS - 1):
            sample[str(slot)] = line
        # density raster of the whole layer (positions are not stored)
        R = math.sqrt(SLOTS)  # r never exceeds sqrt(SLOTS * 1.0)
        x = int((r * math.cos(th) / R + 1) * 0.5 * (RASTER - 1))
        y = int((r * math.sin(th) / R + 1) * 0.5 * (RASTER - 1))
        raster[y * RASTER + x] += 1
    peak = max(raster)
    pgm = os.path.join(a.out, f"layer-{a.layer}-density.pgm")
    with open(pgm, "wb") as f:
        f.write(f"P5 {RASTER} {RASTER} 255\n".encode())
        f.write(bytes(min(255, v * 255 // max(1, peak)) for v in raster))
    manifest = {
        "layer": a.layer, "recipe": a.recipe, "seed": a.seed, "slots": SLOTS,
        "address_first": a.layer * SLOTS, "address_last": a.layer * SLOTS + SLOTS - 1,
        "sha256_of_line_hashes": chain.hexdigest(),
        "chars_total": chars_sum, "rim_radius": round(math.sqrt(cum), 4),
        "raster_peak_particles_per_cell": peak, "sample": sample,
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "python": platform.python_version(), "platform": platform.platform(),
        "seconds": round(time.time() - t0, 2),
    }
    path = os.path.join(a.out, f"layer-{a.layer}.json")
    with open(path, "w") as f:
        json.dump(manifest, f, indent=1)
    print(f"layer {a.layer}: {SLOTS} slots generated, {chars_sum} chars, "
          f"hash {manifest['sha256_of_line_hashes'][:16]}..., {manifest['seconds']} s -> {path}")


# ---------------------------------------------------------------- dna
def regen_hash(m):
    chain = hashlib.sha256()
    for slot in range(m["slots"]):
        chain.update(hashlib.sha256(line_for(m["recipe"], m["seed"], slot).encode()).digest())
    return chain.hexdigest()


def cmd_dna(a):
    m = json.load(open(a.manifest))
    got = regen_hash(m)
    ok = got == m["sha256_of_line_hashes"]
    print(f"DNA: regenerated {m['slots']} of {m['slots']} slots on {platform.platform()}; "
          f"{'MATCH' if ok else 'MISMATCH'} {got[:16]}... vs {m['sha256_of_line_hashes'][:16]}...")
    sys.exit(0 if ok else 1)


def cmd_compare(a):
    ms = [json.load(open(p)) for p in a.manifests]
    keys = ("recipe", "seed", "slots", "sha256_of_line_hashes", "chars_total")
    same = all(m[k] == ms[0][k] for m in ms for k in keys)
    for p, m in zip(a.manifests, ms):
        print(f"{m['platform']}: {m['sha256_of_line_hashes'][:16]}... chars {m['chars_total']}  ({p})")
    print(f"compare: {len(ms)} manifests examined; {'IDENTICAL' if same else 'DIFFER'}")
    sys.exit(0 if same else 1)


# ---------------------------------------------------------------- exactness (T2)
def cmd_exactness(a):
    keys = [1, 250174, SLOTS - 1, 1 << 24, 1 << 31]
    rim_px = 1000.0
    print(f"{'key':>12} {'f32 err rad':>12} {'f32 px':>10} {'int law err rad':>16} {'int px':>10}")
    worst_in_layer = 0.0
    for k in keys:
        exact = (k * GOLDEN) % (2 * math.pi)
        f32v = (f32(f32(k) * f32(GOLDEN))) % (2 * math.pi)
        intv = theta_int(k % SLOTS)                      # slot within its layer
        e32 = abs((f32v - exact + math.pi) % (2 * math.pi) - math.pi)
        eint = abs((intv - exact + math.pi) % (2 * math.pi) - math.pi)
        print(f"{k:>12} {e32:>12.3e} {e32 * rim_px:>10.3f} {eint:>16.3e} {eint * rim_px:>10.3f}")
        if k < SLOTS:
            worst_in_layer = max(worst_in_layer, eint * rim_px)
    # every slot of one layer, not a sample
    worst = 0.0
    for s in range(SLOTS):
        exact = (s * GOLDEN) % (2 * math.pi)
        e = abs((theta_int(s) - exact + math.pi) % (2 * math.pi) - math.pi)
        worst = max(worst, e)
    print(f"whole layer: {SLOTS} slots examined; worst |int law - exact| = {worst:.3e} rad "
          f"= {worst * rim_px:.3f} px at a {rim_px:.0f}-px rim")
    limit = 0.25
    print(f"{'PASS' if worst * rim_px < limit else 'FAIL'}: limit {limit} px within one layer")
    sys.exit(0 if worst * rim_px < limit else 1)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("layer", help="generate a layer: manifest + density raster, no lines stored")
    s.add_argument("--layer", type=int, default=1)
    s.add_argument("--recipe", default="grid-feeder")
    s.add_argument("--seed", default="2026-09-18")
    s.add_argument("--out", default="out")
    s.set_defaults(fn=cmd_layer)
    s = sub.add_parser("dna", help="regenerate a layer from its manifest and compare the hash")
    s.add_argument("manifest")
    s.set_defaults(fn=cmd_dna)
    s = sub.add_parser("compare", help="compare manifests made on different machines")
    s.add_argument("manifests", nargs="+")
    s.set_defaults(fn=cmd_compare)
    s = sub.add_parser("exactness", help="test T2: the angle law in 32-bit, and the whole-number law")
    s.set_defaults(fn=cmd_exactness)
    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
