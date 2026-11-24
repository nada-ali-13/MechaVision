"""Run the frozen V2 comparisons on a separate, physically labelled session."""

import argparse
from collections import Counter
import json
from pathlib import Path
import subprocess

import cv2
import numpy as np

from . import cli
from .geometry import align_corners, project, validate_quad
from .manifest import manifest_frames
from .metrics import distribution

REPO = Path(__file__).resolve().parents[2]
VENDOR_REVISION = "758d5a37913c4b929926721380223c537491cbbe"
VARIANTS = {
    "original": ["--backend", "breadboard", "--option", "require_grid=true", "--max-input-edge", "960"],
    "830-full": ["--backend", "region", "--option", "grid=830", "--option", "proposals=none"],
    "830-fallback": ["--backend", "region", "--option", "grid=830", "--option", "proposals=multiscale"],
}


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def outside_checkout(path):
    if Path(path).resolve().is_relative_to(REPO):
        raise ValueError("Keep held-out photographs, manifests and outputs outside this checkout.")


def measurements(path):
    if path is None:
        return None
    record = read_json(path)
    dimensions = tuple(float(record[key]) for key in ("width_mm", "height_mm"))
    if (not all(np.isfinite(value) and value > 0 for value in dimensions)
            or not isinstance(record.get("measurement_notes"), str)
            or not record["measurement_notes"].strip()
            or not isinstance(record.get("board_id"), str) or not record["board_id"].strip()):
        raise ValueError("Measured width, height and measurement notes are required.")
    return record["board_id"], dimensions


def preflight(manifest, image_root, session, development_inventory, measured):
    previous = read_json(development_inventory)["images"]
    development_hashes = {row["sha256"] for row in previous}
    if not development_hashes or any(row.get("session_id") == session for row in previous):
        raise ValueError("Supply a separate session and a populated development hash inventory.")
    labels = {}
    seen = set()
    landmark_coordinates = {}
    for frame in manifest_frames(manifest, image_root):
        outside_checkout(frame.path)
        if not frame.annotated or frame.record.get("session_id") != session:
            raise ValueError(f"{frame.id}: expected an explicit label from the declared held-out session")
        image, digest = frame.read()
        if digest in development_hashes or digest in seen:
            raise ValueError(f"{frame.id}: duplicate or exact development-image match")
        seen.add(digest)
        record = frame.record
        if record["corners_px"] is not None:
            corners = validate_quad(record["corners_px"])
            direction = corners[1] - corners[0]
            turn = corners[2] - corners[1]
            if record.get("corner_order") != "physical" or direction[0]*turn[1] <= direction[1]*turn[0]:
                raise ValueError(f"{frame.id}: mark the front face clockwise A1, A63, J63, J1")
            if measured and record.get("board_id") != measured[0]:
                raise ValueError(f"{frame.id}: board ID differs from measured profile")
            if measured:
                width, height = measured[1]
                for landmark in record.get("landmarks", []):
                    x, z = landmark["board_mm"]
                    if abs(x) >= width/2 or abs(z) >= height/2:
                        raise ValueError(f"{frame.id}: measured hole is outside the board face")
                    key = landmark["id"]
                    position = tuple(landmark["board_mm"])
                    if landmark_coordinates.setdefault(key, position) != position:
                        raise ValueError(f"{frame.id}: inconsistent measured location for {key}")
        labels[frame.id] = record
    if {label["corners_px"] is None for label in labels.values()} != {True, False}:
        raise ValueError("The held-out session needs both board and no-board frames.")
    return labels


def metric_errors(candidate, reference, landmarks, dimensions):
    width, height = dimensions
    plane = np.float32([[-width/2, -height/2], [width/2, -height/2],
                        [width/2, height/2], [-width/2, height/2]])
    reference_warp = cv2.getPerspectiveTransform(np.float32(reference), plane)
    prediction_warp = cv2.getPerspectiveTransform(np.float32(candidate), plane)
    corner_mm = np.linalg.norm(project(reference_warp, candidate) - plane, axis=1).tolist()
    holes = []
    if landmarks:
        pixels = [item["pixel_px"] for item in landmarks]
        expected = np.array([item["board_mm"] for item in landmarks])
        holes = [
            {"id": item["id"], "error_mm": float(error)}
            for item, error in zip(landmarks, np.linalg.norm(project(prediction_warp, pixels) - expected, axis=1))
        ]
    return corner_mm, holes


