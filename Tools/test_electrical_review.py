"""Regression cases for blocking inconsistent schematic topology before placement."""

from copy import deepcopy
import json
from pathlib import Path
import unittest

from electrical_review import review_project

RESOURCES = Path(__file__).resolve().parents[1] / "Assets/Resources/MechaVision"
CATALOG = json.loads((RESOURCES / "catalog.json").read_text(encoding="utf-8"))
PARTS = {part["id"]: part for part in CATALOG["parts"]}
PROJECTS = {project["id"]: project for project in CATALOG["projects"]}
DEMO = json.loads((RESOURCES / "led_resistor_demo.json").read_text(encoding="utf-8"))


class ElectricalReviewTests(unittest.TestCase):
    def test_teaching_cases_pass_topology_screening_with_hardware_cautions(self):
        for project in (DEMO, PROJECTS["touchless_doorbell"], PROJECTS["smart_dustbin"]):
            with self.subTest(project=project["id"]):
                result = review_project(project, PARTS)
                self.assertEqual(result["blockers_ar"], [])
                self.assertTrue(result["warnings_ar"])

    def test_power_to_ground_short_blocks_plan(self):
        project = deepcopy(DEMO)
        project["connections"].append({"from": "uno.5V", "to": "uno.GND"})
        self.assertTrue(any("قصر" in item for item in review_project(project, PARTS)["blockers_ar"]))

    def test_led_reverse_polarity_blocks_plan(self):
        project = deepcopy(DEMO)
        project["connections"][1]["to"] = "led1.CATHODE"
        project["connections"][2]["from"] = "led1.ANODE"
        self.assertTrue(any("قطبية" in item for item in review_project(project, PARTS)["blockers_ar"]))

    def test_led_resistor_bypass_blocks_plan(self):
        project = deepcopy(DEMO)
        project["connections"].append({"from": "r1.A", "to": "r1.B"})
        self.assertTrue(any("مقاومة" in item for item in review_project(project, PARTS)["blockers_ar"]))

    def test_direct_gpio_to_dc_motor_is_blocked(self):
        project = deepcopy(PROJECTS["timed_water_pump"])
        wire = next(wire for wire in project["connections"] if wire["to"] == "motor.POS")
        wire["from"] = "uno1.D9"
        self.assertTrue(any("دائرة قيادة" in item for item in review_project(project, PARTS)["blockers_ar"]))

    def test_servo_on_uno_5v_is_blocked(self):
        project = deepcopy(PROJECTS["smart_dustbin"])
        wire = next(wire for wire in project["connections"] if wire["to"] == "servo.VCC")
        wire["from"] = "uno1.5V"
        self.assertTrue(any("تغذية مستقلة" in item for item in review_project(project, PARTS)["blockers_ar"]))


if __name__ == "__main__":
    unittest.main()
