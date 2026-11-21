"""Solve named-hole assembly plans from the unchanged MechaVision schematic catalog."""

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path

from breadboard import BreadboardGraph, PROFILE_PATH, WiringError, load_profile
from electrical_review import review_project
from wire_routing import RoutingError, route_wires

ROOT = Path(__file__).resolve().parents[1]
RESOURCES = ROOT / "Assets/Resources/MechaVision"
OUTPUT = RESOURCES / "physical_plans.json"
AXES = "xyz"
HOLE_TOLERANCE = 0.00001
TERMINAL_CLEARANCE = 0.0013
STAR_SOURCE = "https://www.wago.com/global/installation-terminal-blocks-and-connectors/compact-splicing-connector/p/221-415"


class PlanError(ValueError):
    pass


def point(values):
    return {axis: round(value, 6) for axis, value in zip(AXES, values)}


def vector(value):
    return tuple(value[axis] for axis in AXES)


def offset(first, second):
    return tuple(left + right for left, right in zip(first, second))


def distance_sq(first, second):
    return sum((left - right) ** 2 for left, right in zip(first, second))


def schematic_partitions(terminals, connections):
    neighbours = {terminal: set() for terminal in terminals}
    for wire in connections:
        start, end = wire["from"], wire["to"]
        if start == end or start not in neighbours or end not in neighbours:
            raise PlanError(f"وصلة غير صالحة في المخطط ({start} / {end}).")
        neighbours[start].add(end)
        neighbours[end].add(start)
    seen = set()
    partitions = []
    for terminal in sorted(neighbours):
        if terminal in seen:
            continue
        pending = [terminal]
        members = set()
        while pending:
            current = pending.pop()
            if current in members:
                continue
            members.add(current)
            pending.extend(neighbours[current] - members)
        seen.update(members)
        partitions.append(sorted(members))
    return partitions


def high_current(part, pin):
    geometry = part["geometry"]
    if geometry == "servo":
        return pin in {"VCC", "GND"}
    if geometry == "dc_motor":
        return True
    if geometry == "motor_driver":
        return pin in {"VS", "GND", "OUT1", "OUT2", "OUT3", "OUT4"}
    if part["id"] == "fqp30n06l":
        return pin in {"D", "S"}
    return False


def body_box(position, size):
    x, _, z = position
    width, _, depth = vector(size)
    return x - width / 2, x + width / 2, z - depth / 2, z + depth / 2


def overlap(first, second, clearance=0):
    return (first[0] < second[1] + clearance and first[1] > second[0] - clearance
            and first[2] < second[3] + clearance and first[3] > second[2] - clearance)


def inside(position, box, clearance=0):
    x, _, z = position
    return (box[0] - clearance <= x <= box[1] + clearance
            and box[2] - clearance <= z <= box[3] + clearance)


def named_steps(project):
    by_id = {wire["id"]: wire for wire in project["connections"]}
    if len(by_id) != len(project["connections"]):
        raise PlanError("معرّفات وصلات المخطط مكررة.")
    references = [wire_id for step in project["assembly_steps"] for wire_id in step["connection_ids"]]
    if Counter(references) != Counter(by_id.keys()):
        raise PlanError("خطوات المخطط لا تسند كل وصلة إلى خطوة واحدة.")
    return [
        (step["instruction_ar"], [by_id[wire_id] for wire_id in step["connection_ids"]])
        for step in project["assembly_steps"]
    ]


