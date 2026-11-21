# MechaVision V2 — Engineering Implementation Specification

**Product:** MechaVision — offline-first, Arabic educational AR application for school mechatronics/Arduino students.
**Target:** Unity 6000.0.70f1, Android, Galaxy S22 (ARCore); one specific real **830-contact solderless breadboard** (approximately 165 × 55 mm; 2.54 mm hole pitch, to be physically measured).
**Baseline:** Branch \`codex/mechavision-initial-implementation\`, commit \`d2b824998577aa89efb4dc210ae7af46d154577d\`; initial S22 APK was actually installed and its camera, UI, project catalog, marker-based AR, and step display were demonstrated. **Do not overwrite or regress this functioning baseline.**
**Status:** 50 catalog projects and .ino sketches exist but remain educational **drafts**, not independently electrically verified or compiled for AVR. Do not claim otherwise.
**Constraint:** Focus on the functional core first. UI polish and a bespoke app icon come later; automatic visual assessment of a student's real wiring is explicitly FUTURE scope.

## What the current code actually does

Inspect these first; do not assume the architecture:
- \`Assets/MechaVision/Rendering/BoardAssembly.cs\`: creates \`LineRenderer\` wires from literal endpoints, with an elevated direct-arc interpolation; this is not routing. Notice \`ShowStep\` currently uses \`step == 0 || visibleWires.Contains(...)\` and may unintentionally show all wires at step zero.
- \`Assets/MechaVision/Rendering/BoardGeometry.cs\`: constructs stylized parts from Unity primitives (\`Cube\`, \`Cylinder\`, \`Sphere\`), not genuine component 3D models.
- \`Assets/MechaVision/AR/BoardTracker.cs\` and \`BoardCalibration.cs\`: tracked-image marker plus a fixed geometric offset to the real board, not markerless breadboard detection.
- \`Assets/MechaVision/Catalog/CatalogData.cs\`, \`Assets/Resources/MechaVision/catalog.json\`: data model for projects, components, pins, connections and steps.
- \`Assets/MechaVision/UI/MechaVisionApp.cs\`: Arabic UI and existing offline catalog / .ino operations.
- \`Documentation/AR-setup.md\`, \`VALIDATION.md\`, \`Documentation/S22-test-matrix.md\`.

## Non-negotiable engineering principles

1. **Electrical correctness precedes beautiful graphics.** An attractive but false circuit is unacceptable for school instruction.
2. A real breadboard is an **electrical node network**, not a decorative background or a convenient coordinate plane.
3. Each displayed wire must have physically plausible, visually unambiguous **terminal-to-hole/terminal-to-terminal** endpoints. For parts mounted into the board, pins enter designated board holes; connections must be represented through those holes and the internal metal strips. Some components must remain OUTSIDE the board (motors, servo body, chassis, modules and standalone Arduino as appropriate); direct external wire connections are valid when electrically required. Do not force everything through the breadboard.
4. Preserve the original 50 project catalog and .ino code; use explicit statuses \`draft / reviewed / compiled / hardware_tested\` based only on evidence. Never silently invent a source, a measurement, a connector, a power specification, or a verified claim.
5. Preserve working marker-based AR as **fallback** and reference baseline while building markerless mode. Do not remove until markerless tracking is proved on the S22.
6. No permanent ChatGPT API requirement, no online backend, and no demand for internet after ARCore and Android dependencies are installed.
7. No need to inspect/verify the student's physical wiring automatically in V2; that is a future module.

## Priority P0 — truthful electrical model of the specific 830-point breadboard

Create explicit testable model types (names can vary):
- \`BreadboardDefinition\`: dimensions, pitch, hole coordinates, 2-sided terminal strips (A–E and F–J per numbered column), power rails, interruptions of rails **as physically present on the user's board**. Never assume every rail is continuous. Make physical layout and segmentation measurable/configurable.
- \`HoleId\`, \`TerminalId\`, \`PinAttachment\`, \`ElectricalNet\`, \`WireEndpoint\`, \`WireConnection\`, \`PhysicalPlacement\`; separate schematic electrical netlists from physical layout and rendering.
- Use a graph/union-find or equivalent to group holes on the same conductive strip. Each physical pin entering a hole joins that hole's net. Jumpers connect nets. External component pins are distinct terminals.
- A connection is satisfied when the graph yields the intended net topology, not only when a line is drawn between two strings.
- For each project, produce a structured **physical assembly plan** from the schematic connectivity: part positions, pin-to-hole insertion assignments, external terminal placements, jumper endpoints, and ordered teaching steps.
- If a valid plan cannot be found or is electrically unsafe/ambiguous, **do not display it as a verified plan**. Show a clear Arabic limitation or draft status.
- Check power and grounding topology, polarity of LEDs, plausible resistors/limits, shorts across supply rails, unsupported loads on Uno pins, pin-count conflicts, motor drivers and independent power/GND requirements. Identify which checks are heuristics requiring a datasheet/human review.
- Document that initial circuit data were not hardware-tested. Never infer electrical continuity from rendered proximity alone.

Required unit tests (not exhaustive):
- On a standard continuous 5-hole strip, \`A10\` through \`E10\` share one net; \`F10\` does NOT share it.
- Neighboring column strips differ absent a jumper; rails connect only according to the measured board's configured segments.
- A pin inserted at \`C10\` and a jumper entering \`A10\` form the same net.
- Crossed jumpers in 3D do **not** imply an electrical junction.
- Contradictory connections, pin conflicts, and shorts are caught or explicitly marked unverifiable.
- External motor/servo connections are permitted and not forced to fictitious holes.

## Priority P1 — professional physical placement and wire routing

Replace \`BoardAssembly.AddWire\`'s simple arc interpolation with a layout-driven routing system:
- First choose safe and readable part placement, respecting body sizes, pin pitch, breadboard usable space, rows, center gap and rail discontinuities.
- Route wires as tidy realistic jumper paths with explicit waypoints/bends/over-board heights where needed, not arbitrary direct arcs; prefer paths along board margins/rows when useful, minimize crossing and occlusion, avoid passing through components, distinguish crossings from junctions.
- Color code consistently; use ground/power conventions, but not color as the only cue. Clearly label both exact endpoint names, such as \`Uno D9 -> HC-SR04 TRIG\` or \`GND -> blue rail segment\`, and optionally board holes. Show direction/terminal highlight and numbered steps.
- In step view highlight only the current connection; optionally faintly show previously completed ones; hide future wires by default. Fix the current step-zero/all-wires behavior, and provide an explicit optional "Show full circuit" view.
- Implement deterministic layout across sessions, debug overlay of physical terminal names, and a visual regression harness / generated screenshots when possible.
- Use a board **specific** to the current user's actual 830-point board: dimensions and rail continuity must be confirmed by an on-device calibration/measuring checklist. If uncertain, request measurement via UI; do not invent exact physical properties.

First demonstrate and validate:
1. Beginner LED + current-limiting resistor and Uno, with real board nets.
2. HC-SR04 + buzzer project, including labelled power/ground/signal; verify hardware voltage and type assumptions.
3. At least one project with external actuator (e.g., servo smart bin), with its body outside the breadboard and electrically appropriate power.
Follow a machine-checkable report for each: intended schematic netlist, planned board hole IDs, component/terminal mapping, pin-code agreement, power cautions, net-equivalence results, screenshot/wire routing evidence.
Do NOT claim all 50 projects are correct just because JSON schema validates.

## Priority P2 — markerless recognition of the ONE actual user's breadboard

This is an experimental, higher-risk task. A markerless system must not be claimed production-ready without real S22 data.

Functional goal: camera recognizes and estimates pose of the user's specific breadboard **without the printed carrier**, and overlays remain aligned when CAMERA OR BOARD moves; if confidence is low, freeze briefly and/or hide the overlay with an Arabic instruction, rather than showing inaccurate wiring.

Pipeline:
- Add a modular \`IBoardPoseProvider\` interface with \`MarkerPoseProvider\` (existing) and experimental \`MarkerlessPoseProvider\`. Preserve fallback toggle.
- Start with a classical CV baseline (board edges/outer rectangle/holes) and prototype using captured images, if it works. If not, prepare targeted **deep-learning** training:
  - Export/capture on S22 real board images/videos across light, angle, distance, rotation, background and partial occlusion.
  - Provide a convenient capture and annotation tool/data format, labelling **four ordered board corners** (plus optional orientation cue and mask). User has not supplied a labelled dataset; NEVER claim a model was trained or validated on images you do not have.
  - Fine-tune a compact keypoint/detection or segmentation model on a genuinely labelled dataset, validate on held-out video sessions rather than near-duplicate frames.
  - Outputs: ordered 2D board corners/segmentation and confidence; these are **not** by themselves a 6-DOF pose.
- Estimate calibrated 6-DOF pose using real board dimensions, AR camera intrinsics and e.g. OpenCV PnP/homography plus ARCore pose, with correct coordinate-frame conversion to Unity. Handle planar pose ambiguity, mirror flips, corner order, z positivity, temporal smoothness, AR motion tracking and camera/board occlusion; display measured reprojection error.
- IMPORTANT: 2.54 mm pitch creates a strict alignment requirement. Measure actual endpoint-to-hole center error across movement, rotation, varied lighting; define acceptance limits according to results. Do not certify millimetre-level accuracy using bounding-box IoU alone.
- Keep status clear: \`experimental\`, \`validated on held-out clips\`, or \`validated on S22\` with evidence. If reliable markerless tracking cannot be completed, leave marker fallback functional and deliver the dataset tools / trained model results / blockers.

## Priority P3 — visually faithful 3D components, once P0/P1 are correct

The current \`BoardGeometry.cs\` primitives are placeholders.
- Introduce a \`ComponentVisualRegistry\` with real-scale FBX/GLB/Unity prefabs and material/texturing mappings, local pin anchors, orientation and physical dimensions separated from visual asset geometry.
- Prioritize Arduino Uno R3, HC-SR04, LED, axial resistor, SG90 servo, buzzer, typical LCD, motor driver; reuse assets across the 50 projects.
- Prefer open-licensed/properly licensed models with recorded source/license/attribution; validate compatibility with redistribution in a noncommercial school application. If external assets cannot legally or technically be fetched, implement the registry and clearly report what model assets are still needed rather than claim "photorealistic 3D" from crude primitives.
- Keep mobile performance sensible (mesh budgets, shared materials, LOD if needed, batching). Check pin anchors over camera image, not just pretty screenshots.
- Do not make parts appear seated in arbitrary holes or floating above the real board without an instructional reason.

## Priority P4 — premium Arabic RTL UI and brand icon (LOWER priority, after P0/P1)

- Modern cohesive educational design: typography, consistent typography scales, spacing, accessible color contrast, legible AR overlays, clear project cards, search/filter, components checklist, preview/assembly switch, current step/progress, sketch download, helpful error states and calibration.
- Polished but restrained page transitions and micro-interactions, respecting performance and reducing motion. Do not obscure AR camera or cause layout jumps during tracking.
- Proper Arabic shaping and right-to-left layout, English technical terms kept readable.
- Create a **distinct original MechaVision launcher icon**, e.g. recognizable breadboard/grid + lens/wiring motif, delivered as Android adaptive icon assets with foreground/background, plus a simple splash/brand treatment. No copyrighted/trademarked imagery. If an actual graphic asset cannot be authored with sufficient quality, mark as a design deliverable and use transparent honest placeholder, not the default Unity icon.
- UX should be suitable for grade 7–12 students.

## Future scope — explicitly NOT in this deliverable

Computer vision inspection of a student's *real, already plugged in* wires, automatic correctness classification, and electrical contact verification are future versions. Do not let them block V2 foundations.

## Execution / acceptance

### Stage 0: audit and baseline
- Read existing implementation, inspect data and tests; summarize in \`Documentation/V2-status.md\` the three observed failings (non-physical routing, primitive visuals, image-marker dependence).
- Create a clear dependency plan, and make actual code changes, NOT merely a README.
- Preserve the initial branch/release baseline. Do not delete the 50 catalog entries or .ino sketches.
- Work on the currently selected V2 development branch, with small coherent commits.

### Stage 1: P0 + P1 first (FIRST REQUIRED DELIVERY)
Implement the electrical network and wire-routing engine with tests and small functioning scenes. Produce before/after screenshots or a test scene for the first verified case, plus machine-checkable output and honest issue list. Build must continue to work with existing marker-based tracking. No claims of completed implementation without Unity/Android tests.

### Stage 2: P2, only after Stage 1 core is solid
Build data capture/annotation pipeline + markerless baseline; train on real labelled photos if available. If images are missing, prepare training/inference scripts and a concrete photo collection protocol; do not hallucinate training results. Expose fallback to the existing tracking mode.

### Stage 3: P3 + P4 as time permits
Visual asset pipeline, polished UI, transitions, icon; these should never displace electrically correct instruction.

### Quality gates and transparency
- \`python3 Tools/build_catalog.py --check\`; \`python3 -m unittest discover -s Tools -p 'test_*.py'\` and new engine tests where applicable.
- If Arduino CLI is available, compile affected Uno sketches, report real failures. Host C++ syntax checks are not AVR compilation.
- Prefer Unity Editor EditMode and build checks if available; cloud may not have Unity. Do not claim APK works until it is built/tested locally.
- Provide actionable Windows/Unity 6000.0.70f1 build instructions and a real Galaxy S22 check matrix (camera moves; board moves; board rotates; marker removed; pose lost/reacquired; endpoints remain on intended holes).
- For every completed functionality report: files changed, sample outputs, tests actually run, measurements if any, known limitations, and remaining work.
- Push commits to the **V2 branch** and open a draft PR against \`codex/mechavision-initial-implementation\` when possible. Do NOT merge into the working baseline without user review.
- NEVER print or commit secret API tokens.
- Do not attempt to solve issues by silently changing to a totally different Unity version or replacing the AR architecture.

**Start NOW with Stage 0 and Stage 1: make a functioning, test-backed breadboard electrical connectivity and physical routing engine. The immediate definition of success is that the displayed LED-resistor circuit uses actual, named breadboard holes and produces clean teachable wires; only then proceed to markerless detection and visuals.**
