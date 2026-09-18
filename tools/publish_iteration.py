#!/usr/bin/env python3
"""publish_iteration.py: number, label and publish one iteration under globalgrid2050.com/testcode/particles/.

Called by the swarm after each run. Iteration N (1..30) gets its own folder NN-<slug>/ with a plain,
business-like page: the pictures the run drew, the facts it measured, the scope status. The index page
lists every iteration with its label so the owner can decide which to keep. Publishes through the
GitHub contents API (no local clone state), only small files. Stops at 30. No model text is published.
"""
import base64, json, os, subprocess, sys, time

REPO = "Ventusltd/globalgrid2050"
BASE = "testcode/particles"
COUNTER = r"E:\particles-runs\iteration.txt"
MAX_ITER = 30
MAX_KEY = 342795          # the estate's highest issued key on 2026-09-14
PHI = (1 + 5 ** 0.5) / 2


SYSTEMS = ["grid", "grid400", "grid132", "substations", "shotwick", "underground", "uk", "world"]   # real systems the wafer draws
HOME = "../../wafer-development-environment/202609180245-real-systems/"


def system_for(n):
    """Iteration n opens the real-systems wafer on system SYSTEMS[n mod 8]: a tour, deterministic, no choice."""
    return SYSTEMS[n % len(SYSTEMS)]


def key_for(n):
    """The formula: iteration n opens on line 1 + floor(frac(n/phi) * MAX_KEY). Golden-ratio spacing:
    every iteration lands far from every previous one, the sequence never repeats a key before all are
    visited (to rounding), and anyone can recompute which line iteration n shows. No Man's Sky rule:
    nothing chosen, everything derived from n."""
    return 1 + int(((n / PHI) % 1.0) * MAX_KEY)
STYLE = ("body{margin:0;background:#000;color:#ccc;font:15px/1.5 ui-monospace,Consolas,monospace}"
         "main{max-width:1400px;margin:0 auto;padding:0 0 24px}h1,p,table,pre,small{margin-left:16px;margin-right:16px}h1{font-size:18px;color:#f2f2f2;margin:0 0 4px}"
         "img{width:100%;height:auto;display:block;background:#000;margin:16px 0 6px}small{color:#8a8a8a}"
         "a{color:#61d6d6}code{color:#f9f1a5}table{border-collapse:collapse}td,th{padding:2px 10px;text-align:left}")


def put(path, data: bytes, msg):
    body = json.dumps({"message": msg, "content": base64.b64encode(data).decode(), "branch": "main"})
    r = subprocess.run(["gh", "api", "-X", "GET", f"repos/{REPO}/contents/{path}", "--jq", ".sha"], capture_output=True, text=True)
    if r.returncode == 0 and r.stdout.strip():
        body = json.dumps({"message": msg, "content": base64.b64encode(data).decode(), "branch": "main", "sha": r.stdout.strip()})
    r = subprocess.run(["gh", "api", "-X", "PUT", f"repos/{REPO}/contents/{path}", "--input", "-"], input=body, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"publish failed for {path}: {r.stderr[:200]}"); return False
    return True


