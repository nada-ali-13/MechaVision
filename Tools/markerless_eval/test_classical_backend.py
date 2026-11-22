"""Synthetic regression tests for the contour-and-hole backend."""
import unittest

try:
    import cv2
    import numpy as np
except ModuleNotFoundError as error:
    raise unittest.SkipTest("Markerless tests require Tools/markerless_eval/requirements.txt") from error

from Tools.markerless_eval.classical_backend import create_backend


def _synthetic_board(*, perforated: bool, target: np.ndarray) -> np.ndarray:
    width, height = 501, 167
    board = np.full((height, width, 3), 219, dtype=np.uint8)
    cv2.line(board, (4, height // 2), (width - 5, height // 2), (198, 198, 198), 6)
    if perforated:
        pitch = (width - 1) * 2.54 / 165
        for z_mm in (-13.97, -11.43, -8.89, -6.35, -3.81, 3.81, 6.35, 8.89, 11.43, 13.97):
            y = round((height - 1) * (0.5 + z_mm / 55))
            for col in range(63):
                x = round((width - 1) / 2 + (col - 31) * pitch)
                cv2.circle(board, (x, y), 2, (24, 24, 24), -1, cv2.LINE_AA)
        for z_mm in (-22.86, -20.32, 20.32, 22.86):
            y = round((height - 1) * (0.5 + z_mm / 55))
            for group in range(10):
                for col in range(5):
                    x = round((width - 1) / 2 + (group * 6 + col - 29) * pitch)
                    cv2.circle(board, (x, y), 2, (24, 24, 24), -1, cv2.LINE_AA)

    source = np.array([[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]], np.float32)
    transform = cv2.getPerspectiveTransform(source, target)
    return cv2.warpPerspective(board, transform, (870, 620), borderValue=(57, 67, 77))


class ClassicalBackendTests(unittest.TestCase):
    def setUp(self):
        self.detect = create_backend({})
        self.target = np.array([[108, 191], [740, 147], [714, 371], [135, 423]], np.float32)

    def test_recovers_perspective_quad_in_image_order(self):
        image = _synthetic_board(perforated=True, target=self.target)
        result = self.detect(image)
        self.assertEqual(result["corner_order"], "image")
        self.assertIsNotNone(result["corners_px"])
        error = np.linalg.norm(np.array(result["corners_px"]) - self.target, axis=1)
        self.assertLess(float(error.max()), 10)
        self.assertGreater(result["diagnostics"]["hole_like_blobs"], 100)

    def test_recovers_vertical_board(self):
        target = np.array([[583, 69], [561, 551], [396, 560], [377, 94]], np.float32)
        image = _synthetic_board(perforated=True, target=target)
        result = self.detect(image)
        self.assertIsNotNone(result["corners_px"])
        error = np.linalg.norm(np.array(result["corners_px"]) - target[[3, 0, 1, 2]], axis=1)
        self.assertLess(float(error.max()), 10)

    def test_returns_native_pixels_after_internal_resize(self):
        image = _synthetic_board(perforated=True, target=self.target)
        result = create_backend({"max_dimension": "550"})(image)
        self.assertIsNotNone(result["corners_px"])
        error = np.linalg.norm(np.array(result["corners_px"]) - self.target, axis=1)
        self.assertLess(float(error.max()), 13)

    def test_smooth_quadrilateral_is_not_enough(self):
        image = _synthetic_board(perforated=False, target=self.target)
        self.assertIsNone(self.detect(image)["corners_px"])

    def test_empty_image_is_not_a_detection(self):
        self.assertIsNone(self.detect(np.zeros((620, 870, 3), np.uint8))["corners_px"])

    def test_invalid_explicit_options_are_rejected(self):
        with self.assertRaises(ValueError):
            create_backend({"expected_aspect": "-3"})
        with self.assertRaises(ValueError):
            create_backend({"unexpected": "argument"})


if __name__ == "__main__":
    unittest.main()
