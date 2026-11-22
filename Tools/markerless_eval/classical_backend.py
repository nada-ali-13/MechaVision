"""Contour and repeated-hole baseline for markerless breadboard localization."""
from __future__ import annotations

import math

import cv2
import numpy as np

from .geometry import order_corners


def create_backend(options: dict[str, str]):
    """Create a BGR-image detector. Its quadrilateral uses image order."""
    supported = {"max_dimension", "min_area_fraction", "expected_aspect", "min_quality"}
    unknown = options.keys() - supported
    if unknown:
        raise ValueError(f"Unknown classical option(s): {', '.join(sorted(unknown))}")

    max_dimension = int(options.get("max_dimension", 960))
    min_area_fraction = float(options.get("min_area_fraction", 0.015))
    min_quality = float(options.get("min_quality", 0.42))
    aspect_text = options.get("expected_aspect")
    expected_aspect = None if aspect_text is None else float(aspect_text)
    if not 320 <= max_dimension <= 4096:
        raise ValueError("max_dimension must be between 320 and 4096")
    if not 0 < min_area_fraction < 0.9:
        raise ValueError("min_area_fraction must be between 0 and 0.9")
    if not 0 <= min_quality <= 1:
        raise ValueError("min_quality must be between 0 and 1")
    if expected_aspect is not None and not 1 <= expected_aspect <= 6:
        raise ValueError("expected_aspect must be between 1 and 6")

    def detect(image: np.ndarray) -> dict:
        if image.ndim != 3 or image.shape[2] != 3 or image.dtype != np.uint8:
            raise ValueError("Classical backend expects a uint8 BGR image")

        height, width = image.shape[:2]
        if min(height, width) < 32:
            return _miss("image_too_small")

        scale = min(1.0, max_dimension / max(height, width))
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        if scale < 1.0:
            gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)

        resized_height, resized_width = gray.shape
        image_area = resized_height * resized_width
        minimum_area = min_area_fraction * image_area
        candidates = _quadrilaterals(gray, minimum_area)
        best = None
        evaluated = 0
        for area, shape_fit, quad in candidates:
            long_first, aspect = _long_first(quad)
            if not 1.08 <= aspect <= 5.7:
                continue
            ratio_fit = 1.0
            if expected_aspect is not None:
                ratio_error = abs(math.log(aspect / expected_aspect))
                if ratio_error > 0.70:
                    continue
                ratio_fit = 1.0 - ratio_error / 0.70

            evaluated += 1
            texture = _hole_pattern(gray, long_first, aspect)
            if texture is None:
                continue
            periodicity, coverage, hole_count = texture
            area_fit = min(1.0, area / (0.12 * image_area))
            quality = (
                0.55 * periodicity + 0.15 * coverage + 0.14 * shape_fit
                + 0.10 * area_fit + 0.06 * ratio_fit
            )
            if best is None or quality > best[0]:
                best = quality, quad, aspect, hole_count

        if best is None or best[0] < min_quality:
            return _miss("no_board_like_hole_pattern", evaluated)
        quality, quad, aspect, hole_count = best
        points = quad / np.array([resized_width / width, resized_height / height], dtype=np.float32)
        return {
            "corners_px": points.tolist(),
            "corner_order": "image",
            "quality": float(quality),
            "bbox_xyxy": [*points.min(axis=0).tolist(), *points.max(axis=0).tolist()],
            "diagnostics": {
                "candidate_count": evaluated,
                "estimated_aspect": float(aspect),
                "hole_like_blobs": hole_count,
            },
        }

    detect.info = {
        "algorithm": "convex contours with repeated isolated dark-pit evidence",
        "backend_output": "four image-space corners; physical orientation unresolved",
        "quality": "uncalibrated geometry-and-texture ranking score",
        "options": {
            "max_dimension": max_dimension,
            "min_area_fraction": min_area_fraction,
            "expected_aspect": expected_aspect,
            "min_quality": min_quality,
        },
    }
    return detect


def _miss(reason: str, candidate_count: int = 0) -> dict:
    return {
        "corners_px": None,
        "corner_order": "image",
        "diagnostics": {"reason": reason, "candidate_count": candidate_count},
    }


def _long_first(quad: np.ndarray) -> tuple[np.ndarray, float]:
    lengths = np.linalg.norm(np.roll(quad, -1, axis=0) - quad, axis=1)
    horizontal = float((lengths[0] + lengths[2]) / 2)
    vertical = float((lengths[1] + lengths[3]) / 2)
    if horizontal < vertical:
        return np.roll(quad, -1, axis=0), vertical / horizontal
    return quad, horizontal / vertical


