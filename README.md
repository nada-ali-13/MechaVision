# MechaVision

تطبيق Android تعليمي يعرض مكونات Arduino والأسلاك خطوة بخطوة فوق بورد حقيقية. يعمل الكتالوج وعرض الكود محليًا، ويستخدم عرض الواقع المعزّز كاميرا الهاتف وخدمة ARCore.

## تجربة التتبّع

1. افتح جذر المستودع في إصدار Unity المحدد في [ProjectVersion.txt](ProjectSettings/ProjectVersion.txt). أضف Android Build Support بما يشمل SDK وNDK وOpenJDK من Unity Hub.
2. اتبع [إعداد مشهد TrackingProof والمعايرة](Documentation/AR-setup.md) واطبع [حامل التتبّع بحجم A4](Documentation/TrackingProof-carrier-A4.pdf) بالحجم الفعلي. ثبّت الورقة والبورد على سطح صلب واحد.
3. ابنِ التطبيق لهاتف Android يدعم ARCore وثبّته على Galaxy S22. امنح إذن الكاميرا واختبر الحالات الواردة في [مصفوفة اختبار الهاتف](Documentation/S22-test-matrix.md).
4. استخدم وضع المعاينة داخل المحرّر لتصفح المشاريع والخطوات ورؤية النموذج الافتراضي. اختبارات حركة البورد وفقدان الإشارة تُجرى على الهاتف.

## الكتالوج

يحمّل التطبيق [الكتالوج المحلي](Assets/Resources/MechaVision/catalog.json) ويولّد المجسّمات والتوصيلات عند اختيار المشروع. تتوفر ملفات الكود الأصلية في [ArduinoProjects](ArduinoProjects)، ويتيح التطبيق عرض الكود ونسخه أو حفظ ملف `.ino`.

سجلات الكتالوج مسودات تعليمية. اختر **عرض المسودات التعليمية** في شاشة المشاريع لتصفّحها. راجع مواصفات المكوّنات الفعلية والجهد والتيار قبل التركيب. يبيّن [تقرير التحقق](VALIDATION.md) ما اجتاز الاختبارات وما ينتظر المراجعة.

## التحقق

نفّذ الأوامر من جذر المستودع. ثبت تبعيات Python من [Tools/requirements.txt](Tools/requirements.txt) لفحص مخطط JSON. يعتمد فحص C++ المحلي على `g++`.

```bash
python3 Tools/build_catalog.py --check
python3 -m unittest discover -s Tools -p 'test_*.py'
python3 Tools/verify_sketches.py --host
```

لتجميع ملفات Arduino فعليًا، ثبّت Arduino CLI ونواة Arduino AVR Boards والمكتبات بالإصدارات التي يسجلها الكتالوج، ثم شغّل `python3 Tools/verify_sketches.py --avr`. لتشغيل اختبارات Unity، افتح **Window → General → Test Runner → EditMode** وشغّل مجموعة MechaVision.
