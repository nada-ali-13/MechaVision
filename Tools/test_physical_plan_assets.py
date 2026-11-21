"""Verify the checked-in plans that Unity consumes against the schematic catalog."""

from collections import Counter
import json
from pathlib import Path
import unittest

from breadboard import BreadboardGraph, load_profile

RESOURCES = Path(__file__).resolve().parents[1] / "Assets/Resources/MechaVision"
DEMO = "led_resistor_demo"


def resource(name):
    return json.loads((RESOURCES / name).read_text(encoding="utf-8"))


def expected_groups(terminals, connections):
    """Merge schematic nets independently of the physical planner."""
    groups = {terminal: {terminal} for terminal in terminals}
    for connection in connections:
        joined = groups[connection["from"]] | groups[connection["to"]]
        for terminal in joined:
            groups[terminal] = joined
    return {frozenset(group) for group in groups.values()}


class PhysicalPlanAssetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profile = load_profile()
        cls.bundle = resource("physical_plans.json")
        catalog = resource("catalog.json")
        cls.schematics = {project["id"]: project for project in catalog["projects"]}
        cls.schematics[DEMO] = resource(DEMO + ".json")
        cls.parts = {part["id"]: part for part in catalog["parts"]}
        cls.plans = {plan["project_id"]: plan for plan in cls.bundle["plans"]}

    def test_every_original_project_has_a_draft_plan_or_a_limitation(self):
        self.assertEqual(len(self.bundle["plans"]), len(self.plans))
        self.assertEqual(self.plans.keys(), self.schematics.keys())
        self.assertEqual(len(self.plans), 51)
        for plan in self.plans.values():
            if plan["status"] != "planned":
                self.assertEqual(plan["status"], "unavailable")
                self.assertTrue(plan["reason_ar"])
                self.assertFalse(plan["connections"])

    def test_serialized_plans_rebuild_the_schematic_and_have_one_connection_per_end(self):
        for project_id, plan in self.plans.items():
            if plan["status"] != "planned":
                continue
            with self.subTest(project_id=project_id):
                graph = BreadboardGraph(self.profile)
                anchors = set()
                occupied = set()
                pins = set()
                for component in plan["components"]:
                    for pin in component["pins"]:
                        logical = f"{component['instance_id']}.{pin['id']}"
                        pins.add(logical)
                        terminal = pin["terminal"]
                        if component["placement"] == "outside_board":
                            self.assertEqual(terminal, logical)
                            anchors.add(terminal)
                        else:
                            self.assertIn(terminal, self.profile.holes)
                            self.assertNotIn(terminal, occupied)
                            occupied.add(terminal)
                            graph.attach(logical, terminal)
                            for axis, value in zip("xyz", self.profile.hole(terminal).position_m):
                                self.assertAlmostEqual(pin["position_m"][axis], value, places=6)

                for junction in plan["junctions"]:
                    ports = [port["terminal"] for port in junction["ports"]]
                    self.assertTrue(ports)
                    self.assertFalse(set(ports) & anchors)
                    anchors.update(ports)
                    for port in ports[1:]:
                        graph.connect(ports[0], port)

                connections = {w["id"]: w for w in plan["connections"]}
                self.assertEqual(len(connections), len(plan["connections"]))
                for wire in connections.values():
                    start, end = wire["from"], wire["to"]
                    self.assertNotEqual(start, end)
                    for terminal in (start, end):
                        self.assertNotIn(terminal, occupied)
                        occupied.add(terminal)
                        if terminal not in anchors:
                            self.assertFalse(self.profile.hole(terminal).is_rail)
                    graph.connect(start, end)
                    self.assertTrue(wire["via"])

                schematic = self.schematics[project_id]
                expected_pins = {
                    f"{component['id']}.{pin['id']}"
                    for component in schematic["components"]
                    for pin in self.parts[component["part_id"]]["pins"]
                }
                self.assertEqual(pins, expected_pins)
                actual = {frozenset(graph.members(pin)) & pins or frozenset([pin]) for pin in pins}
                expected = expected_groups(pins, schematic["connections"])
                self.assertEqual(actual, expected)
                self.assertTrue(plan["net_equivalent"])
                self.assertEqual(
                    Counter(wire_id for step in plan["assembly_steps"] for wire_id in step["connection_ids"]),
                    Counter(connections.keys()),
                )

    def test_led_fixture_has_real_hole_insertions_and_a_jumper_from_each_uno_terminal(self):
        plan = self.plans[DEMO]
        self.assertEqual(plan["status"], "planned")
        installed = {pin["terminal"] for part in plan["components"] if part["placement"] == "breadboard"
                     for pin in part["pins"]}
        self.assertEqual(len(installed), 4)
        for terminal in ("uno.D9", "uno.GND"):
            wire, = (wire for wire in plan["connections"] if terminal in (wire["from"], wire["to"]))
            hole, = {wire["from"], wire["to"]} - {terminal}
            self.assertIn(hole, self.profile.holes)
            self.assertNotIn(hole, installed)

    def test_hc_sr04_and_servo_examples_have_supported_physical_plans(self):
        for project_id in ("touchless_doorbell", "smart_dustbin"):
            self.assertEqual(self.plans[project_id]["status"], "planned", self.plans[project_id]["reason_ar"])
        servo = self.plans["smart_dustbin"]
        hardware = {component["part_id"]: component for component in servo["components"]}
        self.assertEqual(hardware["servo"]["placement"], "outside_board")
        for terminal in ("servo.VCC", "servo.GND"):
            wire, = (wire for wire in servo["connections"] if terminal in (wire["from"], wire["to"]))
            self.assertTrue(all("." in end for end in (wire["from"], wire["to"])))


if __name__ == "__main__":
    unittest.main()
