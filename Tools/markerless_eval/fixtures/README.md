# Public smoke-test fixtures

The manifest covers eight real camera photographs of populated solderless boards and two challenging board-free perforated-PCB examples. The camera photographs come from the public CS 470 class project. The negatives are photo-based illustrations from Arduino's soldering guide. The input images stay outside the repository. The pinned CS 470 revision has no explicit permission to redistribute its photographs. Arduino's documentation is under CC BY-SA 4.0 at the repository level. The negative illustrations' underlying product-photo rights were not independently established. Review source terms before republishing images or using them beyond evaluation.

- [CS 470 project and raw camera inputs](https://github.com/sparaj333/breadboard-object-detection-cs470/tree/b3310b3175abf787d10db3f450b63ef4ffe5fc7c/CS%20470%20docs/stage2)
- [Arduino soldering guide assets](https://github.com/arduino/docs-content/tree/65d578fc7de843c45c21fc77b31a7a2009c46a5b/content/learn/04.electronics/02.soldering-basics/assets)
- [Arduino documentation license](https://github.com/arduino/docs-content/blob/65d578fc7de843c45c21fc77b31a7a2009c46a5b/LICENSE.md)

From the repository root, download the original bytes to a local directory outside the checkout. SHA-256 verification applies to fresh downloads and existing files.

```sh
python3 Tools/markerless_eval/fixtures/fetch_public_photos.py /tmp/mechavision-markerless-public
```

Pass `Tools/markerless_eval/fixtures/public_photos.json` and `--image-root /tmp/mechavision-markerless-public` to the evaluator. The labels were marked manually using pixel grids on display previews, then scaled back to the native EXIF-oriented image dimensions. They describe the projected top-face boundary, excluding shadows and rail interlock tabs. They follow image order and carry no physical orientation or subpixel ground truth.

These are smoke-test samples from foreign boards. The visible setups and filenames informed the session grouping. Shared boards or camera settings remain possible across those groups. Device calibration, physical dimensions and landmarks were unavailable. Corner scoring here supports a limited image-space detection check. S22 pose, tracking persistence and millimetre alignment require separate measured captures.
