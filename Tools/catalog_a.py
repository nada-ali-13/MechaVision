"""Arduino Uno projects from the first half of the implementation brief."""
from catalog_common import part, project


UNO = ("https://docs.arduino.cc/hardware/uno-rev3/", "حدود ومخطط أطراف Arduino Uno R3")
UNO_PINS = ("https://raw.githubusercontent.com/arduino/ArduinoCore-avr/1.8.6/variants/standard/pins_arduino.h", "خريطة GPIO في Arduino AVR core")
SONAR = ("https://cdn.sparkfun.com/datasheets/Sensors/Proximity/HCSR04.pdf", "مواصفات HC-SR04 وتوقيت نبضة Trigger")
SERVO = ("https://github.com/arduino-libraries/Servo", "مكتبة Servo ومثال التحكم بالزاوية")
SERVO_SPEC = ("https://www.towerpro.com.tw/product/sg90-7/", "مواصفات محرك SG90")
L298 = ("https://www.st.com/resource/en/datasheet/l298.pdf", "دوائر التغذية والتحكم والحماية لمتكاملة L298")
MOTOR_SPEC = ("https://www.adafruit.com/product/3777", "مثال لمحرك TT ذي علبة تروس")
REFLECTIVE = ("https://www.vishay.com/docs/83760/tcrt5000.pdf", "خصائص المرسل والمستقبل في TCRT5000")
BT = ("https://cdn.sparkfun.com/datasheets/Wireless/Bluetooth/HC-05.pdf", "مواصفات واجهة HC-05 ومستويات UART")
SOFTWARE_SERIAL = ("https://raw.githubusercontent.com/arduino/ArduinoCore-avr/1.8.6/libraries/SoftwareSerial/src/SoftwareSerial.h", "واجهة SoftwareSerial وترتيب طرفَي RX وTX")
LCD = ("https://raw.githubusercontent.com/arduino-libraries/LiquidCrystal/master/examples/HelloWorld/HelloWorld.ino", "مثال توصيل LCD بأربعة خطوط بيانات")
MOISTURE = ("https://wiki.dfrobot.com/Capacitive_Soil_Moisture_Sensor_SKU_SEN0193", "أطراف SEN0193 وطريقة المعايرة")
MOSFET = ("https://www.onsemi.com/pdf/datasheet/fqp30n06l-d.pdf", "مخطط أرجل MOSFET وتحمل التيار والجهد")
DIODE = ("https://www.vishay.com/docs/88525/1n5817.pdf", "قطبية وحدود صمام 1N5819")
PUMP = ("https://www.adafruit.com/product/4547", "مثال لمضخة غاطسة منخفضة الجهد 3–5V")
FLOAT = ("https://www.adafruit.com/product/2994", "مثال لمفتاح عوامة مغناطيسي")
REED = ("https://www.adafruit.com/product/375", "مفتاح باب مغناطيسي")
PIR = ("https://learn.adafruit.com/pir-passive-infrared-proximity-motion-sensor/using-a-pir", "توصيل PIR وتهيئة التشغيل")
BREAKBEAM = ("https://learn.adafruit.com/ir-breakbeam-sensors/arduino", "توصيل حاجز الأشعة تحت الحمراء ومنطق الخرج")
PHOTORESISTOR = ("https://learn.adafruit.com/photocells/using-a-photocell", "مقسم الجهد لحساس الضوء")
TMP36 = ("https://www.analog.com/media/en/technical-documentation/data-sheets/TMP35_36_37.pdf", "أرجل TMP36 ومعادلة جهد الخرج")
BME = ("https://learn.adafruit.com/adafruit-bme280-humidity-barometric-pressure-temperature-sensor-breakout/arduino-test", "ربط لوحة Adafruit BME280 عبر I²C")
BME_LIBRARY = ("https://github.com/adafruit/Adafruit_BME280_Library", "مكتبة BME280 وقراءات الضغط والرطوبة")
DHT = ("https://learn.adafruit.com/dht/connecting-to-a-dhtxx-sensor", "أطراف DHT11 ومقاومة السحب")
DHT_LIBRARY = ("https://github.com/adafruit/DHT-sensor-library", "مكتبة DHT وفاصل القراءات")
PULLUP = ("https://docs.arduino.cc/tutorials/generic/digital-input-pullup/", "مقاومة السحب الداخلية ومنطق المفتاح")
ANALOG_READ = ("https://raw.githubusercontent.com/arduino/ArduinoCore-avr/1.8.6/cores/arduino/wiring_analog.c", "تنفيذ قراءة الجهد التماثلي في Arduino AVR core")
LED_PWM = ("https://docs.arduino.cc/tutorials/generic/fading/", "استخدام PWM مع LED ومقاومة على التوالي")
MOTOR_POWER = (
    "شغّل Uno من USB. استخدم حاملة 6 خلايا NiMH (7.2 V اسمياً) لمداخل قدرة وحدة L298N "
    "مع محركي TT متوافقين بجهد 3–6 V وتيار توقف دون حدود الوحدة، مع الأرضي المشترك. "
    "انزع وصلتي ENA وENB، وعطّل منظم 5 V بالوصلة 5V-EN قبل إدخال 5 V المنطقي من Uno. "
    "اتبع أسماء الأطراف المطبوعة على الوحدة لأن توزيعها الفيزيائي يختلف بين اللوحات."
)
ROBOT_WARNING = "ارفع العجلات في الاختبار الأول، وابدأ بسرعة منخفضة. افصل القدرة قبل تبديل طرفي محرك لتصحيح الاتجاه."
SERVO_POWER = "استخدم مصدر 5 V منظّمًا ومستقلًا ملائمًا لتيار توقف SG90، ووحّد الأرضي. غذِّ Uno من USB."
LCD_POWER = "غذِّ Uno من USB. اضبط مقاومة التباين بحيث تظهر الحروف. غذِّ إضاءة LCD الخلفية عبر مقاومة 220 Ω."
PUMP_POWER = (
    "غذِّ Uno من USB والحمل من مصدر 5 V منفصل محدود التيار، بوحدة تقبل 5 V وتيار توقف لا يتجاوز 0.5 A. "
    "اربط الأرضي فقط بين المصدرين. ضع 1N5819 على التوازي مع الحمل والكاثود ناحية الموجب."
)
WATER_WARNING = "ضع خزان الماء خارج منطقة الإلكترونيات. افصل الطاقة قبل تعديل الأسلاك، ولا توصل أي جزء بكهرباء المنزل."
BEAM_NOTE = "حاذِ المرسل والمستقبل. افحص أن خرج المستقبل المسحوب للأعلى HIGH وهو مكشوف وLOW عند حجب الشعاع."


