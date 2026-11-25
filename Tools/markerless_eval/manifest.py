"""Read annotation manifests and check the exact provenance of available images."""

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import re

import cv2
import numpy as np

from .geometry import points, validate_quad


@dataclass
class Frame:
    id: str
    path: Path
    record: dict
    annotated: bool

    def read(self):
        blob = self.path.read_bytes()
        digest = sha256(blob).hexdigest()
        expected = self.record.get("source", {}).get("sha256")
        if expected and digest != expected.lower():
            raise ValueError(f"{self.id}: image SHA-256 mismatch")
        # Decode the bytes already hashed, including when a Windows path uses Arabic characters.
        image = cv2.imdecode(np.frombuffer(blob, dtype=np.uint8), cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError(f"{self.id}: cannot decode image {self.path}")
        height, width = image.shape[:2]
        if (self.record.get("width_px", width), self.record.get("height_px", height)) != (width, height):
            raise ValueError(f"{self.id}: image dimensions differ from the annotation")
        if self.record.get("corners_px") is not None:
            validate_quad(self.record["corners_px"], (width, height))
        landmarks = self.record.get("landmarks", [])
        if landmarks:
            px = points([item["pixel_px"] for item in landmarks], len(landmarks))
            if (px < 0).any() or (px >= [width, height]).any():
                raise ValueError(f"{self.id}: landmark lies outside the image")
            points([item["board_mm"] for item in landmarks], len(landmarks))
        return image, digest


def manifest_frames(path, image_root=None):
    source = Path(path)
    data = json.loads(source.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1 or not isinstance(data.get("images"), list):
        raise ValueError("expected schema_version 1 and an images array")
    root = Path(image_root) if image_root is not None else source.parent
    seen = set()
    for item in data["images"]:
        frame_id = item["id"]
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", frame_id) or frame_id in seen:
            raise ValueError(f"invalid or duplicate image ID {frame_id!r}")
        seen.add(frame_id)
        if item.get("corner_order", "image") not in {"image", "physical"}:
            raise ValueError(f"{frame_id}: unsupported corner_order")
        yield Frame(frame_id, root / item["path"], item, "corners_px" in item)


def direct_frames(paths):
    for index, path in enumerate(paths, 1):
        yield Frame(f"image-{index:03d}", Path(path), {}, False)
