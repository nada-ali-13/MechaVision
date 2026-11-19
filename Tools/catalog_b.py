"""Arduino lessons 26–50 and the additional parts they use."""

from catalog_common import part, project


UNO = ("https://docs.arduino.cc/hardware/uno-rev3/", "Uno electrical limits and pinout")
SERIAL = ("https://docs.arduino.cc/language-reference/en/functions/communication/serial/",
          "USB serial monitor")
SERVO = ("https://docs.arduino.cc/learn/electronics/servo-motors/", "External servo supply")
BUTTON = ("https://docs.arduino.cc/built-in-examples/digital/InputPullupSerial/",
          "Button wiring and internal pull-up")
ANALOG = ("https://docs.arduino.cc/built-in-examples/basics/AnalogReadSerial/",
          "Analog input and serial calibration")
LIGHT = ("https://www.arduino.cc/en/Tutorial/BuiltInExamples/Blink/", "LED polarity and resistor")
PIEZO = ("https://docs.arduino.cc/built-in-examples/digital/toneMelody/", "Passive piezo wiring and tone")
RAIN = ("https://www.handsontec.com/dataspecs/sensor/Rain%20Sensor.pdf", "Rain probe and comparator pinout")
MIC = ("https://learn.adafruit.com/adafruit-microphone-amplifier-breakout/overview",
       "MAX4466 gain and analog microphone signal")
BMP280 = ("https://learn.adafruit.com/adafruit-bmp280-barometric-pressure-plus-temperature-sensor-breakout/pinouts",
          "BMP280 breakout supply and I2C pins")
BMP280_LIB = (
    "https://raw.githubusercontent.com/adafruit/Adafruit_BMP280_Library/2.6.8/Adafruit_BMP280.h",
    "BMP280 library interface at the pinned version",
)
PULSE = ("https://pulsesensor.com/pages/code-and-guide", "PulseSensor Amped wiring and signal")
MATRIX = ("https://docs.arduino.cc/libraries/keypad/", "Matrix keypad row/column scanning reference")
NFC = ("https://learn.adafruit.com/adafruit-pn532-rfid-nfc/arduino-library", "PN532 shield wiring and usage")
NFC_LIB = ("https://raw.githubusercontent.com/adafruit/Adafruit-PN532/1.3.4/examples/readMifare/readMifare.ino",
           "Shield I2C IRQ and reset pin assignment")
ULTRASONIC = ("https://cdn.sparkfun.com/datasheets/Sensors/Proximity/HCSR04.pdf",
              "HC-SR04 pinout and pulse timing")
BEAM = ("https://learn.adafruit.com/ir-breakbeam-sensors/arduino", "IR beam receiver open collector")
LDR = ("https://learn.adafruit.com/photocells/using-a-photocell", "Photoresistor voltage divider")
MPU = ("https://learn.adafruit.com/mpu6050-6-dof-accelerometer-and-gyro/pinouts",
       "MPU6050 breakout power and I2C")
MPU_REGISTERS = ("https://invensense.tdk.com/wp-content/uploads/2015/02/MPU-6000-Register-Map1.pdf",
                 "MPU6050 reset and accelerometer registers")
JOYSTICK = ("https://learn.sparkfun.com/tutorials/thumb-joystick-hookup-guide/all",
            "Analog joystick output and potentiometers")
RGB = ("https://learn.adafruit.com/adafruit-color-sensors/wiring-and-test",
       "TCS34725 breakout connections and color measurement")
RGB_REGISTERS = ("https://raw.githubusercontent.com/adafruit/Adafruit_TCS34725/master/Adafruit_TCS34725.h",
                 "TCS34725 register constants")
HX = ("https://learn.sparkfun.com/tutorials/load-cell-amplifier-hx711-breakout-hookup-guide/all",
      "HX711 pins, bridge wiring and load cell calibration")
RTC = ("https://learn.adafruit.com/adafruit-ds3231-precision-rtc-breakout/pinouts",
       "Genuine DS3231 breakout voltage and pins")
RTC_DATASHEET = ("https://www.analog.com/media/en/technical-documentation/data-sheets/DS3231.pdf",
                 "Clock register format")
LCD = ("https://docs.arduino.cc/learn/electronics/lcd-displays/", "HD44780 4-bit wiring and LiquidCrystal")
VIBRATION = ("https://wiki.seeedstudio.com/Grove-Vibration_Sensor_SW-420/",
             "SW-420 vibration output and sensitivity adjustment")
CHECKED_SOURCES = {BMP280_LIB[0], NFC_LIB[0], RGB_REGISTERS[0]}

