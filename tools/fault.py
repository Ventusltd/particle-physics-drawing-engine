#!/usr/bin/env python3
"""fault.py: a fault study by an existing open-source solver, translated into the wafer's language.

Solver: pandapower (BSD 3-clause; Thurner et al., "pandapower: An Open Source Python Tool for Convenient Modeling,
Analysis, and Optimization of Electric Power Systems", IEEE Transactions on Power Systems, 2018). Its IEC 60909
short-circuit module computes the initial symmetrical short-circuit current I"k for a three-phase fault.
Network: pandapower's mv_oberrhein, a 20 kV distribution network with coordinates (a generic, published example,
not a real utility's data).

The translator carries each line's I"k as an edge weight, so the wafer places more of its particles on the paths
that carry the fault current: illumination by density, no new colour, no new size. Every number here comes
from the solver; the fault bus, the case and the solver version are written into the file. It charts a
calculation on a published example; it is not a design, and above 100 kW a chartered engineer signs.
"""
import argparse, json, math, os
import pandapower as pp, pandapower.networks as nw, pandapower.shortcircuit as sc


def geo(net, b):
    g = net.bus.at[b, "geo"]
    if isinstance(g, str):
        g = json.loads(g)
    return g["coordinates"]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bus", type=int, default=-1, help="faulted bus index; -1 = the bus with the lowest fault level (furthest, electrically)")
    ap.add_argument("--out", default="out/networks")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    net = nw.mv_oberrhein()
    # the example carries no short-circuit parameters: state them (typical 110 kV supply), and leave generation out of the fault contribution
    net.ext_grid["s_sc_max_mva"] = 1000.0; net.ext_grid["rx_max"] = 0.1; net.ext_grid["s_sc_min_mva"] = 800.0; net.ext_grid["rx_min"] = 0.1
    net.sgen["in_service"] = False
    if "endtemp_degree" in net.line.columns: net.line["endtemp_degree"] = net.line["endtemp_degree"].fillna(80.0)
    # fault level at every bus first (case max, 3ph), to choose and to report
    sc.calc_sc(net, fault="3ph", case="max", ip=False, ith=False, branch_results=False)
    ikss_bus = net.res_bus_sc["ikss_ka"]
    bus = int(ikss_bus.idxmin()) if a.bus < 0 else a.bus
    # the study: a three-phase fault at that bus, with branch results, so every line carries its share
    sc.calc_sc(net, fault="3ph", case="max", ip=False, ith=False, branch_results=True, bus=bus)
    line_ik = net.res_line_sc["ikss_ka"].fillna(0.0)
    peak = float(line_ik.max()) or 1.0
    buses = list(net.bus.index)
    idx = {b: i for i, b in enumerate(buses)}
    pts = [geo(net, b) for b in buses]
    lat0 = sum(p[1] for p in pts) / len(pts); c = math.cos(math.radians(lat0))
    xs = [p[0] * c for p in pts]; ys = [p[1] for p in pts]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys); s = max(x1 - x0, y1 - y0) or 1
    stations = [[round((x - x0) / s * 1.8 - 0.9 * (x1 - x0) / s, 4), round((y - y0) / s * 1.8 - 0.9 * (y1 - y0) / s, 4),
                 (f"bus {b}: fault here, I\"k {ikss_bus[b]:.2f} kA" if b == bus else f"bus {b}: I\"k {ikss_bus[b]:.2f} kA")] for (x, y), b in zip(zip(xs, ys), buses)]
    edges = []
    for l in net.line.index:
        w = float(line_ik[l]) / peak
        edges.append([idx[int(net.line.at[l, "from_bus"])], idx[int(net.line.at[l, "to_bus"])], round(max(w, 0.02), 4)])
    carrying = int((line_ik > 0.05 * peak).sum())
    facts = {"solver": f"pandapower {pp.__version__}, IEC 60909 calc_sc, fault 3ph, case max; supply stated as 1000 MVA, R/X 0.1; generation excluded", "network": "pandapower mv_oberrhein (20 kV, published example)",
             "fault_bus": bus, "ikss_at_fault_ka": round(float(ikss_bus[bus]), 3), "peak_line_ikss_ka": round(peak, 3), "lines": len(net.line), "lines_carrying_over_5pct": carrying,
             "min_bus_ikss_ka": round(float(ikss_bus.min()), 3), "max_bus_ikss_ka": round(float(ikss_bus.max()), 3)}
    net_out = {"name": "fault", "source": f"pandapower mv_oberrhein; three-phase fault at bus {bus}; I\"k at the fault {facts['ikss_at_fault_ka']} kA; peak line current {facts['peak_line_ikss_ka']} kA",
               "attribution": "Solver and network: pandapower (BSD 3-clause), Thurner et al. 2018, pandapower.readthedocs.io. IEC 60909 method. A published example network, not a real utility's data; not a design; above 100 kW a chartered engineer signs.",
               "law": "edge weight = the line's initial symmetrical short-circuit current divided by the largest; particles along an edge in proportion to length x weight, so the fault current paths are the dense ones",
               "facts": facts, "stations": stations, "edges": edges}
    p = os.path.join(a.out, "fault-network.json"); json.dump(net_out, open(p, "w"), separators=(",", ":"))
    print(json.dumps(facts)); print(f"-> {p}, {os.path.getsize(p):,} bytes")


if __name__ == "__main__":
    main()
