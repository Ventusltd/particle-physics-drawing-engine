#!/usr/bin/env python3
"""scope_check.py: the scope drives the loop.

Runs every test in SCOPE.md section 8 that has a script, and writes results/SCOPE-STATUS.md with
PASS, FAIL or NOT YET BUILT per test, dated, with the command and its exit code. Exit 1 if any built
test fails; exit 3 if no test could be run (examined nothing); else 0.
The table below mirrors SCOPE.md section 8 by hand; if the scope changes, change it here too.
"""
import os, subprocess, sys, time

TESTS = [
    ("T1", "a physical iPhone draws one layer", None),                       # a person, with the phone in hand
    ("T2", "exactness of the angle law", [sys.executable, "tools/particles.py", "exactness"]),
    ("T3", "cross-device positions within a pixel", None),
    ("T4", "generator determinism: a layer regenerates identically",
        [sys.executable, "-c",
         "import subprocess,sys;p=sys.executable;"
         "subprocess.check_call([p,'tools/particles.py','layer','--layer','2','--out','out/scope']);"
         "subprocess.check_call([p,'tools/particles.py','dna','out/scope/layer-2.json'])"]),
    ("T5", "address to source in one request", None),
    ("T6", "a law missing a fact refuses by name", None),
    ("T7", "sixteen layers served from the workstation's second drive", None),
    ("B1", "spiral and stack side by side", [sys.executable, "tools/spiral_vs_stack.py", "--layers", "4", "--per-layer", "65536", "--out", "out/scope/b1"]),
    ("B2", "a network from a typed command (the Underground)", [sys.executable, "tools/underground.py", "--out", "out/scope/b2"]),
]


def main():
    os.makedirs("results", exist_ok=True)
    rows, ran, failed = [], 0, 0
    for tid, name, cmd in TESTS:
        if cmd is None:
            rows.append((tid, name, "NOT YET BUILT", "", ""))
            continue
        t0 = time.time()
        r = subprocess.run(cmd, capture_output=True, text=True)
        secs = round(time.time() - t0, 1)
        ran += 1
        status = "PASS" if r.returncode == 0 else ("EXAMINED NOTHING" if r.returncode == 3 else "FAIL")
        if r.returncode != 0:
            failed += 1
        last = (r.stdout.strip().splitlines() or r.stderr.strip().splitlines() or [""])[-1][:120]
        rows.append((tid, name, status, f"exit {r.returncode}, {secs} s", last))
    stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with open("results/SCOPE-STATUS.md", "w", encoding="utf-8") as f:
        f.write(f"# Scope status {stamp}\n\nRan {ran} of {len(TESTS)} tests; {failed} failed. "
                f"Tests marked NOT YET BUILT have no script yet (T1 needs a person with the phone).\n\n")
        f.write("| test | what | status | run | last line |\n|---|---|---|---|---|\n")
        for tid, name, status, run, last in rows:
            f.write(f"| {tid} | {name} | **{status}** | {run} | `{last}` |\n")
    for tid, name, status, run, last in rows:
        print(f"{tid} {status:16} {run}")
    print(f"ran {ran} of {len(TESTS)}; failed {failed}")
    sys.exit(3 if ran == 0 else (1 if failed else 0))


if __name__ == "__main__":
    main()
