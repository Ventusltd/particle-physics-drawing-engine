"""Smoke tests: the tools import, and the core laws return sane numbers.

Standard library only (unittest). Run:  python -m unittest discover -s tests -v
Nothing here fetches the network or writes into results/. pandapower (tools/fault.py) is optional and skipped when
it is not installed.
"""
import contextlib
import importlib
import io
import json
import math
import os
import struct
import sys
import tempfile
import unittest
import zlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import particles  # noqa: E402
import geometry  # noqa: E402
import networks  # noqa: E402
import png  # noqa: E402


class Imports(unittest.TestCase):
    def test_tools_import(self):
        for name in ("particles", "geometry", "networks", "png", "spiral_vs_stack", "underground", "scope_check", "publish_iteration"):
            with self.subTest(module=name):
                self.assertIsNotNone(importlib.import_module(name))

    def test_fault_needs_pandapower(self):
        try:
            import pandapower  # noqa: F401
        except ImportError:
            self.skipTest("pandapower is not installed")
        self.assertIsNotNone(importlib.import_module("fault"))


class AngleLaw(unittest.TestCase):
    """Law 2: theta_int is exact whole-number arithmetic and tracks the golden angle within one layer."""

    def test_constants(self):
        self.assertEqual(particles.SLOTS, 1 << 18)
        self.assertEqual(particles.C32, 2654435769)
        self.assertAlmostEqual(particles.GOLDEN, 2.399963229728653, places=12)

    def test_theta_in_range_and_deterministic(self):
        for slot in (0, 1, 2, 39885, particles.SLOTS - 1):
            th = particles.theta_int(slot)
            self.assertTrue(0.0 <= th <= 2 * math.pi, slot)
            self.assertEqual(th, particles.theta_int(slot))
        self.assertEqual(particles.theta_int(0), 2 * math.pi)

    def test_theta_tracks_golden_angle(self):
        # The README states 7.3e-10 rad per slot; over a whole layer that is under 2e-4 rad.
        for slot in (1, 1000, 250174, particles.SLOTS - 1):
            exact = (slot * particles.GOLDEN) % (2 * math.pi)
            err = abs((particles.theta_int(slot) - exact + math.pi) % (2 * math.pi) - math.pi)
            self.assertLess(err, 2e-4, slot)

    def test_f32_round_trip(self):
        self.assertEqual(particles.f32(0.5), 0.5)
        self.assertNotEqual(particles.f32(0.1), 0.1)
        self.assertAlmostEqual(particles.f32(0.1), 0.1, places=7)


class Generator(unittest.TestCase):
    """Law 3: recipe + seed + slot regenerate every line, the same bits every time."""

    def test_line_for_is_deterministic(self):
        a = particles.line_for("grid-feeder", "2026-09-18", 39885)
        b = particles.line_for("grid-feeder", "2026-09-18", 39885)
        self.assertEqual(a, b)
        self.assertTrue(a.startswith("bus[39885] = Bus(kv="), a)
        self.assertNotEqual(a, particles.line_for("grid-feeder", "2026-09-18", 39886))
        self.assertNotEqual(a, particles.line_for("grid-feeder", "other-seed", 39885))

    def test_slot_zero_feeds_from_itself(self):
        self.assertIn("fed_from=bus[0]", particles.line_for("grid-feeder", "s", 0))

    def test_prose_recipe(self):
        line = particles.line_for("prose", "s", 7)
        self.assertTrue(set(line) == {"x"} and 8 <= len(line) < 128)

    def test_unknown_recipe_exits(self):
        with self.assertRaises(SystemExit):
            particles.line_for("no-such-recipe", "s", 0)

    def test_weight_is_bounded(self):
        self.assertEqual(particles.weight(0), 0.25)
        self.assertEqual(particles.weight(40), 0.5)
        self.assertEqual(particles.weight(80), 1.0)
        self.assertEqual(particles.weight(10000), 1.0)

    def test_regen_hash_matches_a_small_manifest(self):
        m = {"recipe": "prose", "seed": "s", "slots": 64}
        h1 = particles.regen_hash(m)
        self.assertEqual(len(h1), 64)
        self.assertEqual(h1, particles.regen_hash(dict(m)))
        self.assertNotEqual(h1, particles.regen_hash({**m, "seed": "t"}))


