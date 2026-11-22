#!/usr/bin/env python3
"""Label board corners in a local browser, then save a markerless evaluation manifest."""

import argparse
import json
import math
import mimetypes
import os
import re
import secrets
import tempfile
import webbrowser
from hashlib import sha256
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

TOOL_DIRECTORY = Path(__file__).resolve().parent
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_REQUEST_BYTES = 64 * 1024
FRAME_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*")


def coordinate(value, label):
    if not isinstance(value, list) or len(value) != 2:
        raise ValueError(f"{label}: expected [x, y].")
    try:
        if all(type(component) in (int, float) and math.isfinite(component) for component in value):
            return value
    except OverflowError:
        pass
    raise ValueError(f"{label}: coordinates must be finite numbers.")


def pixel(value, label, width, height):
    point = coordinate(value, label)
    if not 0 <= point[0] < width or not 0 <= point[1] < height:
        raise ValueError(f"{label}: pixel is outside the image.")
    return point


def ordered_corners(points):
    """Accept either winding, but require four distinct sequential corners."""
    for index in range(4):
        a, b, c = (points[(index + offset) % 4] for offset in range(3))
        yield (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])


def validate_annotation(payload):
    if not isinstance(payload, dict):
        raise ValueError("Expected an annotation object.")
    width, height = payload.get("width_px"), payload.get("height_px")
    if any(type(dimension) != int or dimension < 2 for dimension in (width, height)):
        raise ValueError("Image dimensions must be integers of at least 2 pixels.")

    order = payload.get("corner_order")
    if order not in ("physical", "image"):
        raise ValueError("Select physical or image corner order.")
    corners = payload.get("corners_px")
    landmarks = payload.get("landmarks", [])
    if not isinstance(landmarks, list):
        raise ValueError("Landmarks must be a list.")

    if payload.get("no_board") is True:
        if corners is not None or landmarks:
            raise ValueError("A no-board frame cannot contain corners or landmarks.")
    else:
        if not isinstance(corners, list) or len(corners) != 4:
            raise ValueError("Mark all four corners, or explicitly mark the frame as no-board.")
        corners = [pixel(point, f"Corner {index + 1}", width, height) for index, point in enumerate(corners)]
        turns = list(ordered_corners(corners))
        if not (all(turn > 1e-6 for turn in turns) or all(turn < -1e-6 for turn in turns)):
            raise ValueError("Corners must be distinct and form an ordered convex quadrilateral.")
        twice_area = sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(corners, corners[1:] + corners[:1]))
        if abs(twice_area) < 8:
            raise ValueError("The board area must be at least four square pixels.")

    saved_landmarks = []
    landmark_ids, landmark_pixels, board_positions = set(), set(), set()
    for item in landmarks:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str):
            raise ValueError("Give each landmark an ID.")
        landmark_id = item["id"].strip()
        point = pixel(item.get("pixel_px"), f"Landmark {landmark_id}", width, height)
        board = coordinate(item.get("board_mm"), f"Board location for landmark {landmark_id}")
        if not landmark_id or len(landmark_id) > 80:
            raise ValueError("Landmark IDs must be 1–80 characters.")
        if landmark_id in landmark_ids or tuple(point) in landmark_pixels or tuple(board) in board_positions:
            raise ValueError(f"Duplicate landmark ID or coordinates: {landmark_id}.")
        landmark_ids.add(landmark_id)
        landmark_pixels.add(tuple(point))
        board_positions.add(tuple(board))
        saved_landmarks.append({"id": landmark_id, "pixel_px": point, "board_mm": board})

    return {"width_px": width, "height_px": height, "corner_order": order,
            "corners_px": corners, "landmarks": saved_landmarks}


def normalized_manifest_path(path):
    # JSON paths use portable '/' even when the server is running on Windows.
    return os.path.normcase(os.path.normpath(path.replace("\\", "/")))


