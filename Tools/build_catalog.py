"""Materialize and validate the offline Unity catalog and Arduino TextAssets."""

import argparse
from collections import Counter
from copy import deepcopy
import json
import math
from pathlib import Path
import re

from jsonschema import Draft202012Validator

from catalog_common import BREADBOARD_GEOMETRIES, COLORS, PARTS, PITCH_MM, metric

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "Assets/Resources/MechaVision/catalog.json"
SCHEMA = Path(__file__).with_name("catalog.schema.json")
BOARD_SIZE = metric(165, 9, 55)
ROW_Z = -6.35
HOLE_TOLERANCE_M = 0.000003
UNO_GPIO = {*(f"D{i}" for i in range(14)), *(f"A{i}" for i in range(6))}
PINS_CPP = r"A[0-5]|[0-9]{1,2}|[A-Za-z_]\w*"
PIN_ACTION = re.compile(rf"\b(pinMode|digitalRead|digitalWrite|analogRead|analogWrite|pulseIn|tone|noTone)\s*\(\s*({PINS_CPP})\s*[,)]")
OUTPUT_MODE = re.compile(rf"\bpinMode\s*\(\s*({PINS_CPP})\s*,\s*OUTPUT\s*\)")
PIN_CONSTANT = re.compile(r"\b(\w+)\s*=\s*(A[0-5]|[0-9]{1,2})\s*[,;]")
PIN_DEFINE = re.compile(r"(?m)^\s*#\s*define\s+(\w+)\s+(A[0-5]|[0-9]{1,2})\s*$")
BASE_HEADERS = {"Arduino", "EEPROM", "SPI", "Wire", "SoftwareSerial", "math", "stdint", "stdio", "stdlib", "string"}


class CatalogError(ValueError):
    """Catalog data did not satisfy a structural or consistency check."""


def collect_index(entries, key, context):
    result = {}
    for entry in entries:
        name = entry[key]
        if name in result:
            raise CatalogError(f"{context}: duplicate {key} {name}")
        result[name] = entry
    return result


def place_components(project, parts):
    """Generate metric locations on the board or on surrounding workspace shelves."""
    next_column = -30
    shelf_left = -130
    shelf_depth = 75
    shelf_height = 0
    for component in project["components"]:
        part_id = component["part_id"]
        if part_id not in parts:
            raise CatalogError(f"{project['id']}: unknown part {part_id}")
        part = parts[part_id]
        pins = [pin["position_m"] for pin in part["pins"]]
        pin_columns = [pin["x"] * 1000 / PITCH_MM for pin in pins]
        smallest_pin = min(pin_columns)
        aligned = all(
            math.isclose(value - smallest_pin, round(value - smallest_pin), abs_tol=1e-4)
            for value in pin_columns
        ) and all(pin["y"] == pin["z"] == 0 for pin in pins)
        if not component["placement"]:
            component["placement"] = (
                "breadboard" if part["geometry"] in BREADBOARD_GEOMETRIES and aligned
                else "outside_board"
            )
        width_mm = part["size_m"]["x"] * 1000
        depth_mm = part["size_m"]["z"] * 1000
        if component["placement"] == "breadboard":
            if not aligned:
                raise CatalogError(f"{project['id']}: {part_id} has no supported breadboard footprint")
            half_width = width_mm / 2 / PITCH_MM
            left_margin = math.ceil(max(0, half_width + smallest_pin))
            x = (next_column + left_margin - smallest_pin) * PITCH_MM
            component["position_m"] = metric(x, 0, ROW_Z)
            right_edge = x / PITCH_MM + max(half_width, max(pin_columns))
            next_column = math.ceil(right_edge) + 2
        elif part_id == "uno":
            component["position_m"] = metric(-125, -9, 0)
        else:
            if shelf_left + width_mm > 170:
                shelf_left = -130
                shelf_depth += shelf_height + 20
                shelf_height = 0
            component["position_m"] = metric(shelf_left + width_mm / 2, -9,
                                             shelf_depth + depth_mm / 2)
            shelf_left += width_mm + 18
            shelf_height = max(shelf_height, depth_mm)