PARTS = [
    part("rain_probe", "لوح استشعار المطر", "Rain sensor resistive plate", "sensor",
         (55, 2, 40), ["P1", "P2"], RAIN),
    part("rain_interface", "وحدة قراءة لوح المطر", "Rain sensor LM393 interface", "sensor",
         (32, 12, 17), ["VCC", "GND", "AO", "DO", "PROBE1", "PROBE2"], RAIN),
    part("max4466", "ميكروفون بمضخّم", "Adafruit MAX4466 microphone", "sensor",
         (20, 10, 13), ["VCC", "GND", "OUT"], MIC),
    part("bmp280_5v", "مستشعر الضغط الجوي BMP280", "Adafruit BMP280 breakout", "sensor",
         (21, 5, 18), ["VIN", "GND", "SDI", "SCK"], BMP280),
    part("pulse_sensor", "مستشعر نبض تعليمي", "PulseSensor Amped", "sensor",
         (16, 4, 16), ["VCC", "GND", "SIGNAL"], PULSE),
    part("keypad_4x4", "لوحة مفاتيح غشائية 4×4", "4×4 membrane matrix keypad", "sensor",
         (68, 3, 76), ["R1", "R2", "R3", "R4", "C1", "C2", "C3", "C4"], MATRIX),
    part("pn532_nfc_shield", "درع بطاقات PN532", "Adafruit PN532 NFC Arduino shield", "sensor",
         (68.6, 12, 53.4), ["5V", "GND", "SDA", "SCL", "IRQ"], NFC),
    part("mpu6050_5v", "مستشعر تسارع MPU6050", "Adafruit MPU6050 breakout", "sensor",
         (26, 6, 18), ["VIN", "GND", "SDA", "SCL"], MPU),
    part("analog_joystick", "عصا تحكم تناظرية", "Analog thumb joystick module", "sensor",
         (33, 23, 28), ["VCC", "GND", "HORIZ", "VERT", "SEL"], JOYSTICK),
    part("tcs34725_5v", "مستشعر لون TCS34725", "Adafruit TCS34725 breakout", "sensor",
         (20, 6, 20), ["VIN", "GND", "SDA", "SCL"], RGB),
    part("sparkfun_hx711", "محول قياس القوة HX711", "SparkFun HX711 breakout", "sensor",
         (32, 5, 25), ["VCC", "VDD", "DAT", "CLK", "GND", "E+", "E-", "A+", "A-"], HX),
    part("load_cell_bridge", "خلية حمل بجسر كامل", "Four-wire full-bridge load cell", "sensor",
         (80, 12.7, 12.7), ["EX+", "EX-", "SIG+", "SIG-"], HX),
    part("ds3231_5v", "ساعة الوقت الحقيقي DS3231", "Adafruit DS3231 RTC breakout", "sensor",
         (26, 8, 22), ["VIN", "GND", "SDA", "SCL"], RTC),
    part("grove_sw420", "مستشعر اهتزاز SW-420", "Seeed Grove SW-420 vibration sensor", "sensor",
         (40, 12, 20), ["VCC", "GND", "SIG"], VIBRATION),
]

SERVO_POWER = (
    "غذِّ Arduino عبر USB. استخدم مصدر 5 V منظمًا مستقلًا بقدرة كافية لتيار بدء "
    "وتوقف جميع محركات السيرفو. اربط الأرضي فقط بين المصدر وArduino ولا تجمع خطّي 5 V."
)
SERVO_WARNINGS = (
    "افصل التغذية عند توصيل الأسلاك أو تركيب الأذرع الميكانيكية.",
    "احمِ الأصابع من حركة السيرفو واضبط مدى الحركة قبل تركيب الآلية.",
)
BUZZER_WARNINGS = (
    "استخدم عنصر بيزو سلبيًا منخفض التيار كما في مرجع Arduino. تختلف متطلبات مكبر الصوت أو الطنّان المغناطيسي.",
)


def power(unit, positive="VCC", supply="uno"):
    return [(f"{supply}.5V", f"{unit}.{positive}", "power"),
            (f"{supply}.GND", f"{unit}.GND", "ground")]


def bus(unit, *, positive="VIN", data="SDA", clock="SCL"):
    return [
        *power(unit, positive),
        (f"{unit}.{data}", "uno.A4", "signal"),
        (f"{unit}.{clock}", "uno.A5", "signal"),
    ]


def servo(unit, pin):
    return [*power(unit, supply="motor_power"), ("uno." + pin, unit + ".SIGNAL", "signal")]


def led(unit, pin):
    return [(f"uno.{pin}", f"{unit}_limit.A", "signal"),
            (f"{unit}_limit.B", f"{unit}.ANODE", "signal"),
            (f"{unit}.CATHODE", "uno.GND", "ground")]


def led_parts(unit, color="red"):
    return [(unit, "led_" + color), (unit + "_limit", "resistor")]


def button(unit, pin):
    return [(f"{unit}.A", f"uno.{pin}", "signal"), (f"{unit}.B", "uno.GND", "ground")]