def resistor(part_id, name):
    return part(part_id, f"مقاومة {name}", f"{name} resistor", "resistor", (6, 2.5, 2.5),
                [("A", -2.54, 0, 0), ("B", 2.54, 0, 0)], LED_PWM)


def colored_led(color, name):
    return part(f"led_{color}", f"LED {name}", f"{color.title()} LED", "led", (5, 8.5, 5),
                [("ANODE", -1.27, 0, 0), ("CATHODE", 1.27, 0, 0)], LED_PWM)


def header(*pins):
    return [(pin, (i - (len(pins) - 1) / 2) * 2.54, 0, 0) for i, pin in enumerate(pins)]


PARTS = [
    resistor("resistor_220", "220 Ω"),
    resistor("resistor_1k", "1 kΩ"),
    resistor("resistor_2k", "2 kΩ"),
    resistor("resistor_10k", "10 kΩ"),
    resistor("resistor_100k", "100 kΩ"),
    colored_led("red", "أحمر"),
    colored_led("yellow", "أصفر"),
    colored_led("green", "أخضر"),
    part("dc_supply", "مصدر جهد مستمر منخفض", "Low-voltage DC supply", "power_supply",
         (54, 19, 42), ["POS", "NEG"], UNO),
    part("l298n_module", "وحدة قيادة المحركات L298N", "L298N dual motor module", "motor_driver",
         (44, 25, 44), ["VS", "GND", "5V", "ENA", "IN1", "IN2", "IN3", "IN4", "ENB",
                         "OUT1", "OUT2", "OUT3", "OUT4"], L298),
    part("tt_motor", "محرك TT مع علبة تروس", "TT gear motor", "dc_motor", (70, 24, 23), ["POS", "NEG"], MOTOR_SPEC),
    part("tcrt5000_module", "وحدة عاكس TCRT5000 مع LM393", "TCRT5000/LM393 reflectance module",
         "sensor", (34, 12, 14), ["VCC", "GND", "DO", "AO"], REFLECTIVE),
    part("hc05_breakout", "وحدة Bluetooth HC-05", "HC-05 Bluetooth breakout", "sensor", (37, 8, 16),
         ["VCC", "GND", "TXD", "RXD", "STATE", "KEY"], BT),
    part("lcd1602", "شاشة LCD 1602", "HD44780 16×2 LCD", "display", (80, 13, 36),
         header("VSS", "VDD", "VO", "RS", "RW", "E", "D0", "D1", "D2", "D3", "D4", "D5", "D6", "D7", "A", "K"), LCD),
    part("float_switch", "مفتاح عوامة مستشعر الامتلاء", "Float switch", "sensor", (22, 54, 22), ["A", "B"], FLOAT),
    part("dc_pump", "مضخة ماء غاطسة 3–5 V", "3–5 V submersible pump", "dc_motor",
         (46, 34, 34), ["POS", "NEG"], PUMP),
    part("dc_fan", "مروحة 5 V مزودة بحاجز", "Guarded 5 V fan", "dc_motor", (40, 12, 40),
         ["POS", "NEG"], MOSFET),
    part("fqp30n06l", "ترانزستور MOSFET FQP30N06L", "FQP30N06L logic-level MOSFET", "transistor",
         (10, 16, 4.6), header("G", "D", "S"), MOSFET),
    part("diode_1n5819", "صمام حماية 1N5819", "1N5819 flyback diode", "diode",
         (5, 2.7, 2.7), [("A", -2.54, 0, 0), ("K", 2.54, 0, 0)], DIODE),
    part("moisture_sen0193", "حساس رطوبة تربة سعوي SEN0193", "SEN0193 capacitive soil sensor",
         "sensor", (98, 5, 23), ["VCC", "GND", "AO"], MOISTURE),
    part("photoresistor", "حساس الضوء LDR", "Photoresistor", "sensor", (5, 4, 5),
         [("A", -1.27, 0, 0), ("B", 1.27, 0, 0)], PHOTORESISTOR),
    part("pir_hcsr501", "حساس حركة HC-SR501", "HC-SR501 PIR motion sensor", "sensor", (32, 25, 24),
         ["VCC", "OUT", "GND"], PIR),
    part("reed_switch", "مفتاح مغناطيسي قصبي", "Normally open reed switch", "sensor", (30, 10, 12),
         ["A", "B"], REED),
    part("toggle_switch", "مفتاح تثبيت ثنائي الطرف", "Latching SPST switch", "switch", (12, 10, 7),
         ["A", "B"], PULLUP),
    part("breakbeam_tx", "مرسل حاجز الأشعة تحت الحمراء", "IR breakbeam transmitter", "sensor", (13, 11, 8),
         ["VCC", "GND"], BREAKBEAM),
    part("breakbeam_rx", "مستقبل حاجز الأشعة تحت الحمراء", "IR breakbeam receiver", "sensor", (13, 11, 8),
         ["VCC", "OUT", "GND"], BREAKBEAM),
    part("adafruit_bme280", "لوحة Adafruit BME280", "Adafruit BME280 breakout", "sensor", (25, 5, 19),
         ["VIN", "3VO", "GND", "SCK", "SDO", "SDI", "CS"], BME),
    part("dht11", "حساس DHT11 رباعي الأرجل", "DHT11 four-pin sensor", "sensor", (16, 13, 6),
         header("VCC", "DATA", "NC", "GND"), DHT),
    part("tmp36", "مستشعر الحرارة TMP36", "TMP36 TO-92 sensor", "sensor", (5, 5, 5),
         header("VCC", "VOUT", "GND"), TMP36),
    part("electrode", "قطب من الفولاذ المقاوم للصدأ", "Stainless steel strip electrode",
         "probe", (42, 1, 6), ["TERMINAL"], ANALOG_READ),
]


