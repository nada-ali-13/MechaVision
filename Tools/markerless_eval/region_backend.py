"""Full-frame baseline with bounded optional automatic region fallbacks."""

import cv2
import numpy as np

from . import breadboard_backend
from .geometry import order_corners
from .grid830 import Grid830

INPUT_CAP = 960
MAX_CONTOUR_PROPOSALS = 3


def contour_regions(image):
    """Propose padded regions around large, bright, low-saturation components."""
    height, width = image.shape[:2]
    scale = min(1., 640 / max(height, width))
    small = cv2.resize(image, (round(width*scale), round(height*scale)), interpolation=cv2.INTER_AREA)
    hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)
    bright = max(100, int(np.percentile(hsv[:, :, 2], 64)))
    candidates = cv2.inRange(hsv, (0, 0, bright), (179, 100, 255))
    candidates = cv2.morphologyEx(candidates, cv2.MORPH_CLOSE,
                                  cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))
    count, _, stats, _ = cv2.connectedComponentsWithStats(candidates)
    proposals = []
    area = small.shape[0] * small.shape[1]
    for x, y, w, h, filled in stats[1:count]:
        if not (.012*area <= filled <= .6*area and min(w, h) >= 25 and filled >= .25*w*h):
            continue
        pad = max(w,h)*.13
        box = (max(0, int((x-pad)/scale)), max(0, int((y-pad)/scale)),
               min(width, round((x+w+pad)/scale)), min(height, round((y+h+pad)/scale)))
        if (box[2]-box[0])*(box[3]-box[1]) < .9*width*height:
            proposals.append((int(filled), box))
    return [box for _, box in sorted(proposals, reverse=True)[:MAX_CONTOUR_PROPOSALS]]


def multiscale_regions(width, height):
    """Use a central zoom and two overlapping search windows along the long image axis."""
    yield (width//8, height//8, width-width//8, height-height//8)
    if width >= height:
        yield (0, 0, width*3//4, height)
        yield (width//4, 0, width, height)
    else:
        yield (0, 0, width, height*3//4)
        yield (0, height//4, width, height)


class RegionBackend:
    def __init__(self, normalizer, proposals, grid, profile=None):
        self.normalizer = normalizer
        self.proposals = proposals
        self.grid = grid
        self.validator = Grid830(profile) if grid == "830" and profile else Grid830() if grid == "830" else None
        self.info = {**normalizer.info, "region_proposals": proposals, "grid": grid,
                     "candidate_input_cap": INPUT_CAP}
        if self.validator:
            self.info["board_profile"] = self.validator.profile.id
            self.info["board_profile_measurement"] = self.validator.profile.measurement_status

    def predict_region(self, image, region):
        left, top, right, bottom = region
        cropped = image[top:bottom, left:right]
        height, width = cropped.shape[:2]
        scale = min(1., INPUT_CAP / max(width, height))
        work = cv2.resize(cropped, (round(width*scale), round(height*scale)), interpolation=cv2.INTER_AREA)
        result = self.normalizer(work)
        local = result.get("corners_px")
        if local is None:
            return {"corners_px": None, "reason": result.get("reason", "coarse corners unavailable")}
        local = np.array(local)
        # A candidate ending at a crop boundary can be a fragment of the physical board.
        clipped = bool(np.any(local < 3) or np.any(local >= np.array(work.shape[:2][::-1]) - 3))
        quad = order_corners(local * [width/work.shape[1], height/work.shape[0]] + [left, top])
        result.pop("photo_to_upstream_canonical", None)
        passes = result["wb102_fit_accepted"]
        if self.validator and not clipped:
            profile_score = self.validator(cropped, quad - [left, top])
            result.update(profile_score)
            passes = profile_score["grid830_pass"]
        result.update(corners_px=quad.tolist(), grid_pass=bool(passes and not clipped),
                      region=list(region), clipped_candidate=clipped)
        return result

    def __call__(self, image):
        height, width = image.shape[:2]
        full = (0, 0, width, height)
        regions = [full]
        candidate = None
        attempted = 0
        for index, region in enumerate(regions):
            attempted += 1
            result = self.predict_region(image, region)
            if result.get("grid_pass"):
                result.update(proposals_tried=attempted, proposal_kind="full" if index == 0 else "crop",
                              detection_stage="accepted")
                return result
            if candidate is None and result.get("corners_px") is not None:
                candidate = result
            if index == 0 and self.proposals != "none":
                regions.extend(contour_regions(image))
                if self.proposals == "multiscale":
                    regions.extend(multiscale_regions(width, height))
                regions[:] = list(dict.fromkeys(regions))
        if candidate is None:
            return {"corners_px": None, "corner_order": "image", "proposals_tried": attempted,
                    "reason": "no valid four-corner candidate", "detection_stage": "corner_failure"}
        candidate["rejected_corners_px"] = candidate.pop("corners_px")
        candidate.update(corners_px=None, proposals_tried=attempted,
                         detection_stage="grid_rejection", reason="grid or image-edge check failed")
        return candidate


def create_backend(options):
    options = dict(options)
    proposals = options.pop("proposals", "contours")
    grid = options.pop("grid", "830")
    profile = options.pop("profile", None)
    if proposals not in ("none", "contours", "multiscale") or grid not in ("wb102", "830"):
        raise ValueError("expected proposals=none|contours|multiscale and grid=wb102|830")
    options["require_grid"] = "false"
    return RegionBackend(breadboard_backend.create_backend(options), proposals, grid, profile)