def buzzer(unit, pin):
    return [(f"uno.{pin}", f"{unit}.POS", "signal"), (f"{unit}.NEG", "uno.GND", "ground")]


def beam(unit, pin):
    return [*power(unit + "_tx"), *power(unit + "_rx"), (f"{unit}_rx.OUT", f"uno.{pin}", "signal")]


def beam_parts(unit):
    return [(unit + "_tx", "breakbeam_tx"), (unit + "_rx", "breakbeam_rx")]


def lesson(id, name_ar, name_en, category, level, description, components, wires, sources,
           *, motors=(), warnings=(), libraries=(), **kwargs):
    base_components = [("uno", "uno"), *components]
    base_wires = list(wires)
    base_sources = [UNO, *sources]
    if motors:
        base_components.append(("motor_power", "supply_5v"))
        base_components.extend((name, "servo") for name, _ in motors)
        base_wires.append(("motor_power.GND", "uno.GND", "ground"))
        for name, pin in motors:
            base_wires.extend(servo(name, pin))
        base_sources.append(SERVO)
        warnings = (*warnings, *SERVO_WARNINGS)
        libraries = (*libraries, "Servo")
        kwargs.setdefault("supply", SERVO_POWER)
    entry = project(id, name_ar, name_en, category, level, description, base_components, base_wires,
                    base_sources, warnings=warnings, libraries=libraries, **kwargs)
    for source in entry["sources"]:
        if source["url"] in CHECKED_SOURCES:
            source["accessed_on"] = "2026-11-19"
    return entry


