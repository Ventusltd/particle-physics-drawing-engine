# SCOPE: the particle physics drawing engine

Written 18 September 2026 from Vikram's decisions of that morning. This is the lead repository. Everything else in the estate feeds it or is drawn by it.

**The engine is spatial by design. Scale is a parameter of the law, and the first law was written from the sky.**
**The grid is the first galaxy.**

## 1. Purpose

To see a complex system in one view, in milliseconds, and go straight to any part of it. A quarter of a million things drawn on one page and zoomable to a single one is the demonstration; interpretation, not data, is the product. Data is no longer scarce. Relations are.

The same particles draw any system within reason: lines of code, buses and branches of a grid, an earthing mesh, cells of a solar module, wires and dies of a CPU, stars, planets, moons, asteroids. The word for a system's relations drawn as particles is a **matrix**.

## 2. What it is, and is not

It is a way to see and to navigate. Every particle has a permanent address and something real behind it. Every number on a page comes from a script that can fail, and every check states what it examined.

It is not a design tool, a simulator of failures, or a source of telemetry. Above 100 kW a chartered electrical engineer signs. Engineers, manufacturers and computation are appointed on real project scope, later. Public wording is cold and business-like; the layouts are physics-inspired mathematics, and code is not matter.

## 3. Decisions taken (Vikram, 18 September 2026)

| # | decision | answer | what it means in the build |
|---|---|---|---|
| 1 | Layers or spiral for new galaxies | **Both, and see them visually** | Two named laws, `spiral` and `stack`, on the same particles; a preset button for each; the first visual comparison is build B1 below |
| 2 | Exact whole-number angle inside layers; frozen wafer as home | **Yes** (explained in §4) | A new named law; the existing wafer is untouched and remains the home view |
| 3 | Generated lines | **Their own galaxy** | Galaxy 0 is the estate; generated layers live in galaxy 1 upward; nothing generated enters the estate's numbering |
| 4 | Ventus-only or open | **Open, like Linux; Ventus is the service company** | Licence settled in §7 so that it never needs thinking about again |
| 5 | Brightness for a field or a flash | *left to Claude:* **yes, brightness only** | Light means something is running, chosen or broken; never a new colour or a new size |
| 6 | Primary twin when a key sits in several places | **One-to-many, like a database** | The key is the primary key; twin places are rows in a `places` table with a `primary` flag chosen by rule (newest commit) and all rows shown |
| 7 | The wafer's unit, and versions | **All versions as views; maximum flexibility; playable** | Every count is a view a user clicks; presets are menu buttons like a racing game; short-hand commands exist but nobody must memorise them |
| 8 | Star index | *left to Claude:* **rebuild on every push; date-label the wafer** | The index build is a workflow; every wafer shows the date of the index it draws |
| 9 | Grid-layer licence | *left to Claude:* **hold stands; synthetic and published data only** | No licensed network data until a real project scope says otherwise |
| 10 | Public wording | **Cold, business-like; no religious words** | A symbol only where it serves a purpose; never a doctrine |

## 4. The laws, in plain words

**Address.** A galaxy is a stack of layers; a layer holds 2¹⁸ = 262,144 slots; `address = galaxy · layer · slot`. Existing keys keep their numbers.

**Position is computed, never stored.** Give the same address to the same law on any device, for ever, and you get the same point.

**Decision 2, explained.** Computers hold decimals approximately. A graphics card works in 32-bit decimals, which grow coarse as numbers grow: the angle of particle 250,174 computed that way lands 26 pixels off on a 1,000-pixel wafer, and particle 16 million lands anywhere. The page avoids this today by computing on the processor in 64 bits, which is exact enough but means uploading every position. The whole-number law replaces the decimal: multiply the slot number by a fixed whole number, 2,654,435,769, keep the low 32 bits, and read that as a fraction of a turn. That fraction *is* the golden angle (the constant is 2³² divided by φ), it is exact, it is the same bits on every device, and it is how 1990s engines did their maths. It is exact within a layer, which is one more reason for layers. It is a new named law; the frozen wafer stays as it is.

**Density.** All particles the same size. Meaning is carried by position and density. A weighted law places particle *k* at `r = c · sqrt(Σ w)` with bounded, smoothed weights; measured on 250,174 real lines with zero overlaps.

**Generated layers.** A layer of generated code stores only its recipe, its seed and a hash. The DNA test regenerates it on two machines and compares hashes, or refuses. Implemented in `tools/particles.py`; runs on every push.

**Physics.** Whole-galaxy motion is a pure function of (address, time, law): Kepler solved per particle per frame. Interacting physics only inside a bounded, seeded, replayable scope with conservation asserted by a test.

**Networks and matrices.** A graph is drawn by placing the same particles along its edges under a schematic layout law; a matrix is one instanced cell per entry, never a DOM node. Topology is fact; artwork is ours.

