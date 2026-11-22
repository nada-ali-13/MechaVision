"""MechaVision's offline, reproducible image benchmark."""

import argparse
from importlib import import_module
import json
from pathlib import Path
import platform
import sys
from time import perf_counter_ns

import cv2
import numpy as np

from .geometry import rectification, validate_quad
from .manifest import direct_frames, manifest_frames
from .metrics import score, summary

BACKENDS = {
    "classical": "classical_backend",
    "docaligner": "docaligner_backend",
    "breadboard": "breadboard_backend",
}


def parse_options(options):
    parsed = {}
    for option in options:
        key, sep, value = option.partition("=")
        if not sep or not key or not value or key in parsed:
            raise ValueError(f"use a unique KEY=VALUE backend option: {option!r}")
        parsed[key] = value
    return parsed


def platform_info():
    machine = platform.processor() or platform.machine()
    cpuinfo = Path("/proc/cpuinfo")
    if cpuinfo.is_file():
        for line in cpuinfo.read_text(encoding="utf-8").splitlines():
            if line.startswith("model name"):
                machine = line.partition(":")[-1].strip()
                break
    return {
        "python": platform.python_version(), "opencv": cv2.__version__,
        "numpy": np.__version__, "os": platform.platform(), "cpu": machine,
        "opencv_threads": cv2.getNumThreads(),
    }


def build_backend(args):
    module = import_module(f".{BACKENDS[args.backend]}", __package__)
    start = perf_counter_ns()
    backend = module.create_backend(parse_options(args.option))
    elapsed = (perf_counter_ns() - start) / 1e6
    info = {"name": args.backend, **getattr(backend, "info", {}), "load_ms": elapsed}
    return backend, info


def frames_for(args):
    if args.manifest is not None and args.image:
        raise ValueError("supply either --manifest or --image")
    frames = list(manifest_frames(args.manifest, args.image_root) if args.manifest else direct_frames(args.image))
    if not frames:
        raise ValueError("no input images")
    return frames


def invoke(backend, image, max_input_edge):
    height, width = image.shape[:2]
    if not max_input_edge or max(height, width) <= max_input_edge:
        return backend(image)
    scale = max_input_edge / max(height, width)
    reduced = cv2.resize(image, (max(2, round(width * scale)), max(2, round(height * scale))),
                         interpolation=cv2.INTER_AREA)
    result = dict(backend(reduced))
    sx, sy = width / reduced.shape[1], height / reduced.shape[0]
    for key in ("corners_px", "raw_corners_px", "rejected_corners_px"):
        if result.get(key) is not None:
            result[key] = [None if point is None else [point[0] * sx, point[1] * sy] for point in result[key]]
    if result.get("bbox_xyxy") is not None:
        result["bbox_xyxy"] = [value * ratio for value, ratio in zip(result["bbox_xyxy"], (sx, sy, sx, sy))]
    if result.get("photo_to_upstream_canonical") is not None:
        mapping = np.asarray(result["photo_to_upstream_canonical"], dtype=np.float64)
        result["photo_to_upstream_canonical"] = (mapping @ np.diag([1 / sx, 1 / sy, 1])).tolist()
    return result


def clean_prediction(value, size):
    result = dict(value)
    corner_order = result.get("corner_order", "image")
    if corner_order not in {"image", "physical"}:
        raise ValueError(f"invalid predicted order {corner_order!r}")
    result["corner_order"] = corner_order
    quad = result.get("corners_px")
    result["corners_px"] = (
        None if quad is None else validate_quad(quad, size).tolist()
    )
    if result.get("bbox_xyxy") is not None:
        box = np.asarray(result["bbox_xyxy"], dtype=np.float64)
        if box.shape != (4,) or not np.isfinite(box).all() or np.any(box[2:] <= box[:2]):
            raise ValueError("invalid predicted bounding box")
        result["bbox_xyxy"] = box.tolist()
    return result


