"""Authoring helpers for the MechaVision offline catalog."""

PITCH_MM = 2.54
BREADBOARD_GEOMETRIES = {"led", "resistor", "button", "potentiometer"}
COLORS = {"power": "red", "ground": "black", "signal": "yellow"}
UNO_CORE_PINOUT = ("https://raw.githubusercontent.com/arduino/ArduinoCore-avr/1.8.6/variants/standard/pins_arduino.h",
                   "تعيين أطراف Arduino Uno في Arduino AVR core")
PIEZO_REFERENCE = ("https://raw.githubusercontent.com/arduino/arduino-examples/main/examples/02.Digital/toneMelody/toneMelody.ino",
                   "Arduino tone() sample and passive sounder wiring")
OPENED_SOURCES = {
    "https://github.com/adafruit/Adafruit-PN532",
    "https://github.com/adafruit/Adafruit_BME280_Library",
    "https://github.com/adafruit/Adafruit_BMP280_Library",
    "https://github.com/adafruit/Adafruit_TCS34725",
    "https://github.com/adafruit/DHT-sensor-library",
    "https://github.com/arduino-libraries/Servo",
    "https://raw.githubusercontent.com/arduino-libraries/Servo/1.2.2/examples/Sweep/Sweep.ino",
    "https://raw.githubusercontent.com/arduino-libraries/LiquidCrystal/master/examples/HelloWorld/HelloWorld.ino",
    "https://raw.githubusercontent.com/arduino/ArduinoCore-avr/1.8.6/cores/arduino/wiring_analog.c",
    "https://raw.githubusercontent.com/arduino/ArduinoCore-avr/1.8.6/libraries/SoftwareSerial/src/SoftwareSerial.h",
    "https://raw.githubusercontent.com/arduino/arduino-examples/main/examples/01.Basics/AnalogReadSerial/AnalogReadSerial.ino",
    "https://raw.githubusercontent.com/arduino/arduino-examples/main/examples/01.Basics/Blink/Blink.ino",
    "https://raw.githubusercontent.com/arduino/arduino-examples/main/examples/02.Digital/DigitalInputPullup/DigitalInputPullup.ino",
    UNO_CORE_PINOUT[0],
    PIEZO_REFERENCE[0],
}
LIBRARIES = {
    "Servo": ("1.2.2", ()),
    "LiquidCrystal": ("1.0.7", ()),
    "Adafruit BusIO": ("1.17.0", ()),
    "Adafruit Unified Sensor": ("1.1.15", ()),
    "Adafruit BMP280 Library": ("2.6.8", ("Adafruit Unified Sensor", "Adafruit BusIO")),
    "Adafruit BME280 Library": ("2.2.4", ("Adafruit Unified Sensor", "Adafruit BusIO")),
    "Adafruit PN532": ("1.3.4", ("Adafruit BusIO",)),
    "DHT sensor library": ("1.4.6", ("Adafruit Unified Sensor",)),
    "Wire": ("Arduino AVR core", ()),
    "SoftwareSerial": ("Arduino AVR core", ()),
}


def metric(x, y, z):
    return {axis: round(value / 1000, 6) for axis, value in zip("xyz", (x, y, z))}


def part(id, name_ar, name_en, geometry, size_mm, pins, source):
    width, height, depth = size_mm
    span = width * 0.85
    anchors = []
    for index, pin in enumerate(pins):
        if isinstance(pin, str):
            x = 0 if len(pins) == 1 else span * (index / (len(pins) - 1) - 0.5)
            anchor = metric(x, 1, -depth / 2)
        else:
            pin, *coordinates = pin
            anchor = metric(*coordinates)
        anchors.append({"id": pin, "position_m": anchor})
    return {
        "id": id,
        "name_ar": name_ar,
        "name_en": name_en,
        "geometry": geometry,
        "size_m": metric(width, height, depth),
        "pins": anchors,
        "sources": [source_entry(*source)],
    }


def source_entry(url, purpose):
    entry = {"url": url, "purpose": purpose}
    if url in OPENED_SOURCES:
        entry["accessed_on"] = "2026-11-19"
    return entry


def library_entries(names):
    entries = {}
    for name in names:
        version, dependencies = LIBRARIES[name]
        entries[name] = version
        for dependency in dependencies:
            entries[dependency] = LIBRARIES[dependency][0]
    return [{"name": name, "version": version} for name, version in entries.items()]


