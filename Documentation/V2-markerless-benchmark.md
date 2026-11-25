# MechaVision V2 markerless feasibility benchmark

## Result

Official DocAligner ONNX models and the original breadboard normalizer ran locally on real images. The strongest configuration on this small public set was **FastViT-SA24 with the normalizer’s WB-102 grid acceptance check and a 960 px input cap**. It passed the corner threshold on **8/8 board images**, rejected **2/2 no-board controls**, and took **365 ms median / 550 ms p95** per image on the cloud CPU. This is a candidate for a measured phone prototype. Physical board order, 6-DoF pose, hole alignment on the user's board, and motion tracking on Galaxy S22 are unverified.

## Candidate availability

| Candidate | Evidence and output | Status |
| --- | --- | --- |
| **Breadboard-Classifier**, `758d5a3` | Original rectifier ran on the normalizer’s public `train_medium.jpeg` and reported usable, grid grade 1.00 and column-fit margin +0.065. The CLI uses DocAligner SA24 and WB-102 grid checks. The root repository had no license file or release weights at the inspected revision. Its vendored normalizer is MIT and its vendored ICP is Apache-2.0. [Source](https://github.com/stonestephenson/Breadboard-Classifier/tree/758d5a37913c4b929926721380223c537491cbbe) | **Tested**, using the original CLI for the smoke test and an adapter invoking its vendored code for the common set. |
| **breadboard-normalizer**, `d4f09a4` | MIT source with Apache-licensed ICP and public demos. Uses a DocAligner seed, hole detection, registration and grid/rail checks. Its 85.17 MB tracked Keras file is a cropped-corner **orientation** model. The rough four-corner detector calls DocAligner. [Source](https://github.com/hartleyblakey/breadboard-normalizer/tree/d4f09a41c474e317367eab1fe5efcc27197be25c) | **Tested** via the pinned implementation vendored by Breadboard-Classifier, with both DocAligner and OpenCV seeds. The separate Keras orientation experiment was not evaluated. |
| **DocAligner 1.1.1** | Official document corner heatmap weights downloaded via GitHub Releases and checked against pinned published SHA-256 and size. Tested FP32 SA24 **83.08 MB**, T8 **13.17 MB**, LCNet100 **4.77 MB**. The code is Apache-2.0. The release did not list separate weight licensing terms. Confirm packaging rights before publishing a model in an APK. [Release and weights](https://github.com/DocsaidLab/DocAligner/releases/tag/1.1.1) | **Tested** with ONNX Runtime CPU. SA24 also reproduced the upstream document example’s published corners with a maximum discrepancy of 0.000021 px. That is an implementation check against upstream output. |
| **OpenCV baseline** | Contour quadrilaterals plus spatially distributed hole-pattern evidence. No trained weights. | **Tested** alone and as a seed for the upstream normalizer. |
| **Roboflow ai-breadboard/3** | Specification lists a 588-image version and a breadboard detection class. Its bounding boxes could provide a region for downstream corner fitting. [Model page](https://universe.roboflow.com/ai-breadboard/ai-breadboard) | **Blocked**. Universe, model API/hosted endpoints and export hosts returned proxy CONNECT 403. No lawful local weight/export or model-specific license was verified. |
| **Roboflow breadboard-9y58v** | Specification lists 1,502 detection images, CC BY 4.0 and zero pretrained models. Box annotations would still need corner labels for supervised keypoints. [Dataset page](https://universe.roboflow.com/karlhenz/breadboard-9y58v) | **Blocked** by the same proxy. No dataset download or license recheck. |
| **Roboflow breadboard-roi-seg** | Segmentation dataset candidate. A mask might support boundary fitting, with separate evidence needed for corner order. [Dataset page](https://universe.roboflow.com/deweys-workspace/breadboard-roi-seg) | **Blocked** by the same proxy. Size, current license, exports and weights were not confirmed. |

Roboflow’s SDK distinguishes the dataset ZIP from model artifacts. Dataset availability alone gives no deployable detector. The Ubuntu-side investigation did not use an API key, hosted prediction, or training. [Pinned dataset export implementation](https://github.com/roboflow/roboflow-python/blob/9415946fca4f8a2ce7742778f5265e42051c6e1c/roboflow/core/version.py#L363-L452) · [Pinned inference and license notes](https://github.com/roboflow/inference/blob/b2b30c072b9c01ac0c15927979dd7da1bc06f9c5/README.md#L259-L316)

## Actual public-image measurements

The [fixture manifest](../Tools/markerless_eval/fixtures/public_photos.json) pins eight original camera photos of populated solderless boards and two board-free photo-based illustrations of perforated PCBs. Corners were marked manually on the projected top face and scaled to original EXIF-oriented pixels. These are small, class-project samples with approximate session groupings. They do not establish independent generalization across phone models or board types. The controls challenge rejection of perforated objects and are too few to estimate a field false-positive rate. [Photo provenance and fetching](../Tools/markerless_eval/fixtures/README.md)

A pass requires all four geometry-aligned corners within **2% of the image diagonal**. This deliberately broad threshold is about candidate detection. Corner error is in original-image pixels, using the best perimeter correspondence. Order is checked separately against the declared image order from upper-left clockwise. Rectified error is the discrepancy when the prediction projects the *reference corners* onto the benchmark rectangle. It uses a nominal aspect ratio and an 825 px long edge and has no independent hole landmark information.

| Configuration | Pass / 8 | No quad / 8 | False positive / 2 | Ordered pass / comparable | Corner p50 / p95 px | Rectified p50 px | CPU p50 / p95 ms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| OpenCV | 2 | 4 | 2 | 2/4 | 11.2 / 1825.4 | 4.5 | 40.8 / 57.7 |
| OpenCV + upstream normalizer | 2 | 5 | 2 | 2/3 | 13.5 / 1851.1 | 3.6 | 122.8 / 380.0 |
| DocAligner SA24 | 8 | 0 | 2 | 8/8 | 15.0 / 48.2 | 4.0 | 275.9 / 329.4 |
| DocAligner SA24, 960 px | 8 | 0 | 2 | 8/8 | 17.6 / 53.0 | 4.7 | 171.0 / 193.2 |
| DocAligner T8 | 4 | 2 | 2 | 4/6 | 17.5 / 112.8 | 4.6 | 181.8 / 259.3 |
| DocAligner T8, 960 px | 3 | 3 | 2 | 3/5 | 17.9 / 134.7 | 4.3 | 73.9 / 78.2 |
| DocAligner LCNet100 | 5 | 1 | 2 | 5/7 | 15.9 / 98.8 | 4.5 | 187.4 / 208.7 |
| DocAligner LCNet100, 960 px | 6 | 1 | 2 | 6/7 | 17.4 / 59.9 | 4.9 | 82.0 / 87.7 |
| SA24 + normalizer, rough fallback allowed | 8 | 0 | 2 | 8/8 | 13.7 / 31.9 | 3.3 | 411.4 / 554.8 |
| SA24 + normalizer, rough fallback allowed, 960 px | 8 | 0 | 2 | 8/8 | 13.8 / 27.3 | 3.4 | 373.1 / 591.1 |
| SA24 + normalizer, require WB-102 grid | 7 | 1 | 0 | 7/7 | 12.3 / 25.2 | 3.2 | 396.0 / 551.0 |
| SA24 + normalizer, require WB-102 grid, 960 px | **8** | **0** | **0** | **8/8** | **13.8 / 27.3** | **3.4** | **364.8 / 549.5** |

Error distributions include positive images that emitted a quad, including poorly localized quads. They omit abstentions. The worst native corner error of the leading configuration was **30.4 px**. Order counts refer only to image order. There were no physically ordered outputs or independent surveyed landmarks in this benchmark. The normalizer uses the classifier’s RGB preprocessing, a fixed WB-102 grid, and a working-image cap of 1920 px before the optional explicit 960 px cap. Standalone DocAligner uses its upstream BGR preprocessing. These are pipeline comparisons, so the differences include pre/post-processing choices.

Measured on AMD EPYC 9V74 x86-64, Linux 6.18.57, Python 3.12.14, NumPy 2.2.6, OpenCV 4.12.0 and ONNX Runtime 1.22.1. Two warmup calls, then three calls per image, give 30 timed calls per configuration. OpenCV and ORT each used one intra-op thread. Time covers backend preprocessing, inference, geometry and postprocessing, including the optional input cap. It excludes setup, image decoding and output writing. No backend reported an inference error in this matrix. [Machine-readable measurements](V2-markerless-results.json)

The tool produces amber reference overlays, green predicted corners, and perspective-corrected images. The run archive in the shared workspace contains the measured CPU reports, console output, and selected actual board and rejection images. Source photos and derived pixels with unclear redistribution rights stay outside Git. [Reproduction commands and output format](../Tools/markerless_eval/README.md)

The 19 markerless unit tests and all 44 existing electrical/catalog tests passed. The local annotator also passed a browser-to-CLI smoke test using disposable images, including a no-board label, save/resume, hash verification and rejection of duplicate points.

## S22 and Unity decision

**Keep the existing marker path as the default.** The best public-set pipeline demonstrated local CPU feasibility. Its measured p95 exceeded a 30 fps frame budget by an order of magnitude, and the WB-102 grid acceptance test assumes the geometry and printed features used by upstream. T8 and LCNet100 use smaller weights and took less CPU time with capped input. On this set they missed or mislocalized boards and accepted both controls. The untrained OpenCV baseline also accepted both controls and sometimes found a wrong rectangle.

For an offline phone experiment, first run the pinned ONNX graph with an Android ONNX Runtime CPU build and the same postprocessor. Measure camera-to-result p50/p95, peak memory, installed size, thermal behavior and failure to reacquire on the S22. Quantized weights, TFLite conversion, Sentis import/operator compatibility and hardware acceleration remain untested. The upstream grid fit requires OpenCV and Python-side hole extraction, nearest-neighbor registration and geometric checks. It would need a mobile port separately from the ONNX model. The model file sizes above exclude runtime/APK overhead. Unity and Android were not run for this spike.

A later AR integration needs calibrated S22 intrinsics, correct handling of camera image orientation/crop, measured board dimensions and a stable physical corner identity. Evaluate pose from PnP or calibrated homography in the ARCore camera/world frame. Measure error at **independent** hole centers rather than the same corners used by the fit. Test board motion and camera motion separately, with conceal/reacquire and an explicit uncertain/lost state. The existing marker and electrical routing paths remain available during that work.

## Capture needed for the user's 830-point board

1. Take **eight original rear-camera photos** at 1× on the S22, with the bare board fully visible and the printed marker and paper removed. Take two near-overhead photos at roughly 30 and 50 cm, two photos tilted roughly 25–40° from opposite edges, an in-plane 90° view and a 180° view, and two views on a second background in different lighting. Keep the board’s text, rail stripes and outer corners sharp. Add two no-board photos of the same settings.
2. Record **three 10–15 second clips** at 1080p/30 fps. Move the camera around a stationary board, then move and rotate the board with the phone fixed, then briefly occlude the board and bring it back into view. Keep each independent recording in a separate session folder. Preserve original files and extract frames without cropping or mirroring. If later using data for fine-tuning, keep each session wholly in training or held-out evaluation.
3. Measure the board’s top-face dimensions and hole coordinates relative to its centre. Record the native order of the top-face corners nearest **A1 → A63 → J63 → J1**. In the annotation tool, label those four corners in that order and mark eight or more independent visible hole centres across the corners, sides and centre. Store the measured `[X,Z]` offsets for each landmark. [Board measuring checklist](Breadboard-profile.md) · [Local annotator instructions](../Tools/markerless_eval/README.md#annotate-a-private-capture-session)

That set is the next gate for measuring physical orientation, error in millimetres and motion. No training was run. The public-image results support evaluating the gated pretrained pipeline on that set before deciding whether a custom corner model is needed.
