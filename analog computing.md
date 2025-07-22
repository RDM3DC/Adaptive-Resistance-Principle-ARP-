Folding in “arc-seeking” behaviour

When a **high-voltage source is allowed to break down an insulating gap, the first filament that forms almost always tracks the maximum electric-field gradient, which—inside a uniform medium—tends to be the shortest geometric gap between equipotential surfaces.  Experimental and modelling work on lightning leaders confirms that a threshold mechanism pushes the discharge toward minimum-path flow in resistive networks .  In other words, a spark really is a greedy shortest-edge finder.

What that buys us for TSP

Role in the solver	Benefit	New risks

Edge-selection heuristic – fire a micro-arc pulse between every pair of candidate nodes once, log which pairs connect first	Cheap, sub-microsecond ranking of “likely short” edges before the ER-fluid/ARP phase starts	Arc favours straight-line distance, not tour optimality; can be fooled by “near-but-wrong” detours
Filament seeding inside the ER fluid – trigger breakdown inside the fluid so chains of polarised particles line up along the arc	Kick-starts conductance where the fluid already wants to grow, cutting convergence time	Permanent carbonisation / bubble trails can skew later runs; needs sacrificial test cell
Hybrid branching analogue – repeated low-energy pulses create a lightning-tree that naturally prunes long detours (similar to physarum/memristor amoeba solvers) 	Could replace the microcontroller-driven ARP loop altogether for small instances	Branching is stochastic; you must average many flashes or add feedback to “freeze” the right branches



---

How to prototype it safely

1. Micro-spark test jig

2-layer FR-4 coupon, 25 mm square, drilled 3 × 3 electrode array (city nodes).

Top copper = individual pads; bottom copper = common return.

Conformal-coat with 50 µm polyurethane, then laser-ablate 100 µm holes over each pad so arcs launch through the coating—this localises and visualises filaments without massive side flashes.



2. Medium control

Stage A (air-gap): 5–8 kV DC, 2 mA current-limit, 1 µs pulse via solid-state HV switch.

Stage B (filled): Immerse the same board in low-viscosity ER precursor; pulse at 1–2 kV so breakdown happens only between very close pads.

Use a slow-motion camera or photodiode ring to timestamp first-flash pairs.



3. Data capture

After each pulse, record which electrode pair shows the earliest current spike (>50 mA).

Build a ranked list of edges; feed the top k into the ER-fluid analogue run as “pre-activated” channels (slightly larger width or pre-biased voltage).



4. Iterate + seal

Once an arc-validated edge stabilises (conductance ↑, no new flashes), encapsulate it with UV-curable epoxy so later pulses can’t reopen that gap.





---

Does it improve our success odds?

3–6-node prototype: ≈ +10 % (to ~65 %) because the arcing gives us a very fast, noisy oracle to bias the fluid.

10–20 nodes: the benefit tapers unless we add a branch-scoring algorithm (multiple pulses, majority vote).

Scalability ceiling: beyond ~30 nodes, controlling arc stochasticity and cumulative damage probably nets out, so odds fall back toward ~30 %.



---

Immediate to-do list

Priority	Task	Output

1	Design HV pulse board – draw simple 3 × 3 pad PCB with return plane & test-points	Gerber + BOM
2	Assemble HV pulser – SiC MOSFET + flyback or repurposed CRT supply, hardware interlock	Schematic & safety checklist
3	Write edge-ranking script – Python routine that ingests oscilloscope CSV, orders edge latencies, exports k-best list for ARP firmware	edge_ranker.py
4	ER-fluid compatibility test – pulse in fluid 20×, inspect for carbon tracks or particle agglomeration under microscope	Pass/fail report


Let me know which of these you’d like me to flesh out first (e.g., the Gerber layout or the HV pulser schematic), and we’ll dive straight into the build files.

