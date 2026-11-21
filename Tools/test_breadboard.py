"""Checks for the 830-contact physical profile and explicit electrical topology."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from breadboard import BreadboardGraph, PROFILE_PATH, ProfileError, WiringError, load_profile


class BreadboardProfileTests(unittest.TestCase):
    def setUp(self):
        self.profile = load_profile()
        self.data = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))

    def load_modified(self):
        with TemporaryDirectory() as temporary:
            path = Path(temporary) / "board.json"
            path.write_text(json.dumps(self.data), encoding="utf-8")
            return load_profile(path)

    def test_830_contacts_and_placement_frame(self):
        self.assertEqual(len(self.profile.holes), 830)
        self.assertEqual(sum(hole.is_rail for hole in self.profile.holes.values()), 200)
        self.assertEqual(len({hole.position_m for hole in self.profile.holes.values()}), 830)
        self.assertEqual(self.profile.hole("a01").position_m, (-0.07874, 0, -0.01397))
        self.assertEqual(self.profile.hole("J63").position_m, (0.07874, 0, 0.01397))
        self.assertEqual(self.profile.hole("E32").position_m, (0, 0, -0.00381))
        self.assertEqual(self.profile.hole("F32").position_m, (0, 0, 0.00381))
        self.assertEqual(self.profile.hole("TP01").to_dict()["position_m"],
                         {"x": -0.07366, "y": 0, "z": -0.02286})
        self.assertFalse(self.profile.is_measured)

    def test_rail_geometry_gap_is_separate_from_electrical_cut(self):
        profile = self.profile
        hole_x = lambda name: profile.hole(name).position_m[0]
        self.assertAlmostEqual(hole_x("TP5") - hole_x("TP4"), profile.pitch_m)
        self.assertAlmostEqual(hole_x("TP6") - hole_x("TP5"), 2 * profile.pitch_m)
        graph = BreadboardGraph(profile)
        self.assertTrue(graph.equivalent("TP5", "TP6"))
        self.assertFalse(graph.equivalent("TP25", "TP26"))
        self.assertFalse(graph.equivalent("TN1", "TP1"))
        self.assertFalse(graph.equivalent("BN1", "TN1"))

    def test_individual_rails_can_be_measured_and_configured(self):
        self.data["measurement_status"] = "measured"
        self.data["measurement_notes_ar"] = "قيم اصطناعية لهذا الاختبار"
        self.data["dimensions_m"]["z"] = 0.056
        self.data["rails"][0]["cut_after"] = []
        self.data["rails"][1]["cut_after"] = [10, 35]
        self.data["rails"][1]["first_x_m"] = -0.074
        self.data["rails"][1]["z_m"] = -0.020
        profile = self.load_modified()
        graph = BreadboardGraph(profile)
        self.assertTrue(profile.is_measured)
        self.assertEqual(profile.dimensions_m["z"], 0.056)
        self.assertEqual(profile.hole("TN1").position_m, (-0.074, 0, -0.020))
        self.assertTrue(graph.equivalent("TP1", "TP50"))
        self.assertFalse(graph.equivalent("TN10", "TN11"))
        self.assertTrue(graph.equivalent("TN11", "TN35"))
        self.assertFalse(graph.equivalent("TN35", "TN36"))
        graph.wire_to_hole("uno1.GND", "TN1")
        self.assertFalse(graph.uses_unconfirmed_rails)

    def test_profile_rejects_missing_or_duplicate_rows(self):
        self.data["rows"][2]["name"] = "B"
        with self.assertRaisesRegex(ProfileError, "must contain"):
            self.load_modified()

    def test_profile_rejects_cut_after_last_hole(self):
        self.data["rails"][0]["cut_after"] = [50]
        with self.assertRaisesRegex(ProfileError, "cut_after"):
            self.load_modified()

    def test_profile_rejects_rail_on_wrong_side(self):
        self.data["rails"][0]["z_m"] = 0.02
        with self.assertRaisesRegex(ProfileError, "named side"):
            self.load_modified()

    def test_profile_rejects_board_smaller_than_column_extent(self):
        self.data["dimensions_m"]["x"] = 0.16
        self.data["column_first_x_m"] = -0.081
        with self.assertRaisesRegex(ProfileError, "outside the board"):
            self.load_modified()


class BreadboardGraphTests(unittest.TestCase):
    def setUp(self):
        self.profile = load_profile()
        self.graph = BreadboardGraph(self.profile)

    def test_five_holes_per_strip_with_unbridged_gap_and_columns(self):
        self.assertEqual(self.graph.members("A10"), ("A10", "B10", "C10", "D10", "E10"))
        self.assertEqual(self.graph.members("F10"), ("F10", "G10", "H10", "I10", "J10"))
        self.assertFalse(self.graph.equivalent("E10", "F10"))
        self.assertFalse(self.graph.equivalent("A10", "A11"))

    def test_component_and_jumper_join_through_spare_holes(self):
        self.graph.attach("led1.ANODE", "C10")
        self.graph.jumper("A10", "F20")
        self.graph.wire_to_hole("uno1.D9", "J20")
        self.assertTrue(self.graph.equivalent("led1.ANODE", "uno1.D9"))
        self.assertEqual(self.graph.occupant("c010"), "led1.ANODE")
        self.assertEqual(self.graph.occupant("A10"), "F20")
        self.assertIsNone(self.graph.occupant("B10"))
        self.assertFalse(self.graph.equivalent("led1.ANODE", "C11"))

    def test_crossed_jumpers_do_not_join_nets(self):
        # These diagonals cross in X/Z halfway between rows A and J and columns 1 and 10.
        self.graph.jumper("A1", "J10")
        self.graph.jumper("A10", "J1")
        self.assertTrue(self.graph.equivalent("A1", "J10"))
        self.assertTrue(self.graph.equivalent("A10", "J1"))
        self.assertFalse(self.graph.equivalent("A1", "J1"))
        self.assertFalse(self.graph.equivalent("J10", "A10"))

    def test_physical_occupancy_is_enforced_without_partial_mutation(self):
        self.graph.attach("r.A", "C10")
        with self.assertRaisesRegex(WiringError, "already occupied"):
            self.graph.jumper("A10", "C10")
        with self.assertRaisesRegex(WiringError, "already occupied"):
            self.graph.wire_to_hole("uno1.GND", "C10")
        with self.assertRaisesRegex(WiringError, "already attached"):
            self.graph.attach("r.A", "J31")
        self.assertIsNone(self.graph.occupant("A10"))
        self.assertIsNone(self.graph.occupant("J31"))
        self.assertFalse(self.graph.equivalent("uno1.GND", "r.A"))

    def test_unknown_or_identical_endpoints_are_rejected(self):
        with self.assertRaisesRegex(WiringError, "unknown board hole"):
            self.graph.attach("r.A", "J64")
        with self.assertRaisesRegex(WiringError, "invalid external"):
            self.graph.attach("malformed.terminal.", "A1")
        with self.assertRaisesRegex(WiringError, "to itself"):
            self.graph.jumper("A1", "a01")
        with self.assertRaisesRegex(WiringError, "unknown board hole"):
            self.graph.equivalent(None, "A1")

    def test_bridging_a_template_rail_cut_marks_measurement_needed(self):
        self.assertFalse(self.graph.uses_unconfirmed_rails)
        self.assertFalse(self.graph.equivalent("TP20", "TP30"))
        self.graph.jumper("TP25", "TP26")
        self.assertTrue(self.graph.equivalent("TP20", "TP30"))
        self.assertTrue(self.graph.uses_unconfirmed_rails)

    def test_external_actuator_can_wire_directly(self):
        self.graph.connect("supply.5V", "servo.VCC")
        self.graph.connect("supply.GND", "servo.GND")
        self.graph.connect("uno1.GND", "supply.GND")
        self.graph.connect("uno1.D9", "servo.SIGNAL")
        self.assertEqual(self.graph.members("servo.VCC"), ("servo.VCC", "supply.5V"))
        self.assertTrue(self.graph.equivalent("uno1.GND", "servo.GND"))
        self.assertFalse(self.graph.equivalent("supply.5V", "supply.GND"))

    def test_conflicts_detect_distinct_supply_and_ground_joined_by_jumper(self):
        self.graph.register_source("uno1.5V", "usb_5v")
        self.graph.register_source("uno1.GND", "ground")
        self.graph.wire_to_hole("uno1.5V", "A20")
        self.graph.wire_to_hole("uno1.GND", "F20")
        self.assertEqual(self.graph.conflicts(), ())
        self.graph.jumper("C20", "J20")
        conflict, = self.graph.conflicts()
        self.assertEqual(conflict.kind, "source_short")
        self.assertEqual(conflict.sources, ("ground", "usb_5v"))
        self.assertIn("uno1.GND", conflict.nodes)

    def test_common_ground_is_valid_but_independent_positive_supplies_must_stay_apart(self):
        self.graph.register_source("usb.GND", "ground")
        self.graph.register_source("battery.GND", "ground")
        self.graph.connect("usb.GND", "battery.GND")
        self.graph.register_source("usb.5V", "usb_5v")
        self.graph.register_source("battery.5V", "battery_5v")
        self.assertEqual(self.graph.conflicts(), ())
        self.graph.connect("usb.5V", "battery.5V")
        conflict, = self.graph.conflicts()
        self.assertEqual(conflict.kind, "source_short")
        self.assertEqual(conflict.sources, ("battery_5v", "usb_5v"))

    def test_competing_outputs_or_output_tied_to_supply(self):
        self.graph.register_output("uno1.D9", "uno1.D9")
        self.graph.register_output("sensor.ECHO", "sensor.ECHO")
        self.graph.connect("uno1.D9", "sensor.ECHO")
        self.assertEqual([conflict.kind for conflict in self.graph.conflicts()], ["output_contention"])
        self.graph.register_source("uno1.5V", "usb_5v")
        self.graph.connect("uno1.D9", "uno1.5V")
        self.assertEqual([conflict.kind for conflict in self.graph.conflicts()],
                         ["output_contention", "output_to_supply"])


if __name__ == "__main__":
    unittest.main()
