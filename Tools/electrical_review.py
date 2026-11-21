"""Conservative schematic checks for the V2 placement pipeline.

A passing result is a topology check. Ratings, connector fit, module variants,
live circuits and firmware behavior require independent review.
"""

from collections import defaultdict
from pathlib import Path

from build_catalog import CatalogError, UNO_GPIO, WireNets, validate_sketch

ROOT = Path(__file__).resolve().parents[1]
EXTERNAL_SUPPLIES = {"dc_supply": ("POS", "NEG"), "supply_5v": ("5V", "GND")}
MOTOR_PARTS = {"tt_motor", "dc_fan", "dc_pump"}
LED_SERIES_OHMS = {
    "resistor": 220, "resistor_220": 220, "resistor_1k": 1000,
    "resistor_2k": 2000, "resistor_10k": 10000, "resistor_100k": 100000,
}


def review_project(project, parts):
    """Return blocking topology issues and nonblocking hardware checks in Arabic."""
    blockers = []
    warnings = []
    by_part = defaultdict(list)
    for component in project["components"]:
        by_part[component["part_id"]].append(component["id"])
    if len(by_part["uno"]) != 1:
        return {"blockers_ar": ["يتطلب هذا المخطط لوحة Uno واحدة."], "warnings_ar": []}
    uno = by_part["uno"][0]

    terminals = [
        f"{component['id']}.{pin['id']}"
        for component in project["components"]
        for pin in parts[component["part_id"]]["pins"]
    ]
    nets = WireNets(terminals)
    for wire in project["connections"]:
        if wire["from"] not in nets.parent or wire["to"] not in nets.parent:
            return {"blockers_ar": ["يحتوي المخطط على طرف غير معرّف."], "warnings_ar": []}
        nets.join(wire["from"], wire["to"])

    def node(component, pin):
        return nets.root(f"{component}.{pin}")

    members = defaultdict(set)
    for terminal in terminals:
        members[nets.root(terminal)].add(terminal)
    ground = node(uno, "GND")
    uno_supply = {node(uno, "5V"), node(uno, "3V3")}
    uno_drive = {node(uno, pin) for pin in UNO_GPIO}
    external_positive = []
    external_returns = set()
    for part_id, (positive, negative) in EXTERNAL_SUPPLIES.items():
        external_positive.extend(node(component, positive) for component in by_part[part_id])
        external_returns.update(node(component, negative) for component in by_part[part_id])
    positive_rails = [node(uno, "5V"), node(uno, "3V3"), *external_positive]
    returns = {ground, *external_returns}
    if len(positive_rails) != len(set(positive_rails)) or returns.intersection(positive_rails):
        blockers.append("يوجد قصر بين مصادر التغذية أو بين التغذية والأرضي.")

    try:
        sketch = (ROOT / project["sketch_path"]).read_text(encoding="utf-8")
        validate_sketch(project, sketch, uno, nets, returns | set(positive_rails))
    except (OSError, CatalogError):
        blockers.append("تعذّر مطابقة منافذ الكود مع المخطط أو وُجد تعارض في أحد المخارج.")

    series_other_sides = defaultdict(set)
    for resistor, resistance in LED_SERIES_OHMS.items():
        if resistance < 220:
            continue
        for resistor_id in by_part[resistor]:
            a, b = node(resistor_id, "A"), node(resistor_id, "B")
            if a != b:
                series_other_sides[a].add(b)
                series_other_sides[b].add(a)

    for component in project["components"]:
        part_id = component["part_id"]
        name = component["id"]
        part = parts[part_id]
        if part["geometry"] == "led":
            anode, cathode = node(name, "ANODE"), node(name, "CATHODE")
            limited = any(
                len(members[side]) == 2 and any(len(members[other]) >= 2 for other in series_other_sides[side])
                for side in (anode, cathode)
            )
            if anode == cathode or not limited:
                blockers.append(f"تحقّق من وجود مقاومة تسلسلية ملائمة للصمام {name}.")
            if (anode == ground or cathode in positive_rails
                    or (len(members[anode]) == 2 and ground in series_other_sides[anode])
                    or (len(members[cathode]) == 2 and set(positive_rails) & series_other_sides[cathode])):
                blockers.append(f"قطبية الصمام {name} تعاكس قطبية التغذية في المخطط.")
        elif part_id == "servo":
            if node(name, "VCC") not in external_positive or node(name, "GND") != ground:
                blockers.append(f"يتطلب السيرفو {name} تغذية مستقلة وأرضيًا مشتركًا مع Uno.")
            if node(name, "SIGNAL") not in uno_drive:
                blockers.append(f"إشارة السيرفو {name} غير متصلة بمنفذ Uno.")
        elif part_id in MOTOR_PARTS:
            motor = {node(name, "POS"), node(name, "NEG")}
            driver_outputs = {node(driver, f"OUT{number}") for driver in by_part["l298n_module"]
                              for number in range(1, 5)}
            low_side_outputs = {node(mosfet, "D") for mosfet in by_part["fqp30n06l"]
                                if node(mosfet, "S") == ground}
            bridge = motor <= driver_outputs
            low_side = node(name, "POS") in external_positive and node(name, "NEG") in low_side_outputs
            if len(motor) != 2 or motor & (uno_drive | uno_supply) or not (bridge or low_side):
                blockers.append(f"المحرّك {name} يحتاج دائرة قيادة وتغذية منفصلتين عن مخارج Uno.")
            if low_side and not any(node(diode, "A") == node(name, "NEG")
                                    and node(diode, "K") == node(name, "POS")
                                    for diode in by_part["diode_1n5819"]):
                blockers.append(f"صمام الحماية من الجهد العكسي للمحرّك {name} غير موجود أو معكوس.")
        elif part_id == "l298n_module":
            if node(name, "VS") not in external_positive or node(name, "GND") != ground:
                blockers.append(f"مُشغّل المحرّك {name} يحتاج تغذية محرّك مستقلة وأرضيًا مشتركًا.")
        elif part_id == "hc_sr04":
            if (node(name, "VCC") != node(uno, "5V") or node(name, "GND") != ground
                    or node(name, "ECHO") not in uno_drive or node(name, "TRIG") not in uno_drive):
                blockers.append(f"راجع تغذية 5 V وأرضي وإشارات المستشعر {name} مع Uno R3.")

    if any(by_part[part] for part in LED_SERIES_OHMS):
        warnings.append("قِس قيمة المقاومة وتحقّق من قطبية LED وانخفاض جهده قبل تغذية الدائرة.")
    if by_part["hc_sr04"]:
        warnings.append("المخطط لمستشعر HC-SR04 بجهد 5 V مع Uno R3؛ راجع ترتيب أطراف الوحدة الفعلية.")
    if by_part["piezo"]:
        warnings.append("استخدم عنصر بيزو سلبيًا منخفض التيار. تحقّق من مواصفاته قبل وصله بمنفذ Uno.")
    if by_part["servo"] or any(by_part[part] for part in MOTOR_PARTS):
        warnings.append("تحقّق من جهد المصدر المستقل وتيار التوقف وتصنيف الموصلات قبل تشغيل المحرّك.")
    if by_part["l298n_module"]:
        warnings.append("راجع وصلة تمكين منظم 5 V ووضع تغذية المنطق في إصدار L298N الفعلي.")
    return {"blockers_ar": blockers, "warnings_ar": warnings}