def assemble(parts, projects):
    parts = sorted(deepcopy(parts), key=lambda part: part["id"])
    parts_index = collect_index(parts, "id", "parts")
    projects = deepcopy(projects)
    for project in projects:
        place_components(project, parts_index)
        project["layout"] = {
            "reference_board": "breadboard_830",
            "breadboard_size_m": BOARD_SIZE.copy(),
            "hole_pitch_m": PITCH_MM / 1000,
        }
        project["verification"]["schema_valid"] = True
    return {"schema_version": 1, "parts": parts, "projects": projects}


class WireNets:
    def __init__(self, endpoints):
        self.parent = {endpoint: endpoint for endpoint in endpoints}

    def root(self, endpoint):
        while endpoint != self.parent[endpoint]:
            self.parent[endpoint] = self.parent[self.parent[endpoint]]
            endpoint = self.parent[endpoint]
        return endpoint

    def join(self, start, end):
        self.parent[self.root(start)] = self.root(end)


def check_layout(components, parts, nets):
    occupied_holes = set()
    occupied_strips = {}
    for component in components.values():
        part = parts[component["part_id"]]
        base = component["position_m"]
        if component["placement"] == "outside_board":
            if (abs(base["x"]) - part["size_m"]["x"] / 2 < BOARD_SIZE["x"] / 2
                    and abs(base["z"]) - part["size_m"]["z"] / 2 < BOARD_SIZE["z"] / 2):
                raise CatalogError(f"{component['id']}: external component overlaps the breadboard")
            continue
        for pin in part["pins"]:
            pin_position = pin["position_m"]
            x, y, z = (base[axis] + pin_position[axis] for axis in "xyz")
            pitch_m = PITCH_MM / 1000
            column = round(x / pitch_m)
            row = round((abs(z) - 1.5 * pitch_m) / pitch_m)
            endpoint = f"{component['id']}.{pin['id']}"
            if (not -31 <= column <= 31 or not 0 <= row <= 4
                    or abs(x - column * pitch_m) > HOLE_TOLERANCE_M
                    or abs(y) > HOLE_TOLERANCE_M
                    or abs(abs(z) - (1.5 + row) * pitch_m) > HOLE_TOLERANCE_M):
                raise CatalogError(f"{endpoint}: placement misses a breadboard terminal hole")
            strip = (z > 0, column)
            hole = (strip, row)
            if hole in occupied_holes:
                raise CatalogError(f"{endpoint}: duplicate hole occupancy")
            occupied_holes.add(hole)
            root = nets.root(endpoint)
            if occupied_strips.setdefault(strip, root) != root:
                raise CatalogError(f"{endpoint}: unconnected pins use the same conductive strip")


def resolve_gpio(expression, constants, action=None):
    value = constants.get(expression, expression)
    if not value.isdecimal():
        return value
    number = int(value)
    if action == "analogRead" and 0 <= number <= 5:
        return f"A{number}"
    if 0 <= number <= 13:
        return f"D{number}"
    if 14 <= number <= 19:
        return f"A{number - 14}"
    return value


def validate_sketch(project, sketch, uno_id, nets, fixed_rails):
    if any(not re.search(rf"\bvoid\s+{name}\s*\(", sketch) for name in ("setup", "loop")):
        raise CatalogError("sketch must define setup() and loop()")

    without_comments = re.sub(r"/\*.*?\*/|//[^\n]*", "", sketch, flags=re.DOTALL)
    constants = dict(PIN_CONSTANT.findall(without_comments))
    constants.update(PIN_DEFINE.findall(without_comments))
    pin_uses = []
    for action, expression in PIN_ACTION.findall(without_comments):
        value = resolve_gpio(expression, constants, action)
        if value in UNO_GPIO or re.fullmatch(r"[0-9]+|[AD][0-9]+", value):
            pin_uses.append(value)

    for annotation in re.findall(r"(?m)//\s*@pin\s+([^\n]+)", sketch):
        pin_uses.extend(re.findall(r"\b[AD]\d+\b", annotation))
    if re.search(r"\bWire\.begin\s*\(", without_comments):
        pin_uses.extend(("A4", "A5"))
    used_wired_endpoints = {wire[key] for wire in project["connections"] for key in ("from", "to")}
    for pin in sorted(set(pin_uses)):
        if f"{uno_id}.{pin}" not in used_wired_endpoints:
            raise CatalogError(f"sketch GPIO {pin} has no matching connection")

    outputs = {resolve_gpio(expression, constants) for expression in OUTPUT_MODE.findall(without_comments)}
    driven_nets = {}
    for pin in sorted(outputs & UNO_GPIO):
        connection = nets.root(f"{uno_id}.{pin}")
        if connection in fixed_rails:
            raise CatalogError(f"sketch GPIO output {pin} is directly connected to a supply rail")
        other_pin = driven_nets.setdefault(connection, pin)
        if other_pin != pin:
            raise CatalogError(f"sketch GPIO outputs {other_pin} and {pin} drive the same net")

    libraries = collect_index(project["required_libraries"], "name", "required libraries")
    included = set(re.findall(r"(?m)^\s*#\s*include\s+<([A-Za-z0-9_]+)\.h>", sketch))
    for header in included - BASE_HEADERS:
        normalized = re.sub(r"[^a-z0-9]", "", header.lower())
        if not any(normalized in re.sub(r"[^a-z0-9]", "", lib.lower())
                   or re.sub(r"[^a-z0-9]", "", lib.lower()) in normalized for lib in libraries):
            raise CatalogError(f"include {header}.h has no matching required library metadata")