UNO_PART = ("uno1", "uno")
SONAR_PART = ("sonar", "hc_sr04")
SERVO_PARTS = [("servo", "servo"), ("servo_supply", "dc_supply")]
LCD_PARTS = [("lcd", "lcd1602"), ("contrast", "potentiometer"), ("backlight", "resistor_220")]
MOTOR_PARTS = [("motor_supply", "dc_supply"), ("driver", "l298n_module"),
               ("motor_l", "tt_motor"), ("motor_r", "tt_motor")]
MOISTURE_PART = ("soil", "moisture_sen0193")
PIR_PART = ("pir", "pir_hcsr501")
BUZZER_PART = ("piezo", "piezo")
PUMP_PARTS = [("motor_supply", "dc_supply"), ("mosfet", "fqp30n06l", "breadboard"),
              ("motor", "dc_pump"), ("flyback", "diode_1n5819", "breadboard"),
              ("gate_series", "resistor_220"), ("gate_pull", "resistor_10k")]


def powered(instance, positive="VCC"):
    return [("uno1.5V", f"{instance}.{positive}", "power"), ("uno1.GND", f"{instance}.GND", "ground")]


def sonar(trigger=7, echo=8):
    return ("ثبّت HC-SR04 خارج البورد، ثم صِل التغذية وTRIG وECHO حسب الأطراف.", powered("sonar") + [
        (f"uno1.D{trigger}", "sonar.TRIG", "signal"), ("sonar.ECHO", f"uno1.D{echo}", "signal")
    ])


def servo():
    return ("صِل مصدر 5 V الخارجي بمحرك SG90، ووحّد الأرضي، ثم صِل إشارة التحكم D9.", [
        ("servo_supply.POS", "servo.VCC", "power"), ("servo_supply.NEG", "servo.GND", "ground"),
        ("servo_supply.NEG", "uno1.GND", "ground"), ("uno1.D9", "servo.SIGNAL", "signal"),
    ])


def lcd():
    return [
        ("صِل تغذية الشاشة وRW إلى الأرضي، واضبط VO بمقاومة التباين، وصِل الإضاءة عبر 220 Ω.", [
            ("uno1.5V", "lcd.VDD", "power"), ("uno1.GND", "lcd.VSS", "ground"), ("uno1.GND", "lcd.RW", "ground"),
            ("uno1.5V", "contrast.VCC", "power"), ("uno1.GND", "contrast.GND", "ground"),
            ("contrast.SIGNAL", "lcd.VO", "signal"), ("uno1.5V", "backlight.A", "power"),
            ("backlight.B", "lcd.A", "power"), ("lcd.K", "uno1.GND", "ground"),
        ]),
        ("صِل RS وE وخطوط البيانات الأربعة D4 إلى D7. اترك D0 إلى D3 غير موصولة.", [
            ("uno1.D12", "lcd.RS", "signal"), ("uno1.D11", "lcd.E", "signal"),
            ("uno1.D5", "lcd.D4", "signal"), ("uno1.D4", "lcd.D5", "signal"),
            ("uno1.D3", "lcd.D6", "signal"), ("uno1.D2", "lcd.D7", "signal"),
        ]),
    ]


def motor_driver():
    return [
        ("افصل الطاقة. انزع وصلات ENA وENB و5V-EN، ثم صِل قدرة المحركات والمنطق والأرضي المشترك.", [
            ("motor_supply.POS", "driver.VS", "power"), ("motor_supply.NEG", "driver.GND", "ground"),
            ("uno1.GND", "driver.GND", "ground"), ("uno1.5V", "driver.5V", "power"),
        ]),
        ("صِل خطوط PWM والاتجاه، ثم صِل المحرك الأيسر إلى OUT1/OUT2 والأيمن إلى OUT3/OUT4.", [
            ("uno1.D5", "driver.ENA", "signal"), ("uno1.D7", "driver.IN1", "signal"),
            ("uno1.D8", "driver.IN2", "signal"), ("uno1.D6", "driver.ENB", "signal"),
            ("uno1.D9", "driver.IN3", "signal"), ("uno1.D10", "driver.IN4", "signal"),
            ("driver.OUT1", "motor_l.POS", "signal"), ("driver.OUT2", "motor_l.NEG", "signal"),
            ("driver.OUT3", "motor_r.POS", "signal"), ("driver.OUT4", "motor_r.NEG", "signal"),
        ]),
    ]