def project(id, name_ar, name_en, category, level, description_ar, components, connections,
            sources, *, aliases=(), supply=None, warnings=(), libraries=(), objectives=(),
            steps=None):
    wires = [
        {
            "id": f"wire_{index:02d}",
            "from": start,
            "to": end,
            "kind": kind,
            "color": COLORS[kind],
        }
        for index, (start, end, kind) in enumerate(connections, 1)
    ]
    if steps is None:
        steps = [
            (f"صِل {wire['from']} بالطرف {wire['to']}.", [index])
            for index, wire in enumerate(wires)
        ]
    steps = list(steps)
    steps.insert(0, ("افصل التغذية وثبّت القطع في المواضع المعروضة قبل التوصيل.", []))
    steps.append(("راجع التوصيلات واتجاه التغذية ثم حمّل البرنامج بعد موافقة المعلّم.", []))
    return {
        "id": id,
        "name_ar": name_ar,
        "name_en": name_en,
        "description_ar": description_ar,
        "aliases": list(aliases),
        "category": category,
        "level": level,
        "learning_objectives": list(objectives) or [description_ar],
        "board": "arduino:avr:uno",
        "components": [
            {"id": component[0], "part_id": component[1], "qty": 1,
             "placement": component[2] if len(component) == 3 else ""}
            for component in components
        ],
        "connections": wires,
        "assembly_steps": [
            {"step": number, "connection_ids": [wires[index]["id"] for index in indices],
             "instruction_ar": instruction}
            for number, (instruction, indices) in enumerate(steps, 1)
        ],
        "sketch_path": f"ArduinoProjects/{id}/{id}.ino",
        "sketch_resource": f"MechaVision/Sketches/{id}",
        "required_libraries": library_entries(libraries),
        "electrical_constraints": {
            "supply_notes_ar": supply or "غذِّ Arduino Uno من USB بجهد 5 V.",
            "warnings_ar": list(warnings) or ["افصل التغذية قبل تعديل التوصيلات."],
        },
        "sources": [source_entry(*item) for item in (*sources, UNO_CORE_PINOUT)],
        "verification": {
            "schema_valid": False,
            "pin_reviewed": False,
            "power_reviewed": False,
            "code_compiled": False,
            "hardware_tested": False,
            "ar_layout_reviewed": False,
            "status": "draft",
        },
    }


UNO_PINS = [
    *[(f"D{number}", 31 - number * PITCH_MM, 4, -24) for number in range(14)],
    *[(f"A{number}", 24 - number * PITCH_MM, 4, 24) for number in range(6)],
    ("5V", 0, 4, 24), ("3V3", -2.54, 4, 24), ("GND", 2.54, 4, 24),
    ("VIN", 7.62, 4, 24), ("RESET", -5.08, 4, 24),
]
PARTS = [
    part("uno", "لوحة أردوينو أونو", "Arduino Uno R3", "uno", (68.6, 15, 53.4), UNO_PINS,
         ("https://docs.arduino.cc/hardware/uno-rev3/", "Board dimensions and pinout")),
    part("led", "صمام ضوئي", "5 mm LED", "led", (5, 9, 5),
         [("ANODE", -1.27, 0, 0), ("CATHODE", 1.27, 0, 0)],
         ("https://www.arduino.cc/en/Tutorial/BuiltInExamples/Blink/", "LED polarity and resistor")),
    part("resistor", "مقاومة 220 أوم", "220 Ω resistor", "resistor", (5, 2.5, 2.5),
         [("A", -3.81, 0, 0), ("B", 3.81, 0, 0)],
         ("https://www.arduino.cc/en/Tutorial/BuiltInExamples/Blink/", "Series resistance")),
    part("button", "زر لحظي", "Momentary pushbutton", "button", (6, 5, 6),
         [("A", -2.54, 0, 0), ("B", 2.54, 0, 0)],
         ("https://docs.arduino.cc/built-in-examples/digital/InputPullupSerial/", "Active-low switch")),
    part("potentiometer", "مقاومة متغيرة", "10 kΩ potentiometer", "potentiometer", (10, 14, 10),
         [("VCC", -2.54, 0, 0), ("SIGNAL", 0, 0, 0), ("GND", 2.54, 0, 0)],
         ("https://docs.arduino.cc/built-in-examples/basics/AnalogReadSerial/", "Analog divider wiring")),
    part("piezo", "طنّان بيزو سلبي", "Passive piezo sounder", "buzzer", (12, 9, 12), ["POS", "NEG"],
         PIEZO_REFERENCE),
    part("hc_sr04", "مستشعر الموجات فوق الصوتية", "HC-SR04", "ultrasonic", (45, 20, 15),
         ["VCC", "TRIG", "ECHO", "GND"],
         ("https://cdn.sparkfun.com/datasheets/Sensors/Proximity/HCSR04.pdf", "Electrical and pin timing")),
    part("servo", "محرّك سيرفو صغير", "SG90 micro servo", "servo", (23, 29, 12),
         ["VCC", "SIGNAL", "GND"],
         ("https://docs.arduino.cc/learn/electronics/servo-motors/", "Servo signals and external power")),
    part("supply_5v", "مصدر منظم 5 فولت", "Regulated 5 V supply", "power", (45, 20, 30),
         ["5V", "GND"],
         ("https://docs.arduino.cc/learn/electronics/servo-motors/", "External supply and common ground")),
]

SUPPLEMENTAL_SOURCES = {
    "uno": UNO_CORE_PINOUT,
    "led": ("https://raw.githubusercontent.com/arduino/arduino-examples/main/examples/01.Basics/Blink/Blink.ino",
            "Arduino Blink sketch and circuit notes"),
    "potentiometer": ("https://raw.githubusercontent.com/arduino/arduino-examples/main/examples/01.Basics/AnalogReadSerial/AnalogReadSerial.ino",
                      "Arduino analog divider pin mapping"),
    "button": ("https://raw.githubusercontent.com/arduino/arduino-examples/main/examples/02.Digital/DigitalInputPullup/DigitalInputPullup.ino",
               "Arduino active-low switch wiring"),
    "servo": ("https://raw.githubusercontent.com/arduino-libraries/Servo/1.2.2/examples/Sweep/Sweep.ino",
              "Arduino Servo library sweep sample"),
}
for entry in PARTS:
    if source := SUPPLEMENTAL_SOURCES.get(entry["id"]):
        entry["sources"].append(source_entry(*source))