def _quadrilaterals(gray: np.ndarray, minimum_area: float) -> list:
    height, width = gray.shape
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, otsu = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    edges = cv2.Canny(blurred, 38, 112)
    close_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    closed_edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, close_kernel)

    candidates = []
    for mask in (otsu, cv2.bitwise_not(otsu), closed_edges):
        contours, _ = cv2.findContours(mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        largest = sorted(contours, key=cv2.contourArea, reverse=True)[:40]
        for contour in largest:
            area = cv2.contourArea(contour)
            if not minimum_area <= area <= 0.93 * height * width:
                continue
            hull = cv2.convexHull(contour)
            perimeter = cv2.arcLength(hull, True)
            quad = None
            for tolerance in (0.012, 0.020, 0.031):
                approx = cv2.approxPolyDP(hull, tolerance * perimeter, True)
                if len(approx) == 4 and cv2.isContourConvex(approx):
                    quad = approx.reshape(4, 2).astype(np.float32)
                    break
            if quad is None:
                quad = cv2.boxPoints(cv2.minAreaRect(hull))
                if area < 0.85 * cv2.contourArea(quad):
                    continue

            if (
                quad[:, 0].min() < 2 or quad[:, 0].max() > width - 3
                or quad[:, 1].min() < 2 or quad[:, 1].max() > height - 3
            ):
                continue

            try:
                quad = order_corners(quad).astype(np.float32)
            except ValueError:
                continue
            lengths = np.linalg.norm(np.roll(quad, -1, axis=0) - quad, axis=1)
            if lengths.min() < 14 or max(lengths[0] / lengths[2], lengths[2] / lengths[0],
                                         lengths[1] / lengths[3], lengths[3] / lengths[1]) > 3.0:
                continue
            quad_area = cv2.contourArea(quad)
            if quad_area <= 0:
                continue
            fit = min(area, quad_area) / max(area, quad_area)
            if fit >= 0.66:
                candidates.append((quad_area, fit, quad))

    candidates.sort(key=lambda item: (item[1], item[0]), reverse=True)
    unique = []
    duplicate_distance = max(4.0, 0.007 * max(height, width))
    for candidate in candidates:
        if any(
            float(np.linalg.norm(candidate[2] - previous[2], axis=1).mean()) < duplicate_distance
            for previous in unique
        ):
            continue
        unique.append(candidate)
        if len(unique) == 24:
            break
    return unique


def _hole_pattern(gray: np.ndarray, quad: np.ndarray, aspect: float) -> tuple[float, float, int] | None:
    """Reject smooth rectangles and score recurrence of isolated dark punctures."""
    rect_height = 144
    rect_width = int(np.clip(round(rect_height * aspect), 150, 720))
    destination = np.array(
        [[0, 0], [rect_width - 1, 0], [rect_width - 1, rect_height - 1], [0, rect_height - 1]],
        dtype=np.float32,
    )
    transform = cv2.getPerspectiveTransform(quad, destination)
    rect = cv2.warpPerspective(gray, transform, (rect_width, rect_height))
    margin_x, margin_y = round(0.055 * rect_width), round(0.074 * rect_height)
    core = rect[margin_y:-margin_y, margin_x:-margin_x]
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    contrast = cv2.morphologyEx(core, cv2.MORPH_BLACKHAT, kernel)
    threshold = max(7, 0.55 * float(np.percentile(contrast, 93)))
    pits = (contrast >= threshold).astype(np.uint8)
    count, _, stats, centers = cv2.connectedComponentsWithStats(pits, connectivity=8)

    areas = stats[1:count, cv2.CC_STAT_AREA]
    widths = stats[1:count, cv2.CC_STAT_WIDTH]
    heights = stats[1:count, cv2.CC_STAT_HEIGHT]
    good = (
        (areas >= 2) & (areas <= 44) & (widths <= 10) & (heights <= 10)
        & (widths <= 3 * heights) & (heights <= 3 * widths)
    )
    centers = centers[1:count][good]
    if len(centers) < 36:
        return None

    spread_x, spread_y = np.percentile(centers, 90, axis=0) - np.percentile(centers, 10, axis=0)
    coverage = min(float(spread_x) / (0.70 * core.shape[1]), 1.0) * min(
        float(spread_y) / (0.56 * core.shape[0]), 1.0
    )
    if coverage < 0.38:
        return None

    center_x = np.rint(centers[:, 0]).astype(np.int32)
    center_y = np.rint(centers[:, 1]).astype(np.int32)
    x_profile = np.bincount(center_x, minlength=core.shape[1]).astype(np.float32)
    y_profile = np.bincount(center_y, minlength=core.shape[0]).astype(np.float32)
    x_repeat = _recurrence(x_profile, 3, 16)
    y_repeat = _recurrence(y_profile, 4, 12)
    if min(x_repeat, y_repeat) < 0.20:
        return None

    periodicity = math.sqrt(x_repeat * y_repeat)
    return periodicity, coverage, len(centers)


def _recurrence(profile: np.ndarray, minimum_lag: int, maximum_lag: int) -> float:
    smoothed = np.convolve(profile, [0.22, 0.56, 0.22], mode="same")
    smoothed -= smoothed.mean()
    best = 0.0
    for lag in range(minimum_lag, maximum_lag + 1):
        left, right = smoothed[:-lag], smoothed[lag:]
        norm = float(np.linalg.norm(left) * np.linalg.norm(right))
        if norm > 0:
            best = max(best, float(np.dot(left, right) / norm))
    return min(best, 1.0)
