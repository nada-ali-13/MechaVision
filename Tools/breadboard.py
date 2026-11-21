"""Physical breadboard contacts and explicit conductive connections.

Coordinates use metres and the top centre of the board as the origin.
Template rail continuity is hypothetical until checked on the physical board.
"""

from collections import defaultdict
from dataclasses import dataclass
from itertools import chain
import json
import math
from pathlib import Path
import re
from types import MappingProxyType
from typing import Mapping


PROFILE_PATH = (Path(__file__).resolve().parents[1] / "Assets" / "Resources" /
                "MechaVision" / "breadboard_830.json")
ROW_NAMES = "ABCDEFGHIJ"
RAIL_IDS = ("TP", "TN", "BP", "BN")
HOLE_NAME = re.compile(r"([A-J]|TP|TN|BP|BN)0*([1-9][0-9]*)", re.IGNORECASE)
TERMINAL_NAME = re.compile(r"[A-Za-z][A-Za-z0-9_]*\.[A-Za-z0-9_+\-]+")


class ProfileError(ValueError):
    """The physical board definition is incomplete or inconsistent."""


class WiringError(ValueError):
    """A physical endpoint or connection conflicts with the board model."""


@dataclass(frozen=True)
class Hole:
    name: str
    row: str
    column: int
    strip_id: str
    position_m: tuple[float, float, float]
    is_rail: bool

    def to_dict(self):
        return {
            "name": self.name,
            "row": self.row,
            "column": self.column,
            "strip_id": self.strip_id,
            "position_m": dict(zip("xyz", self.position_m)),
            "is_rail": self.is_rail,
        }


@dataclass(frozen=True)
class BoardProfile:
    id: str
    dimensions_m: Mapping[str, float]
    pitch_m: float
    measurement_status: str
    measurement_notes_ar: str
    holes: Mapping[str, Hole]

    @property
    def is_measured(self):
        """Whether this profile records a documented physical measurement."""
        return self.measurement_status == "measured"

    def hole(self, name):
        match = HOLE_NAME.fullmatch(name) if isinstance(name, str) else None
        if match:
            canonical = f"{match[1].upper()}{match[2]}"
            if canonical in self.holes:
                return self.holes[canonical]
        raise WiringError(f"unknown board hole: {name}")


def _number(value, label, *, positive=False):
    if type(value) not in (int, float) or not math.isfinite(value) or (positive and value <= 0):
        qualifier = "positive and finite" if positive else "finite"
        raise ProfileError(f"{label} must be a {qualifier} number")
    return float(value)


def _count(value, label, expected=None):
    if type(value) is not int or value < 1 or (expected is not None and value != expected):
        requirement = str(expected) if expected is not None else "a positive integer"
        raise ProfileError(f"{label} must be {requirement}")
    return value


def _named_records(records, key, names, label):
    if type(records) is not list or any(not isinstance(entry, dict) for entry in records):
        raise ProfileError(f"{label} must be a list of objects")
    keys = [entry.get(key) for entry in records]
    if len(keys) != len(names) or any(keys.count(name) != 1 for name in names):
        raise ProfileError(f"{label} must contain each of {', '.join(names)} once")
    return {entry[key]: entry for entry in records}


def _terminal_holes(data, pitch):
    count = _count(data["column_count"], "column_count", 63)
    start = _number(data["column_first_x_m"], "column_first_x_m")
    rows = _named_records(data["rows"], "name", ROW_NAMES, "rows")
    last_z = float("-inf")
    for row in ROW_NAMES:
        z = _number(rows[row]["z_m"], f"{row}.z_m")
        correct_side = z < 0 if row in "ABCDE" else z > 0
        if z <= last_z or not correct_side:
            raise ProfileError("tie rows must be in ascending A–J order on opposite sides of Z=0")
        last_z = z
        side = "AE" if row in "ABCDE" else "FJ"
        for column in range(1, count + 1):
            x = round(start + (column - 1) * pitch, 9)
            yield Hole(f"{row}{column}", row, column, f"{side}:{column}", (x, 0.0, z), False)