class PhysicalPlanner:
    def __init__(self, project, parts, profile):
        self.project = project
        self.parts = parts
        self.profile = profile
        self.graph = BreadboardGraph(profile)
        self.holes = {name: hole for name, hole in profile.holes.items() if not hole.is_rail}
        self.holes_by_strip = defaultdict(list)
        for hole in self.holes.values():
            self.holes_by_strip[hole.strip_id].append(hole)
        self.hole_by_point = {self.key(hole.position_m): hole for hole in self.holes.values()}
        self.hole_use = set()
        self.external_use = set()
        self.strip_nets = {}
        self.boxes = []
        self.components = []
        self.junctions = []
        self.wires = []
        self.pin_terms = {}
        self.hubs = {}
        self.star_ports = {}

        self.endpoints = {}
        self.used = Counter(end for wire in project["connections"] for end in (wire["from"], wire["to"]))
        for component in project["components"]:
            part = parts.get(component["part_id"])
            if part is None:
                raise PlanError(f"قطعة غير معرّفة ({component['part_id']}).")
            if component.get("qty", 1) != 1:
                raise PlanError(f"يجب أن يكون لكل نسخة من القطعة معرّف منفصل ({component['id']}).")
            for pin in part["pins"]:
                endpoint = f"{component['id']}.{pin['id']}"
                if endpoint in self.endpoints:
                    raise PlanError(f"طرف أو قطعة مكررة ({endpoint}).")
                self.endpoints[endpoint] = (part, pin)
        self.partitions = schematic_partitions(self.endpoints, project["connections"])
        self.schematic_nets = {
            endpoint: number for number, partition in enumerate(self.partitions)
            for endpoint in partition
        }
        self.actuator_nets = {
            self.schematic_nets[end] for end, (part, pin) in self.endpoints.items()
            if self.used[end] and high_current(part, pin["id"])
        }

    @staticmethod
    def key(position):
        return tuple(round(value / HOLE_TOLERANCE) for value in position)

    def choose_board_placement(self, component, part):
        pins = part["pins"]
        if any(self.schematic_nets[f"{component['id']}.{pin['id']}"] in self.actuator_nets for pin in pins):
            raise PlanError(f"يجب إبقاء مسار تيار المحرّك خارج اللوح؛ يلزم تركيب خارجي مناسب للقطعة {component['id']}.")
        first_offset = vector(pins[0]["position_m"])
        original = vector(component.get("position_m", point((0, 0, -0.00635))))
        limit_x = self.profile.dimensions_m["x"] / 2
        limit_z = self.profile.dimensions_m["z"] / 2
        best = None
        for first_hole in self.holes.values():
            position = tuple(value - delta for value, delta in zip(first_hole.position_m, first_offset))
            if abs(position[1]) > HOLE_TOLERANCE:
                continue
            box = body_box(position, part["size_m"])
            if box[0] < -limit_x or box[1] > limit_x or box[2] < -limit_z or box[3] > limit_z:
                continue
            if any(overlap(box, prior, clearance=0.001) for prior in self.boxes):
                continue
            assignments = []
            local_strips = {}
            same_strip = 0
            for pin in pins:
                endpoint = f"{component['id']}.{pin['id']}"
                net = self.schematic_nets[endpoint]
                pin_position = offset(position, vector(pin["position_m"]))
                hole = self.hole_by_point.get(self.key(pin_position))
                if hole is None or hole.name in self.hole_use or hole in assignments:
                    break
                occupied_net = local_strips.get(hole.strip_id, self.strip_nets.get(hole.strip_id, net))
                if net != occupied_net:
                    break
                local_strips[hole.strip_id] = net
                same_strip += int(hole.strip_id in self.strip_nets)
                assignments.append(hole)
            if len(assignments) != len(pins):
                continue
            if any(
                not self.free_holes(strip, extra_box=box, extra_occupied=assignments)
                for strip, net in local_strips.items() if len(self.partitions[net]) > 1
            ):
                continue
            score = (-same_strip, distance_sq(original, position), first_hole.name)
            if best is None or score < best[0]:
                best = (score, position, box, assignments)
        if best is None:
            raise PlanError(f"لا توجد ثقوب مناسبة ومتاحة للقطعة {component['id']} في هذا المخطط.")
        _, position, box, assignments = best
        return position, box, assignments

    def place_components(self):
        definitions = self.project["components"]
        for component in sorted(definitions, key=lambda item: item["placement"] != "breadboard"):
            part = self.parts[component["part_id"]]
            mounted = component["placement"] == "breadboard"
            if mounted:
                position, box, assignments = self.choose_board_placement(component, part)
            elif component["placement"] == "outside_board":
                position = vector(component.get("position_m", point((-0.125, 0, 0))))
                position = position[0], -self.profile.dimensions_m["y"], position[2]
                box = body_box(position, part["size_m"])
                limits = self.profile.dimensions_m
                board_box = (-limits["x"] / 2, limits["x"] / 2, -limits["z"] / 2, limits["z"] / 2)
                if overlap(box, board_box) or any(overlap(box, prior) for prior in self.boxes):
                    raise PlanError(f"الموضع الخارجي للقطعة {component['id']} يتداخل مع قطعة أخرى أو مع اللوح.")
                assignments = [None] * len(part["pins"])
            else:
                raise PlanError(f"موضع غير مدعوم للقطعة {component['id']}.")
            pins = []
            for pin, hole in zip(part["pins"], assignments):
                endpoint = f"{component['id']}.{pin['id']}"
                location = offset(position, vector(pin["position_m"]))
                terminal = endpoint
                if hole is not None:
                    terminal = hole.name
                    location = hole.position_m
                    self.graph.attach(endpoint, terminal)
                    self.hole_use.add(terminal)
                    self.strip_nets[hole.strip_id] = self.schematic_nets[endpoint]
                self.pin_terms[endpoint] = terminal
                pins.append({"id": pin["id"], "terminal": terminal, "position_m": point(location)})
            self.boxes.append(box)
            self.components.append({"instance_id": component["id"], "part_id": component["part_id"],
                                    "placement": component["placement"], "position_m": point(position),
                                    "pins": pins})

    def free_holes(self, strip, *, extra_box=None, extra_occupied=()):
        boxes = self.boxes if extra_box is None else [*self.boxes, extra_box]
        occupied = {item.name for item in extra_occupied}
        return [
            hole for hole in self.holes_by_strip[strip]
            if hole.name not in self.hole_use and hole.name not in occupied
            and not any(inside(hole.position_m, box, TERMINAL_CLEARANCE) for box in boxes)
        ]

    def external_position(self, endpoint):
        instance, pin_id = endpoint.split(".", 1)
        for item in self.components:
            if item["instance_id"] != instance:
                continue
            return vector(next(pin for pin in item["pins"] if pin["id"] == pin_id)["position_m"])
        for item in self.junctions:
            if item["id"] == instance:
                return vector(next(port for port in item["ports"] if port["id"] == pin_id)["position_m"])
        raise PlanError(f"موضع الطرف {endpoint} غير معروف.")

    def allocate_strip(self, near, net):
        candidates = []
        for strip in self.holes_by_strip:
            if strip in self.strip_nets:
                continue
            free = self.free_holes(strip)
            if len(free) < 3:
                continue
            distance = min(distance_sq(hole.position_m, near) for hole in free)
            candidates.append((distance, strip))
        if not candidates:
            raise PlanError("لا توجد مجموعة ثقوب فارغة لإنشاء نقطة توزيع آمنة.")
        _, strip = min(candidates)
        self.strip_nets[strip] = net
        return strip

    def select_hole(self, strip, near):
        options = self.free_holes(strip)
        if not options:
            raise PlanError(f"لا توجد فتحة ظاهرة ومتاحة في الشريط {strip}.")
        return min(options, key=lambda hole: (distance_sq(hole.position_m, near), hole.name)).name

    def add_wire(self, start, end, source):
        if start == end:
            raise PlanError(f"لا يمكن توصيل الطرف {start} بنفسه.")
        for terminal in (start, end):
            if terminal in self.holes:
                if terminal in self.hole_use:
                    raise PlanError(f"الثقب {terminal} مستخدم بالفعل.")
                self.hole_use.add(terminal)
            else:
                if terminal in self.external_use:
                    raise PlanError(f"لا يمكن وضع سلكين في الطرف الخارجي {terminal}.")
                self.external_use.add(terminal)
        if start in self.holes and end in self.holes:
            self.graph.jumper(start, end)
        elif start in self.holes or end in self.holes:
            hole, terminal = (start, end) if start in self.holes else (end, start)
            self.graph.wire_to_hole(terminal, hole)
        else:
            self.graph.connect(start, end)
        wire = {"id": f"jumper_{len(self.wires) + 1:02d}", "from": start, "to": end,
                "kind": source["kind"], "color": source["color"],
                "schematic_connection_id": source["id"]}
        self.wires.append(wire)

    def add_servo_star(self):
        if self.project["id"] != "smart_dustbin":
            return
        expected = {"uno1.GND", "servo.GND", "servo_supply.NEG", "sonar.GND"}
        servo_net = next((partition for partition in self.partitions if expected == set(partition)), None)
        if servo_net is None:
            raise PlanError("أطراف توصيل الأرضي المشترك في السلة الذكية غير مطابقة لمخطط الوصلة النجمية.")
        position = (-0.115, -self.profile.dimensions_m["y"], -0.062)
        # Conservative display envelope, not a measurement of a user-owned connector.
        size = point((0.032, 0.012, 0.023))
        ports = []
        for index in range(1, 6):
            port_id = f"P{index}"
            terminal = f"star_ground.{port_id}"
            if index <= len(servo_net):
                self.star_ports[servo_net[index - 1]] = terminal
            self.graph.connect("star_ground.bonded", terminal)
            port_position = offset(position, ((index - 3) * 0.005, 0.003, -0.0115))
            ports.append({"id": port_id, "terminal": terminal, "position_m": point(port_position)})
        self.junctions.append({
            "id": "star_ground", "name_ar": "موصّل أرضي نجمي بخمسة مداخل مترابطة",
            "part_number": "WAGO 221-415", "source_url": STAR_SOURCE,
            "position_m": point(position), "size_m": size, "ports": ports,
        })
        self.boxes.append(body_box(position, size))

    def near_terminal(self, endpoint):
        terminal = self.pin_terms[endpoint]
        return self.holes[terminal].position_m if terminal in self.holes else self.external_position(terminal)

    def contact_for(self, endpoint, near, source, remaining):
        terminal = self.pin_terms[endpoint]
        if terminal in self.holes:
            strip = self.hubs.get(endpoint, self.holes[terminal].strip_id)
        elif self.used[endpoint] == 1:
            return terminal
        else:
            if endpoint not in self.hubs:
                net = self.schematic_nets[endpoint]
                strip = self.allocate_strip(self.external_position(endpoint), net)
                hole = self.select_hole(strip, self.external_position(endpoint))
                self.add_wire(terminal, hole, source)
                self.hubs[endpoint] = strip
            strip = self.hubs[endpoint]
        free = self.free_holes(strip)
        if len(free) == 1 and remaining > 1:
            prior = free[0]
            strip = self.allocate_strip(prior.position_m, self.schematic_nets[endpoint])
            bridge = self.select_hole(strip, prior.position_m)
            self.add_wire(prior.name, bridge, source)
            self.hubs[endpoint] = strip
        return self.select_hole(strip, near)

    def connect_schematic_edge(self, source, remaining):
        start, end = source["from"], source["to"]
        if self.graph.equivalent(start, end):
            if self.pin_terms[start] in self.holes and self.pin_terms[end] in self.holes:
                return f"يتصل {self.pin_terms[start]} و{self.pin_terms[end]} عبر شبكة اللوح الحالية."
            return f"تكتمل الوصلة بين {start} و{end} عبر نقطة التوزيع."
        if start in self.star_ports and end in self.star_ports:
            for endpoint in (start, end):
                port = self.star_ports[endpoint]
                if port not in self.external_use:
                    self.add_wire(endpoint, port, source)
            return ""
        if self.schematic_nets[start] in self.actuator_nets:
            if any(self.pin_terms[endpoint] in self.holes or self.used[endpoint] > 1
                   for endpoint in (start, end)):
                raise PlanError("مسار تيار المحرّك يحتاج موصّل توزيع خارجيًا موثقًا؛ لا يمر هذا التيار باللوح.")
            self.add_wire(start, end, source)
            return ""
        start_contact = self.contact_for(start, self.near_terminal(end), source, remaining[start])
        end_contact = self.contact_for(end, self.near_terminal(start), source, remaining[end])
        self.add_wire(start_contact, end_contact, source)
        return ""

    def create_steps(self):
        remaining = self.used.copy()
        steps = []
        source_steps = named_steps(self.project)
        if source_steps and source_steps[0][1]:
            source_steps.insert(0, ("افصل التغذية وثبّت القطع قبل التوصيل.", []))
        for index, (instruction, connections) in enumerate(source_steps, 1):
            first_wire = len(self.wires)
            text = []
            for source in connections:
                note = self.connect_schematic_edge(source, remaining)
                if note:
                    text.append(note)
                remaining.subtract((source["from"], source["to"]))
            new_wires = self.wires[first_wire:]
            if new_wires:
                labels = "، ".join(f"{wire['from']} ← {wire['to']}" for wire in new_wires)
                text.append(f"نفّذ الوصلات الموضحة: {labels}.")
            if not connections:
                text.insert(0, instruction)
            elif new_wires:
                text.insert(0, instruction)
            if index == 1:
                placements = [
                    f"{component['instance_id']}.{pin['id']} ← {pin['terminal']}"
                    for component in self.components if component["placement"] == "breadboard"
                    for pin in component["pins"]
                ]
                if placements:
                    text.append("أدخل الأرجل في الثقوب التالية: " + "، ".join(placements) + ".")
            steps.append({"step": index, "instruction_ar": " ".join(text),
                          "connection_ids": [wire["id"] for wire in new_wires],
                          "schematic_connection_ids": [wire["id"] for wire in connections]})
        return steps

    def check_net_equivalence(self):
        for start in self.endpoints:
            for end in self.endpoints:
                expected = self.schematic_nets[start] == self.schematic_nets[end]
                if start != end and self.graph.equivalent(start, end) != expected:
                    raise PlanError(f"تختلف شبكة التركيب عن المخطط بين {start} و{end}.")

    def build(self, warnings):
        self.place_components()
        self.add_servo_star()
        steps = self.create_steps()
        self.check_net_equivalence()
        if self.junctions:
            warnings = [*warnings, (
                "يتطلب المسار موصّل WAGO 221-415 منفصلًا يجمع أرضي السيرفو وسالب مزوّده وأرضي Uno والمستشعر. اترك المدخل الخامس فارغًا. "
                "تحقق من توافق نوع السلك ومقطعه وتجريده مع مواصفات الموصّل. أبقِ تيار السيرفو خارج اللوح."
            )]
        plan = {
            "project_id": self.project["id"], "status": "planned", "reason_ar": "",
            "warnings_ar": warnings, "net_equivalent": True,
            "netlist": [{"id": f"net_{index:02d}", "terminals": endpoints}
                        for index, endpoints in enumerate(self.partitions, 1) if len(endpoints) > 1],
            "components": self.components, "junctions": self.junctions,
            "connections": self.wires, "assembly_steps": steps,
        }
        routes = route_wires(plan, self.parts, self.profile)
        for wire in plan["connections"]:
            wire["via"] = routes[wire["id"]]
        return plan


