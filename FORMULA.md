# The formula the swarm follows

Deterministic, like a procedural universe: nothing is chosen per iteration, everything is derived from the iteration number n. Anyone can recompute any iteration from n alone.

| quantity | formula | why |
|---|---|---|
| the line the iteration opens on | `key_n = 1 + floor(frac(n / φ) × 342,795)`, φ = (1+√5)/2 | golden-ratio spacing: each iteration lands far from all previous ones and the sequence visits the estate evenly; the same law that places the wafer's dust |
| network law: snapping passes | `50 + 50 × (n mod 10)` | sweeps 50 to 500 |
| network law: step | `0.02 + 0.01 × (n mod 9)` | sweeps 0.02 to 0.10 |
| network law: particle spacing | `0.002 + 0.001 × (n mod 5)` | sweeps 0.002 to 0.006 |
| layers regenerated and hashed | 1, 16, 64, 256 every run | the DNA test never skips a size |
| angle within a layer | `frac = (slot × 2,654,435,769) mod 2³² / 2³²`, `θ = 2π(1 − frac)` | exact, same bits everywhere |
| page | the state wafer opened on `key_n`, then the run's evidence | the home view first, always |
| cadence and cap | every 30 minutes, 30 iterations | the owner ticks what to keep |

Every number on every page is measured by the script that drew it; a run that examined nothing refuses; no model text is published. Iteration 04 was the first made under this formula, by Claude and the swarm together, 18 September 2026.

| the system the iteration draws | `SYSTEMS[n mod 8]` over grid, grid400, grid132, substations, shotwick, underground, uk, world | a deterministic tour of real systems on the wafer, one an hour |