def motor_switch():
    return [
        ("صِل مسار القدرة مع MOSFET، واربط سالب المصدر بأرضي Uno. اتجاه خط الصمام الأبيض نحو الموجب.", [
            ("motor_supply.POS", "motor.POS", "power"), ("motor_supply.POS", "flyback.K", "power"),
            ("motor.NEG", "mosfet.D", "signal"), ("flyback.A", "mosfet.D", "signal"),
            ("motor_supply.NEG", "mosfet.S", "ground"), ("motor_supply.NEG", "uno1.GND", "ground"),
        ]),
        ("صِل D5 إلى البوابة عبر 220 Ω، وضع 10 kΩ من البوابة إلى الأرضي ليظل المحرك مطفأ أثناء إعادة الضبط.", [
            ("uno1.D5", "gate_series.A", "signal"), ("gate_series.B", "mosfet.G", "signal"),
            ("mosfet.G", "gate_pull.A", "signal"), ("gate_pull.B", "uno1.GND", "ground"),
        ]),
    ]


def soil():
    return ("صِل تغذية SEN0193 وخرجه التماثلي A0. ضع الجزء الحساس فقط في التربة.", powered("soil") + [
        ("soil.AO", "uno1.A0", "signal"),
    ])


def switch(instance, destination, instructions):
    return (instructions, [(f"{instance}.A", f"uno1.D{destination}", "signal"), (f"{instance}.B", "uno1.GND", "ground")])


def piezo(pin):
    return ("صِل الصفارة الكهروضغطية السلبية؛ الطرف السالب إلى GND.", [
        (f"uno1.D{pin}", "piezo.POS", "signal"), ("piezo.NEG", "uno1.GND", "ground"),
    ])


def led_parts(instance, color=None):
    return [(instance, f"led_{color}" if color else "led"), (f"{instance}_r", "resistor_220")]


def led(instance, pin, instruction):
    return (instruction, [
        (f"uno1.D{pin}", f"{instance}_r.A", "signal"), (f"{instance}_r.B", f"{instance}.ANODE", "signal"),
        (f"{instance}.CATHODE", "uno1.GND", "ground"),
    ])


def beams(*instances):
    return [(f"{name}_tx", "breakbeam_tx") for name in instances] + [
        (f"{name}_rx", "breakbeam_rx") for name in instances
    ]


def beam(name, pin, instruction):
    return (instruction, powered(f"{name}_tx") + powered(f"{name}_rx") + [
        (f"{name}_rx.OUT", f"uno1.D{pin}", "signal"),
    ])


OBJECTIVES = {
    "ultrasonic_radar": "ربط زاوية المسح بزمن رحلة الصدى وتمثيل القراءات كأزواج زاوية ومسافة",
    "obstacle_avoiding_car": "التمييز بين عائق قريب وغياب الصدى ثم اختيار حركة مناسبة لكل حالة",
    "line_follower": "معايرة حساسي الانعكاس وتصحيح اتجاه العربة بسرعتين مختلفتين",
    "bluetooth_car": "تحويل أوامر UART إلى حركة وإيقاف المحركات عند فقدان الإشارة",
    "smart_dustbin": "ربط قياس المسافة بحالة الغطاء وإغلاقه بمؤقت مستقل",
    "water_tank_level": "تحويل مسافة الصدى إلى نسبة امتلاء باستخدام نقطتي معايرة",
    "overflow_alarm": "إزالة ارتداد مفتاح العوامة وتمثيل حد الامتلاء بضوء وصوت",
    "timed_water_pump": "التحكم بحمل قدرة عبر MOSFET وتحديد زمن العمل والراحة",
    "automatic_irrigation": "معايرة رطوبة التربة وتطبيق ري متقطع يراعي انتشار الماء",
    "soil_moisture_station": "ترشيح قراءات تماثلية وعرض النسبة والقراءة الخام معًا",
    "smart_street_light": "تحويل قراءة مقسم الجهد إلى سطوع LED عبر PWM",
    "motion_activated_light": "التفريق بين الإشارة اللحظية ومدة الإضاءة المحسوبة بعدها",
    "pir_security_alarm": "إنشاء حالات تعطيل وتسليح وإنذار دائم باستخدام مفتاح وحساس حركة",
    "door_window_alarm": "استنتاج وضع الباب من مفتاح مغناطيسي وحفظ الإنذار حتى الإقرار",
    "automatic_parking_gate": "إبقاء نموذج البوابة مفتوحًا أثناء حجب الشعاع وإغلاقه بعد مهلة",
    "parking_slot_detector": "جمع قراءتين رقميتين وعرض عدد الأماكن المتاحة وحالة كل مكان",
    "pedestrian_traffic_light": "تطبيق آلة حالات لا تمنح المرور للسيارات والمشاة في الوقت نفسه",
    "ir_object_counter": "عد انتقالات إشارة الشعاع بعد ترشيحها بدل عد كل قراءة",
    "bidirectional_people_counter": "استنتاج الاتجاه من ترتيب إشارتين واستبعاد العبور غير المكتمل",
    "digital_distance_meter": "حساب المسافة من زمن رحلة الصدى وفصل القراءات الصالحة عن غيرها",
    "obstacle_alert_demo": "تمثيل انخفاض المسافة بزيادة وتيرة النبضات الصوتية",
    "mini_weather_station": "جمع ثلاث قراءات عبر I²C وتحويل الضغط إلى hPa وتصدير سجل CSV",
    "room_climate_monitor": "قراءة الحرارة والرطوبة باحترام فترة الحساس واكتشاف فشل القياس",
    "temperature_controlled_fan": "تطبيق عتبتين مختلفتين للتشغيل والإيقاف لتثبيت استجابة المروحة",
    "water_leak_alarm": "قياس تغير الموصلية بنبضات قصيرة والتمييز بين حالتي البلل والجفاف",
}


