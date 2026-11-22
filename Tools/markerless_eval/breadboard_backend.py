"""Run Breadboard-Classifier's pinned vendored normalizer from a local checkout.

Only the vendor package is imported. The classifier's application code, demo
photos and weights are never copied into MechaVision. The coarse corner source
is explicit; both options use upstream ICP, RANSAC and rail orientation code.
"""

from contextlib import redirect_stdout
from hashlib import sha256
from importlib import import_module
from importlib.util import module_from_spec, spec_from_file_location
import io
from pathlib import Path
import subprocess
import sys

import cv2
import numpy as np

from .geometry import order_corners, validate_quad


CLASSIFIER_SOURCE = "https://github.com/stonestephenson/Breadboard-Classifier"
NORMALIZER_SOURCE = "https://github.com/hartleyblakey/breadboard-normalizer"
VENDORED_REVISION = "7cc71d0"
DEFAULT_MAX_SIDE = 1920
MIN_COLUMN_MARGIN = 0.02
CANONICAL_SIZE = (1024, 340)


def _load_vendored_module(checkout):
    package = checkout / "breadboard" / "_vendor" / "breadboard_normalizer"
    module_path = package / "normalizer.py"
    license_path = package / "LICENSE"
    if not module_path.is_file() or not license_path.is_file():
        raise ValueError(
            "checkout must point to a trusted local Breadboard-Classifier repository "
            "with the vendored normalizer and its license"
        )

    # Load the vendor package in its own namespace, independent of Tools/breadboard.py.
    alias = "_mechavision_normalizer_" + sha256(str(package).encode()).hexdigest()[:12]
    if alias not in sys.modules:
        spec = spec_from_file_location(
            alias, package / "__init__.py", submodule_search_locations=[str(package)]
        )
        if spec is None or spec.loader is None:
            raise ValueError("could not locate the upstream normalizer package")
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        sys.modules[alias] = module
    try:
        with redirect_stdout(io.StringIO()):
            upstream = import_module(f"{alias}.normalizer")
    except ImportError as error:
        raise ValueError(f"upstream normalizer dependencies unavailable: {error}") from error
    return upstream, sha256(module_path.read_bytes()).hexdigest()


def _revision(checkout):
    try:
        result = subprocess.run(
            ["git", "-C", str(checkout), "rev-parse", "--verify", "HEAD"],
            check=True, capture_output=True, text=True,
        )
        return result.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


