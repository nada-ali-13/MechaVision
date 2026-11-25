"""DocAligner 1.1.1 four-corner heatmaps on local ONNX Runtime CPU.

Model and preprocessing reference: DocsaidLab/DocAligner, Apache-2.0.
The heatmap threshold, Otsu mask and centroid follow the upstream
docaligner/heatmap_reg/infer.py procedure.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import cv2
import numpy as np

from .docaligner_models import DOWNLOAD, LICENSE, MODELS, RELEASE
from .geometry import order_corners


class DocAlignerBackend:
    def __init__(self, session, color: str, info: dict):
        self.session = session
        self.color = color
        self.info = info

    def __call__(self, image: np.ndarray) -> dict:
        if image.dtype != np.uint8 or image.ndim != 3 or image.shape[2] != 3:
            raise ValueError("DocAligner expects a uint8 BGR image with three channels")
        height, width = image.shape[:2]
        resized = cv2.resize(image, (256, 256), interpolation=cv2.INTER_LINEAR)
        if self.color == "rgb":
            resized = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        tensor = np.transpose(resized, (2, 0, 1))[None].astype(np.float32) / 255.0
        (output,) = self.session.run(["heatmap"], {"img": tensor})
        if output.ndim != 4 or output.shape[:2] != (1, 4):
            raise RuntimeError(f"Unexpected DocAligner output shape {output.shape}")

        raw_corners = []
        heatmap_peaks = []
        for channel in output[0]:
            heat = cv2.resize(channel, (width, height), interpolation=cv2.INTER_LINEAR)
            heatmap_peaks.append(float(heat.max()))
            heat[heat < 0.3] = 0
            gray = np.uint8(heat * 255)
            _, mask = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            largest = max(contours, key=cv2.contourArea, default=None)
            moments = cv2.moments(largest) if largest is not None else {"m00": 0.0}
            area = moments["m00"]
            raw_corners.append(
                [moments["m10"] / area, moments["m01"] / area] if area > 0 else None
            )

        corners = None
        if all(point is not None for point in raw_corners):
            try:
                corners = order_corners(raw_corners).tolist()
            except ValueError:
                pass

        return {
            "corners_px": corners,
            "corner_order": "image",
            "raw_corners_px": raw_corners,
            "heatmap_peaks": heatmap_peaks,
        }


def create_backend(options: dict[str, str]) -> DocAlignerBackend:
    unknown = options.keys() - {"weights", "threads", "color"}
    if unknown:
        raise ValueError(f"Unknown DocAligner options: {', '.join(sorted(unknown))}")
    if not options.get("weights"):
        raise ValueError(f"DocAligner requires a local weights path from {RELEASE}")

    color = options.get("color", "bgr").lower()
    if color not in {"bgr", "rgb"}:
        raise ValueError("DocAligner color must be bgr or rgb")
    threads = int(options.get("threads", "1"))
    if threads < 1:
        raise ValueError("DocAligner threads must be positive")

    path = Path(options["weights"]).expanduser()
    with path.open("rb") as weights:
        sha256 = hashlib.file_digest(weights, "sha256").hexdigest()
        size = weights.tell()
    model = next((value for value in MODELS.values() if value.sha256 == sha256 and value.size == size), None)
    if model is None:
        raise ValueError(f"Unrecognized DocAligner checkpoint SHA-256 {sha256}. Use an official 1.1.1 heatmap model.")

    import onnxruntime as ort

    ort.disable_telemetry_events()
    config = ort.SessionOptions()
    config.intra_op_num_threads = threads
    config.inter_op_num_threads = 1
    session = ort.InferenceSession(str(path), sess_options=config, providers=["CPUExecutionProvider"])
    return DocAlignerBackend(session, color, {
        "model": model.filename,
        "version": "1.1.1",
        "sha256": sha256,
        "weights_bytes": size,
        "source_url": DOWNLOAD + model.filename,
        "release_url": RELEASE,
        "code_license": "Apache-2.0",
        "license_url": LICENSE,
        "weight_license": "Official project release. No separate weight license listed.",
        "task": "four-corner heatmaps for documents",
        "runtime": "ONNX Runtime " + ort.__version__,
        "provider": "CPUExecutionProvider",
        "intra_op_threads": threads,
        "input_color": color,
        "peak_semantics": "Uncalibrated heatmap activations.",
    })
