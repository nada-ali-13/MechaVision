import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import cv2
import numpy as np

from Tools.markerless_eval.cli import invoke
from Tools.markerless_eval.geometry import align_corners, order_corners, project, rectification, validate_quad
from Tools.markerless_eval.manifest import manifest_frames
from Tools.markerless_eval.metrics import score, summary


REFERENCE = np.array([[10, 20], [175, 20], [175, 75], [10, 75]], dtype=np.float64)
SIZE = (220, 100)
BOARD = (165, 55)


class TestGeometry(unittest.TestCase):
    def test_permuted_corner_candidates_use_image_order(self):
        np.testing.assert_array_equal(order_corners(REFERENCE[[2, 0, 3, 1]]), REFERENCE)

    def test_rejects_crossing_corners_on_input(self):
        with self.assertRaisesRegex(ValueError, "convex"):
            validate_quad(REFERENCE[[0, 2, 1, 3]], SIZE)

    def test_rejects_outside_image(self):
        with self.assertRaisesRegex(ValueError, "outside"):
            validate_quad(REFERENCE, (170, 100))

    def test_correspondence_accounts_for_reflected_order(self):
        _, mirrored, _, aligned, errors = align_corners(REFERENCE[::-1], REFERENCE)
        self.assertTrue(mirrored)
        np.testing.assert_allclose(aligned, REFERENCE)
        np.testing.assert_allclose(errors, 0)

    def test_rectification_maps_a_perspective_quad(self):
        quad = np.array([[12, 15], [185, 24], [156, 80], [43, 73]], dtype=np.float64)
        mapping, canonical, size = rectification(quad, BOARD)
        self.assertEqual(size, (825, 275))
        np.testing.assert_allclose(project(mapping, quad), canonical, atol=1e-7)

    def test_reduced_input_corner_coordinates_return_to_native_scale(self):
        image = np.zeros((100, 200, 3), dtype=np.uint8)

        def backend(resized):
            self.assertEqual(resized.shape, (25, 50, 3))
            return {"corners_px": None, "rejected_corners_px": [[2, 3], [40, 3], [40, 20], [2, 20]]}

        self.assertEqual(invoke(backend, image, 50)["rejected_corners_px"],
                         [[8, 12], [160, 12], [160, 80], [8, 80]])


class TestMetrics(unittest.TestCase):
    def frame(self, corners, order="physical", landmarks=()):
        class Frame:
            annotated = True
            record = {"corners_px": corners, "corner_order": order, "landmarks": landmarks}
        return Frame()

    def run_score(self, frame, corners, order="physical"):
        return score(frame, {"corners_px": corners, "corner_order": order}, SIZE, BOARD, .02, 825)

    def test_hole_metric_requires_physical_order_and_independent_landmark(self):
        frame = self.frame(REFERENCE, landmarks=[{"id": "centre", "pixel_px": [92.5, 47.5], "board_mm": [0, 0]}])
        verified = self.run_score(frame, REFERENCE)
        self.assertTrue(verified["physical_order_verified"])
        self.assertAlmostEqual(verified["landmark_errors_mm"][0]["error_mm"], 0)
        image_order_only = self.run_score(frame, REFERENCE, order="image")
        self.assertIsNone(image_order_only["physical_order_verified"])
        self.assertFalse(image_order_only["landmark_errors_mm"])

    def test_geometry_success_does_not_imply_correct_orientation(self):
        frame = self.frame(REFERENCE)
        result = self.run_score(frame, np.roll(REFERENCE, 2, axis=0))
        self.assertEqual(result["outcome"], "corner_pass")
        self.assertFalse(result["order_correct_within_threshold"])
        self.assertFalse(result["physical_order_verified"])

    def test_negative_and_missing_corners_are_reported_separately(self):
        self.assertEqual(self.run_score(self.frame(None), REFERENCE)["outcome"], "false_positive")
        self.assertEqual(self.run_score(self.frame(None), None)["outcome"], "true_negative")
        self.assertEqual(self.run_score(self.frame(REFERENCE), None)["outcome"], "no_corners")

    def test_summary_accepts_group_iterators(self):
        report = summary(iter([{"truth": "board", "outcome": "no_corners", "inference_ms": [3, 5]}]))
        self.assertEqual(report["positive_failures"], 1)
        self.assertEqual(report["inference_ms"]["median"], 4)


class TestManifest(unittest.TestCase):
    def test_loads_unicode_paths_and_rejects_substituted_photo(self):
        with TemporaryDirectory() as tmp:
            directory = Path(tmp)
            image = np.zeros((100, 220, 3), dtype=np.uint8)
            jpeg = cv2.imencode(".png", image)[1].tobytes()
            photo = directory / "بورد.png"
            photo.write_bytes(jpeg)
            manifest = directory / "manifest.json"
            manifest.write_text(json.dumps({"schema_version": 1, "images": [{
                "id": "board", "path": photo.name, "corners_px": REFERENCE.tolist(),
                "source": {"sha256": hashlib.sha256(jpeg).hexdigest()},
            }]}), encoding="utf-8")
            frame, = manifest_frames(manifest)
            decoded, _ = frame.read()
            self.assertEqual(decoded.shape, image.shape)
            photo.write_bytes(b"other content")
            with self.assertRaisesRegex(ValueError, "SHA-256"):
                frame.read()


if __name__ == "__main__":
    unittest.main()
