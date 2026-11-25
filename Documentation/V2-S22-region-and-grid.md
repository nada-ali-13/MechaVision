# S22 board acquisition follow-up

The private S22 image set from the [previous evaluation](V2-S22-board-evaluation.md) was still available. All six configurations used the same 12 board images, three no-board controls, pinned SA24 weights, and pinned Breadboard Normalizer. The baseline continues to use a single 960 px full-frame input and the original WB-102 check. The new backend caps each candidate at 960 px separately, so a crop can retain detail from the original photo. It never reads labels or reference corners during inference.

## Changes

- **Automatic crops.** On a full-frame miss, the contour variant proposes up to three padded bright, low-saturation connected regions. Multiscale also tests a central zoom and two overlapping windows along the long image axis. The first passing candidate wins. Quads near a candidate-image boundary are rejected as possible board fragments.
- **830-contact validation.** The new validator projects the local board profile into a metric-proportioned rectangle and tests both possible long axes. It uses the 63-column spacing, two independent five-row terminal strips, central gap, and the four rails with their specified hole grouping. The test requires contrast at expected hole positions versus the spaces between them, sufficient coverage across both strips, support on both rail sides, and low periodic hole evidence in the central gap. It allows bounded scale and translation errors in the profile fit.
- The board profile is still unmeasured. The check models visible hole geometry from the editable template and cannot determine rail continuity. An initial brightness-based gap test accepted only 1/12 on the full frame because a continuous dark trench can resemble holes by contrast alone. The final check uses column periodicity in that gap. That change was made on this development set.

## Results

| 960 px configuration | Board located / 12 | Corner failures | Grid or edge rejections | False positive / 3 | Clockwise image order | CPU p50 / p95 ms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Original WB-102, full frame | 6 | 4 | 2 | 0 | 6/6 | 438 / 497 |
| WB-102 + contour fallback | 6 | 4 | 2 | 0 | 6/6 | 430 / 838 |
| WB-102 + multiscale fallback | 7 | 2 | 3 | 0 | 7/7 | 704 / 1406 |
| 830 grid, full frame | 7 | 4 | 1 | 0 | 7/7 | 408 / 483 |
| 830 grid + contour fallback | 7 | 4 | 1 | 0 | 7/7 | 440 / 499 |
| 830 grid + multiscale fallback | **8** | **2** | **2** | **0** | **8/8** | **651 / 1335** |

There were zero inference errors. A board counts as located when the pipeline accepted a quad on the actual board. The accepted crops were visually reviewed. Some low-angle estimates included part of the board's side wall, so they should not be used as precise top-face corner references. Clockwise order is checked against the tool’s visual upper-left convention. Physical A1 orientation and numerical corner, hole, or pose errors remain unmeasured because the CSV contains presence labels only.

The multiscale fallback recovered a small overhead board on patterned fabric by taking the central zoom. The 830 gate recovered a low-angle dark-background board that already had full-frame corner candidates. The combined method still failed to produce corners on two strongly oblique views, one with the board reaching the top edge of the frame. It rejected candidates on two other tilted views. Contour fallback added no accepted boards. The best variant also rejected two public perforated-PCB controls after producing candidate corners, a separate gate sanity check. The five controls do not estimate the false-positive rate in use.

Timing is from the cloud Intel Xeon Platinum 8573C CPU, OpenCV 4.12.0 and ONNX Runtime 1.22.1, one thread each. There were two warmups and 45 timed calls per configuration. Times include the full inference chain and all fallback proposals, with decoding and overlay writing excluded. No phone speed or live tracking was measured. The private output archive contains all run records and selected overlays. Original filenames, images and per-frame predictions remain outside Git.

## Decision

Use the full-frame 830 validator as the first offline acquisition experiment and limit multiscale fallback to occasional recovery attempts. It added one hit over the original baseline at comparable cloud latency. The combined variant remains too slow here for continuous overlays. Keep marker-based tracking for live instruction.

No separate capture session was available. Reserve a fresh marker-free S22 session with annotated physical corners and measured, independently selected hole centres. Include fully visible strongly tilted or distant boards, partially cropped boards, and perforated no-board controls. Measure orientation, hole alignment, and on-device latency. Targeted fine-tuning is justified as the next experiment only if fully visible hard views still fail during corner acquisition on that held-out session. Grid-only failures are a reason to measure and recalibrate the validator first.

## Reproduction

Prepare the private manifest with the binary labels as in the [previous evaluation](V2-S22-board-evaluation.md). Supply the original image directory to the region backend so it can crop before resizing.

```sh
python -m Tools.markerless_eval predict --manifest "$run/manifest.json" --image-root "$dataset" \
  --backend region --option "checkout=$vendor" --option "weights=$sa24" \
  --option grid=830 --option proposals=multiscale --output "$run/830-multiscale"
python -m Tools.markerless_eval.presence "$dataset/labels.csv" --manifest "$run/manifest.json" \
  --results "$run/830-multiscale/results.json" > "$run/830-multiscale/presence.json"
```

Options `grid=830|wb102` and `proposals=none|contours|multiscale` reproduce the variant rows. Use the original `breadboard` invocation with `--max-input-edge 960` for the baseline. The region backend applies its own per-candidate cap. Optionally set `profile=/path/to/measured-profile.json` for the 830 grid. No profile edits or training were made in this comparison.