def validate_project(project, parts, root):
    components = collect_index(project["components"], "id", "components")
    uno_ids = [component["id"] for component in components.values() if component["part_id"] == "uno"]
    if len(uno_ids) != 1:
        raise CatalogError("exactly one Uno R3 is required")
    uno_id = uno_ids[0]
    endpoints = {}
    for component in components.values():
        part = parts.get(component["part_id"])
        if part is None:
            raise CatalogError(f"unknown part {component['part_id']}")
        for pin in part["pins"]:
            endpoints[f"{component['id']}.{pin['id']}"] = component
    nets = WireNets(endpoints)
    wires = collect_index(project["connections"], "id", "connections")
    wire_pairs = set()
    involved = set()
    for wire in wires.values():
        start, end = wire["from"], wire["to"]
        for endpoint in (start, end):
            if endpoint not in endpoints:
                raise CatalogError(f"{wire['id']}: unknown endpoint {endpoint}")
            involved.add(endpoints[endpoint]["id"])
        pair = frozenset((start, end))
        if start == end or pair in wire_pairs:
            raise CatalogError(f"{wire['id']}: duplicate or self-loop wire")
        if COLORS[wire["kind"]] != wire["color"]:
            raise CatalogError(f"{wire['id']}: color does not match wire function")
        wire_pairs.add(pair)
        nets.join(start, end)
    if missing := components.keys() - involved:
        raise CatalogError(f"unwired components: {', '.join(sorted(missing))}")

    grounds = {nets.root(endpoint) for endpoint, component in endpoints.items()
               if endpoint.endswith(".GND")
               or component["part_id"] == "dc_supply" and endpoint.endswith(".NEG")}
    supplies = [f"{uno_id}.5V", f"{uno_id}.3V3"]
    supplies.extend(f"{component['id']}.5V" for component in components.values()
                    if component["part_id"] == "supply_5v")
    supplies.extend(f"{component['id']}.POS" for component in components.values()
                    if component["part_id"] == "dc_supply")
    supply_nets = [nets.root(endpoint) for endpoint in supplies]
    if grounds.intersection(supply_nets) or len(supply_nets) != len(set(supply_nets)):
        raise CatalogError("direct connection between power rails or from rail to ground")
    net_members = {}
    for endpoint in endpoints:
        net_members.setdefault(nets.root(endpoint), set()).add(endpoint)
    resistive_nets = set()
    for component in components.values():
        part = parts[component["part_id"]]
        pins = part["pins"]
        if part["geometry"] == "resistor" and len(pins) == 2:
            first, second = (f"{component['id']}.{pin['id']}" for pin in pins)
            if nets.root(first) != nets.root(second):
                if len(net_members[nets.root(first)]) >= 2 and len(net_members[nets.root(second)]) >= 2:
                    resistive_nets.update((nets.root(first), nets.root(second)))
    for component in components.values():
        part = parts[component["part_id"]]
        if part["geometry"] != "led" or {pin["id"] for pin in part["pins"]} != {"ANODE", "CATHODE"}:
            continue
        led_nets = {nets.root(f"{component['id']}.{pin}") for pin in ("ANODE", "CATHODE")}
        series_nets = {net for net in led_nets & resistive_nets if len(net_members[net]) == 2}
        if len(led_nets) != 2 or not series_nets:
            raise CatalogError(f"{component['id']}: LED appears shorted or has no series resistor")
    check_layout(components, parts, nets)

    covered = Counter()
    for number, step in enumerate(project["assembly_steps"], 1):
        if step["step"] != number:
            raise CatalogError("assembly steps are out of order")
        for wire_id in step["connection_ids"]:
            if wire_id not in wires:
                raise CatalogError(f"step {number} references unknown connection {wire_id}")
            covered[wire_id] += 1
    if covered != Counter(wires.keys()):
        raise CatalogError("assembly steps must introduce every wire exactly once")

    project_id = project["id"]
    sketch_path = f"ArduinoProjects/{project_id}/{project_id}.ino"
    if (project["sketch_path"] != sketch_path
            or project["sketch_resource"] != f"MechaVision/Sketches/{project_id}"):
        raise CatalogError("sketch path or resource key does not match project id")
    sketch = (root / sketch_path).read_text(encoding="utf-8")
    validate_sketch(project, sketch, uno_id, nets, grounds | set(supply_nets))

    verification = project["verification"]
    if any(value for key, value in verification.items() if key not in {"schema_valid", "status"}):
        raise CatalogError("manual verification flags require a recorded review")
    if verification["status"] != "draft" or not verification["schema_valid"]:
        raise CatalogError("this catalog is schema-validated and all projects remain draft")


