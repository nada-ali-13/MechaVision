import json
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from jsonschema import Draft202012Validator

from build_catalog import CatalogError, SCHEMA, assemble, validate_project
from catalog_common import PARTS, metric, project


def sample_project():
    return project(
        "bench_led", "اختبار صمام ضوئي", "Bench LED", "basics", "beginner",
        "اختبار طرف رقمي بدائرة آمنة.",
        [("uno", "uno"), ("lamp", "led"), ("limit", "resistor")],
        [("uno.D7", "limit.A", "signal"), ("limit.B", "lamp.ANODE", "signal"),
         ("lamp.CATHODE", "uno.GND", "ground")],
        [("https://docs.arduino.cc/built-in-examples/basics/Blink/", "LED wiring")],
    )


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.data = assemble(PARTS, [sample_project()])
        self.project = self.data["projects"][0]
        self.parts = {entry["id"]: entry for entry in self.data["parts"]}
        self.sketch = self.root / self.project["sketch_path"]
        self.sketch.parent.mkdir(parents=True)
        self.sketch.write_text("const int lamp = 7;\nvoid setup(){pinMode(lamp, OUTPUT);}\n"
                               "void loop(){digitalWrite(lamp, HIGH);}\n", encoding="utf-8")

    def check_project(self):
        validate_project(self.project, self.parts, self.root)

    def test_schema_rejects_missing_pins_and_incomplete_catalog(self):
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema)
        del self.data["parts"][0]["pins"]
        errors = list(validator.iter_errors(self.data))
        self.assertEqual({error.validator for error in errors}, {"required", "minItems"})

    def test_correct_sample_and_aligned_holes(self):
        self.check_project()
        lamp = self.project["components"][1]
        self.assertEqual(lamp["placement"], "breadboard")
        x = lamp["position_m"]["x"] + self.parts["led"]["pins"][0]["position_m"]["x"]
        self.assertAlmostEqual(x / 0.00254, round(x / 0.00254), places=5)

    def test_unrecognised_port_is_rejected(self):
        self.project["connections"][0]["from"] = "uno.D42"
        with self.assertRaisesRegex(CatalogError, "unknown endpoint uno.D42"):
            self.check_project()

    def test_unwired_sketch_gpio_is_rejected(self):
        self.sketch.write_text("void setup(){pinMode(8, OUTPUT);}\nvoid loop(){}\n", encoding="utf-8")
        with self.assertRaisesRegex(CatalogError, "sketch GPIO D8 has no matching connection"):
            self.check_project()

    def test_rail_short_is_rejected_even_via_multiple_wires(self):
        self.project["connections"][0]["from"] = "uno.5V"
        self.project["connections"][1]["from"] = "limit.A"
        self.project["connections"][1]["to"] = "uno.GND"
        with self.assertRaisesRegex(CatalogError, "from rail to ground"):
            self.check_project()

    def test_multiple_output_pins_cannot_drive_one_net(self):
        self.project["connections"].append({
            "id": "wire_04", "from": "uno.D8", "to": "limit.A", "kind": "signal", "color": "yellow",
        })
        self.project["assembly_steps"][1]["connection_ids"].append("wire_04")
        self.sketch.write_text("void setup(){pinMode(7, OUTPUT); pinMode(8, OUTPUT);}\n"
                               "void loop(){}\n", encoding="utf-8")
        with self.assertRaisesRegex(CatalogError, "GPIO outputs D7 and D8 drive the same net"):
            self.check_project()

    def test_missing_step_wire_is_rejected(self):
        self.project["assembly_steps"][1]["connection_ids"].clear()
        with self.assertRaisesRegex(CatalogError, "every wire exactly once"):
            self.check_project()

    def test_shared_tie_strip_is_detected_across_rows(self):
        lamp, limit = self.project["components"][1:]
        lamp_x = lamp["position_m"]["x"] * 1000
        limit["position_m"] = metric(lamp_x - 2.54, 0, -8.89)
        with self.assertRaisesRegex(CatalogError, "same conductive strip"):
            self.check_project()

    def test_exactly_shared_holes_are_rejected(self):
        lamp, limit = self.project["components"][1:]
        limit["position_m"] = deepcopy(lamp["position_m"])
        limit["position_m"]["x"] -= 0.00254
        with self.assertRaisesRegex(CatalogError, "duplicate hole occupancy"):
            self.check_project()

    def test_review_status_requires_evidence(self):
        self.project["verification"]["hardware_tested"] = True
        with self.assertRaisesRegex(CatalogError, "require a recorded review"):
            self.check_project()