def _rail_holes(data, pitch):
    rails = _named_records(data["rails"], "id", RAIL_IDS, "rails")
    for rail_id in RAIL_IDS:
        rail = rails[rail_id]
        z = _number(rail["z_m"], f"{rail_id}.z_m")
        start = _number(rail["first_x_m"], f"{rail_id}.first_x_m")
        rail_pitch = _number(rail.get("pitch_m", pitch), f"{rail_id}.pitch_m", positive=True)
        per_group = _count(rail["holes_per_group"], f"{rail_id}.holes_per_group")
        group_count = _count(rail["group_count"], f"{rail_id}.group_count")
        count = _count(per_group * group_count, f"{rail_id} hole count", 50)
        gap = _number(rail["gap_after_group_pitches"], f"{rail_id}.gap_after_group_pitches")
        cuts = rail["cut_after"]
        if gap < 0:
            raise ProfileError(f"{rail_id}.gap_after_group_pitches cannot be negative")
        if (type(cuts) is not list or any(type(cut) is not int or not 1 <= cut < count for cut in cuts)
                or sorted(set(cuts)) != cuts):
            raise ProfileError(f"{rail_id}.cut_after must be sorted, distinct hole numbers from 1 to {count - 1}")
        cut_positions = set(cuts)
        segment = 1
        for column in range(1, count + 1):
            index = column - 1
            x = round(start + (index + index // per_group * gap) * rail_pitch, 9)
            yield Hole(f"{rail_id}{column}", rail_id, column, f"{rail_id}:{segment}", (x, 0.0, z), True)
            if column in cut_positions:
                segment += 1


def load_profile(path=PROFILE_PATH):
    """Read a configurable 630 tie-hole and 200 rail-hole board profile."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(data, dict) or type(data.get("profile_version")) is not int or data["profile_version"] != 1:
            raise ProfileError("profile_version must be 1")
        profile_id = data["id"]
        if not isinstance(profile_id, str) or not profile_id.strip():
            raise ProfileError("id must identify the profile")
        status = data["measurement_status"]
        if status not in ("unmeasured_template", "measured"):
            raise ProfileError("measurement_status must be unmeasured_template or measured")
        notes = data["measurement_notes_ar"]
        if not isinstance(notes, str) or not notes.strip():
            raise ProfileError("measurement_notes_ar must document the profile's measurement status")
        dimensions = {
            axis: _number(data["dimensions_m"][axis], f"dimensions_m.{axis}", positive=True)
            for axis in "xyz"
        }
        pitch = _number(data["pitch_m"], "pitch_m", positive=True)
        holes = {}
        positions = set()
        for hole in chain(_terminal_holes(data, pitch), _rail_holes(data, pitch)):
            x, _, z = hole.position_m
            if abs(x) >= dimensions["x"] / 2 or abs(z) >= dimensions["z"] / 2:
                raise ProfileError(f"{hole.name} lies outside the board")
            if hole.is_rail:
                correct_side = z < holes["A1"].position_m[2] if hole.row.startswith("T") else z > holes["J1"].position_m[2]
                if not correct_side:
                    raise ProfileError(f"{hole.row} rail belongs outside the tie rows on its named side")
            position = (round(x, 9), round(z, 9))
            if position in positions:
                raise ProfileError(f"{hole.name} overlaps another hole")
            positions.add(position)
            holes[hole.name] = hole
    except (KeyError, TypeError, OverflowError, OSError, json.JSONDecodeError) as error:
        raise ProfileError(f"cannot load board profile {path}: {error}") from error
    return BoardProfile(profile_id, MappingProxyType(dimensions), pitch, status, notes, MappingProxyType(holes))


@dataclass(frozen=True)
class NetConflict:
    kind: str
    nodes: tuple[str, ...]
    sources: tuple[str, ...]
    outputs: tuple[str, ...]


class BreadboardGraph:
    """Group explicit conductive connections. The crossing of wires has no electrical effect."""

    def __init__(self, profile):
        self.profile = profile
        self._leader = {}
        self._size = {}
        self._occupied = {}
        self._terminal_holes = {}
        self._sources = {}
        self._outputs = {}
        self._uses_rails = False

        strips = {}
        for name, hole in profile.holes.items():
            self._add(name)
            self._union(name, strips.setdefault(hole.strip_id, name))

    @property
    def uses_unconfirmed_rails(self):
        return self._uses_rails and not self.profile.is_measured

    def _add(self, node):
        self._leader.setdefault(node, node)
        self._size.setdefault(node, 1)

    def _root(self, node):
        while node != self._leader[node]:
            self._leader[node] = self._leader[self._leader[node]]
            node = self._leader[node]
        return node

    def _union(self, first, second):
        left, right = self._root(first), self._root(second)
        if left != right:
            if self._size[left] < self._size[right]:
                left, right = right, left
            self._leader[right] = left
            self._size[left] += self._size[right]

    @staticmethod
    def _terminal(node):
        if not isinstance(node, str) or not TERMINAL_NAME.fullmatch(node):
            raise WiringError(f"invalid external or component terminal: {node}")
        return node

    def _node(self, node):
        if isinstance(node, str) and "." in node:
            return self._terminal(node)
        return self.profile.hole(node).name

    def _join(self, first, second):
        self._uses_rails |= any(node in self.profile.holes and self.profile.holes[node].is_rail
                                for node in (first, second))
        self._add(first)
        self._add(second)
        self._union(first, second)

    def connect(self, first, second):
        """Join nodes whose connection or endpoint capacity is managed by the caller."""
        left, right = self._node(first), self._node(second)
        if left == right:
            raise WiringError(f"connection joins {left} to itself")
        self._join(left, right)

    def _free_hole(self, name):
        canonical = self.profile.hole(name).name
        if canonical in self._occupied:
            raise WiringError(f"hole {canonical} is already occupied by {self._occupied[canonical]}")
        return canonical

    def occupant(self, hole):
        return self._occupied.get(self.profile.hole(hole).name)

    def attach(self, terminal, hole):
        """Insert one component pin into a hole."""
        terminal = self._terminal(terminal)
        destination = self._free_hole(hole)
        if terminal in self._terminal_holes:
            raise WiringError(f"terminal {terminal} is already attached to {self._terminal_holes[terminal]}")
        self._occupied[destination] = terminal
        self._terminal_holes[terminal] = destination
        self._join(terminal, destination)

    def jumper(self, first_hole, second_hole):
        """Insert two jumper ends into separate free holes."""
        left, right = self._free_hole(first_hole), self._free_hole(second_hole)
        if left == right:
            raise WiringError(f"jumper joins {left} to itself")
        self._occupied[left], self._occupied[right] = right, left
        self._join(left, right)

    def wire_to_hole(self, terminal, hole):
        """Join an external terminal to a free hole; the caller manages terminal capacity."""
        terminal = self._terminal(terminal)
        destination = self._free_hole(hole)
        self._occupied[destination] = terminal
        self._join(terminal, destination)

    def equivalent(self, first, second):
        left, right = self._node(first), self._node(second)
        return left in self._leader and right in self._leader and self._root(left) == self._root(right)

    def members(self, node):
        canonical = self._node(node)
        if canonical not in self._leader:
            return ()
        root = self._root(canonical)
        return tuple(sorted(member for member in self._leader if self._root(member) == root))

    def _register(self, node, identifier, roles):
        if not isinstance(identifier, str) or not identifier.strip():
            raise WiringError("electrical role requires an identifier")
        canonical = self._node(node)
        self._add(canonical)
        roles.setdefault(canonical, set()).add(identifier)

    def register_source(self, node, source_id):
        """Declare a fixed supply net identity; a shared ground can use one identity."""
        self._register(node, source_id, self._sources)

    def register_output(self, node, output_id):
        """Declare a push-pull output identity used to detect competing drivers."""
        self._register(node, output_id, self._outputs)

    def conflicts(self):
        """Find joined distinct supplies, competing outputs and outputs tied to a supply."""
        supplies_by_root = defaultdict(set)
        outputs_by_root = defaultdict(set)
        for role_map, by_root in ((self._sources, supplies_by_root), (self._outputs, outputs_by_root)):
            for node, identifiers in role_map.items():
                by_root[self._root(node)].update(identifiers)
        conflicts = []
        for root in sorted(supplies_by_root.keys() | outputs_by_root.keys()):
            supplies = tuple(sorted(supplies_by_root[root]))
            outputs = tuple(sorted(outputs_by_root[root]))
            if len(supplies) > 1 or len(outputs) > 1 or (supplies and outputs):
                nodes = self.members(root)
                if len(supplies) > 1:
                    conflicts.append(NetConflict("source_short", nodes, supplies, outputs))
                if len(outputs) > 1:
                    conflicts.append(NetConflict("output_contention", nodes, supplies, outputs))
                if supplies and outputs:
                    conflicts.append(NetConflict("output_to_supply", nodes, supplies, outputs))
        return tuple(conflicts)
