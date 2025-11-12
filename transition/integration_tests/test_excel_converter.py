import unittest
import pandas as pd
import os
import tempfile
import json
from datetime import datetime
from excel_to_json_converter import ExcelToJsonConverter

class TestExcelToJsonConverter(unittest.TestCase):
    
    def setUp(self):
        """إعداد بيانات اختبارية"""
        self.converter = ExcelToJsonConverter()
        
        # إنشاء ملف Excel اختباري
        self.test_data = {
            'Name': ['أحمد', 'محمد', 'فاطمة', ''],
            'Age': [25, 30, '', 40],
            'Salary': ['1000', '2000', '3000', ''],
            'Account': ['001234', '005678', '009999', ''],
            'Date': ['2023-01-01', '2023-02-01', '', '2023-03-01']
        }
        self.df = pd.DataFrame(self.test_data)
    
    def create_test_excel_file(self):
        """إنشاء ملف Excel مؤقت للاختبار"""
        temp_file = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
        self.df.to_excel(temp_file.name, index=False, engine='openpyxl')
        return temp_file.name
    
    def test_clean_data_smart(self):
        """اختبار وظيفة تنظيف البيانات"""
        # اختبار مع تفعيل التنظيف
        converter = ExcelToJsonConverter(clean_data=True)
        df_cleaned = converter.clean_data_smart(self.df)
        
        # التحقق من إزالة الصفوف الفارغة تماماً
        self.assertLessEqual(len(df_cleaned), len(self.df))
        
        # التحقق من تنظيف المسافات
        for col in df_cleaned.select_dtypes(include=['object']).columns:
            for value in df_cleaned[col]:
                if isinstance(value, str):
                    self.assertEqual(value, value.strip())
    
    def test_clean_data_disabled(self):
        """اختبار عند تعطيل تنظيف البيانات"""
        converter = ExcelToJsonConverter(clean_data=False)
        df_cleaned = converter.clean_data_smart(self.df)
        
        # يجب أن تبقى البيانات كما هي
        self.assertEqual(len(df_cleaned), len(self.df))
    
    def test_analyze_column(self):
        """اختبار تحليل الأعمدة"""
        # اختبار عمود نصي
        text_series = pd.Series(['أحمد', 'محمد', 'فاطمة'])
        analysis = self.converter.analyze_column(text_series, text_series.tolist())
        self.assertEqual(analysis['type'], 'text')
        
        # اختبار عمود أرقام
        numeric_series = pd.Series([1000, 2000, 3000])
        analysis = self.converter.analyze_column(numeric_series, numeric_series.tolist())
        self.assertEqual(analysis['type'], 'numeric_string')
        
        # اختبار عمود مختلط
        mixed_series = pd.Series(['001234', '005678', 'محتوى نصي'])
        analysis = self.converter.analyze_column(mixed_series, mixed_series.tolist())
        self.assertEqual(analysis['type'], 'mixed')
    
    def test_is_numeric_string(self):
        """اختبار التعرف على الأرقام النصية"""
        self.assertTrue(self.converter.is_numeric_string("123"))
        self.assertTrue(self.converter.is_numeric_string("1,234.56"))
        self.assertTrue(self.converter.is_numeric_string(1234))
        self.assertFalse(self.converter.is_numeric_string("123abc"))
        self.assertFalse(self.converter.is_numeric_string("نص عربي"))
    
    def test_is_potential_date(self):
        """اختبار التعرف على التواريخ"""
        self.assertTrue(self.converter.is_potential_date("2023-01-01"))
        self.assertTrue(self.converter.is_potential_date("01/01/2023"))
        self.assertTrue(self.converter.is_potential_date(datetime.now()))
        self.assertFalse(self.converter.is_potential_date("نص عادي"))
    
    def test_detect_data_types_improved(self):
        """اختبار كشف أنواع البيانات المحسن"""
        data_types = self.converter.detect_data_types_improved(self.df)
        
        self.assertIn('Name', data_types)
        self.assertIn('Age', data_types)
        self.assertIn('Salary', data_types)
        
        # التحقق من اكتشاف الأرقام النصية المحافظة على التنسيق
        account_analysis = data_types['Account']
        self.assertEqual(account_analysis['type'], 'text_preserve_format')
    
    def test_validate_file(self):
        """اختبار التحقق من الملف"""
        # إنشاء ملف اختباري
        test_file = self.create_test_excel_file()
        
        try:
            # اختبار ملف صالح
            result = self.converter.validate_file(test_file)
            self.assertTrue(result)
            
            # اختبار ملف غير موجود
            with self.assertRaises(FileNotFoundError):
                self.converter.validate_file('file_does_not_exist.xlsx')
                
            # اختبار صيغة غير مدعومة
            with self.assertRaises(ValueError):
                self.converter.validate_file('test.txt')
                
        finally:
            # تنظيف الملف المؤقت
            if os.path.exists(test_file):
                os.unlink(test_file)
    
    def test_prepare_records(self):
        """اختبار تحضير السجلات"""
        data_types = self.converter.detect_data_types_improved(self.df)
        records = self.converter.prepare_records(self.df, data_types)
        
        self.assertEqual(len(records), len(self.df))
        self.assertIsInstance(records, list)
        self.assertIsInstance(records[0], dict)
        
        # التحقق من الحفاظ على تنسيق الأرقام
        account_record = records[0]['Account']
        self.assertEqual(account_record, '001234')  # يجب أن يبقى نصاً
    
    def test_empty_dataframe(self):
        """اختبار مع DataFrame فارغ"""
        empty_df = pd.DataFrame()
        data_types = self.converter.detect_data_types_improved(empty_df)
        self.assertEqual(data_types, {})
    
    def test_mixed_data_types_detection(self):
        """اختبار اكتشاف أنواع البيانات المختلطة"""
        mixed_data = {
            'MixedColumn': [123, '456', 'نص', 789.0, '0123']
        }
        mixed_df = pd.DataFrame(mixed_data)
        
        data_types = self.converter.detect_data_types_improved(mixed_df)
        mixed_analysis = data_types['MixedColumn']
        
        self.assertEqual(mixed_analysis['type'], 'mixed')
        self.assertIn('numeric_string', mixed_analysis['types_found'])
        self.assertIn('text', mixed_analysis['types_found'])