def build(project_id, name_ar, name_en, category, level, description, components, sections, sources, **options):
    connections = []
    steps = []
    for instruction, section_wires in sections:
        start = len(connections)
        connections.extend(section_wires)
        steps.append((instruction, list(range(start, len(connections)))))
    return project(project_id, name_ar, name_en, category, level, description, [UNO_PART] + components,
                   connections, [UNO, UNO_PINS] + sources, steps=steps, objectives=(OBJECTIVES[project_id],), **options)


PROJECTS = [
    build("ultrasonic_radar", "رادار بالموجات فوق الصوتية", "Ultrasonic Radar", "measurement", "intermediate",
          "يدور مستشعر المسافة ويكتب أزواج الزاوية والمسافة بالسنتيمتر على Serial بسرعة 9600. تشير القيمة ‎-1 إلى غياب الصدى.",
          [SONAR_PART] + SERVO_PARTS, [sonar(), servo()], [SONAR, SERVO, SERVO_SPEC],
          aliases=("رادار", "سونار"), supply=SERVO_POWER, libraries=("Servo",),
          warnings=("ثبّت الحساس على ذراع خفيفة واختبر زوايا الحركة قبل الربط الميكانيكي.",)),
    build("obstacle_avoiding_car", "سيارة تتجنّب العوائق", "Obstacle Avoiding Car", "robotics", "intermediate",
          "تتقدم سيارة بمحركين عند خلو الطريق، وتقف عند غياب قراءة الصدى، وتنعطف عند اكتشاف جسم أقرب من 25 سم.",
          MOTOR_PARTS + [SONAR_PART], motor_driver() + [sonar(11, 12)], [L298, MOTOR_SPEC, SONAR],
          aliases=("سيارة ذاتية", "robot car"), supply=MOTOR_POWER, warnings=(ROBOT_WARNING,)),
    build("line_follower", "سيارة تتبع الخط", "Line Follower Robot", "robotics", "intermediate",
          "تتبع عربة خطًا داكنًا باستخدام حساسين انعكاسيين مضبوطين على خرج LOW فوق الخط، وتتوقف إذا خرج كلاهما عنه.",
          MOTOR_PARTS + [("left", "tcrt5000_module"), ("right", "tcrt5000_module")], motor_driver() + [
              ("صِل خرجي DO إلى A0 وA1. ضع الحساسين فوق خط عريض بحيث يراه كلاهما وهما متمركزان.",
               powered("left") + powered("right") + [
                   ("left.DO", "uno1.A0", "signal"), ("right.DO", "uno1.A1", "signal"),
               ]),
          ], [L298, MOTOR_SPEC, REFLECTIVE], aliases=("روبوت تتبع الخط",), supply=MOTOR_POWER,
          warnings=(ROBOT_WARNING, "اختر وحدة يكون DO فيها LOW فوق الخط أو عدّل ثابت DARK بعد اختبار القطبية.")),
    build("bluetooth_car", "سيارة تتحكم بها بالبلوتوث", "Bluetooth Controlled Car", "robotics", "advanced",
          "تستجيب العربة لأوامر F/B/L/R/S من تطبيق طرفية Bluetooth Classic على Android بسرعة UART ‏9600. كرّر أوامر الحركة أسرع من كل 500 ms وإلا توقفت.",
          MOTOR_PARTS + [("bluetooth", "hc05_breakout"), ("divider_top", "resistor_1k"), ("divider_bottom", "resistor_2k")],
          motor_driver() + [
              ("صِل TXD إلى D2. صِل D3 إلى RXD عبر مقسم 1 kΩ و2 kΩ ليصل إلى RXD نحو 3.3 V.",
               powered("bluetooth") + [
                   ("bluetooth.TXD", "uno1.D2", "signal"), ("uno1.D3", "divider_top.A", "signal"),
                   ("divider_top.B", "bluetooth.RXD", "signal"), ("bluetooth.RXD", "divider_bottom.A", "signal"),
                   ("divider_bottom.B", "uno1.GND", "ground"),
               ]),
          ], [L298, MOTOR_SPEC, BT, SOFTWARE_SERIAL],
          libraries=("SoftwareSerial",), supply=MOTOR_POWER + " استخدم لوحة HC-05 الحاملة ذات مدخل تغذية 5 V؛ إشارة RXD ‏3.3 V.",
          warnings=(ROBOT_WARNING, "اختبر أمر S وفقدان الاتصال قبل إنزال المركبة إلى الأرض.")),
    build("smart_dustbin", "سلة مهملات ذكية", "Smart Dustbin", "automation", "beginner",
          "عند اقتراب جسم من الحساس يرفع محرك السيرفو غطاء نموذج خفيف ويعيده بعد غياب الجسم لمدة 2.2 ثانية.",
          [SONAR_PART] + SERVO_PARTS, [sonar(), servo()], [SONAR, SERVO, SERVO_SPEC],
          aliases=("سلة تلقائية", "automatic trash bin"), supply=SERVO_POWER, libraries=("Servo",),
          warnings=("استخدم غطاء ورقيًا خفيفًا. جرّب النهايتين بلا غطاء لتفادي الانحشار.",)),
    build("water_tank_level", "مقياس مستوى خزان المياه", "Water Tank Level Monitor", "environment", "intermediate",
          "يقيس المسافة من أعلى نموذج الخزان ويعرض النسبة على LCD بين نقطتي خزان فارغ وممتلئ. عدّل EMPTY_CM وFULL_CM قبل التشغيل.",
          [SONAR_PART] + LCD_PARTS, [sonar()] + lcd(), [SONAR, LCD],
          supply=LCD_POWER, libraries=("LiquidCrystal",),
          warnings=(WATER_WARNING, "أبقِ HC-SR04 جافًا وثابتًا فوق سطح الماء، وعاير FULL_CM فوق حد الحساس الأدنى.")),
    build("overflow_alarm", "إنذار امتلاء خزان الماء", "Water Overflow Alarm", "environment", "beginner",
          "يضيء المؤشر وتصدر الصفارة نغمة متقطعة عندما يغلق مفتاح العوامة عند مستوى الامتلاء.",
          [("float", "float_switch"), BUZZER_PART] + led_parts("alarm", "red"), [
              switch("float", 2, "صِل العوامة بين D2 والأرضي واضبط وضعها لتغلق عند ارتفاعها."),
              piezo(8), led("alarm", 9, "صِل LED الأحمر إلى D9 عبر 220 Ω."),
          ], [FLOAT, PULLUP, LED_PWM], warnings=(WATER_WARNING, "هذا نموذج تعليمي للامتلاء.")),
    build("timed_water_pump", "مضخة مياه منخفضة الجهد بمؤقت", "Timed Low-Voltage Water Pump", "automation", "intermediate",
          "يشغّل ضغط زر المضخة لثلاث ثوانٍ ثم يمنع إعادة التشغيل لمدة عشر ثوانٍ.",
          PUMP_PARTS + [("start", "button")], motor_switch() + [
              switch("start", 2, "صِل زر البدء بين D2 وGND. استعمل طرفين على جهتين مختلفتين من الزر."),
          ], [PUMP, MOSFET, DIODE, PULLUP], supply=PUMP_POWER,
          warnings=(WATER_WARNING, "لا تشغّل المضخة جافة أو خارج مواصفات الشركة.")),
    build("automatic_irrigation", "ري نباتات آلي", "Automatic Plant Irrigation", "environment", "advanced",
          "يسقي النبات على دفعات قصيرة عندما تقل رطوبة التربة المعايرة، ويترك دقيقة لتوزيع الماء قبل قرار الري التالي.",
          PUMP_PARTS + [MOISTURE_PART], motor_switch() + [soil()], [PUMP, MOSFET, DIODE, MOISTURE],
          supply=PUMP_POWER, warnings=(WATER_WARNING, "عاير قيم DRY_ADC وWET_ADC والمضخة مفصولة. راقب التشغيل ولا تترك المضخة تجف.")),
    build("soil_moisture_station", "محطة مراقبة رطوبة التربة", "Soil Moisture Monitoring Station",
          "environment", "intermediate", "تعرض الشاشة متوسط قراءة الحساس والنسبة النسبية بعد المعايرة. سجّل قراءتي الجفاف والرطوبة واضبط ثوابتهما.",
          [MOISTURE_PART] + LCD_PARTS, [soil()] + lcd(), [MOISTURE, LCD],
          supply=LCD_POWER, libraries=("LiquidCrystal",), warnings=(WATER_WARNING,)),
    build("smart_street_light", "إنارة شارع متدرجة", "Adaptive Street Lighting", "automation", "beginner",
          "يزداد سطوع LED للنموذج تدريجيًا مع انخفاض الضوء على حساس LDR باستخدام PWM.",
          [("ldr", "photoresistor", "breadboard"), ("divider", "resistor_10k")] + led_parts("lamp", "yellow"), [
              ("صِل LDR من 5 V إلى نقطة A0، ثم مقاومة 10 kΩ من A0 إلى GND.", [
                  ("uno1.5V", "ldr.A", "power"), ("ldr.B", "uno1.A0", "signal"),
                  ("uno1.A0", "divider.A", "signal"), ("divider.B", "uno1.GND", "ground"),
              ]),
              led("lamp", 5, "صِل LED بمخرج PWM ‏D5 عبر 220 Ω."),
          ], [PHOTORESISTOR, LED_PWM], aliases=("إنارة شوارع ذكية",)),
    build("motion_activated_light", "إنارة تلقائية بالحركة", "Motion-Activated Lighting", "automation", "beginner",
          "يشغّل حساس PIR LED لخمس ثوانٍ بعد انتهاء إشارة الحركة، بعد إحماء الحساس عند التشغيل.",
          [PIR_PART] + led_parts("lamp"), [
              ("صِل PIR ذي التغذية 5 V ثم OUT إلى D2 وانتظر استقرار الحساس.", powered("pir") + [
                  ("pir.OUT", "uno1.D2", "signal"),
              ]),
              led("lamp", 9, "صِل LED على D9 عبر 220 Ω."),
          ], [PIR, LED_PWM], warnings=("اقتصر على LED منخفض الجهد في نموذج الإنارة.",)),
    build("pir_security_alarm", "إنذار حركة قابل للتسليح", "PIR Home Security Alarm", "safety", "intermediate",
          "يمنحك مفتاح التسليح خمس ثوانٍ للمغادرة، ثم تثبّت أي حركة إنذار النموذج حتى تعطيل المفتاح.",
          [PIR_PART, ("arm", "toggle_switch"), BUZZER_PART] + led_parts("armed", "red"), [
              ("صِل حساس PIR. خرج الحركة OUT يدخل إلى D2.", powered("pir") + [("pir.OUT", "uno1.D2", "signal")]),
              switch("arm", 4, "صِل مفتاح التسليح الثابت بين D4 والأرضي."),
              piezo(8), led("armed", 9, "صِل مؤشر التسليح إلى D9 عبر 220 Ω."),
          ], [PIR, PULLUP, LED_PWM], warnings=("هذا نموذج تعليمي لحساس الحركة، ولا يعتمد عليه لحماية الأشخاص أو الممتلكات.",)),
    build("door_window_alarm", "إنذار فتح باب أو نافذة", "Door and Window Alarm", "safety", "beginner",
          "يسجّل فتح النموذج عند ابتعاد المغناطيس عن مفتاح Reed، ويظل الإنذار حتى يُغلق الباب ويُضغط زر الإقرار.",
          [("door", "reed_switch"), ("ack", "button"), BUZZER_PART] + led_parts("alarm", "red"), [
              switch("door", 2, "ثبّت المغناطيس قرب المفتاح في وضع الإغلاق. صِل مفتاح Reed بين D2 والأرضي."),
              switch("ack", 4, "صِل زر الإقرار بين D4 والأرضي."), piezo(8),
              led("alarm", 9, "صِل مؤشر الإنذار إلى D9 عبر 220 Ω."),
          ], [REED, PULLUP, LED_PWM], warnings=("نفّذ التجربة على إطار مصغّر واختبر حالات الباب المفتوح عند بدء التشغيل.",)),
    build("automatic_parking_gate", "بوابة موقف سيارات تلقائية", "Automatic Parking Gate", "automation",
          "intermediate", "ترتفع بوابة نموذجية عند حجب الشعاع، وتغلق بعد ثانيتين من انكشافه.",
          beams("gate") + SERVO_PARTS, [
              beam("gate", 2, "صِل مرسل ومستقبل الشعاع على جانبي مسار السيارة. صِل OUT إلى D2."),
              servo(),
          ], [BREAKBEAM, SERVO, SERVO_SPEC], libraries=("Servo",),
          supply=SERVO_POWER, warnings=(BEAM_NOTE, "استخدم ذراعًا ورقية خفيفة؛ لا تركّب النموذج على بوابة حقيقية.")),
    build("parking_slot_detector", "محدد الأماكن المتاحة في موقف", "Parking Slot Detector", "automation",
          "intermediate", "تكشف الشاشة حالة مكانَي موقف سيارة مصغّر وتحسب عدد الأماكن الخالية.",
          beams("slot_a", "slot_b") + LCD_PARTS, [
              beam("slot_a", 6, "حاذِ زوج الشعاع الأول عبر المكان A، وصِل خرجه إلى D6."),
              beam("slot_b", 7, "كرر للمكان B وصِل الخرج إلى D7. وجّه الشعاعين بحيث لا يتداخلان."),
          ] + lcd(), [BREAKBEAM, LCD], supply=LCD_POWER, libraries=("LiquidCrystal",), warnings=(BEAM_NOTE,)),
    build("pedestrian_traffic_light", "إشارة معبر مشاة", "Pedestrian Traffic Light", "automation", "intermediate",
          "ينفذ نموذج الإشارة حالات متتابعة من الضوء الأخضر للسيارات إلى عبور المشاة، مع فترة حمراء للطرفين قبل العبور وبعده.",
          [("request", "button")] + led_parts("car_red", "red") + led_parts("car_yellow", "yellow") +
          led_parts("car_green", "green") + led_parts("walk_red", "red") + led_parts("walk_green", "green"), [
              switch("request", 2, "صِل زر طلب العبور بين D2 وGND."),
              led("car_red", 3, "صِل LED السيارات الأحمر إلى D3 عبر 220 Ω."),
              led("car_yellow", 4, "صِل LED السيارات الأصفر إلى D4 عبر 220 Ω."),
              led("car_green", 5, "صِل LED السيارات الأخضر إلى D5 عبر 220 Ω."),
              led("walk_red", 6, "صِل LED المشاة الأحمر إلى D6 عبر 220 Ω."),
              led("walk_green", 7, "صِل LED المشاة الأخضر إلى D7 عبر 220 Ω."),
          ], [PULLUP, LED_PWM], warnings=("هذا نموذج مكتبي لتعلم آلة الحالات.",)),
    build("ir_object_counter", "عداد الأجسام بالأشعة تحت الحمراء", "IR Object Counter", "measurement", "beginner",
          "يزيد العداد مرة واحدة عند بدء حجب الشعاع ويطبع العدد في Serial بسرعة 9600؛ يصفّره زر الإعادة.",
          beams("count") + [("reset", "button")], [
              beam("count", 2, "صِل زوج الشعاع عبر مسار قطعة متحركة، ووصل OUT إلى D2."),
              switch("reset", 4, "صِل زر التصفير بين D4 وGND."),
          ], [BREAKBEAM, PULLUP], warnings=(BEAM_NOTE,)),
    build("bidirectional_people_counter", "عداد زوار باتجاهين", "Bidirectional People Counter", "measurement",
          "advanced", "يستخدم ترتيب حجب شعاعين لتحديد الدخول أو الخروج، ويعرض الحصيلة عبر Serial بسرعة 9600.",
          beams("outside", "inside"), [
              beam("outside", 2, "صِل حاجز الشعاع الخارجي A إلى D2."),
              beam("inside", 3, "صِل حاجز الشعاع الداخلي B إلى D3. قرّبه من A بحيث يحجب الجسم شعاعين لحظة العبور."),
          ], [BREAKBEAM, PULLUP], warnings=(BEAM_NOTE, "اختبر مرور نموذج جسم واحد في كل مرة.")),
    build("digital_distance_meter", "جهاز قياس مسافة رقمي", "Digital Distance Meter", "measurement", "intermediate",
          "يعرض مسافة الصدى بالسنتيمتر حتى منزلة عشرية، مع رسالة عند انقطاع القياس أو تجاوزه نطاق 2 إلى 400 سم.",
          [SONAR_PART] + LCD_PARTS, [sonar()] + lcd(), [SONAR, LCD], supply=LCD_POWER, libraries=("LiquidCrystal",)),
    build("obstacle_alert_demo", "نموذج صوتي للتنبيه من العوائق", "Obstacle Alert Prototype", "safety", "beginner",
          "تزداد وتيرة صوت صفارة النموذج عند اقتراب عائق ضمن مدى 2 إلى 80 سم.",
          [SONAR_PART, BUZZER_PART], [sonar(), piezo(9)], [SONAR],
          aliases=("عصا تنبيه", "obstacle beeper"), warnings=("النموذج للنشاط المدرسي فقط ولا يعتمد عليه في التنقل.",)),
    build("mini_weather_station", "محطة طقس مصغرة", "Mini Weather Station", "environment", "intermediate",
          "تقرأ محطة الطقس الحرارة والرطوبة والضغط من BME280 وتكتب سجل CSV عبر Serial بسرعة 9600.",
          [("weather", "adafruit_bme280")], [
              ("صِل VIN إلى 5 V وGND إلى الأرضي. صِل SCK/SCL إلى A5 وSDI/SDA إلى A4 على لوحة Adafruit.",
               powered("weather", "VIN") + [("uno1.A5", "weather.SCK", "signal"), ("weather.SDI", "uno1.A4", "signal")]),
          ], [BME, BME_LIBRARY],
          libraries=("Wire", "Adafruit BME280 Library"),
          warnings=("يستخدم الكود عنوان 0x77 الافتراضي للوحة Adafruit ذات محوّل المستويات. لا توصل مجس BME280 عاريًا إلى 5 V.",)),
    build("room_climate_monitor", "مراقب حرارة ورطوبة الغرفة", "Room Climate Monitor", "environment",
          "intermediate", "يعرض LCD حرارة الغرفة والرطوبة النسبية كل 2.2 ثانية، وينبه عند انقطاع القراءة.",
          [("climate", "dht11", "breadboard"), ("pull", "resistor_10k")] + LCD_PARTS, [
              ("صِل DHT11 رباعي الأرجل وخرج DATA إلى D7، وضع 10 kΩ بين DATA و5 V. اترك NC غير موصول.",
               powered("climate") + [
                   ("climate.DATA", "uno1.D7", "signal"), ("uno1.5V", "pull.A", "power"),
                   ("pull.B", "climate.DATA", "signal"),
               ]),
          ] + lcd(), [DHT, DHT_LIBRARY, LCD], supply=LCD_POWER,
          libraries=("DHT sensor library", "LiquidCrystal")),
    build("temperature_controlled_fan", "مروحة تتحكم بها الحرارة", "Temperature-Controlled Fan", "automation",
          "intermediate", "تبدأ مروحة 5 V عند 30 °C وتتوقف عند 27 °C، ويطبع البرنامج حرارة TMP36 عبر Serial.",
          [("motor", "dc_fan") if item[0] == "motor" else item for item in PUMP_PARTS] + [("temperature", "tmp36", "breadboard")],
          motor_switch() + [
              ("واجه الجانب المسطّح من TMP36 وطابق ترتيب VCC ثم VOUT ثم GND مع المخطط. صِل VOUT إلى A0.",
               powered("temperature") + [("temperature.VOUT", "uno1.A0", "signal")]),
          ], [TMP36, MOSFET, DIODE], supply=PUMP_POWER,
          warnings=("اختر مروحة بغطاء واقٍ. أبعد حساس الحرارة عن أصابع المروحة ومصادر الحرارة الشديدة.",)),
    build("water_leak_alarm", "إنذار تسرب المياه", "Water Leak Alarm", "environment", "beginner",
          "يقيس مقاومة الماء بين قطبين عبر نبضة قصيرة ثم يصدر تنبيهًا عند ابتلال المنطقة. عاير حدّي WET_THRESHOLD وDRY_THRESHOLD لعينتك.",
          [("drive_probe", "electrode"), ("sense_probe", "electrode"), ("series", "resistor_10k"),
           ("sense_pull", "resistor_100k"), BUZZER_PART], [
              ("صِل قطب التغذية إلى D4 عبر 10 kΩ، وقطب القياس إلى A0. ضع 100 kΩ بين A0 وGND.",
               [("uno1.D4", "series.A", "signal"), ("series.B", "drive_probe.TERMINAL", "signal"),
                ("sense_probe.TERMINAL", "uno1.A0", "signal"), ("uno1.A0", "sense_pull.A", "signal"),
                ("sense_pull.B", "uno1.GND", "ground")]),
              piezo(8),
          ], [ANALOG_READ], warnings=(WATER_WARNING, "ضع قطبين متباعدين 2 إلى 5 مم فوق قاعدة عازلة، وجرّب بضع قطرات.")),
]