class BreadboardNormalizer:
    def __init__(self, checkout, seed, max_side, require_grid):
        self.seed = seed
        self.max_side = max_side
        self.require_grid = require_grid
        upstream, digest = _load_vendored_module(checkout)
        with redirect_stdout(io.StringIO()):
            self.normalizer = upstream.Normalizer(
                output_resolution=CANONICAL_SIZE, corner_model=self._seed_corners
            )
        self.info = {
            "source": CLASSIFIER_SOURCE,
            "source_commit": _revision(checkout),
            "normalizer_source": NORMALIZER_SOURCE,
            "vendored_reference_revision": VENDORED_REVISION,
            "normalizer_source_sha256": digest,
            "normalizer_license": "MIT (normalizer); Apache-2.0 (vendored ICP)",
            "backend_output": "four image-space corners; no physical orientation guarantee",
            "canonical_size_px": list(CANONICAL_SIZE),
            "max_working_side_px": max_side,
            "required_wb102_grid_check": require_grid,
            "seed": seed.info,
            "quality": "upstream hole alignment grade (1, 0.75 or 0); not a probability",
        }

    def _seed_corners(self, rgb):
        # The normalizer uses RGB for its rail heuristic. The evaluator seeds take BGR.
        prediction = self.seed(cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))
        corners = prediction["corners_px"]
        return np.float32(corners) if corners is not None else np.empty((0, 2), np.float32)

    def __call__(self, bgr):
        if bgr.ndim != 3 or bgr.shape[2] != 3 or bgr.dtype != np.uint8:
            raise ValueError("breadboard backend expects a uint8 BGR image")
        height, width = bgr.shape[:2]
        if min(height, width) < 2:
            return {"corners_px": None, "corner_order": "image", "reason": "image too small"}
        scale = min(1.0, self.max_side / max(height, width))
        work_size = (max(1, round(width * scale)), max(1, round(height * scale)))
        if work_size != (width, height):
            bgr = cv2.resize(bgr, work_size, interpolation=cv2.INTER_AREA)
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        with redirect_stdout(io.StringIO()):
            canonical, coordinates, quality = self.normalizer.normalize_image(rgb)
        if coordinates is None:
            return {"corners_px": None, "corner_order": "image", "reason": "coarse corners unavailable"}

        # Refined output coordinates may be rotated 180 degrees by the WB-102 rail
        # convention. Image ordering avoids claiming this is the user's column 1.
        xy_scale = np.array([work_size[0] / width, work_size[1] / height])
        try:
            corners = order_corners(coordinates / xy_scale)
            validate_quad(corners, size=(width, height))
        except ValueError as error:
            return {"corners_px": None, "corner_order": "image", "reason": str(error)}

        oriented = self.normalizer.breadboard_orientation_cv(canonical) == "correct"
        margin = self._column_margin(quality)
        mapping = np.asarray(self.normalizer.last_homography) @ np.diag([*xy_scale, 1.0])
        fit_accepted = quality > 0 and oriented and margin >= MIN_COLUMN_MARGIN
        result = {
            "corners_px": corners.tolist(),
            "corner_order": "image",
            "quality": float(quality),
            "wb102_rail_orientation_confirmed": oriented,
            "column_margin": margin,
            "wb102_fit_accepted": fit_accepted,
            "photo_to_upstream_canonical": mapping.tolist(),
        }
        if self.require_grid and not fit_accepted:
            result["rejected_corners_px"] = result["corners_px"]
            result["corners_px"] = None
            result["reason"] = "WB-102 hole grid, rail orientation or column check failed"
        return result

    def _column_margin(self, quality):
        detections = self.normalizer.last_pinhole_detections
        if not quality or detections is None or len(detections) == 0:
            return 0.0
        detections = np.asarray(detections, dtype=np.float32).reshape(-1, 2)
        grid = self.normalizer.pingrid
        base_ratio = grid.evaluate_fit(detections)[1]
        competing_ratios = [
            grid.evaluate_fit(detections + np.float32([offset * grid.pitch[0], 0]))[1]
            for offset in (-2, -1, 1, 2)
        ]
        return float(base_ratio - max(competing_ratios))


def create_backend(options):
    """Configure the original upstream refinement with a local coarse detector."""
    supported = {"checkout", "seed", "max_side", "require_grid", "weights", "threads", "color"}
    if unknown := options.keys() - supported:
        raise ValueError(f"unknown breadboard option(s): {', '.join(sorted(unknown))}")
    if not options.get("checkout"):
        raise ValueError("breadboard backend requires checkout=/path/to/Breadboard-Classifier")
    checkout = Path(options["checkout"]).expanduser().resolve()
    seed_name = options.get("seed", "docaligner")
    if seed_name == "docaligner":
        from .docaligner_backend import create_backend as create_seed
        # Breadboard-Classifier explicitly runs its upstream checkpoint on RGB.
        seed_options = {"color": options.get("color", "rgb")}
        for name in ("weights", "threads"):
            if name in options:
                seed_options[name] = options[name]
    elif seed_name == "classical":
        from .classical_backend import create_backend as create_seed
        seed_options = {}
    else:
        raise ValueError("breadboard seed must be docaligner or classical")

    max_side = int(options.get("max_side", DEFAULT_MAX_SIDE))
    if max_side < 256:
        raise ValueError("breadboard max_side must be at least 256 pixels")
    require_grid = options.get("require_grid", "false").lower()
    if require_grid not in {"true", "false"}:
        raise ValueError("breadboard require_grid must be true or false")
    return BreadboardNormalizer(checkout, create_seed(seed_options), max_side, require_grid == "true")
