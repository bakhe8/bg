# BGLApp

نظام متكامل لمعالجة خطابات الضمان البنكية: رفع ملفات Excel، تحويلها إلى JSON موحد، مراجعة الأعمدة غير المعروفة، حفظ الخطابات وطباعتها فوراً عبر واجهة واحدة.

## التهيئة الأولية

```
pip install -r requirements.txt
```

## تشغيل الخادم الرسمي (FastAPI + Uvicorn)

```
python -m main.app  # يستخدم uvicorn لتشغيل main.api.server:app
```
- واجهة الطباعة: <http://localhost:5000>
- لوحة مراجعة الأعمدة: <http://localhost:5000/review>
- لوحة المراقبة (عرض السجلات): <http://localhost:5000/monitor> _(اختياريًا محمية بـ Basic Auth)_.
- توثيق Swagger/OpenAPI: <http://localhost:5000/docs> و <http://localhost:5000/redoc>.

## البنية الحالية

```
BGLApp/
├ legacy/                ← مرجع ثابت (لا يُمس)
├ transition/            ← مساحة التطوير المساندة
└ main/                  ← النظام التشغيلي
    ├ app.py             ← نقطة تشغيل Flask الرسمية
    ├ api/               ← واجهات /api (رفع، حفظ، مراجعة)
    ├ web/               ← مسارات الواجهة (index / preview / review)
    ├ bg_ui/             ← الواجهة الأمامية للطباعة والمراجعة
    ├ data/              ← أرشيف JSON/PDF + سجلات + بيانات مراجعة
    ├ config.py          ← مسارات ثابتة + إعدادات البيئة (BGLAPP_*)
    └ ...
```

## دورة العمل

1. **رفع** ملف Excel (واحد أو عدة ملفات).
2. **تحويل** تلقائي عبر خوارزمية التطبيع الذكي (transition/backend/data_pipeline).
3. **مراجعة** الأعمدة غير المعروفة من صفحة `/review` وإضافتها للمراجع أو تجاهلها.
4. **حفظ/طباعة**: تعبئة القالب البنكي مباشرة ثم تحميل PDF أو إرسال JSON إلى `/api/letters`.

## سجلات النظام

- main/data/logs/convert.log: كل عمليات الرفع/التحويل.
- main/data/logs/letters.log: كل عمليات حفظ الخطابات.
- main/data/logs/review.log: أحداث لوحة المراجعة.
- main/data/review/unknown_columns.log: سجل الأعمدة غير المعرَّفة.

## ملاحظات إضافية

- أي تعديل في الأعمدة المرجعية يتم من خلال واجهة المراجعة أو محرر البيانات؛ الخوارزمية تتبنى التحديث مباشرة.
- النسخة الانتقالية (transition/) تبقى للرجوع أو الاختبارات ولا تُستخدم في التشغيل.
- لا تُرفع مخرجات main/data/archives/ و main/data/logs/ إلى Git؛ يتم تجاهلها تلقائياً.
- لتنشيط الصلاحيات والتنبيهات:
  - عيّن `BGLAPP_MONITOR_USER` و `BGLAPP_MONITOR_PASS` لحماية `/monitor`, `/review`, `/api/logs` بـ Basic Auth.
  - عيّن `BGLAPP_ALERT_WEBHOOK` (Slack أو أي Webhook) + `BGLAPP_ALERT_TIMEOUT` (اختياري) لتلقّي تنبيه فوري عند فشل التحويل أو حفظ الخطاب.