**Any device.** WebGL2 with a 2-D fallback that draws the same particles; first paint under 2 MB; WebGPU only as an optional fast path.

## 5. Playable

- **Presets are buttons.** Home, spiral, stack, orbit, ring, chord, feeder, matrix. One tap each, like a racing game's menu. Nobody memorises anything.
- **Commands are short-hand for the same presets**, with a fixed grammar parsed without a model, identical for a person and an AI. `help` lists them; every button shows the command it runs, so the user learns by playing.
- **Every version is a view.** The 250,174-line wafer and the 128,369-line family wafer are two buttons, not a decision.
- **Every particle has a card**: what it is, where it comes from, what it relates to, where it leads.

## 6. Data model

- `keys`: the permanent address, issued once, never reused.
- `places`: one-to-many, `key → (repo, commit, path, line, primary)`; the primary place is the newest commit unless a rule says otherwise; all places are shown.
- `laws`: name, source hash, the facts it reads, the constants it uses.
- `layers`: galaxy, layer, recipe, seed, hash, generated time.
- `index`: rebuilt on every push by a workflow; every wafer is labelled with the index date it draws.

## 7. Licence, settled

- **Code: Apache License 2.0.** Anyone may use, change and sell it; contributors grant patent rights; nobody may claim the Ventus name. This is the licence under which the Red Hat model works, it is what most open infrastructure uses, and it needs no lawyer to apply.
- **Data and documents produced here: Creative Commons Attribution 4.0.** Take it, credit the source.
- **Other people's code and data keep their own licences.** Nothing under a hold (grid network data, map artwork, proprietary catalogues) is redistributed.
- **Contributions in, credit out.** Contributors keep their copyright and license it the same way (the Apache licence's §5 does this without a separate agreement).
- Ventus Ltd builds and sells services on top, as Red Hat does on Linux. This is a working decision for the R&D phase, not legal advice; it will be reviewed when a real project scope requires it, and not before.

## 8. Tests that can fail

T1 a physical iPhone draws one layer · T2 exactness (in this repo, passing) · T3 cross-device positions within a pixel · T4 generator determinism across machines (in this repo, passing) · T5 address to source in one request · T6 a law missing a fact refuses by name · T7 sixteen layers served from the workstation's second drive.

## 9. The first three builds

- **B1. Spiral and stack, side by side.** The same particles under both laws, a button for each, with the density picture of every layer. Decision 1 is taken by looking.
- **B2. A network from a typed command.** DONE on the renderer, 18 September: `draw underground` in version 202609180205-underground places 245,170 lines along the Underground's 314 edges. Next: a feeder from the engine's own data under the same law, and `draw` as a preset button.
- **B3. The phone.** T1, with the phone in hand, before anything is called "any device".

## 10. Out of scope now

Engineering design, failure prediction, telemetry, licensed network data, any claim not measured, any agent fan-out, any spend on collecting data.

## 10a. Decisions of the same morning, machines and delivery (Vikram)

| # | decision | answer |
|---|---|---|
| 11 | MSI runners for this repository | **Up to 40**, with the GPU and RAM, watching resources so the PC never crashes; the MSI is cheaper than credits. Registered by Vikram's hand (`register-runners.ps1` plan updated to 40). |
| 12 | Old runner copy on C: | Kept until the first job runs through the junction, then deleted. |
| 13 | RAM | **32 GB is enough.** GitHub for slow runs, the MSI for local ones; two Alienwares available later. |
| 14 | Local model | **A smaller model** than the 14B, so Chrome keeps its graphics memory. |
| 15 | Where things live | **E: is the big data store.** GitHub holds records, testcodes and final versions in their repositories. The homepage receives only what is satisfied with, and only public-facing, business-like material. |
| 16 | Pace | Small steps, as much as possible within reason; real budget from Saturday. |
| 17 | Signatory | **After the app is mature and on real projects.** Until then: build without warranty, like Ubuntu. |
| 18 | First network from a typed command | **The London Underground**, topology only, no artwork. The wordmark already drawn from particles (`logo` mode in the cockpit) goes to the homepage under a new nest, **About**, once it assembles fully; on 17 September it assembled 3 %, so it is build B2, not a publish. |
| 19 | The phone test | Vikram opens https://ventusltd.github.io/star-electron-star/ on his iPhone and reports draw or blank and seconds to first draw. |

## 11. How work is paid for

Repeatable work runs on GitHub-hosted runners and the workstation for free. Reasoning is spent one turn at a time. One agent at most, and only after the rules and the scope exist. This document is that scope.

## The home view (Vikram, 18 September 2026, 02:20)

The preferred look, and the thing everything above evolves towards, is the Wafer Development Environment key-to-code version: https://globalgrid2050.com/testcode/wafer-development-environment/202609170044-key-to-code/ . Its dust, its black, its command box and its card are the home; every preset, law, network and matrix in this scope is a change of scope or law on that renderer, never a new page and never a new look.
