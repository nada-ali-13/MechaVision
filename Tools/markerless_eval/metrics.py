"""Score geometry, corner correspondence and time without inferring physical pose."""

import cv2
import numpy as np

from .geometry import align_corners, order_corners, project, rectification, validate_quad


def distribution(values):
    values = list(values)
    if not values:
        return {"n": 0, "mean": None, "median": None, "p95": None, "max": None}
    return {
        "n": len(values), "mean": float(np.mean(values)), "median": float(np.median(values)),
        "p95": float(np.percentile(values, 95)), "max": float(np.max(values)),
    }


def score(frame, prediction, size, board_mm, threshold_fraction, long_edge_px):
    if not frame.annotated:
        return {"outcome": "unannotated"}
    record = frame.record
    reference = record["corners_px"]
    candidate = prediction.get("corners_px")
    if reference is None:
        detected = candidate is not None or prediction.get("bbox_xyxy") is not None or prediction.get("mask") is not None
        return {"outcome": "false_positive" if detected else "true_negative"}
    if candidate is None:
        return {"outcome": "no_corners"}

    reference = validate_quad(reference, size)
    candidate = validate_quad(candidate, size)
    ref_order = record.get("corner_order", "image")
    model_order = prediction.get("corner_order", "image")
    _, mirrored, shift, aligned, errors = align_corners(candidate, reference)
    direct = np.linalg.norm(candidate - reference, axis=1)
    threshold = threshold_fraction * float(np.linalg.norm(size))
    good = bool(np.max(errors) <= threshold)
    if ref_order == model_order:
        ordered_errors = direct
    elif ref_order == "image":
        ordered_errors = np.linalg.norm(order_corners(candidate) - reference, axis=1)
    else:
        ordered_errors = None

    warp, canonical, _ = rectification(aligned, board_mm, long_edge_px, ref_order)
    warp_errors = np.linalg.norm(project(warp, reference) - canonical, axis=1)
    result = {
        "outcome": "corner_pass" if good else "corner_error",
        "threshold_px": threshold,
        "aligned_corner_errors_px": errors.tolist(),
        "raw_index_corner_errors_px": direct.tolist(),
        "assessed_order_errors_px": None if ordered_errors is None else ordered_errors.tolist(),
        "order_correct_within_threshold": None if ordered_errors is None else bool(np.max(ordered_errors) <= threshold),
        "reference_corner_projection_errors_rectified_px": warp_errors.tolist(),
        "best_cyclic_shift": shift,
        "best_winding_reversed": mirrored,
        "physical_order_verified": None,
        "landmark_errors_mm": [],
    }
    if ref_order == model_order == "physical":
        result["physical_order_verified"] = bool(good and not mirrored and shift == 0)
        landmarks = record.get("landmarks")
        if landmarks and not mirrored and shift == 0:
            width, height = board_mm
            destination_mm = np.array([[0, 0], [width, 0], [width, height], [0, height]])
            warp_mm = cv2.getPerspectiveTransform(np.float32(candidate), np.float32(destination_mm))
            observed = project(warp_mm, [item["pixel_px"] for item in landmarks])
            expected = np.array([item["board_mm"] for item in landmarks]) + [width / 2, height / 2]
            result["landmark_errors_mm"] = [
                {"id": item["id"], "error_mm": float(error)}
                for item, error in zip(landmarks, np.linalg.norm(observed - expected, axis=1))
            ]
    return result

def summary(rows):
    rows = list(rows)
    positives = [r for r in rows if r["truth"] == "board"]
    negatives = [r for r in rows if r["truth"] == "no_board"]
    comparable = [r for r in positives if r.get("order_correct_within_threshold") is not None]
    physical = [r for r in positives if r.get("physical_order_verified") is not None]
    corner_passes = sum(r["outcome"] == "corner_pass" for r in positives)
    return {
        "images": len(rows),
        "positive_images": len(positives),
        "negative_images": len(negatives),
        "positive_corner_passes": corner_passes,
        "positive_failures": len(positives) - corner_passes,
        "positive_without_corners": sum(r.get("corners_px") is None for r in positives),
        "negative_false_positives": sum(r["outcome"] == "false_positive" for r in negatives),
        "inference_errors": sum(r["outcome"] == "inference_error" for r in rows),
        "order_comparable_images": len(comparable),
        "order_passes": sum(r["order_correct_within_threshold"] for r in comparable),
        "physical_order_comparable_images": len(physical),
        "physical_order_passes": sum(r["physical_order_verified"] for r in physical),
        "aligned_corner_error_px": distribution(
            error for row in positives for error in row.get("aligned_corner_errors_px", [])
        ),
        "ordered_corner_error_px": distribution(
            error for row in comparable for error in row["assessed_order_errors_px"]
        ),
        "rectified_reference_corner_error_px": distribution(
            error for row in positives for error in row.get("reference_corner_projection_errors_rectified_px", [])
        ),
        "independent_hole_error_mm": distribution(
            item["error_mm"] for row in positives for item in row.get("landmark_errors_mm", [])
        ),
        "inference_ms": distribution(ms for row in rows for ms in row["inference_ms"]),
    }
