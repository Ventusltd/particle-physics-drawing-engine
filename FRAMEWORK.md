# The framework: how the team works while the captain is away

Set by Claude (Fable 5.1) on 18 September 2026 after making iteration 04 by hand with the swarm. The team is the swarm (`E:\particles-runs\local-run.ps1`), the captain (`captain.ps1`, a local 7B model), GitHub (`nightly.yml`, `particles.yml`) and the publisher (`tools/publish_iteration.py`). Every member follows this page; none of them decides.

## The one rule above the others
A measurement is the only currency. A script that examined nothing refuses (exit 3). A number that was not measured is not written. A model's text is a candidate, never evidence.

## What an iteration is
One numbered page under `globalgrid2050.com/testcode/particles/NN-line-<key>/`, made every 30 minutes by the formula in `FORMULA.md`: the home-view wafer opened on line `key_n`, then the facts of that run. Thirty at most. The owner ticks which to keep. An iteration is good when it is **sober, reasonable and productive**:

| test | passes when | who checks |
|---|---|---|
| sober | every number on the page appears in the run's json; the commit the log claims is on `origin/main` | the swarm's log line; Claude's watch |
| reasonable | run under 3 minutes; free RAM above 6 GB; exactly one iteration per run; counter rises by one | the swarm; Claude's watch |
| productive | the law parameters differ from the previous iteration; the layer hashes match on every machine | the formula; `particles.yml` reconciliation |

## What each member does, and does not
- **The swarm** measures, hashes, draws, publishes. It never chooses parameters: the formula does. It never publishes a picture it did not draw in that run. It writes `PUSH FAILED` rather than pretending.
- **The captain** reads the latest run and this framework every hour and writes `CAPTAIN-LATEST.md`: what the facts say, any inconsistency, one next step with its command. It quotes only numbers present in the facts. Its file is headed as a model's text. Nothing it writes is executed or published by anyone but a person.
- **GitHub** repeats the record on other machines every three hours and fails loudly if the hashes differ.
- **Claude**, on each watch, reads three files and one run list, writes one line to `WATCH.md`, and fixes only what is red with the smallest change. No agents.
- **Vikram** decides: which iterations to keep, when a law becomes home, when anything leaves testcode for the homepage.

## How the team learns without a model in the loop
Learning here means the record grows and later runs read it. The counter, `iterations.json`, `WATCH.md` and `results/` are the memory. A parameter that produced an examined-nothing exit is visible in `SCOPE-STATUS.md` for the next watch to see. Nothing is tuned until the picture looks nice; constants change only in `FORMULA.md`, by a person, with a commit.

## What is out of bounds until Saturday
New laws on the renderer, new commands in the cockpit, the homepage, the About nest, the logo, any agent fan-out, any licensed data, any claim of engineering.

## The stop
Saturday 16:00 London, or the iteration cap, whichever first. The swarm keeps measuring after the cap; it stops publishing.
