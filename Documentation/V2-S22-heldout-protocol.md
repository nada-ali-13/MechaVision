# MechaVision V2 held-out physical evaluation

Freeze the original full-frame WB-102 pipeline, the full-frame 830 gate, and the 830 gate with multiscale fallback from [the development comparison](V2-S22-region-and-grid.md). A new capture session is the test set. Keep its images out of development and retain its results before making further changes.

## Minimum data to capture

- **One new session** of at least eight marker-free board photos and three no-board controls. Use the S22 rear camera at 1×. Take near and far overhead views, 90° and 180° rotations, several fully visible tilted views from different edges, and at least one view on a second background or under different lighting. Keep the four top-face corners visible. Use original unmirrored images and include a perforated-object control if available. Keep partially clipped and moving-video frames as a separate challenge set until the fully visible comparison is complete.
- **Measured board dimensions** in millimetres. Measure the straight outer edges of the top surface. Width follows the column-1 to column-63 direction and height spans the terminal strips and rails. Record the actual measurements and instrument resolution. Repeat the measurements and record the spread.
- **Independent hole centres.** Identify at least eight visible holes spread along the length and across both terminal strips. For example, use A5, C17, E30, A57, J6, F34, H48 and J58 if clear. Use the same physical IDs across photos where visible. Measure each hole’s centre relative to the outer edges with a caliper or a calibrated overhead measurement. Use the centre of the top face as origin. Subtract half the measured width from the distance along X from the column-1 edge, and half the measured height from the distance along Z from the A-row side. X increases toward column 63 and Z toward row J. Record measured offsets and measurement uncertainty. The nominal 2.54 mm pitch and the unmeasured layout template are insufficient evidence for metric accuracy.

Label the four **outer top-face corners nearest A1 → A63 → J63 → J1** in that order. A1 and the others identify the nearby corner, so click the outer face intersection and use the hole-centre fields separately. Follow the same physical order when the board is rotated. Zoom in on each hole and click the centre of its opening. Omit any hole you cannot identify confidently. Mark every control explicitly as no-board. Add a second independent annotation pass if the expected errors approach the uncertainty in the labels.

Run the existing annotation tool from the repository root. Store the manifest and photos outside the Git checkout.

```sh
python Tools/markerless_eval/annotate.py --images "$session_dir" \
  --session-id s22-holdout-01 --board-id my-830 --corner-order physical \
  --output "$session_dir/manifest.json"
```

Open the full localhost link printed by the launcher on the computer running it. The page and JPEGs are served by that process. Keep the terminal open while labeling. The base port address alone returns a 404 because the annotation session uses a private link. Restarting the server generates a new link while saved annotations remain in the manifest. When the cloud workspace provides no browser preview, use a private local copy of the tool and photos on your own computer.

Create a private `measurements.json` containing `board_id` with the same ID used in the annotator, numeric `width_mm` and `height_mm`, and `measurement_notes` describing the instrument, uncertainty and what was measured. Keep these fields blank in your own notes until you have the measured values. You can run the pixel-only comparison by omitting the measurements file.

## Run the fixed comparison

Use the dependencies and local SA24 checkpoint from [the previous benchmark](../Tools/markerless_eval/README.md). Keep the Breadboard-Classifier checkout at clean commit `758d5a37913c4b929926721380223c537491cbbe`. Supply the earlier development set's private `image-inventory.json` or a `results.json` covering all 15 original photos. The runner verifies hashes against that inventory before it starts. It rejects duplicate bytes and conflicting session labels. This check cannot detect a resized copy or a near-duplicate frame from an earlier session. Use a genuinely new capture session.

```sh
python -m Tools.markerless_eval.heldout \
  --manifest "$session_dir/manifest.json" --image-root "$session_dir" \
  --session s22-holdout-01 --development-inventory "$development_inventory" \
  --measurements "$session_dir/measurements.json" \
  --weights "$sa24" --checkout "$vendor" --output "$private_results"
```

The runner uses the same 960 px caps, grid profiles, region proposals, and 2%-of-image-diagonal corner pass threshold as the prior tools. Measured dimensions affect scoring, with the original grid gate frozen. Each result gives acceptance and corner pass rates for board images, false-positive rate on controls, and counts for missing corners, grid rejections and crop-edge rejections. It retains backend latency and per-frame output. The pixel pass threshold is an acquisition check and carries no metric tolerance.

All three detectors currently output **image-order** corners. The report records any cyclic shift or reversal needed to match physical labels and how often the raw order coincides on corner passes. Such coincidence gives no evidence of a native A1 detector. The explicit physical-order field reports that the backends emit no physical order. If measured dimensions are supplied, the evaluator uses the reference corners to establish correspondence *after* inference. It reports planar corner error in millimetres and tests the predicted warp against independently annotated, measured hole centres. These conditional results diagnose geometry after the orientation ambiguity is resolved. They give no claim of autonomous hole alignment, camera pose, or AR accuracy.

The fixed comparison ran end to end on disposable synthetic inputs in the cloud. The tests exercise millimetre calculations, image reuse rejection and missing-corner/grid separation. There is no new physical capture or annotation in the workspace, so held-out scores and real millimetre errors are pending.

## Android measurement

The [standalone Android benchmark](../Tools/markerless_eval/android/README.md) runs the pinned OFFLINE SA24 model on one original photo from the new session. The checkpoint was verified at **83,084,930 bytes**. Android package size, process memory and latency are pending a phone run. The benchmark isolates the model stage and leaves a later full-pipeline measurement for the corner, grid, region and AR integration stages. The working marker tracker and electrical and routing systems require no changes.