class AnnotationSession:
    def __init__(self, images, output, image_root, session_id, board_id, default_order):
        if not images.is_dir():
            raise ValueError(f"Image directory does not exist: {images}")
        self.output = output
        self.session_id = session_id
        self.board_id = board_id
        self.default_order = default_order
        self.manifest = {"schema_version": 1, "images": []}
        if output.is_file():
            self.manifest = json.loads(output.read_text(encoding="utf-8"))
        if (not isinstance(self.manifest, dict) or self.manifest.get("schema_version") != 1
                or not isinstance(self.manifest.get("images"), list)):
            raise ValueError("Expected a schema_version 1 markerless manifest.")
        self.entries = {}
        ids = set()
        for entry in self.manifest["images"]:
            if (not isinstance(entry, dict) or not isinstance(entry.get("id"), str)
                    or not FRAME_ID.fullmatch(entry["id"]) or not isinstance(entry.get("path"), str)
                    or not entry["path"]):
                raise ValueError("Every existing entry must have a portable frame ID and image path.")
            key = normalized_manifest_path(entry["path"])
            if key in self.entries or entry["id"] in ids:
                raise ValueError(f"Duplicate existing image or ID: {entry['path']}")
            self.entries[key] = entry
            ids.add(entry["id"])

        self.images = []
        seen = set()
        for file in sorted(images.rglob("*")):
            if not file.is_file() or file.suffix.lower() not in IMAGE_EXTENSIONS:
                continue
            resolved = file.resolve()
            if not resolved.is_relative_to(image_root):
                raise ValueError(f"Image is outside {image_root}: {file}. Move it or set --image-root.")
            path = resolved.relative_to(image_root).as_posix()
            key = normalized_manifest_path(path)
            if key in seen:
                raise ValueError(f"Duplicate image path: {path}")
            seen.add(key)
            existing = self.entries.get(key)
            if existing and (existing.get("session_id") != session_id or existing.get("board_id") != board_id):
                raise ValueError(f"Image already belongs to a different session or board: {path}")
            identity = sha256(f"{session_id}\0{path}".encode("utf-8")).hexdigest()[:20]
            image_id = existing["id"] if existing else f"frame-{identity}"
            if not existing and image_id in ids:
                raise ValueError(f"Duplicate image ID: {image_id}")
            ids.add(image_id)
            self.images.append((resolved, path, image_id))
        if not self.images:
            raise ValueError("No JPEG, PNG or WebP images were found.")

    def describe(self):
        return {
            "session_id": self.session_id,
            "board_id": self.board_id,
            "default_order": self.default_order,
            "images": [{"path": path, "annotation": self.entries.get(normalized_manifest_path(path))}
                       for _, path, _ in self.images],
        }

    def save(self, index, payload):
        file, path, image_id = self.images[index]
        key = normalized_manifest_path(path)
        entries = dict(self.entries)
        if payload == {"remove": True}:
            entries.pop(key, None)
            record = None
        else:
            annotations = validate_annotation(payload)
            digest = sha256(file.read_bytes()).hexdigest()
            if payload.get("image_sha256") != digest:
                raise ValueError("The image has changed. Reload it before saving.")
            prior = entries.get(key, {})
            record = {
                **prior,
                **annotations,
                "source": {**prior.get("source", {}), "sha256": digest},
                "id": image_id,
                "path": path,
                "session_id": self.session_id,
                "board_id": self.board_id,
            }
            entries[key] = record
        manifest = {**self.manifest, "images": list(entries.values())}

        self.output.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=self.output.parent,
                                         suffix=".tmp", delete=False) as temporary:
            temporary_path = Path(temporary.name)
            try:
                json.dump(manifest, temporary, ensure_ascii=False, indent=2, allow_nan=False)
                temporary.write("\n")
                temporary.close()
                temporary_path.replace(self.output)
            finally:
                temporary.close()
                temporary_path.unlink(missing_ok=True)
        self.manifest = manifest
        self.entries = entries
        return record


