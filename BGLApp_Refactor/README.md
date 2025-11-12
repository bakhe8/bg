# BGLApp Refactor Workspace

هذا الدليل خاص ببيئة إعادة الهيكلة (BGLApp_Refactor). يتم نسخ الملفات
من النظام الحالي تدريجيًا وفق خارطة الطريق `docs/refactor_map.md`.

## كيفية الاستخدام

1. لا تعدّل النظام القديم داخل `main/` أثناء العمل هنا.
2. استورد أي منطق حالي من `main/…` حتى تكتمل عملية النقل ثم قم بإزالته.
3. تأكّد بعد كل خطوة من أن `python app.py`, `pytest`, و `python build_portable.py` ما زالت تعمل.

## المحتويات

- `core/` – الطبقات المشتركة (Excel/PDF/Logging/Config).
- `api/` – نسخة FastAPI الجديدة.
- `web/` – القوالب والملفات الثابتة.
- `tests/` – اختبارات PyTest المحدثة.
- `docs/` – المستندات الرسمية.

لمزيد من التفاصيل راجع `docs/refactor_map.md`.
