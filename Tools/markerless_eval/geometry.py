"""Pixel-space quadrilateral geometry shared by the evaluation backends."""

import cv2
import numpy as np


def points(value, count=4):
    result = np.asarray(value, dtype=np.float64)
    if result.shape != (count, 2) or not np.all(np.isfinite(result)):
        raise ValueError(f"expected {count} finite (x, y) points")
    return result


def validate_quad(value, size=None):
    """Keep the supplied order and require a simple, strictly convex polygon."""
    quad = points(value)
    edges = np.roll(quad, -1, axis=0) - quad
    following = np.roll(edges, -1, axis=0)
    turns = edges[:, 0] * following[:, 1] - edges[:, 1] * following[:, 0]
    if not (np.all(turns > 1e-6) or np.all(turns < -1e-6)):
        raise ValueError("corners must form a convex quadrilateral in perimeter order")
    if abs(cv2.contourArea(quad.astype(np.float32))) < 4:
        raise ValueError("quadrilateral area is too small")
    if size is not None and (np.any(quad < 0) or np.any(quad >= np.asarray(size))):
        raise ValueError("corner lies outside the image")
    return quad


def order_corners(value):
    """Clockwise image order from the visual upper-left; no physical index claim."""
    quad = points(value)
    relative = quad - quad.mean(axis=0)
    ordered = quad[np.argsort(np.arctan2(relative[:, 1], relative[:, 0]))]
    upper_left = np.lexsort((ordered[:, 0], ordered[:, 1], ordered.sum(axis=1)))[0]
    return validate_quad(np.roll(ordered, -int(upper_left), axis=0))


def align_corners(prediction, reference):
    """Find the nearest cyclic or mirrored correspondence for geometry-only scoring."""
    candidates = []
    for mirrored, winding in ((False, prediction), (True, prediction[::-1])):
        for shift in range(4):
            candidate = np.roll(winding, -shift, axis=0)
            error = np.linalg.norm(candidate - reference, axis=1)
            candidates.append((float(np.mean(error ** 2)), mirrored, shift, candidate, error))
    return min(candidates, key=lambda item: item[:3])


def rectification(quad, board_mm, long_edge_px=825, corner_order="image"):
    """Map a predicted quad to a rectangle, stating when its axes were inferred."""
    width_mm, height_mm = board_mm
    lengths = np.linalg.norm(np.roll(quad, -1, axis=0) - quad, axis=1)
    portrait = corner_order == "image" and (lengths[1] + lengths[3]) > (lengths[0] + lengths[2])
    dimensions = (height_mm, width_mm) if portrait else board_mm
    scale = long_edge_px / max(dimensions)
    width, height = (max(2, round(value * scale)) for value in dimensions)
    canonical = np.array([[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]])
    mapping = cv2.getPerspectiveTransform(np.float32(quad), np.float32(canonical))
    return mapping, canonical, (width, height)


def project(mapping, coordinates):
    return cv2.perspectiveTransform(np.float64(coordinates)[None, :, :], mapping)[0]
