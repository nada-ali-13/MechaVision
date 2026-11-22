# V2 evaluation on the user's 830-contact board

The dataset contained 12 board photographs and three no-board controls from a Galaxy S22. Both ZIP archives passed CRC validation. All 15 JPEGs decoded and matched the filenames and binary labels in the CSV. Original bytes, labels, prediction images, and per-file results were kept outside the checkout.

## Measured results

| Outcome | Count |
| --- | ---: |
| Board photos accepted | 6/12 |
| Board photos rejected | 6/12 |
| No-board controls rejected | 3/3 |
| False positives | 0/3 |
| Inference errors | 0/15 |

The benchmark used release 1.1.1 of the verified official DocAligner FastViT-SA24 FP32 ONNX checkpoint, RGB preprocessing through the pinned Breadboard Normalizer, its WB-102 grid acceptance check, and a 960 px input cap. The two runs produced the same decisions. In the final run, 45 timed calls after two warmups gave a median of **412 ms** and p95 of **578 ms** on the cloud Intel Xeon Platinum 8573C CPU with ONNX Runtime 1.22.1 and OpenCV 4.12.0, each configured for one thread. The first run gave 367 ms median and 462 ms p95. Times cover the backend and resizing, excluding image decode and output rendering. There is no on-phone latency measurement.

Visual review placed all six accepted quadrilaterals on the actual board. These quads were convex and consistently ordered clockwise from the visual upper-left by the tool's image convention. All six rectifications show the terminal strips and rails. Image order can rotate with the camera, so physical A1 orientation and independent hole alignment remain unverified. The CSV contains presence labels only, so no numerical corner or hole accuracy was measured.

Four positive misses came from missing coarse corners. Two produced candidate corners that failed the WB-102 grid check. On patterned fabric, 2 of 5 positives were accepted. The smaller overhead board and two strongly foreshortened views missed, while another tilted fabric view passed. Both wood-background images passed, including a tilted view. Two of three tile views passed. The missed tile view combines oblique perspective and uneven illumination, so this set does not isolate lighting. Both dark-background views missed, including a strongly foreshortened close-up with its far edge near or beyond the frame boundary.

## Integration decision

The 50% acceptance rate and desktop timing rule out the current pipeline as the primary per-frame AR tracker. Keep the working marker mode. For an offline S22 prototype, evaluate SA24 as an intermittent acquisition or reacquisition candidate and require a measured geometry and confidence gate before showing routes. Compare board-region cropping and a board-specific grid configuration against the unchanged 960 px baseline on a separate session. Annotate the accepted and missed frames with four physical corners and independent hole centres, then measure S22 latency and hole alignment. Four misses were upstream of the grid gate, so a gate change alone cannot recover them. Consider targeted fine-tuning only if the coarse detector still misses fully visible boards after that controlled comparison.

## Reproduction

With the dependencies and checkpoint from the [public benchmark](V2-markerless-benchmark.md), use an extracted dataset outside the Git checkout. These commands keep presence scoring separate from corner accuracy.

```sh
python -m Tools.markerless_eval.presence "$dataset/labels.csv" --manifest "$run/manifest.json"
python -m Tools.markerless_eval predict --manifest "$run/manifest.json" --image-root "$dataset" \
  --backend breadboard --option "checkout=$vendor" --option "weights=$sa24" \
  --option require_grid=true --max-input-edge 960 --output "$run/predictions"
python -m Tools.markerless_eval.presence "$dataset/labels.csv" --manifest "$run/manifest.json" \
  --results "$run/predictions/results.json" > "$run/presence.json"
```

For physical reference labels, use the existing [private annotation workflow](../Tools/markerless_eval/README.md#annotate-a-private-capture-session).
