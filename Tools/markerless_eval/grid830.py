"""Validate a rectified candidate against the editable 830-contact visual template."""

import cv2
import numpy as np

from Tools.breadboard import PROFILE_PATH, load_profile
from .geometry import order_corners

PIXELS_PER_METRE = 6000


class Grid830:
    def __init__(self, profile_path=PROFILE_PATH):
        profile = load_profile(profile_path)
        self.profile = profile
        self.width, self.height = (
            round(profile.dimensions_m[axis] * PIXELS_PER_METRE) for axis in ("x", "z")
        )
        self.dest = np.float32([[0, 0], [self.width-1, 0],
                                [self.width-1, self.height-1], [0, self.height-1]])
        terminal = sorted((hole for hole in profile.holes.values() if not hole.is_rail),
                          key=lambda hole: (hole.row, hole.column))
        rail = sorted((hole for hole in profile.holes.values() if hole.is_rail),
                      key=lambda hole: (hole.position_m[2], hole.column))
        self.terminal = self.positions(terminal).reshape(10, 63, 2)
        self.rail = self.positions(rail).reshape(4, 50, 2)
        self.pitch = profile.pitch_m * PIXELS_PER_METRE

    def positions(self, holes):
        return (np.array([(hole.position_m[0], hole.position_m[2]) for hole in holes])
                * PIXELS_PER_METRE + [(self.width-1)/2, (self.height-1)/2])

    @staticmethod
    def axes(values, center):
        return np.array([center + (values - center) * scale + shift
                         for scale in (.94, .97, 1., 1.03, 1.06)
                         for shift in (-8, -4, 0, 4, 8)]).reshape(25, *values.shape)

    def sample(self, evidence, xs, ys):
        xi = np.rint(xs).astype(int).clip(0, self.width-1)
        yi = np.rint(ys).astype(int).clip(0, self.height-1)
        return evidence[yi, xi]

    def score_warp(self, image, quad):
        warp = cv2.getPerspectiveTransform(np.float32(quad), self.dest)
        gray = cv2.cvtColor(cv2.warpPerspective(image, warp, (self.width, self.height)), cv2.COLOR_BGR2GRAY)
        # Local contrast from dark holes. A small dilation tolerates pixel rounding.
        blackhat = cv2.morphologyEx(gray, cv2.MORPH_BLACKHAT,
                                  cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (13, 13)))
        evidence = cv2.dilate(blackhat, np.ones((5, 5), np.uint8)) >= 15
        x = self.terminal[0, :, 0]
        y = self.terminal[:, 0, 1]
        xa = self.axes(x, (self.width-1)/2)
        ya = self.axes(y, (self.height-1)/2)
        on = self.sample(evidence, xa[:, None, None, :], ya[None, :, :, None])
        off = self.sample(evidence, xa[:, None, None, :] + self.pitch/2, ya[None, :, :, None])
        merit = on.mean(axis=(2, 3)) - off.mean(axis=(2, 3))
        ix, iy = np.unravel_index(np.argmax(merit), merit.shape)

        both_strips = on[ix, iy].reshape(2, 5, 3, 21).mean(axis=(1, 3))
        center_y = np.mean(ya[iy, 4:6])
        center = float(self.sample(evidence, xa[ix], center_y).mean())
        # A dark trench can be continuous. Reject repeated holes in the gap
        # by testing column phase at several lines across the separator.
        gap_phase = max(float(self.sample(evidence, xa[ix], center_y + dy).mean()
                              - self.sample(evidence, xa[ix] + self.pitch/2, center_y + dy).mean())
                        for dy in (-4, -2, 0, 2, 4))
        # Apply the same fitted geometry to actual rail positions and group pitch.
        sx = (xa[ix, -1] - xa[ix, 0]) / (x[-1] - x[0])
        sy = (ya[iy, -1] - ya[iy, 0]) / (y[-1] - y[0])
        rails_x = (self.rail[:, :, 0] - x[0]) * sx + xa[ix, 0]
        rails_y = (self.rail[:, :, 1] - y[0]) * sy + ya[iy, 0]
        rail_support = []
        rail_contrast = []
        for indexes in (slice(0, 2), slice(2, 4)):
            rx, ry = rails_x[indexes], rails_y[indexes]
            matches = []
            for dx in (-5, 0, 5):
                for dy in (-4, 0, 4):
                    hit = float(self.sample(evidence, rx+dx, ry+dy).mean())
                    miss = float(self.sample(evidence, rx+dx+self.pitch/2, ry+dy).mean())
                    matches.append((hit-miss, hit))
            contrast, support = max(matches)
            rail_support.append(support)
            rail_contrast.append(contrast)
        contrast = float(merit[ix, iy])
        terminal_support = float(on[ix, iy].mean())
        minimum_sector = float(both_strips.min())
        passes = bool(terminal_support >= .45 and minimum_sector >= .25 and contrast >= .18
                      and gap_phase <= .12
                      and min(rail_support) >= .27 and min(rail_contrast) >= .07)
        return {
            "grid830_pass": passes,
            "grid830_score": contrast + min(rail_contrast) + minimum_sector * .25,
            "terminal_support": terminal_support, "minimum_sector_support": minimum_sector,
            "terminal_phase_contrast": contrast, "central_gap_support": center,
            "central_gap_phase_contrast": gap_phase,
            "rail_support": rail_support, "rail_phase_contrast": rail_contrast,
        }

    def __call__(self, image, quad):
        ordered = order_corners(quad)
        scores = [self.score_warp(image, np.roll(ordered, -axis, axis=0)) for axis in range(2)]
        return max(scores, key=lambda result: (result["grid830_pass"], result["grid830_score"]))
