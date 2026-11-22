# MechaVision V2 — Markerless breadboard feasibility spike (evaluate before training)

Date: 2026-11-22
Branch: `codex/mechavision-v2-development`
Scope: user's **specific physical 830-contact solderless breadboard**, Samsung Galaxy S22, Unity 6000.0.70f1 / AR Foundation / ARCore; OFFLINE INFERENCE target.
Status: research-based evaluation plan; **no markerless model is yet trained or validated on the user's board**.

## Grounded starting points

| Source | Verified published information | Caveat |
| --- | --- | --- |
| https://github.com/stonestephenson/Breadboard-Classifier | Describes a breadboard geometric rectifier, based on the MIT `breadboard-normalizer`, using a DocAligner corner model. README says first run downloads approximately 83 MB weights and validates their hash; rectification worked on 13 test photos. | 13 photos do **not** establish mobile real-time tracking, 6-DoF, or accuracy on this user's board. Test pretrained weights locally, inspect licenses/weight download provenance. |
| https://github.com/hartleyblakey/breadboard-normalizer | Breadboard normalization/perspective correction code and demos; earlier YOLO pose experiment described. | Some earlier datasets/notebooks are described as residing outside GitHub; do not assume trained corner-specific weights are present. |
| https://github.com/DocsaidLab/DocAligner | Pretrained document four-corner estimation. | Designed for documents, not breadboards; benchmark for transfer/generalization, not a proven solution. |
| https://universe.roboflow.com/ai-breadboard/ai-breadboard | Public object detection model `ai-breadboard/3` with Breadboard among classes, trained on a listed 588-image dataset version. | Outputs bounding boxes, **not** ordered four corners or 6-DoF pose. Online API requires external access; no permanent cloud dependency for app. Verify export availability, model/license separately. |
| https://universe.roboflow.com/karlhenz/breadboard-9y58v | Public Object Detection dataset; 1,502 listed images; CC BY 4.0 on dataset page, **0 pretrained models**. | Detection boxes are not labeled corners; likely augmentation/reannotation required for four-corner supervision. |
| https://universe.roboflow.com/deweys-workspace/breadboard-roi-seg | Segmentation-oriented dataset. | Check current dataset size, license, exports; segmentation mask alone may not resolve pose/orientation. |

Sources have not been benchmarked on the user's image/video distribution. Verify every upstream repo license, downloaded weights' license and redistribution rights before bringing assets into the Unity project. Do not store API keys or large weights in Git commits.

## Immediate work: offline reproducible comparison (NO premature training)

**Deliver actual working test tools and measured reports, not research prose only.** Follow the order below:

1. Inspect original repos, licenses, model download/checkpoint requirements, preprocessing and runtime dependencies. Create a matrix: model availability (weights vs code vs dataset), license, size, task output (bbox / segmentation / four corners), CPU latency, on-device export feasibility and known limitations.
2. Implement `Tools/markerless_eval/` with documented installation requirements and CLI:
   - `inspect` command: inventory installed model, license/source, model hash/checksum, image dimensions.
   - `predict` command: run publicly available pretrained *local* breadboard normalizer/DocAligner variant on images (include genuine upstream integration rather than fabricated simulated detections), and optionally a licensed detection/segmentation model if weights are lawfully accessible. Save annotated images, four ordered corners and confidence/quality when supported; if model only gives bbox/mask, label output accordingly.
   - `evaluate` command: compare to manually annotated four corners; report actual per-corner pixel errors, rectification errors, correctness of corner order and failure frequency, frame latency, and per-configuration results. No fabricated numbers. Include deterministic tests using simple synthetic quadrilaterals and positive/negative cases.
   - Optional `export` / JSONL format for calibration and a later Unity bridge; keep annotation format documented.
3. Check source compatibility and run at least one baseline on **available legitimately accessible sample photos**; include actual resulting output images + actual command/log and machine/software used. If any source cannot be accessed or run, explain specifically and do not claim a benchmark.
4. Prepare a tiny real-board validation set recipe for user: start with **5–10 original photos** of the bare 830 board without paper/marker (front/tilted/rotated/varied lighting), then short videos with phone moving and with board moving. Train/validation splits must be by recording session. Photos already supplied in chat of the app overlaid on board and paper are not a reliable markerless benchmark; do not assume they are available to Codex.
5. Compare baseline on real board *before* deciding whether to fine-tune. If corners wrong, masks/bbox insufficient or latency unacceptable, create a clear gap analysis and minimal labeled data plan for custom 4-keypoint model rather than training blindly.

## Pose/AR technical requirements (next phase after baseline)

- Four ordered 2D corners **are not 6-DoF pose**. Need precise measured board dimensions, S22 AR camera intrinsics and a calibrated (PnP) / homography approach. Handle mirror flips/orientation ambiguities, pixel coordinates vs preview crop, correct Unity/ARCore camera/world transforms.
- Test on physically moving board with a stationary phone AND moving camera with stationary board. A detection at one frame is not full tracking; use temporal filtering with explicit uncertainty/lost state and hide overlay if confidence fails.
- Conversion to holes requires approximately 2.54mm pitch and under-hole-spacing real-world reprojection errors. Report **millimeters** at known reference holes; never extrapolate from bbox IoU alone. Target (to be experimentally negotiated) <=1mm mean/median hole-overlay error and track 95th percentile/worst-case, with honest limitations.
- User must be able to switch Marker / Experimental Markerless AR modes in Arabic. Keep working marker mode and the existing physical electrical/routing plans unmodified. If markerless isn't experimentally proven, do NOT expose it as default.
- Offline on Android after model/install requirements. Analyze inference feasibility on S22 (conversion to ONNX / TFLite / Sentis / local mobile native runtime), without requiring a Roboflow cloud API at run time. Report APK size, latency, memory costs and licensing if measured.
- DO NOT conflate "model draws a rectangular box" with correctly anchoring jumper wires to holes.

## Deliverables and status report

- Usable commands/code in `Tools/markerless_eval/`, with dependency lock/requirements as appropriate.
- `Documentation/V2-markerless-benchmark.md` reporting provenance, executed tests, metrics/results, annotated outputs and explicit unknowns/blockers; never invent data/results.
- Clear request for *only the missing real-board data* if indispensable.
- Do **not** overwrite the V1 working branch, break the marker AR fallback, remove physical routing improvements, or commit private images/models/secrets.
- Small coherent commits on current V2 branch. State which work is COMPLETE, PARTIAL, or BLOCKED. Start with actual baseline invocation and artifacts; not only plans.
