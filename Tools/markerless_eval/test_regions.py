import unittest

import cv2
import numpy as np

from Tools.markerless_eval.grid830 import Grid830
from Tools.markerless_eval.region_backend import RegionBackend, contour_regions, multiscale_regions


class GridTests(unittest.TestCase):
    def setUp(self):
        self.validator = Grid830()
        self.image = np.full((self.validator.height, self.validator.width, 3), 235, np.uint8)

    def draw(self, holes):
        for x, y in np.rint(holes.reshape(-1, 2)).astype(int):
            cv2.circle(self.image, (x, y), 3, (30, 30, 30), -1)

    def test_accepts_profile_and_rotated_image(self):
        self.draw(self.validator.terminal)
        self.draw(self.validator.rail)
        self.assertTrue(self.validator(self.image, self.validator.dest)["grid830_pass"])
        rotated = cv2.rotate(self.image, cv2.ROTATE_90_CLOCKWISE)
        height, width = rotated.shape[:2]
        self.assertTrue(self.validator(rotated, [[0, 0], [width-1, 0], [width-1, height-1],
                                                [0, height-1]])["grid830_pass"])

    def test_rejects_blank_and_pattern_without_rails(self):
        self.assertFalse(self.validator(self.image, self.validator.dest)["grid830_pass"])
        self.draw(self.validator.terminal)
        self.assertFalse(self.validator(self.image, self.validator.dest)["grid830_pass"])

    def test_rejects_missing_central_gap(self):
        self.draw(self.validator.terminal)
        self.draw(self.validator.rail)
        center = self.validator.terminal[4:5].copy()
        center[:, :, 1] = (self.validator.height-1)/2
        self.draw(center)
        self.assertFalse(self.validator(self.image, self.validator.dest)["grid830_pass"])

    def test_accepts_a_continuous_dark_center_trench(self):
        self.draw(self.validator.terminal)
        self.draw(self.validator.rail)
        y = self.validator.height // 2
        cv2.line(self.image, (0, y), (self.validator.width-1, y), (35, 35, 35), 4)
        self.assertTrue(self.validator(self.image, self.validator.dest)["grid830_pass"])


class RegionTests(unittest.TestCase):
    def test_crop_uses_original_pixels_and_maps_coordinates(self):
        class Seed:
            info = {}

            def __call__(self, _):
                return {"corners_px": [[20, 20], [80, 20], [80, 60], [20, 60]],
                        "wb102_fit_accepted": True}

        region = RegionBackend(Seed(), "contours", "wb102")
        image = np.zeros((200, 300, 3), np.uint8)
        result = region.predict_region(image, (100, 40, 220, 140))
        self.assertEqual(result["corners_px"], [[120, 60], [180, 60], [180, 100], [120, 100]])
        self.assertTrue(result["grid_pass"])

    def test_regions_are_bounded(self):
        image = np.zeros((300, 430, 3), np.uint8)
        image[80:220, 150:290] = 230
        contours = contour_regions(image)
        self.assertTrue(contours)
        for x1, y1, x2, y2 in [*contours, *multiscale_regions(430, 300)]:
            self.assertTrue(0 <= x1 < x2 <= 430 and 0 <= y1 < y2 <= 300)
