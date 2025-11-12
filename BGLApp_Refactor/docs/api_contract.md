# BGLApp API Contract

كل نقاط الـ API متاحة عبر FastAPI (`python -m main.app`). جميع الردود بصيغة JSON وتُستخدم الأسماء العربية في الرسائل عند الخطأ. السكيمات الأساسية موحدة ولا يجب تغييرها بدون تحديث هذا المستند.

## 1. تحويل ملف واحد

```
POST /api/convert
multipart/form-data
  file : UploadFile (.xlsx/.xls)
  sheet (اختياري، افتراضي all)
```

ردّ النجاح:
```json
{
  "data": {
    "file_info": {
      "file_name": "111.xlsx",
      "sheet_name": "Sheet1",
      "records_count": 63,
      "unknown_columns": ["Supplier Bank", "PO Reference"]
    },
    "records": [
      {
        "bank_name": "بنك الرياض",
        "guarantee_number": "M113528",
        "contract_number": "PO-00991",
        "amount": "١٢٥٬٠٠٠٫٥٠",
        "validity_date": "2025-06-30",
        "company_name": "شركة المعدات العربية"
      }
    ]
  }
}
```

## 2. تحويل دفعة ملفات

```
POST /api/convert/batch
multipart/form-data
  files : [UploadFile ...]
  sheet : "all" | index | اسم ورقة
```

ردّ النجاح (قد يكون `200` أو `207` عند وجود أخطاء جزئية):
```json
{
  "results": [
    { "filename": "file1.xlsx", "records": 20, "data": { ... } }
  ],
  "errors": [
    { "filename": "file2.xlsx", "error": "تفاصيل الخطأ" }
  ]
}
```

## 3. حفظ خطاب الضمان

```
POST /api/letters
Content-Type: application/json
{
  "filename": "letter_A1.json",   // اختياري
  "data": { ... نفس هيكل السجل ... }
}
```

إرجاع:
```json
{
  "status": "saved",
  "path": "main/data/exports/letter_d0c8b1.json",
  "filename": "letter_d0c8b1.json"
}
```

## 4. إدارة الأعمدة المرجعية

- `GET /api/aliases` → يعيد جميع الحقول القياسية والأسماء المرتبطة بها.
- `POST /api/aliases` (body: `{ "canonical": "bank_name", "alias": "ISSUING BANK" }`) → يضيف الاسم للمرجع.

## 5. لوحة المراجعة

- `GET /api/review/unknown-columns`
  ```json
  {
    "columns": [
      {
        "label": "Supplier Bank",
        "count": 5,
        "files": ["file1.xlsx", "file3.xlsx"],
        "sheets": ["Sheet1"]
      }
    ],
    "ignored": ["supplier bank"]
  }
  ```
- `POST /api/review/ignore` أو `DELETE /api/review/ignore`
  ```json
  { "label": "Supplier Bank" }
  ```

## 6. توليد PDF من الخادم

```
POST /api/pdf
Content-Type: application/json
{
  "filename": "letter_M113528.pdf",  // اختياري
  "data": {
    "bank_name": "...",
    "bank_center": "...",
    ...
  }
}
```

يرجع الملف مباشرة كـ `application/pdf`.

## 7. عرض السجلات

```
GET /api/logs?file=convert&limit=200
```

المعامل `file` يقبل القيم: `convert`, `letters`, `review`. يعيد آخر `limit` سطرًا من السجل المناسب. هذه النهاية محمية اختياريًا بـ Basic Auth (`MONITOR_USER` / `MONITOR_PASS`).

## 7. العقد القياسي للبيانات

كل سجل ناتج عن التحويل أو الحفظ يجب أن يحتوي على الحقول الآتية:

| الحقل            | النوع  | الوصف                                          |
|------------------|--------|------------------------------------------------|
| `bank_name`      | string | اسم البنك بالعربية بعد التطبيع               |
| `guarantee_number` | string | رقم الضمان (يُحافظ على الصفر البادئ)        |
| `contract_number`  | string | رقم العقد أو أمر الشراء                       |
| `amount`         | string | قيمة الضمان بأرقام عربية (٢ منازل عشرية)     |
| `validity_date`  | string | تاريخ نهاية الضمان بصيغة `YYYY-MM-DD`        |
| `company_name`   | string | اسم الشركة أو المورد                          |

## 9. الملاحظات

- جميع الردود في حالة الخطأ ترجع `{"error": "رسالة عربية واضحة"}` مع كود HTTP مناسب.
- الأعمدة المجهولة تُسجل تلقائياً في `main/data/review/unknown_columns.log` ويمكن إدارتها من صفحة `/review`.
- FastAPI يولد OpenAPI تلقائياً (يمكن تفعيل `/docs` بإزالة الحجب في إعدادات الخادم إذا لزم الأمر).