def solve_project(project, parts, profile):
    warnings = []
    if not profile.is_measured:
        warnings.append("ملف اللوح تقديري. أكّد أبعاد الثقوب واستمرارية الشرائط على اللوح الفعلي قبل التركيب.")
    try:
        planner = PhysicalPlanner(project, parts, profile)
        review = review_project(project, parts)
        warnings[:0] = review["warnings_ar"]
        if review["blockers_ar"]:
            raise PlanError(" ".join(review["blockers_ar"]))
        return planner.build(warnings)
    except (PlanError, RoutingError, WiringError) as error:
        reason = str(error)
        if isinstance(error, (RoutingError, WiringError)):
            reason = f"تعذّر حل مسار التوصيل ضمن حدود اللوح والقطع ({error})."
        return {
            "project_id": project["id"], "status": "unavailable", "reason_ar": reason,
            "warnings_ar": warnings, "net_equivalent": False, "netlist": [],
            "components": [], "junctions": [], "connections": [], "assembly_steps": [],
        }


def generate():
    catalog = json.loads((RESOURCES / "catalog.json").read_text(encoding="utf-8"))
    demo = json.loads((RESOURCES / "led_resistor_demo.json").read_text(encoding="utf-8"))
    parts = {part["id"]: part for part in catalog["parts"]}
    profile = load_profile()
    profile_bytes = PROFILE_PATH.read_text(encoding="utf-8").encode("utf-8")
    plans = [solve_project(project, parts, profile) for project in [demo, *catalog["projects"]]]
    return {
        "schema_version": 1, "board_profile_id": profile.id,
        "board_profile_sha256": hashlib.sha256(profile_bytes).hexdigest(),
        "measurement_status": profile.measurement_status, "plans": plans,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify the committed Unity data is reproducible")
    args = parser.parse_args()
    bundle = generate()
    result = json.dumps(bundle, ensure_ascii=False, indent=2) + "\n"
    if args.check:
        if not OUTPUT.is_file() or OUTPUT.read_text(encoding="utf-8") != result:
            parser.exit(1, "Physical plan data is missing or stale. Run python3 Tools/physical_plans.py.\n")
    else:
        OUTPUT.write_text(result, encoding="utf-8")
    statuses = Counter(plan["status"] for plan in bundle["plans"])
    print(f"Assembly plans: {statuses['planned']} solved; {statuses['unavailable']} unavailable.")


if __name__ == "__main__":
    main()