class Geometry(unittest.TestCase):
    def test_circle_and_rect(self):
        pts, edges = geometry.circle(0, 0, 10, 6.0)
        self.assertEqual(len(pts), len(edges))
        self.assertGreaterEqual(len(pts), 12)
        for x, y in pts:
            self.assertAlmostEqual(math.hypot(x, y), 10, places=9)
        pts, edges = geometry.rect(0, 0, 2, 1)
        self.assertEqual(len(pts), 4)
        self.assertEqual(edges, [[0, 1], [1, 2], [2, 3], [3, 0]])

    def test_trench_and_fit(self):
        nodes, edges = geometry.trench(4, 2, 90.0, 150.0, 300.0, 900.0)
        self.assertGreater(len(nodes), 12 * 4 * 3 + 4)
        self.assertEqual(len(edges), len(nodes))
        for a, b in edges:
            self.assertTrue(0 <= a < len(nodes) and 0 <= b < len(nodes))
        fitted = geometry.fit(nodes)
        self.assertEqual(len(fitted), len(nodes))
        for x, y, _label in fitted:
            self.assertTrue(-0.9 - 1e-9 <= x <= 0.9 + 1e-9 and -0.9 - 1e-9 <= y <= 0.9 + 1e-9)


class Networks(unittest.TestCase):
    def test_douglas_peucker_keeps_ends_and_drops_the_middle(self):
        line = [[0, 0], [1, 0.001], [2, 0], [3, 0.001], [4, 0]]
        self.assertEqual(networks.dp(line, 0.01), [[0, 0], [4, 0]])
        self.assertEqual(len(networks.dp(line, 0.0001)), 5)
        self.assertEqual(networks.dp([[0, 0], [1, 1]], 0.1), [[0, 0], [1, 1]])

    def test_normalise_fits_the_unit_square(self):
        out = networks.normalise([[-1.0, 51.0], [0.0, 51.5], [1.0, 52.0]])
        self.assertEqual(len(out), 3)
        xs = [p[0] for p in out]; ys = [p[1] for p in out]
        self.assertAlmostEqual(max(xs), 0.9, places=3)
        self.assertAlmostEqual(min(xs), -0.9, places=3)
        self.assertTrue(all(-0.9 - 1e-9 <= v <= 0.9 + 1e-9 for v in ys))


class Png(unittest.TestCase):
    def test_writes_a_valid_greyscale_png(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "t.png")
            png.raster_to_png(path, 4, [0, 1, 2, 3] * 4)
            with open(path, "rb") as f:
                data = f.read()
        self.assertTrue(data.startswith(b"\x89PNG\r\n\x1a\n"))
        w, h, depth, ctype = struct.unpack(">IIBB", data[16:26])
        self.assertEqual((w, h, depth, ctype), (4, 4, 8, 0))
        idat = data.index(b"IDAT")
        n = struct.unpack(">I", data[idat - 4:idat])[0]
        raw = zlib.decompress(data[idat + 4:idat + 4 + n])
        self.assertEqual(len(raw), 4 * (4 + 1))
        self.assertEqual(raw[4], 255)  # the peak cell is full white
        self.assertEqual(raw[1], 0)    # an empty cell stays black
        self.assertTrue(data.endswith(b"IEND\xaeB`\x82"))


class Manifest(unittest.TestCase):
    def test_compare_reads_manifests(self):
        m = {"recipe": "prose", "seed": "s", "slots": 4, "sha256_of_line_hashes": "x", "chars_total": 1, "platform": "test"}
        with tempfile.TemporaryDirectory() as d:
            paths = []
            for i in range(2):
                p = os.path.join(d, f"m{i}.json")
                with open(p, "w") as f:
                    json.dump(m, f)
                paths.append(p)

            class Args:
                manifests = paths

            with self.assertRaises(SystemExit) as cm, contextlib.redirect_stdout(io.StringIO()):
                particles.cmd_compare(Args())
            self.assertEqual(cm.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