def summarize(results, labels, measured):
    stages = Counter()
    rows = []
    for result in results["images"]:
        label = labels[result["id"]]
        reference = label["corners_px"]
        corners = result.get("corners_px")
        if result["outcome"] == "inference_error":
            stage = "inference_error"
        elif corners is not None:
            stage = "accepted"
        elif result.get("rejected_corners_px") is not None:
            stage = "edge_rejected" if result.get("clipped_candidate") else "grid_rejected"
        else:
            stage = "corner_failure"
        truth = "board" if reference is not None else "no_board"
        stages[truth + "_" + stage] += 1
        row = {"id": result["id"], "truth": truth, "stage": stage, "quality_outcome": result["outcome"],
               "physical_order": "not_emitted", "reason": result.get("reason")}
        if reference is not None and corners is not None:
            _, reversed_order, shift, aligned, errors = align_corners(np.array(corners), np.array(reference))
            row.update(aligned_corner_errors_px=errors.tolist(), reference_reindex_shift=shift,
                       reference_reindex_reversed=reversed_order)
            if result["outcome"] == "corner_pass":
                row["raw_order_agrees_with_reference"] = not reversed_order and shift == 0
            if result["corner_order"] == "physical":
                row["physical_order"] = "matches" if not reversed_order and shift == 0 else "mismatch"
            if measured:
                # Diagnostic only. Physical correspondence is supplied by reference labels after inference.
                corner_mm, holes = metric_errors(aligned, reference, label.get("landmarks", []), measured[1])
                row.update(reference_aligned_corner_mm=corner_mm, reference_aligned_hole_errors_mm=holes)
        rows.append(row)
    overall = results["summary"]
    order_comparison = [row["raw_order_agrees_with_reference"] for row in rows
                        if "raw_order_agrees_with_reference" in row]
    return {
        "stages": dict(stages), "detector_metrics": results["summary"],
        "board_acceptance_rate": stages["board_accepted"] / overall["positive_images"],
        "board_corner_pass_rate": overall["positive_corner_passes"] / overall["positive_images"],
        "false_positive_rate": stages["no_board_accepted"] / overall["negative_images"],
        "raw_order_agreement_on_corner_passes": {"matched": sum(order_comparison), "compared": len(order_comparison)},
        "physical_order_counts_on_accepted_positives": dict(Counter(
            row["physical_order"] for row in rows if row["truth"] == "board" and row["stage"] == "accepted"
        )),
        "reference_aligned_corner_mm": distribution(v for row in rows for v in row.get("reference_aligned_corner_mm", [])),
        "reference_aligned_independent_hole_mm": distribution(
            hole["error_mm"] for row in rows for hole in row.get("reference_aligned_hole_errors_mm", [])
        ),
        "images": rows,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("manifest", "image-root", "development-inventory", "weights", "checkout", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--session", required=True, help="ID of a newly captured, previously unused session")
    parser.add_argument("--measurements", type=Path)
    args = parser.parse_args()
    try:
        for path in (args.manifest, args.image_root, args.development_inventory, args.output, args.measurements):
            if path is not None:
                outside_checkout(path)
        measured = measurements(args.measurements)
        labels = preflight(args.manifest, args.image_root, args.session, args.development_inventory, measured)
        git = ["git", "-C", str(args.checkout)]
        revision = subprocess.check_output(git + ["rev-parse", "HEAD"], text=True).strip()
        changes = subprocess.check_output(git + ["status", "--porcelain", "--untracked-files=no"], text=True)
        if revision != VENDOR_REVISION or changes.strip():
            raise ValueError("Use the clean, pinned Breadboard-Classifier checkout.")
        args.output.mkdir(parents=True, exist_ok=False)
        common = ["evaluate", "--manifest", str(args.manifest), "--image-root", str(args.image_root),
                  "--option", f"weights={args.weights}", "--option", f"checkout={args.checkout}"]
        if measured:
            common += ["--board-mm", *(str(value) for value in measured[1])]
        results = {"session": args.session, "measured_board_mm": None if measured is None else measured[1],
                   "metric_alignment": "Reference-ordered diagnostic only; not autonomous physical pose",
                   "variants": {}}
        has_errors = False
        for name, options in VARIANTS.items():
            output = args.output / name
            code = cli.main(common + options + ["--output", str(output)])
            if code not in (0, 1) or not (output / "results.json").exists():
                raise RuntimeError(f"The {name} configuration did not produce results.")
            has_errors |= code != 0
            results["variants"][name] = summarize(read_json(output / "results.json"), labels, measured)
        (args.output / "comparison.json").write_text(json.dumps(results, indent=2, allow_nan=False) + "\n",
                                                    encoding="utf-8")
        return int(has_errors)
    except (OSError, TypeError, ValueError, KeyError, RuntimeError, subprocess.CalledProcessError) as error:
        parser.exit(2, f"error: {error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
