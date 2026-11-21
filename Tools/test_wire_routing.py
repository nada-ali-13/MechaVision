"""Geometry tests for breadboard-local insulated jumper routes."""

from dataclasses import dataclass
from itertools import pairwise
import unittest

from wire_routing import RoutingError, route_wires


@dataclass
class Hole:
    position_m: tuple


class Profile:
    def __init__(self, **holes):
        self.holes = holes

    def hole(self, name):
        return Hole(self.holes[name])


def point(x, y, z):
    return {"x": x, "y": y, "z": z}


def wire(name, first, last):
    return {"id": name, "from": first, "to": last}


def body(name, x, z, *, y=0.0, pins=()):
    return {"instance_id": name, "part_id": "body", "position_m": point(x, y, z), "pins": pins}


class WireRoutingTests(unittest.TestCase):
    def setUp(self):
        self.parts = {"body": {"size_m": point(0.010, 0.016, 0.012)}}

    def test_short_row_jumper_has_vertical_insertions_and_simple_level_span(self):
        profile = Profile(A10=(-0.05588, 0.0, -0.01397), A14=(-0.04572, 0.0, -0.01397))
        plan = {"connections": [wire("signal", "A10", "A14")], "components": []}
        waypoints = route_wires(plan, self.parts, profile)["signal"]
        self.assertEqual(len(waypoints), 2)
        self.assertEqual(waypoints[0]["x"], -0.05588)
        self.assertEqual(waypoints[-1]["x"], -0.04572)
        self.assertEqual(waypoints[0]["z"], waypoints[-1]["z"])
        self.assertEqual(waypoints[0]["y"], waypoints[-1]["y"])
        self.assertGreater(waypoints[0]["y"], 0.0)

    def test_jumper_goes_around_a_component_instead_of_through_it(self):
        profile = Profile(A10=(-0.027, 0.0, -0.012), A30=(0.024, 0.0, -0.012))
        plan = {"connections": [wire("signal", "A10", "A30")],
                "components": [body("led", 0.0, -0.012)]}
        route = route_wires(plan, self.parts, profile)["signal"]
        self.assertGreaterEqual(len(route), 4)
        self.assertTrue(any(abs(vertex["z"] + 0.012) >= 0.0069 for vertex in route))
        for first, last in pairwise(route):
            self.assertEqual(sum(first[axis] != last[axis] for axis in "xyz"), 1)
            self.assertLessEqual(max(first["y"], last["y"]), 0.006)
            if min(first["x"], last["x"]) <= 0.0 <= max(first["x"], last["x"]):
                self.assertGreaterEqual(abs(first["z"] + 0.012), 0.0069)

    def test_unavoidable_crossing_uses_distinct_levels_and_stays_deterministic(self):
        profile = Profile(A1=(0, 0, -0.045), J1=(0, 0, 0.045),
                          E1=(-0.045, 0, 0), E63=(0.045, 0, 0))
        plan = {"connections": [wire("z_axis", "A1", "J1"), wire("x_axis", "E1", "E63")],
                "components": []}
        first = route_wires(plan, self.parts, profile)
        second = route_wires({**plan, "connections": list(reversed(plan["connections"]))}, self.parts, profile)
        self.assertEqual(first, second)
        self.assertEqual(len(first["z_axis"]), 2)
        self.assertEqual(len(first["x_axis"]), 2)
        self.assertGreaterEqual(first["z_axis"][0]["y"] - first["x_axis"][0]["y"], 0.002)
        self.assertEqual(set(first), {"z_axis", "x_axis"})

    def test_body_cannot_hide_a_board_jumper_terminal(self):
        profile = Profile(C31=(0.0, 0.0, -0.01), A60=(0.071, 0.0, -0.014))
        plan = {"connections": [wire("signal", "C31", "A60")],
                "components": [body("block", 0.0, -0.01)]}
        with self.assertRaisesRegex(RoutingError, "C31.*inside a component footprint"):
            route_wires(plan, self.parts, profile)

    def test_visibility_grid_routes_around_a_u_shaped_obstacle_group(self):
        profile = Profile(E30=(0, 0, 0), E13=(-0.045, 0, 0))
        parts = {
            "side": {"size_m": point(0.050, 0.016, 0.012)},
            "back": {"size_m": point(0.010, 0.016, 0.024)},
        }
        plan = {"connections": [wire("routed", "E30", "E13")], "components": [
            {**body("back", -0.027, 0.0), "part_id": "back"},
            {**body("north", -0.007, 0.011), "part_id": "side"},
            {**body("south", -0.007, -0.011), "part_id": "side"},
        ]}
        route = route_wires(plan, parts, profile)["routed"]
        self.assertGreaterEqual(len(route), 5)
        self.assertGreaterEqual(max(vertex["x"] for vertex in route), 0.019)
        self.assertGreaterEqual(max(abs(vertex["z"]) for vertex in route), 0.018)

    def test_external_connector_reaches_corridor_before_rising(self):
        profile = Profile(A30=(0, 0, -0.014))
        star = {"id": "star", "position_m": point(-0.035, -0.009, 0.045),
                "size_m": point(0.019, 0.008, 0.020),
                "ports": [{"id": "P1", "terminal": "star.P1", "position_m": point(-0.034, -0.007, 0.036)}]}
        plan = {"connections": [wire("ground", "star.P1", "A30")],
                "components": [], "junctions": [star]}
        route = route_wires(plan, self.parts, profile)["ground"]
        self.assertEqual(route[0], point(-0.034, -0.007, 0.034))
        self.assertEqual(route[1]["z"], route[0]["z"])
        self.assertGreater(route[1]["y"], 0.0)
        self.assertEqual(route[-1]["z"], -0.014)

    def test_route_projection_avoids_unrelated_terminal_stems(self):
        profile = Profile(A1=(-0.025, 0, -0.012), A25=(0.025, 0, -0.012),
                          A13=(0, 0, -0.012), J20=(0.016, 0, 0.014))
        plan = {"connections": [wire("a", "A1", "A25"), wire("b", "A13", "J20")],
                "components": []}
        route = route_wires(plan, self.parts, profile)["a"]
        for first, last in pairwise(route):
            if min(first["x"], last["x"]) <= 0 <= max(first["x"], last["x"]):
                self.assertGreaterEqual(abs(first["z"] - (-0.012)), 0.001)


if __name__ == "__main__":
    unittest.main()
