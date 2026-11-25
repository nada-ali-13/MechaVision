import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import cv2
import numpy as np

from Tools.markerless_eval.heldout import metric_errors, preflight, summarize


class HeldOutTests(unittest.TestCase):
    def test_reference_aligned_metric_is_in_millimetres(self):
        reference = [[10, 10], [210, 10], [210, 110], [10, 110]]
        shifted = np.array(reference) + [4, 0]
        corners, holes = metric_errors(shifted, reference, [
            {"id": "C20", "pixel_px": [90, 50], "board_mm": [-10, -5]},
        ], (100, 50))
        np.testing.assert_allclose(corners, [2]*4)
        self.assertAlmostEqual(holes[0]["error_mm"], 2)

    def test_preflight_rejects_reused_bytes_even_with_new_session_id(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            photos = root / "picture.png"
            photos.write_bytes(cv2.imencode(".png", np.zeros((60, 80, 3), np.uint8))[1].tobytes())
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps({"schema_version": 1, "images": [{
                "id": "image", "path": photos.name, "session_id": "new", "corners_px": None,
            }]}))
            inventory = root / "inventory.json"
            inventory.write_text(json.dumps({"images": [{"sha256": hashlib.sha256(photos.read_bytes()).hexdigest()}]}))
            with self.assertRaisesRegex(ValueError, "development-image match"):
                preflight(manifest, root, "new", inventory, None)

    def test_image_order_is_not_called_physical_after_diagnostic_reindexing(self):
        reference = [[210, 110], [10, 110], [10, 10], [210, 10]]
        corners = [reference[i] for i in (2, 3, 0, 1)]
        results = {"summary": {"positive_images": 3, "negative_images": 1, "positive_corner_passes": 1},
                   "images": [
                       {"id": "board", "corners_px": corners, "corner_order": "image", "outcome": "corner_pass"},
                       {"id": "missing", "corners_px": None, "outcome": "no_corners"},
                       {"id": "grid", "corners_px": None, "rejected_corners_px": corners, "outcome": "no_corners"},
                       {"id": "negative", "corners_px": None, "outcome": "true_negative"},
                   ]}
        labels = {key: {"corners_px": reference} for key in ("board", "missing", "grid")}
        labels["negative"] = {"corners_px": None}
        report = summarize(results, labels, ("demo", (100, 50)))
        self.assertEqual(report["stages"]["board_grid_rejected"], 1)
        self.assertEqual(report["stages"]["board_corner_failure"], 1)
        self.assertEqual(report["physical_order_counts_on_accepted_positives"], {"not_emitted": 1})
        self.assertEqual(report["reference_aligned_corner_mm"]["max"], 0)
        self.assertIsNone(report["reference_aligned_independent_hole_mm"]["median"])
