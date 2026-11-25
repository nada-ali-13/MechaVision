# MechaVision markerless evaluation

Run from the repository root with Python 3.12. All inference is local once the fixtures, model and dependencies have been downloaded. Example commands below use a POSIX shell. On Windows use the Python executable of the activated virtual environment and substitute local paths.

```sh
python -m pip install -r Tools/markerless_eval/requirements-docaligner.txt
python -m Tools.markerless_eval.fetch_weights --output-dir /tmp/mecha-weights
python Tools/markerless_eval/fixtures/fetch_public_photos.py /tmp/mecha-photos
python -m unittest discover -s Tools/markerless_eval -p 'test_*.py'
```

Use the base `requirements.txt` for the OpenCV baseline alone. For the optional upstream normalizer, install `requirements-breadboard.txt` in the same environment. Only supply a trusted checkout. The adapter imports its vendored MIT normalizer and Apache-licensed ICP code. Models, checkouts and images belong in local directories outside the MechaVision Git tree.

```sh
git clone https://github.com/stonestephenson/Breadboard-Classifier.git /tmp/mecha-upstream
git -C /tmp/mecha-upstream checkout 758d5a37913c4b929926721380223c537491cbbe
python -m pip install -r Tools/markerless_eval/requirements-breadboard.txt
```

## Inspect, predict, evaluate

`inspect` lists runtime and image provenance. With a backend selected it also loads that backend and shows its model digest, source, size and other active options.

```sh
python -m Tools.markerless_eval inspect --backend docaligner \
  --option weights=/tmp/mecha-weights/lcnet100_h_e_bifpn_256_fp32.onnx \
  --manifest Tools/markerless_eval/fixtures/public_photos.json --image-root /tmp/mecha-photos

python -m Tools.markerless_eval predict --backend docaligner \
  --option weights=/tmp/mecha-weights/fastvit_sa24_h_e_bifpn_256_fp32.onnx \
  --image /path/to/photo.jpg --output /tmp/mecha-single
```

For the measured comparison, use the same fixture manifest, threshold, repeat count and fresh output directory for each configuration.

```sh
manifest=Tools/markerless_eval/fixtures/public_photos.json
python -m Tools.markerless_eval evaluate --manifest "$manifest" --image-root /tmp/mecha-photos \
  --backend classical --output /tmp/mecha-classical

for model in fastvit_sa24 fastvit_t8 lcnet100; do
  python -m Tools.markerless_eval evaluate --manifest "$manifest" --image-root /tmp/mecha-photos \
    --backend docaligner --option "weights=/tmp/mecha-weights/${model}_h_e_bifpn_256_fp32.onnx" \
    --output "/tmp/mecha-$model"
done

python -m Tools.markerless_eval evaluate --manifest "$manifest" --image-root /tmp/mecha-photos \
  --backend breadboard --option checkout=/tmp/mecha-upstream \
  --option weights=/tmp/mecha-weights/fastvit_sa24_h_e_bifpn_256_fp32.onnx \
  --option require_grid=true --max-input-edge 960 --output /tmp/mecha-grid-960
```

Add `--max-input-edge 960` with a distinct output directory to run a reduced-resolution configuration. Use `--option require_grid=false` (default) to inspect raw normalizer results even when its WB-102 grid rejects them. Use `--option seed=classical` for the upstream normalizer without pretrained weights. DocAligner defaults to upstream BGR preprocessing; the classifier adapter defaults to its upstream RGB. The normalizer internally caps its working image edge at 1920 unless changed via `--option max_side=...`.

The CLI saves the annotated originals, the warped candidate when a quad was emitted, and `results.json` with original-pixel coordinates, timing per invocation and an image-to-rectified homography. Green is predicted geometry and amber is the manual reference. A rectification can be produced for a wrong board candidate. Consult the result for false positives and misses. Public test measurements and limitations are in the [benchmark report](../../Documentation/V2-markerless-benchmark.md).

## Annotate a private capture session

Keep photos in a directory outside this checkout. The annotation server listens only on loopback and uses Python's standard library.

```sh
python Tools/markerless_eval/annotate.py \
  --images /path/to/dataset/session-01 --session-id session-01 \
  --board-id my-830 --output /path/to/dataset/manifest.json
```

Use the same dataset root and output manifest with a new session ID when labeling additional captures. Use physical order for the four outside corners of the board's **top face** nearest **A1 → A63 → J63 → J1** in that sequence even when the board is upside down in the photo. Put an uncertain or occluded corner aside for separate qualitative evaluation. For unknown boards use image order (clockwise from the upper-left as defined by smallest x+y). Explicitly mark negative frames; unannotated frames are omitted. An optional independent hole landmark records its center in the image and measured planar board coordinates in millimetres, X along A1→A63 and Z toward J. Use the board top centre as the physical origin.

Each manifest contains `schema_version: 1` and `images`. An image record has a unique portable `id`, a `path` relative to the manifest parent or supplied `--image-root`, a `session_id`, a `board_id`, `corner_order`, and `corners_px` as four `[x,y]` pairs or `null` for a verified negative. Optional fields include oriented `width_px` and `height_px`, `source.sha256`, and `landmarks` as records with `id`, `pixel_px: [x,y]` and `board_mm: [x,z]`. Use source images at their original EXIF orientation as shown in the annotator. The evaluator checks declared dimensions, decode, bounds and file digests.

For a measured profile pass its width and height with `--board-mm WIDTH HEIGHT`. Hole error in millimetres is reported only when independent landmark annotations and matching physical corner ordering are both available. Current backends produce image-order corners.