def validate(catalog, root=ROOT):
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=Draft202012Validator.FORMAT_CHECKER)
    errors = sorted(validator.iter_errors(catalog), key=lambda error: str(error.json_path))
    if errors:
        raise CatalogError("\n".join(f"{error.json_path}: {error.message}" for error in errors))
    parts = collect_index(catalog["parts"], "id", "parts")
    for part in parts.values():
        collect_index(part["pins"], "id", f"{part['id']} pins")
        for anchor in [part["size_m"], *(pin["position_m"] for pin in part["pins"])]:
            if not all(math.isfinite(value) for value in anchor.values()):
                raise CatalogError(f"{part['id']}: non-finite dimensions or pins")
    projects = collect_index(catalog["projects"], "id", "projects")
    unique_text = set()
    errors = []
    for project in projects.values():
        try:
            for key in ("name_ar", "name_en", "description_ar"):
                pair = (key, " ".join(project[key].casefold().split()))
                if pair in unique_text:
                    raise CatalogError(f"duplicate {key}")
                unique_text.add(pair)
            validate_project(project, parts, root)
        except (CatalogError, OSError) as error:
            errors.append(f"{project['id']}: {error}")
    expected_sketches = {root / project["sketch_path"] for project in projects.values()}
    extra_sketches = set((root / "ArduinoProjects").glob("*/*.ino")) - expected_sketches
    if extra_sketches:
        errors.append("unreferenced Arduino sketches: "
                      + ", ".join(str(path.relative_to(root)) for path in sorted(extra_sketches)))
    if errors:
        raise CatalogError("\n".join(errors))


def output_files(catalog):
    yield CATALOG, (json.dumps(catalog, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    for project in catalog["projects"]:
        sketch = ROOT / project["sketch_path"]
        resource = ROOT / "Assets/Resources" / (project["sketch_resource"] + ".txt")
        yield resource, sketch.read_bytes()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="validate and compare committed outputs")
    args = parser.parse_args()
    from catalog_a import PARTS as parts_a, PROJECTS as projects_a
    from catalog_b import PARTS as parts_b, PROJECTS as projects_b

    try:
        catalog = assemble(PARTS + parts_a + parts_b, projects_a + projects_b)
        validate(catalog)
        seen = set()
        for path, content in output_files(catalog):
            seen.add(path)
            if args.check:
                if not path.exists() or path.read_bytes() != content:
                    raise CatalogError(f"stale or missing output: {path.relative_to(ROOT)}")
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                if not path.exists() or path.read_bytes() != content:
                    path.write_bytes(content)
        extra = set((CATALOG.parent / "Sketches").glob("*.txt")) - seen
        if extra:
            raise CatalogError("remove obsolete TextAssets: " + ", ".join(p.name for p in sorted(extra)))
    except (CatalogError, OSError) as error:
        parser.exit(1, f"Catalog validation failed:\n{error}\n")
    print(f"Validated {len(catalog['projects'])} draft projects, {len(catalog['parts'])} part definitions, "
          f"{sum(len(project['connections']) for project in catalog['projects'])} wiring connections "
          "and 50 matching Arduino sketches.")


if __name__ == "__main__":
    main()