def write_jpeg(path, image):
    success, encoded = cv2.imencode(".jpg", image)
    if not success:
        raise OSError(f"could not encode {path.name}")
    path.write_bytes(encoded.tobytes())


def write_visuals(out, frame, image, row, args):
    canvas = image.copy()
    layers = (
        (frame.record.get("corners_px"), (65, 190, 255), "ref"),
        (row.get("corners_px"), (65, 245, 125), "pred"),
        (row.get("rejected_corners_px"), (65, 80, 255), "reject"),
    )
    for quad, color, label in layers:
        if quad is None:
            continue
        pixels = np.rint(quad).astype(np.int32)
        cv2.polylines(canvas, [pixels], True, color, 2, cv2.LINE_AA)
        for index, (x, y) in enumerate(pixels, 1):
            cv2.circle(canvas, (x, y), 5, color, -1, cv2.LINE_AA)
            origin = (max(2, min(x + 6, canvas.shape[1] - 65)), max(15, y - 8 if label == "pred" else y + 18))
            marker = f"{label}{index}"
            cv2.putText(canvas, marker, origin, cv2.FONT_HERSHEY_SIMPLEX, .55, (0, 0, 0), 3, cv2.LINE_AA)
            cv2.putText(canvas, marker, origin, cv2.FONT_HERSHEY_SIMPLEX, .55, color, 1, cv2.LINE_AA)
    if row.get("bbox_xyxy") is not None and row.get("corners_px") is None:
        x1, y1, x2, y2 = (round(value) for value in row["bbox_xyxy"])
        cv2.rectangle(canvas, (x1, y1), (x2, y2), (65, 245, 125), 2)
    status = row["outcome"].replace("_", " ")
    if row["outcome"] == "unannotated":
        status = "accepted quad" if row.get("corners_px") is not None else "no accepted quad"
    banner = f"{args.backend}: {status}"
    cv2.putText(canvas, banner, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, .6, (0, 0, 0), 4, cv2.LINE_AA)
    cv2.putText(canvas, banner, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, .6, (255, 255, 255), 1, cv2.LINE_AA)
    overlay_name = f"{frame.id}-annotated.jpg"
    write_jpeg(out / overlay_name, canvas)
    row["annotated_output"] = overlay_name
    if row.get("corners_px") is not None:
        quad = np.array(row["corners_px"], dtype=np.float64)
        warp, _, shape = rectification(quad, args.board_mm, args.long_edge_px, row["corner_order"])
        rectified = cv2.warpPerspective(image, warp, shape)
        rectified_name = f"{frame.id}-rectified.jpg"
        write_jpeg(out / rectified_name, rectified)
        row["rectified_output"] = rectified_name
        row["image_to_rectified"] = warp.tolist()
        row["rectification_axis"] = "physical order" if row["corner_order"] == "physical" else "inferred from projected edges"


def inspect(args):
    report = {"machine": platform_info(), "backends": sorted(BACKENDS), "images": []}
    if args.backend:
        _, report["backend"] = build_backend(args)
    if args.manifest or args.image:
        for frame in frames_for(args):
            image, digest = frame.read()
            height, width = image.shape[:2]
            report["images"].append({
                "id": frame.id, "width_px": width, "height_px": height,
                "sha256": digest, "session_id": frame.record.get("session_id"),
                "source": frame.record.get("source"),
            })
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