def make_handler(session, secret):
    prefix = f"/{secret}/"

    class AnnotationHandler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def send_bytes(self, code, body, content_type, image_digest=None):
            self.send_response(code)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'self'; img-src 'self' blob:; style-src 'self' 'unsafe-inline'")
            if image_digest is not None:
                self.send_header("X-Image-SHA256", image_digest)
            self.end_headers()
            self.wfile.write(body)

        def send_json(self, code, value):
            self.send_bytes(code, json.dumps(value, ensure_ascii=False).encode("utf-8"),
                            "application/json; charset=utf-8")

        def resource(self):
            return self.path[len(prefix):] if self.path.startswith(prefix) else None

        def image_index(self, resource):
            if resource is not None and resource.startswith("image/"):
                index = resource.removeprefix("image/")
                if index.isdecimal() and len(index) <= 8 and 0 <= int(index) < len(session.images):
                    return int(index)
            return None

        def do_GET(self):
            resource = self.resource()
            if resource == "":
                self.send_bytes(200, (TOOL_DIRECTORY / "annotate.html").read_bytes(), "text/html; charset=utf-8")
            elif resource == "annotate.js":
                self.send_bytes(200, (TOOL_DIRECTORY / "annotate.js").read_bytes(), "text/javascript; charset=utf-8")
            elif resource == "session.json":
                self.send_json(200, session.describe())
            else:
                index = self.image_index(resource)
                if index is None:
                    self.send_error(404)
                    return
                path = session.images[index][0]
                try:
                    body = path.read_bytes()
                except OSError:
                    self.send_error(404)
                    return
                content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
                self.send_bytes(200, body, content_type, sha256(body).hexdigest())

        def do_PUT(self):
            index = self.image_index(self.resource())
            if index is None:
                self.send_error(404)
                return
            if self.headers.get_content_type() != "application/json":
                self.send_error(415)
                return
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if not 0 < size <= MAX_REQUEST_BYTES:
                    self.send_error(413)
                    return
                payload = json.loads(self.rfile.read(size))
                self.send_json(200, {"annotation": session.save(index, payload)})
            except ValueError as error:
                self.send_json(400, {"error": str(error)})
            except OSError as error:
                self.send_json(500, {"error": str(error)})

    return AnnotationHandler


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--images", type=Path, required=True, help="Directory of photos for one capture session")
    parser.add_argument("--session-id", required=True, help="Capture session ID, unique across independent captures")
    parser.add_argument("--board-id", required=True, help="ID of the physical board photographed")
    parser.add_argument("--output", type=Path, required=True, help="Manifest JSON, updated in place")
    parser.add_argument("--image-root", type=Path, help="Image path base, defaults to the manifest directory")
    parser.add_argument("--corner-order", choices=("physical", "image"), default="physical", help="Default for new annotations")
    parser.add_argument("--port", type=int, default=0, help="Loopback port, defaults to a free port")
    parser.add_argument("--no-open", action="store_true", help="Print the browser URL without opening it")
    args = parser.parse_args()
    session_id, board_id = args.session_id.strip(), args.board_id.strip()
    if not session_id or not board_id:
        parser.error("Session and board IDs cannot be empty.")
    try:
        output = args.output.resolve()
        image_root = (args.image_root or output.parent).resolve()
        session = AnnotationSession(args.images.resolve(), output, image_root, session_id, board_id, args.corner_order)
        secret = secrets.token_urlsafe(18)
        with HTTPServer(("127.0.0.1", args.port), make_handler(session, secret)) as server:
            url = f"http://127.0.0.1:{server.server_port}/{secret}/"
            print(f"Open {url}\nManifest: {output}\nPress Ctrl+C when done.", flush=True)
            if not args.no_open:
                webbrowser.open(url)
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                pass
    except (OSError, ValueError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