class TestIntegration(unittest.TestCase):
    """اختبارات التكامل"""
    
    def test_end_to_end_conversion(self):
        """اختبار التحويل الكامل من Excel إلى JSON"""
        converter = ExcelToJsonConverter(clean_data=True)
        
        # إنشاء بيانات اختبارية متنوعة
        test_data = {
            'ID': ['001', '002', '003'],
            'الاسم': ['أحمد', 'محمد', 'فاطمة'],
            'الراتب': [5000, 6000, 7000],
            'الحساب': ['000123', '000456', '000789'],
            'ملاحظات': ['', 'تفاصيل إضافية', '']
        }
        df = pd.DataFrame(test_data)
        
        # حفظ كملف Excel مؤقت
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            df.to_excel(temp_file.name, index=False, engine='openpyxl')
            temp_path = temp_file.name
        
        try:
            # التحويل
            result, message = converter.convert_excel_to_json(temp_path, output_file=None)
            
            # التحقق من النتيجة
            self.assertIsNotNone(result)
            json_data = json.loads(result)
            
            # التحقق من الهيكل
            self.assertIn('file_info', json_data)
            self.assertIn('records', json_data)
            self.assertIn('data_types', json_data)
            
            # التحقق من البيانات
            self.assertEqual(len(json_data['records']), 3)
            self.assertEqual(json_data['records'][0]['ID'], '001')
            self.assertEqual(json_data['records'][0]['الاسم'], 'أحمد')
            
        finally:
            # تنظيف
            if os.path.exists(temp_path):
                os.unlink(temp_path)

def run_tests():
    """تشغيل الاختبارات مع تقرير مفصل"""
    print("🧪 تشغيل اختبارات محول Excel إلى JSON...")
    print("=" * 50)
    
    # تحميل و تشغيل الاختبارات
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestExcelToJsonConverter)
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    # تشغيل مع تقرير مفصل
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # طباعة الملخص
    print("\n" + "=" * 50)
    print(f"📊 ملخص الاختبارات:")
    print(f"   ✅ نجح: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"   ❌ فشل: {len(result.failures)}")
    print(f"   ⚠️  أخطاء: {len(result.errors)}")
    
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)