PROJECTS = [
    lesson(
        "rain_window", "نافذة مصغرة تستجيب للمطر", "Rain-Sensing Window Model",
        "environment", "intermediate",
        "يقرأ البرنامج جهد لوح المطر. تغلق النافذة الورقية عند البلل وتفتح ثانية بعد الجفاف.",
        [("plate", "rain_probe"), ("rain", "rain_interface")],
        [*power("rain"), ("plate.P1", "rain.PROBE1", "signal"), ("plate.P2", "rain.PROBE2", "signal"),
         ("rain.AO", "uno.A0", "signal")],
        [RAIN, ANALOG], motors=[("window_servo", "D9")],
        aliases=["كاشف المطر", "rain sensor", "نافذة آلية"],
        objectives=["قياس تغير المقاومة بالبلل.", "استخدام عتبتين لمنع حركة النافذة قرب الحد."],
        warnings=["بلّل اللوح بقطرات قليلة بعيدًا عن USB والإلكترونيات. جفّفه بعد التجربة.",
                  "راقب قراءة A0 الجافة والرطبة وعدّل العتبتين قبل تشغيل النموذج."],
    ),
    lesson(
        "clap_switch", "مفتاح إضاءة بالتصفيق", "Clap-Activated Light",
        "automation", "beginner",
        "يقيس فرق أعلى وأدنى عينة صوتية خلال نافذة قصيرة ثم يبدّل الصمام عند تصفيقة واضحة.",
        [("mic", "max4466"), *led_parts("lamp")],
        [*power("mic"), ("mic.OUT", "uno.A0", "signal"), *led("lamp", "D6")],
        [MIC, LIGHT],
        aliases=["كاشف التصفيق", "clap switch", "sound sensor"],
        objectives=["ملاحظة تغير سعة الإشارة.", "اختيار عتبة حسب ضجيج الصف وإضافة زمن حجب."],
        warnings=["اضبط gain والعتبة من Serial Monitor. لا تقرّب مصدر صوت شديد من الأذن."],
    ),
    lesson(
        "barometric_altimeter", "مقياس ارتفاع بالضغط الجوي", "Barometric Altimeter",
        "measurement", "intermediate",
        "يقيس BMP280 الضغط ويقدر فرق الارتفاع بالنسبة إلى مكان تشغيل البرنامج. تُعرض النتيجة في Serial Monitor.",
        [("pressure", "bmp280_5v")], bus("pressure", data="SDI", clock="SCK"),
        [BMP280, BMP280_LIB, SERIAL], libraries=["Adafruit BMP280 Library"],
        aliases=["بارومتر", "pressure sensor", "ارتفاع السلم"],
        objectives=["مقارنة قراءات الضغط عند تغير الارتفاع.", "فصل مرجع البداية عن مستوى سطح البحر."],
        warnings=["استخدم لوحة Adafruit BMP280 ذات تنظيم الجهد وتحويل المستوى. توصيل VIN بجهد 5 V لا يصلح للحساس العاري.",
                  "القراءة تعليمية وتتأثر بالطقس وتيارات الهواء."],
    ),
    lesson(
        "pulse_rate_display", "عرض نبض القلب التعليمي", "Educational Pulse Rate Display",
        "measurement", "intermediate",
        "يتتبع تجاوزات إشارة مستشعر النبض ويقدّر عدد النبضات في الدقيقة من الزمن بين القمم.",
        [("pulse", "pulse_sensor")], [*power("pulse"), ("pulse.SIGNAL", "uno.A0", "signal")],
        [PULSE, ANALOG], aliases=["مستشعر النبض", "heart rate", "bpm"],
        objectives=["التمييز بين إشارة دورية وضجيج الحركة.", "تحويل الفترة الزمنية إلى معدل تقريبي."],
        warnings=["استخدم مستشعرًا سليم العزل مع مصدر USB محمول. القرار الطبي يتطلب جهازًا معتمدًا.",
                  "أبقِ الإصبع ثابتًا واضبط threshold من الإشارة المقروءة عند الحاجة. لا تحفظ قياسات الطلاب."],
    ),
    lesson(
        "keypad_door_lock", "مزلاج صندوق بلوحة مفاتيح", "Keypad Lock Model",
        "automation", "intermediate",
        "يقرأ صفوف وأعمدة لوحة 4×4. اكتب 2468 ثم # لتحريك مزلاج عرض مؤقتًا، و* لمسح الإدخال.",
        [("keys", "keypad_4x4")],
        [(f"keys.{pin}", f"uno.D{index + 2}", "signal")
         for index, pin in enumerate(("R1", "R2", "R3", "R4", "C1", "C2", "C3", "C4"))],
        [MATRIX], motors=[("latch", "D10")], aliases=["قفل رقمي", "pin lock", "matrix keypad"],
        objectives=["مسح مصفوفة مفاتيح بثمانية أسلاك.", "التعامل مع ارتداد الزر وزمن فتح المزلاج."],
        warnings=["حدّد ترتيب أطراف لوحة المفاتيح من توثيق نسختها. استخدم النموذج مع صندوق عرض مفتوح.",
                  "اعرض آلية المزلاج الورقية مع الإشراف ودون قفل باب أو حاوية فعلية."],
    ),
    lesson(
        "rfid_access", "تعرّف بطاقات RFID ببطاقة مرجعية", "RFID Tag Recognition Demo",
        "automation", "advanced",
        "تُسجّل أول بطاقة MIFARE بمعرّف من 4 أو 7 بايت مؤقتًا كمرجع. يشير صمامان إلى التطابق أو الاختلاف.",
        [("reader", "pn532_nfc_shield"), *led_parts("accepted", "green"), *led_parts("different")],
        [*bus("reader", positive="5V"), ("reader.IRQ", "uno.D2", "signal"),
         *led("accepted", "D6"), *led("different", "D7")],
        [NFC, NFC_LIB, LIGHT], libraries=["Adafruit PN532"],
        aliases=["بطاقة ذكية", "nfc", "rfid access"],
        objectives=["قراءة معرّف بطاقة ومقارنة مجموعة بايتات.", "تمييز معرّف العرض عن إثبات الهوية."],
        warnings=["اختر درع Adafruit PN532 في وضع I2C. ركّبه مباشرة على Uno مستخدمًا D2 للمقاطعة. "
                  "طرف D3 المحجوز للمكتبة غير موصول افتراضيًا.",
                  "استخدم بطاقات تجريبية بلا بيانات شخصية. معرّف UID قابل للنسخ ولا يصلح كوسيلة أمان."],
    ),
    lesson(
        "touchless_doorbell", "جرس باب دون لمس", "Touchless Doorbell",
        "automation", "beginner",
        "يطلق الجرس نبضة صوتية قصيرة عند اقتراب اليد. لا يعيد التنبيه حتى تبتعد ثم تقترب مجددًا.",
        [("distance", "hc_sr04"), ("bell", "piezo")],
        [*power("distance"), ("uno.D7", "distance.TRIG", "signal"),
         ("distance.ECHO", "uno.D8", "signal"), *buzzer("bell", "D6")],
        [ULTRASONIC, PIEZO], aliases=["جرس تلقائي", "proximity chime", "ultrasonic doorbell"],
        objectives=["تحويل عرض نبضة الصدى إلى مجال اقتراب.", "استخدام حالة إعادة التسليح لتجنب تكرار الجرس."],
        warnings=BUZZER_WARNINGS,
    ),
    lesson(
        "automatic_pet_feeder", "نموذج موزع طعام حيوانات أليف", "Automatic Pet Feeder Model",
        "automation", "intermediate",
        "يفتح السيرفو بوابة حبيبات العرض كل 30 ثانية أو بضغطة اختبار ثم يغلقها بعد 800 ملي ثانية.",
        [("manual", "button")], button("manual", "D2"), [BUTTON], motors=[("gate", "D9")],
        aliases=["مغذي آلي", "timed feeder", "dispenser hopper"],
        objectives=["جدولة حدث باستخدام millis.", "تشغيل بوابة لفترة محددة وإتاحة اختبار يدوي."],
        warnings=["اختبر بحبيبات ورقية أو مواد عرض فقط. الإطعام الفعلي يتطلب تصميمًا واختبارات إضافية.",
                  "تحقق من زمن الفتح وحدود حركة البوابة قبل تركيبها."],
    ),
    lesson(
        "touchless_dispenser", "موزع تجريبي دون لمس", "Touchless Dispenser Model",
        "automation", "intermediate",
        "يحرك السيرفو ذراع موزع جاف عند حجب الحزمة الضوئية ثم ينتظر إزالة اليد.",
        beam_parts("sensor"), beam("sensor", "D2"), [BEAM],
        motors=[("lever", "D9")], aliases=["موزع لا تلامسي", "break beam dispenser"],
        objectives=["استخدام شعاع متقابل كمفتاح بدون تماس.", "إعادة تفعيل الحركة بعد عدة قراءات متتالية."],
        warnings=["حاذِ باعث الشعاع ومستقبله واترك الشعاع مفتوحًا عند تشغيل اللوحة.",
                  "استخدم نموذجًا جافًا وتجنب السوائل والمواد المطهرة في النشاط."],
    ),
    lesson(
        "single_axis_solar_tracker", "متتبع ضوئي بمحور واحد", "Single-Axis Solar Tracker",
        "robotics", "intermediate",
        "يدير السيرفو منصة كرتونية نحو الجهة الأكثر إضاءة استنادًا إلى فرق قراءتي مقاومتي الضوء.",
        [("left", "photoresistor"), ("right", "photoresistor"),
         ("left_fixed", "resistor_10k"), ("right_fixed", "resistor_10k")],
        [(f"uno.5V", f"{side}.A", "power") for side in ("left", "right")]
        + [(f"{side}.B", f"uno.A{channel}", "signal") for channel, side in enumerate(("left", "right"))]
        + [(f"{side}.B", f"{side}_fixed.A", "signal") for side in ("left", "right")]
        + [(f"{side}_fixed.B", "uno.GND", "ground") for side in ("left", "right")],
        [LDR], motors=[("turntable", "D9")], aliases=["متتبع شمسي", "ldr tracker", "light seeking"],
        objectives=["إنشاء مقسمي جهد ومقارنة القراءتين.", "استخدام منطقة سماح للحد من الاهتزاز."],
        warnings=["ثبّت حساسي الضوء على المنصة مع حاجز ورقي بينهما. جرّب بمصباح يدوي.",
                  "النموذج لتوجيه الإضاءة دون أسلاك إلى ألواح طاقة فعلية."],
    ),
    lesson(
        "tilt_indicator", "مقياس الميل بالتسارع", "Accelerometer Tilt Indicator",
        "measurement", "intermediate",
        "يقدّر ميل اللوحة الساكنة عن الأفقي من متجه الجاذبية ويغيّر الصمام عند 20 درجة.",
        [("motion", "mpu6050_5v"), *led_parts("tilted"), *led_parts("level", "green")],
        [*bus("motion"), *led("tilted", "D6"), *led("level", "D7")],
        [MPU, MPU_REGISTERS, LIGHT], aliases=["ميزان ميل إلكتروني", "mpu6050", "inclinometer"],
        objectives=["قراءة ثلاثة محاور عبر I2C.", "مقارنة الميل الساكن بقياس يتأثر بالتسارع والحركة."],
        warnings=["استخدم إصدار Adafruit المتوافق مع 5 V واضبط AD0 على القيمة الافتراضية للعنوان 0x68.",
                  "قراءات العرض تقريبية عند تثبيت اللوحة، وتتغير أثناء هزها."],
    ),
    lesson(
        "pan_tilt_controller", "حامل متحرك بعصا التحكم", "Joystick Pan-Tilt Platform",
        "robotics", "intermediate",
        "تحرك محوران في عصا التحكم سيرفو أفقيًا وآخر عموديًا لتحريك حامل ورقي خفيف.",
        [("stick", "analog_joystick")],
        [*power("stick"), ("stick.HORIZ", "uno.A0", "signal"), ("stick.VERT", "uno.A1", "signal")],
        [JOYSTICK], motors=[("pan", "D9"), ("tilt", "D10")],
        aliases=["حامل كاميرا", "pan tilt", "joystick servo"],
        objectives=["ربط كل محور تناظري بزاوية مستقلة.", "حصر الحركة ضمن مدى ميكانيكي مناسب."],
        warnings=["اترك طرف SEL غير موصول. اختبر مع حامل خفيف دون تثبيت هاتف أو جسم ثقيل."],
    ),
    lesson(
        "servo_robotic_arm", "ذراع سيرفو تتذكر وضعية", "Servo Robotic Arm with Pose Recall",
        "robotics", "advanced",
        "تحكم القاعدة والمرفق والقبضة بوساطة ثلاث مقابض. الضغطة الأولى تحفظ الوضعية والضغط المستمر يستعيدها.",
        [("memory", "button"), *[(f"dial{index}", "potentiometer") for index in range(3)]],
        [*button("memory", "D2"),
         *[wire for index in range(3) for wire in (
             *power(f"dial{index}"), (f"dial{index}.SIGNAL", f"uno.A{index}", "signal"))]],
        [ANALOG, BUTTON], motors=[("base", "D9"), ("elbow", "D10"), ("gripper", "D11")],
        aliases=["ذراع روبوتية", "robotic arm", "pose memory"],
        objectives=["ربط التحكم بمحركات متعددة.", "حفظ قيم الزوايا واستدعاؤها قبل إعادة التشغيل."],
        warnings=["استخدم ذراعًا خفيفة ولوحة تغذية سيرفو مناسبة لتيار ثلاث وحدات.",
                  "لا تضع الأصابع في القبضة ولا تجبر السيرفو على الحركة خارج مداه."],
    ),
    lesson(
        "color_sorter", "فارز قطع حسب اللون", "Color Sorting Demonstrator",
        "robotics", "advanced",
        "يقرأ المستشعر شدة الأحمر والأخضر والأزرق. يوجه لسانًا ورقيًا للأحمر أو الأزرق ويعود للوسط عند لون آخر.",
        [("color_sensor", "tcs34725_5v")], bus("color_sensor"), [RGB, RGB_REGISTERS],
        motors=[("sorter", "D9")], aliases=["فرز ألوان", "tcs34725", "rgb sorter"],
        objectives=["قراءة قنوات RGB عبر I2C.", "مقارنة النسب بدل الشدة المطلقة."],
        warnings=["استخدم لوحة Adafruit بمدخل VIN المتوافق مع 5 V.",
                  "ثبت مسافة المستشعر واضبط العتبات تحت إضاءة ثابتة باستخدام قطع كرتون."],
    ),
    lesson(
        "hx711_digital_scale", "ميزان رقمي بخلية حمل", "HX711 Digital Scale",
        "measurement", "advanced",
        "يقرأ المحول فرق إشارة خلية الحمل. يصفّر الزر الميزان ويتيح قراءة الكتلة بعد معايرته بوزن معلوم.",
        [("adc", "sparkfun_hx711"), ("cell", "load_cell_bridge"), ("tare", "button")],
        [*power("adc"), ("uno.5V", "adc.VDD", "power"),
         ("adc.DAT", "uno.D3", "signal"), ("uno.D4", "adc.CLK", "signal"),
         ("adc.E+", "cell.EX+", "power"), ("adc.E-", "cell.EX-", "ground"),
         ("cell.SIG+", "adc.A+", "signal"), ("cell.SIG-", "adc.A-", "signal"),
         *button("tare", "D2")],
        [HX, BUTTON], aliases=["خلية حمل", "load cell", "وزن إلكتروني"],
        objectives=["التعرف إلى جسر قياس القوة.", "تصفير القياس وحساب countsPerGram بمعيار معروف."],
        warnings=["راجع ورقة بيانات خلية الحمل لتحديد أطراف الإثارة والإشارة. تختلف الألوان حسب النموذج.",
                  "صفّر دون حمل، وسجّل فرق القراءة بكتلة معلومة، ثم حدّث countsPerGram في الكود.",
                  "ثبّت الخلية ميكانيكيًا وفق دليلها واستخدم أوزانًا دون حدها الاسمي."],
    ),
    lesson(
        "ir_tachometer", "عداد دوران بحاجز ضوئي", "Optical RPM Tachometer",
        "measurement", "intermediate",
        "تحسب Arduino نبضات مرور قرص مشقوق بين باعث ومستقبل، وتعرض السرعة التقريبية بالدورات في الدقيقة.",
        beam_parts("optical"), beam("optical", "D2"),
        [BEAM, ("https://docs.arduino.cc/language-reference/en/functions/external-interrupts/attachInterrupt/",
                "External interrupts on Uno")],
        aliases=["عداد rpm", "مقياس دوران", "optical tachometer"],
        objectives=["استخدام المقاطعة لعد النبضات.", "تحويل عدد حواف الإشارة في الثانية إلى سرعة دوران."],
        warnings=["استخدم قرص كرتون خفيفًا يدور باليد واحسب عدد الفتحات في الكود.",
                  "ثبّت الحساسين على جانبي الحافة. تجنب استخدام محور أو محرك سريع."],
    ),
    lesson(
        "dual_ir_speed_meter", "قياس السرعة ببوابتين ضوئيتين", "Dual-IR Speed Meter",
        "measurement", "intermediate",
        "يحسب متوسط سرعة عربة لعب من زمن انتقالها بين بوابتين ضوئيتين تفصل بينهما مسافة معروفة.",
        [*beam_parts("first"), *beam_parts("second")],
        [*beam("first", "D2"), *beam("second", "D3")],
        [BEAM, ("https://docs.arduino.cc/language-reference/en/functions/time/micros/", "Microsecond timing")],
        aliases=["عداد سرعة عربة", "photogate", "speed gate"],
        objectives=["قياس المسافة والزمن وتحويلهما إلى متر/ثانية.", "رفض المرور بالاتجاه العكسي والقياسات المنتهية."],
        warnings=["اجعل المسافة بين خطي الشعاع 15 سم أو اكتب المسافة المقاسة في spacingM.",
                  "اترك الشعاعين غير محجوبين عند تشغيل اللوحة وامنع التداخل البصري بين البوابتين."],
    ),
    lesson(
        "rtc_digital_clock", "ساعة رقمية بوحدة RTC", "RTC Digital Clock",
        "measurement", "intermediate",
        "يعرض الوقت بصيغة 24 ساعة من وحدة DS3231. اختر Newline في Serial Monitor وأرسل أمرًا مثل T 08:30:00.",
        [("clock", "ds3231_5v")], bus("clock"), [RTC, RTC_DATASHEET, SERIAL],
        aliases=["ساعة حقيقية", "ds3231", "real time clock"],
        objectives=["قراءة الوقت من جهاز مستقل عبر I2C.", "تحويل BCD إلى أرقام عشرية."],
        warnings=["استخدم لوحة Adafruit المحددة واحتفظ ببطارية الساعة بعيدًا عن الأطفال.",
                  "شغّل الساعة من USB في التجربة، ولا تركب بطارية غير ملائمة لإصدار اللوحة."],
    ),
    lesson(
        "rtc_alarm_clock", "منبّه مضبوط بمقبض", "Programmable RTC Alarm Clock",
        "automation", "intermediate",
        "يحدد المقبض موعدًا يوميًا بخطوات 45 دقيقة. يعرض Serial Monitor الموعد ويوقف الزر صوت المنبّه.",
        [("clock", "ds3231_5v"), ("dial", "potentiometer"), ("silence", "button"), ("bell", "piezo")],
        [*bus("clock"), *power("dial"), ("dial.SIGNAL", "uno.A0", "signal"),
         *button("silence", "D2"), *buzzer("bell", "D6")],
        [RTC, RTC_DATASHEET, ANALOG, PIEZO], aliases=["ساعة منبهة", "programmable alarm"],
        objectives=["تحويل القراءة التناظرية إلى وقت محدد.", "منع تكرار التشغيل داخل الدقيقة الواحدة."],
        warnings=["اضبط DS3231 أولًا باستخدام برنامج الساعة الرقمية. استخدم لوحة RTC الموصوفة.",
                  *BUZZER_WARNINGS],
    ),
    lesson(
        "digital_countdown", "مؤقت عد تنازلي", "Digital Countdown Timer",
        "automation", "beginner",
        "يحدد زر مدة من 10 إلى 120 ثانية. يبدأ الزر الثاني العد أو يوقفه، ويصدر تنبيه عند وصوله إلى الصفر.",
        [("add_time", "button"), ("start", "button"), ("bell", "piezo")],
        [*button("add_time", "D2"), *button("start", "D3"), *buzzer("bell", "D6")],
        [BUTTON, PIEZO, ("https://docs.arduino.cc/built-in-examples/digital/BlinkWithoutDelay/",
                  "Non-blocking timing with millis")],
        aliases=["مؤقت مطبخ", "عداد تنازلي", "countdown"], warnings=BUZZER_WARNINGS,
        objectives=["تصميم حالات انتظار وتشغيل وإنهاء.", "متابعة الأزرار أثناء قياس الزمن."],
    ),
    lesson(
        "classroom_voting", "عداد تصويت صفي مجهول", "Anonymous Classroom Voting Counter",
        "education", "beginner",
        "يعد الأصوات لخيارين ويعرض الإجماليات في Serial Monitor. يمسح زر ثالث العددين.",
        [("option_a", "button"), ("option_b", "button"), ("clear", "button")],
        [*button("option_a", "D2"), *button("option_b", "D3"), *button("clear", "D4")],
        [BUTTON, SERIAL], aliases=["اقتراع صفي", "voting machine", "poll counter"],
        objectives=["تسجيل ضغطة واحدة لكل صوت.", "عرض أرقام إجمالية دون بيانات تعريف."],
        warnings=["ضع تعليمات خيار A وخيار B بجانب الزرين. تجنب استخدام النشاط لاقتراع رسمي."],
    ),
    lesson(
        "electronic_scoreboard", "لوحة نقاط بشاشة LCD", "Electronic Scoreboard",
        "education", "intermediate",
        "يزيد زران نقاط الفريقين ويصفرهما زر ثالث. تعرض شاشة 16×2 النتيجة دون كمبيوتر.",
        [("display", "lcd1602"), ("contrast", "potentiometer"), ("backlight", "resistor"),
         ("home", "button"), ("guest", "button"), ("clear", "button")],
        [("uno.5V", "display.VDD", "power"), ("display.VSS", "uno.GND", "ground"),
         ("display.RW", "uno.GND", "ground"), *power("contrast"),
         ("contrast.SIGNAL", "display.VO", "signal"), ("uno.5V", "backlight.A", "power"),
         ("backlight.B", "display.A", "power"), ("display.K", "uno.GND", "ground"),
         *[(f"uno.D{pin}", f"display.{terminal}", "signal")
           for terminal, pin in zip(("RS", "E", "D4", "D5", "D6", "D7"), range(7, 1, -1))],
         *button("home", "D8"), *button("guest", "D9"), *button("clear", "D10")],
        [LCD, BUTTON], libraries=["LiquidCrystal"], aliases=["عداد نقاط", "sports score", "lcd scoreboard"],
        objectives=["تشغيل شاشة LCD بالتوازي في وضع 4 بت.", "منع تكرار زيادة النقاط عند إبقاء الزر مضغوطًا."],
        warnings=["استخدم لوحة HD44780 متوافقة مع 5 V. راجع اتجاه طرفي إضاءة الخلفية واضبط التباين بالمقبض."],
    ),
    lesson(
        "reaction_time_game", "لعبة سرعة الاستجابة", "Reaction Time Game",
        "education", "beginner",
        "ينتظر الصمام مدة عشوائية بعد بدء الجولة. يقيس البرنامج زمن ضغط الزر بعد الإضاءة ويسجّل البدء المبكر.",
        [("player", "button"), *led_parts("target")],
        [*button("player", "D2"), *led("target", "D6")],
        [BUTTON, LIGHT, ("https://docs.arduino.cc/language-reference/en/functions/random-numbers/random/",
                        "Generate variable delay")],
        aliases=["سرعة رد الفعل", "reaction timer", "لعبة رد الفعل"],
        objectives=["قياس الزمن بالملي ثانية.", "المقارنة بين عدة محاولات دون الاعتماد على قياس طبي."],
        warnings=["استخدم النشاط كلعبة تعليمية ولا تربط النتيجة بتقييم قدرات الطالب الصحية."],
    ),
    lesson(
        "schedule_reminder", "لوحة تذكير بجدول يومي", "RTC Schedule Reminder",
        "education", "intermediate",
        "يفعّل جدول داخل البرنامج أضواء نشاط بداية الدرس والتنظيف وإعادة القطع. يطفئ الزر ضوء التذكير.",
        [("clock", "ds3231_5v"), ("confirm", "button"),
         *led_parts("lesson", "green"), *led_parts("clean", "yellow"), *led_parts("return_parts")],
        [*bus("clock"), *button("confirm", "D2"),
         *led("lesson", "D5"), *led("clean", "D6"), *led("return_parts", "D7")],
        [RTC, RTC_DATASHEET, LIGHT], aliases=["تذكير بالمواعيد", "lesson schedule", "rtc reminder"],
        objectives=["مقارنة الوقت مع جدول متعدد الأحداث.", "ربط كل موعد بمؤشر مستقل حتى التأكيد."],
        warnings=["اضبط الوقت ببرنامج الساعة الرقمية وعدّل times لتجربة مواعيد قريبة. اختر ألوانًا مختلفة للأضواء."],
    ),
    lesson(
        "vibration_alarm", "مؤشر اهتزاز تجريبي", "Vibration Indicator Demo",
        "measurement", "beginner",
        "يومض مؤشر ضوئي لمدة قصيرة عند اهتزاز القاعدة. يستخدم البرنامج مقاطعة لالتقاط النبضة.",
        [("shake", "grove_sw420"), *led_parts("indicator")],
        [*power("shake"), ("shake.SIG", "uno.D2", "signal"), *led("indicator", "D6")],
        [VIBRATION, LIGHT], aliases=["إنذار اهتزاز", "tamper alarm", "sw420"],
        objectives=["ملاحظة الفرق بين ارتجاج قصير وزمن عرض طويل.", "الضبط اليدوي لحساسية المستشعر."],
        warnings=["اترك اللوحة ساكنة عند التشغيل لمعايرة الحالة الأولية. استخدمه كمؤشر صفّي فقط."],
    ),
]