def benchmark(args):
    frames = frames_for(args)
    if args.command == "evaluate" and not all(frame.annotated for frame in frames):
        raise ValueError("evaluate requires a manifest with one annotation or explicit negative per image")
    backend, info = build_backend(args)
    out = args.output
    out.mkdir(parents=True, exist_ok=True)
    if (out / "results.json").exists():
        raise ValueError(f"results already exist in {out}; choose a new output directory")
    if args.warmup:
        warm_image, _ = frames[0].read()
        for _ in range(args.warmup):
            invoke(backend, warm_image, args.max_input_edge)

    rows = []
    for frame in frames:
        image, digest = frame.read()
        height, width = image.shape[:2]
        truth = "unannotated" if not frame.annotated else (
            "no_board" if frame.record["corners_px"] is None else "board"
        )
        row = {
            "id": frame.id, "sha256": digest, "image_size_px": [width, height], "truth": truth,
            "session_id": frame.record.get("session_id"), "board_id": frame.record.get("board_id"),
            "inference_ms": [],
        }
        try:
            for _ in range(args.repeats):
                start = perf_counter_ns()
                raw = invoke(backend, image, args.max_input_edge)
                row["inference_ms"].append((perf_counter_ns() - start) / 1e6)
            prediction = clean_prediction(raw, (width, height))
            row.update(prediction)
            row.update(score(frame, prediction, (width, height), args.board_mm,
                             args.corner_threshold_fraction, args.long_edge_px))
        except (RuntimeError, ValueError, cv2.error) as error:
            row.update(outcome="inference_error", error=str(error), corners_px=None)
        write_visuals(out, frame, image, row, args)
        rows.append(row)

    groups = sorted({row["session_id"] for row in rows if row["session_id"] is not None})
    report = {
        "schema_version": 1, "machine": platform_info(), "backend": info,
        "settings": {
            "repeats": args.repeats, "warmup_frames": args.warmup, "board_mm": args.board_mm,
            "max_input_edge_px": args.max_input_edge or None,
            "long_edge_px": args.long_edge_px, "corner_threshold_fraction_of_image_diagonal": args.corner_threshold_fraction,
            "timed_scope": "backend return, including its pre/post-processing; excludes image decode and visualization",
        },
        "summary": summary(rows),
        "sessions": {group: summary(row for row in rows if row["session_id"] == group) for group in groups},
        "images": rows,
    }
    (out / "results.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"], ensure_ascii=False))
    print(f"Results: {out / 'results.json'}")
    return int(report["summary"]["inference_errors"] > 0)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("inspect", "predict", "evaluate"):
        sub = subparsers.add_parser(name)
        sub.add_argument("--backend", choices=BACKENDS, required=name != "inspect")
        sub.add_argument("--option", action="append", default=[], metavar="KEY=VALUE")
        sub.add_argument("--manifest", type=Path)
        sub.add_argument("--image-root", type=Path)
        sub.add_argument("--image", type=Path, action="append", default=[])
        sub.add_argument("--opencv-threads", type=int, default=1)
        if name != "inspect":
            sub.add_argument("--output", type=Path, required=True)
            sub.add_argument("--warmup", type=int, default=2)
            sub.add_argument("--repeats", type=int, default=3)
            sub.add_argument("--board-mm", type=float, nargs=2, default=[165.0, 55.0],
                             metavar=("WIDTH", "HEIGHT"))
            sub.add_argument("--long-edge-px", type=int, default=825)
            sub.add_argument("--max-input-edge", type=int, default=0,
                             help="cap model input edge length in pixels; 0 keeps source resolution")
            sub.add_argument("--corner-threshold-fraction", type=float, default=.02)

    args = parser.parse_args(argv)
    if args.opencv_threads < 1:
        parser.error("--opencv-threads must be positive")
    if args.command != "inspect":
        if (args.repeats < 1 or args.warmup < 0 or args.long_edge_px < 2
                or 0 < args.max_input_edge < 2 or args.max_input_edge < 0
                or not all(np.isfinite(value) and value > 0 for value in args.board_mm)
                or not 0 < args.corner_threshold_fraction < 1):
            parser.error("invalid evaluation repeat count, board dimensions, output size or corner threshold")
    cv2.setNumThreads(args.opencv_threads)
    try:
        return inspect(args) if args.command == "inspect" else benchmark(args)
    except (OSError, ImportError, KeyError, RuntimeError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
