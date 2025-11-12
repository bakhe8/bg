# Migration Notes

تُسجَّل هنا تطورات نقل الوظائف بين Legacy → Transition → Main.

## 2025-11-12

- استُبدل محول `ExcelToJsonConverter` في طبقة transition بإصدار يعتمد على خط أنابيب `data_pipeline` (ColumnMapper + ExcelPreprocessor + DataCleaner + DataValidator + PipelineLogger).
- أضيفت ملفات التهيئة (`config/column_aliases.json`, `banks.json`, `normalization_rules.json`) كمصدر واحد للحاكمية والإثراء.
- المخرجات الآن تقتصر على الحقول القياسية (`bank_name`, `guarantee_number`, `contract_number`, `amount`, `validity_date`, `company_name`) بعد تنظيف وتوحيد تلقائي.
- تم تفعيل التسجيل المركزي في `transition/backend/reports/pipeline.log` لتوثيق كل عملية رفع/تنظيف.
- أعيدت كتابة اختبارات التكامل (`transition/integration_tests/test_excel_converter.py`) للتحقق من التطبيع، الأوراق المتعددة، وتحقق سلامة الملفات.