def put_many(files, msg):
    """One commit for all files of an iteration, through the git data API: one deploy, not three."""
    def api(method, path, body=None):
        args = ["gh", "api", "-X", method, path]
        r = subprocess.run(args + (["--input", "-"] if body is not None else []), input=json.dumps(body) if body is not None else None, capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(f"{method} {path}: {r.stderr[:200]}")
        return json.loads(r.stdout)
    head = api("GET", f"repos/{REPO}/git/ref/heads/main")["object"]["sha"]
    base_tree = api("GET", f"repos/{REPO}/git/commits/{head}")["tree"]["sha"]
    tree = []
    for path, data in files.items():
        blob = api("POST", f"repos/{REPO}/git/blobs", {"content": base64.b64encode(data).decode(), "encoding": "base64"})["sha"]
        tree.append({"path": path, "mode": "100644", "type": "blob", "sha": blob})
    new_tree = api("POST", f"repos/{REPO}/git/trees", {"base_tree": base_tree, "tree": tree})["sha"]
    commit = api("POST", f"repos/{REPO}/git/commits", {"message": msg, "tree": new_tree, "parents": [head]})["sha"]
    api("PATCH", f"repos/{REPO}/git/refs/heads/main", {"sha": commit})
    return commit


def load(p):
    try:
        return json.load(open(p))
    except Exception:
        return None


def main(run_dir):
    n = int(open(COUNTER).read().strip()) + 1 if os.path.exists(COUNTER) else 1
    if n > MAX_ITER:
        print(f"iteration cap {MAX_ITER} reached; nothing published"); return 0
    b1 = load(os.path.join(run_dir, "b1-layers-256", "spiral-vs-stack.json")) or load(os.path.join(run_dir, "b1-layers-64", "spiral-vs-stack.json"))
    b2 = load(os.path.join(run_dir, "b2", "underground.json"))
    layers = [load(os.path.join(run_dir, f"layer-{L}", f"layer-{L}.json")) for L in (1, 16, 64, 256)]
    layers = [m for m in layers if m]
    status = open(os.path.join(run_dir, "SCOPE-STATUS.md"), encoding="utf-8").read() if os.path.exists(os.path.join(run_dir, "SCOPE-STATUS.md")) else ""
    passed = status.split("Ran ")[1].split(".")[0] if "Ran " in status else "not run"
    stamp = os.path.basename(run_dir)
    key = key_for(n); system = system_for(n)
    slug = f"{n:02d}-{system}-line-{key}"
    label = (f"Iteration {n}: {system} drawn on the wafer; line {key}; {b1['particles']:,} particles under two laws" if b1 else f"Iteration {n}") + \
            (f"; the Underground, {b2['stations']} stops" if b2 else "") + f"; scope tests {passed}"
    rows = "".join(f"<tr><td>layer {m['layer']}</td><td>{m['slots']:,} slots</td><td><code>{m['sha256_of_line_hashes'][:16]}…</code></td><td>{m['seconds']} s</td></tr>" for m in layers)
    page = f"""<!doctype html><html lang="en-GB"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Particles iteration {n:02d}</title><style>{STYLE}</style></head><body><main>
<iframe src="{HOME}?draw={system}" title="the wafer drawing a real system" style="width:100%;height:92vh;border:0;background:#000"></iframe>
<p><small>Above: the wafer drawing <code>{system}</code> with its own particles, live (iteration {n}: system {n} mod 8 of the tour, line {key} by the formula 1 + floor(frac(n/φ) × 342,795)); type <code>release</code>, then any button. Below: what the swarm measured in this run. The wafer does not yet answer <code>draw underground</code>; that is the next build on this renderer.</small></p>
<h1>{label}</h1>
<p>testcode/particles/{slug} · machine-made on the MSI at {stamp} by <a href="https://github.com/Ventusltd/particle-physics-drawing-engine">particle-physics-drawing-engine</a> · <a href="../">all iterations</a></p>
<p>Same-sized particles, positions computed from the address by a named law, nothing stored. Left: one spiral. Right: a stack of layers of 262,144 slots, angle by whole-number arithmetic.</p>
{'<img src="spiral-vs-stack.png" alt="spiral versus stack">' if b1 else ''}
{f'<small>{b1["particles"]:,} particles; spiral {b1["spiral"]["seconds"]} s, stack {b1["stack"]["seconds"]} s; cells lit {b1["spiral"]["cells_lit"]:,} / {b1["stack"]["cells_lit"]:,}</small>' if b1 else ''}
<p style="margin-top:24px">A network from the typed command <code>draw underground</code>: topology from Transport for London's open data, drawn as the same particles under an eight-direction schematic law. No map artwork.</p>
{'<img src="underground.png" alt="the Underground as particles">' if b2 else ''}
{f'<small>{b2["lines"]} lines, {b2["stations"]} stops, {b2["edges"]} edges, {b2["particles_drawn"]:,} particles. Powered by TfL Open Data. Contains OS data © Crown copyright and database rights 2016 and Geomni UK Map data © and database rights 2019.</small>' if b2 else ''}
<h2 style="font-size:16px;margin-top:28px">Generated layers, regenerated and hashed on this machine</h2>
<table><tr><th>layer</th><th>size</th><th>hash of every line</th><th>time</th></tr>{rows}</table>
<h2 style="font-size:16px;margin-top:28px">Scope status</h2>
<pre style="white-space:pre-wrap;color:#aaa">{status.replace('<','&lt;')}</pre>
<small>This page charts measured facts. It is not a design tool; above 100 kW a chartered electrical engineer signs.</small>
</main></body></html>"""
    files = {f"{BASE}/{slug}/index.html": page.encode()}
    for src, name in ((os.path.join(run_dir, "b1-layers-256", "spiral-vs-stack.png"), "spiral-vs-stack.png"), (os.path.join(run_dir, "b2", "underground.png"), "underground.png")):
        if os.path.exists(src):
            files[f"{BASE}/{slug}/{name}"] = open(src, "rb").read()
    # index: append this iteration to a machine-kept list, then render
    listing = r"E:\particles-runs\iterations.json"
    items = load(listing) or []
    items.append({"n": n, "slug": slug, "label": label, "stamp": stamp})
    lis = "".join(f'<tr><td>{i["n"]:02d}</td><td><a href="{i["slug"]}/">{i["label"]}</a></td><td>{i["stamp"]}</td><td>keep? ☐</td></tr>' for i in items)
    index = f"""<!doctype html><html lang="en-GB"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Particles: numbered iterations</title><style>{STYLE}</style></head><body><main>
<h1>Particle physics drawing engine: numbered iterations</h1>
<p>One iteration every 30 minutes, machine-made and measured, up to 30. Each is a page of what the swarm drew and hashed. The owner decides which to keep. Source and scope: <a href="https://github.com/Ventusltd/particle-physics-drawing-engine">particle-physics-drawing-engine</a>. Home view: <a href="../wafer-development-environment/202609170044-key-to-code/">the key-to-code wafer</a>.</p>
<table><tr><th>#</th><th>iteration</th><th>run (UTC)</th><th></th></tr>{lis}</table>
<small>Proof of the kind of work this leads to: <a href="https://ventusltd.github.io/gridatlas/">GridAtlas</a> and <a href="https://ventusltd.github.io/ventus-grid-engine/">Ventus Grid Engine</a>.</small>
</main></body></html>"""
    files[f"{BASE}/index.html"] = index.encode()
    try:
        commit = put_many(files, f"testcode/particles {n:02d}: {label}")
    except RuntimeError as e:
        print(f"publish failed: {e}"); return 1
    json.dump(items, open(listing, "w"), indent=1)
    open(COUNTER, "w").write(str(n))
    print(f"published iteration {n:02d} in one commit {commit[:7]}: {label}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
