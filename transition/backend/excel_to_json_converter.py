import pandas as pd
import json
import sys
import os
import argparse
from datetime import datetime
import warnings

# كتم تحذيرات pandas غير الضرورية
warnings.filterwarnings('ignore')

class ExcelToJsonConverter:
    def __init__(self, clean_data=True, optimize_memory=True):
        self.supported_formats = ['.xlsx', '.xls']
        self.clean_data = clean_data
        self.optimize_memory = optimize_memory
        
        # التحقق من وجود المكتبات المطلوبة
        self.check_dependencies()
    
    def check_dependencies(self):
        """التحقق من المكتبات المطلوبة"""
        try:
            import pandas
            import openpyxl
        except ImportError as e:
            print("❌ المكتبات المطلوبة غير مثبتة!")
            print("📦 قم بتثبيتها باستخدام:")
            print("   pip install pandas openpyxl")
            sys.exit(1)
    
    def validate_file(self, file_path):
        """التحقق من وجود الملف وصيغته"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"الملف '{file_path}' غير موجود")
        
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext not in self.supported_formats:
            raise ValueError(f"الصيغة '{file_ext}' غير مدعومة. الصيغ المدعومة: {self.supported_formats}")
        
        return True
    
    def read_excel_optimized(self, file_path, sheet_name=0):
        """قراءة ملف Excel بطرق محسنة للأداء"""
        try:
            # خيارات القراءة المحسنة للأداء
            read_options = {
                'sheet_name': sheet_name,
                'keep_default_na': False,  # عدم تحويل القيم الفارغة إلى NaN
                'na_values': ['', ' ', 'NULL', 'null'],  # القيم التي تعتبر فارغة
            }
            
            if self.optimize_memory:
                read_options.update({
                    'dtype': str,  # قراءة كل شيء كنص للحفاظ على التنسيق
                    'usecols': None,  # قراءة كل الأعمدة (يمكن تحسينه لقراءة أعمدة محددة)
                })
            
            # قراءة البيانات
            if sheet_name == "all":
                read_options["sheet_name"] = None
            else:
                read_options["sheet_name"] = sheet_name
            return pd.read_excel(file_path, **read_options)
                
        except ImportError as e:
            raise ImportError(f"خطأ في استيراد المكتبات: {e}")
        except Exception as e:
            raise Exception(f"خطأ في قراءة الملف: {e}")
    
    def clean_data_smart(self, df):
        """تنظيف ذكي للبيانات مع الحفاظ على الهيكل"""
        if not self.clean_data:
            return df
            
        df_clean = df.copy()
        
        # تنظيف انتقائي - إزالة الصفوف التي تكون فارغة تماماً فقط
        initial_rows = len(df_clean)
        df_clean = df_clean.dropna(how='all')
        removed_rows = initial_rows - len(df_clean)
        
        if removed_rows > 0:
            print(f"   🧹 تم إزالة {removed_rows} صف فارغ تماماً")
        
        # تنظيف المسافات الزائدة في النصوص فقط
        text_columns = df_clean.select_dtypes(include=['object']).columns
        for col in text_columns:
            df_clean[col] = df_clean[col].apply(
                lambda x: x.strip() if isinstance(x, str) else x
            )
        
        return df_clean
    
    def detect_data_types_improved(self, df):
        """كشف محسن لأنواع البيانات مع التعامل مع الحالات الخاصة"""
        data_types = {}
        mixed_types = {}
        
        for col in df.columns:
            if df[col].empty:
                data_types[col] = {"type": "empty", "sample": ""}
                continue
            
            # أخذ عينة صغيرة للتحليل
            sample_size = min(10, len(df[col]))
            sample_data = df[col].iloc[:sample_size].tolist()
            
            # التحليل المتعمق للعمود
            col_analysis = self.analyze_column(df[col], sample_data)
            data_types[col] = col_analysis
            
            # اكتشاف الأعمدة المختلطة
            if col_analysis.get('mixed_types', False):
                mixed_types[col] = col_analysis
        
        if mixed_types:
            print("   ⚠️  تم اكتشاف أعمدة بأنواع بيانات مختلطة:")
            for col, info in mixed_types.items():
                print(f"     - {col}: {info['types_found']}")
        
        return data_types
    
    def analyze_column(self, series, sample_data):
        """تحليل متعمق للعمود"""
        non_empty = series.dropna()
        if non_empty.empty:
            return {"type": "empty", "sample": ""}
        
        # اكتشاف أنواع البيانات المختلفة في العمود
        types_found = set()
        numeric_count = 0
        text_count = 0
        date_count = 0
        
        for item in sample_data:
            if pd.isna(item) or item == '':
                continue
                
            if self.is_numeric_string(item):
                types_found.add("numeric_string")
                numeric_count += 1
            elif self.is_potential_date(item):
                types_found.add("date_like")
                date_count += 1
            else:
                types_found.add("text")
                text_count += 1
        
        # تحديد النوع السائد
        total_non_empty = len([x for x in sample_data if x != ''])
        if not total_non_empty:
            return {"type": "empty", "sample": ""}
        
        # الحفاظ على الأرقام كنص إذا كانت تحتوي على أصفار بادئة
        if "numeric_string" in types_found and any(
            str(item).startswith('0') and len(str(item)) > 1 
            for item in sample_data if item != ''
        ):
            final_type = "text_preserve_format"  # نص للحفاظ على التنسيق
        elif len(types_found) == 1:
            final_type = list(types_found)[0]
        else:
            final_type = "mixed"
        
        sample_value = sample_data[0] if sample_data else ""
        if pd.isna(sample_value):
            sample_value = ""

        return {
            "type": final_type,
            "types_found": list(types_found),
            "sample": sample_value,
            "numeric_ratio": numeric_count / total_non_empty,
            "text_ratio": text_count / total_non_empty,
            "mixed_types": len(types_found) > 1
        }
    
    def is_numeric_string(self, value):
        """التحقق إذا كان النص يمكن أن يكون رقماً"""
        if isinstance(value, (int, float)):
            return True
        if isinstance(value, str):
            try:
                float(value.replace(',', ''))
                return True
            except ValueError:
                return False
        return False
    
    def is_potential_date(self, value):
        """التحقق إذا كان القيمة يمكن أن تكون تاريخ"""
        if isinstance(value, (pd.Timestamp, datetime)):
            return True
        if isinstance(value, str):
            date_patterns = ['-', '/', ':', '202', '199']  # أنماط تواريخ شائعة
            return any(pattern in value for pattern in date_patterns)
        return False
    
    def convert_excel_to_json(self, excel_file, sheet_name=0, output_file=None):
        """الدالة الرئيسية للتحويل مع معالجة أخطاء محددة"""
        try:
            print(f"📖 جاري قراءة الملف: {excel_file}")
            
            # التحقق من الملف
            self.validate_file(excel_file)
            
            # قراءة ملف Excel بطريقة محسنة
            data = self.read_excel_optimized(excel_file, sheet_name)
            
            if sheet_name == "all":
                return self.process_multiple_sheets(data, excel_file, output_file)
            else:
                return self.process_single_sheet(data, excel_file, sheet_name, output_file)
            
        except FileNotFoundError as e:
            raise e
        except ImportError as e:
            raise e
        except pd.errors.EmptyDataError:
            raise Exception("الملف لا يحتوي على بيانات")
        except pd.errors.ParserError as e:
            raise Exception(f"خطأ في تحليل الملف: {e}")
        except Exception as e:
            raise Exception(f"خطأ غير متوقع: {e}")
    
    def process_single_sheet(self, df, excel_file, sheet_name, output_file):
        """معالجة ورقة مفردة"""
        print(f"   🔄 معالجة البيانات في الورقة: {sheet_name}")
        
        # تنظيف البيانات (إذا مطلوب)
        if self.clean_data:
            df_processed = self.clean_data_smart(df)
        else:
            df_processed = df
        
        # كشف أنواع البيانات
        data_types = self.detect_data_types_improved(df_processed)
        
        # إعداد البيانات النهائية
        result_data = {
            "file_info": {
                "file_name": os.path.basename(excel_file),
                "sheet_name": sheet_name,
                "conversion_date": datetime.now().isoformat(),
                "records_count": len(df_processed),
                "columns_count": len(df_processed.columns),
                "cleaning_applied": self.clean_data
            },
            "data_types": data_types,
            "columns": list(df_processed.columns),
            "records": self.prepare_records(df_processed, data_types)
        }
        
        return self.save_output(result_data, output_file)
    
    def process_multiple_sheets(self, data_dict, excel_file, output_file):
        """معالجة أوراق متعددة"""
        all_sheets_data = {}
        
        for sheet_name, df in data_dict.items():
            print(f"   🔄 معالجة الورقة: {sheet_name}")
            
            if self.clean_data:
                df_clean = self.clean_data_smart(df)
            else:
                df_clean = df
            
            data_types = self.detect_data_types_improved(df_clean)
            
            all_sheets_data[sheet_name] = {
                "metadata": {
                    "records_count": len(df_clean),
                    "columns_count": len(df_clean.columns),
                    "cleaning_applied": self.clean_data
                },
                "data_types": data_types,
                "records": self.prepare_records(df_clean, data_types)
            }
        
        result_data = {
            "file_info": {
                "file_name": os.path.basename(excel_file),
                "conversion_date": datetime.now().isoformat(),
                "total_sheets": len(data_dict),
                "cleaning_applied": self.clean_data
            },
            "sheets": all_sheets_data
        }
        
        return self.save_output(result_data, output_file)
    
    def prepare_records(self, df, data_types):
        """تحضير السجلات مع الحفاظ على التنسيق"""
        records = []
        for _, row in df.iterrows():
            record = {}
            for col in df.columns:
                value = row[col]
                if pd.isna(value):
                    record[col] = None
                    continue
                
                # الحفاظ على التنسيق للأرقام النصية
                col_info = data_types.get(col, {})
                if col_info.get('type') == 'text_preserve_format' and value != '':
                    record[col] = str(value)  # الحفاظ كنص
                else:
                    record[col] = value
            records.append(record)
        return records
    
    def save_output(self, result_data, output_file):
        """حفظ المخرجات"""
        json_output = json.dumps(
            result_data,
            ensure_ascii=False,
            indent=2,
            default=str,
            allow_nan=False,
        )
        
        if output_file:
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(json_output)
                print(f"💾 تم حفظ النتائج في: {output_file}")
            except IOError as e:
                raise Exception(f"خطأ في حفظ الملف: {e}")
        
        return json_output

def setup_argparse():
    """إعداد واجهة سطر الأوامر مع argparse"""
    parser = argparse.ArgumentParser(
        description='برنامج تحويل Excel إلى JSON',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
أمثلة:
  %(prog)s data.xlsx                    # تحويل الورقة الأولى
  %(prog)s data.xlsx --sheet all        # تحويل جميع الأوراق
  %(prog)s data.xlsx --no-clean         # بدون تنظيف البيانات
  %(prog)s data.xlsx -o output.json     # تحديد ملف الإخراج
        '''
    )
    
    parser.add_argument('file', help='مسار ملف Excel المدخل')
    parser.add_argument('--sheet', default=0, help='اسم الورقة أو "all" لجميع الأوراق (افتراضي: الأولى)')
    parser.add_argument('-o', '--output', help='ملف JSON الإخراج (اختياري)')
    parser.add_argument('--no-clean', action='store_true', help='تعطيل تنظيف البيانات')
    parser.add_argument('--no-optimize', action='store_true', help='تعطيل تحسين الذاكرة')
    
    return parser

def main():
    """الدالة الرئيسية للبرنامج"""
    parser = setup_argparse()
    
    # معالجة المدخلات من سطر الأوامر أولاً
    if len(sys.argv) > 1:
        args = parser.parse_args()
        
        converter = ExcelToJsonConverter(
            clean_data=not args.no_clean,
            optimize_memory=not args.no_optimize
        )
        
        try:
            result = converter.convert_excel_to_json(
                args.file,
                args.sheet,
                args.output
            )
            
            data = json.loads(result)
            if "sheets" in data:
                total_records = sum(sheet["metadata"]["records_count"] for sheet in data["sheets"].values())
                print(f"✅ تم التحويل بنجاح: {len(data['sheets'])} أوراق، {total_records} سجل")
            else:
                print(f"✅ تم التحويل بنجاح: {data['file_info']['records_count']} سجل")
                
        except Exception as e:
            print(f"❌ {e}")
            sys.exit(1)
    
    else:
        # الوضع التفاعلي
        print("🔄 برنامج تحويل Excel إلى JSON")
        print("=" * 50)
        
        converter = ExcelToJsonConverter()
        
        try:
            excel_file = input("📁 أدخل مسار ملف Excel: ").strip()
            
            # استخدام parser للمساعدة في التحقق
            args = parser.parse_args([excel_file] + sys.argv[1:])
            
            # استكمال الإدخال التفاعلي
            sheet_names = converter.get_sheet_names(excel_file) if hasattr(converter, 'get_sheet_names') else []
            
            if sheet_names and len(sheet_names) > 1:
                print(f"\n📑 اختر الورقة المراد تحويلها:")
                print("   all - جميع الأوراق")
                for sheet in sheet_names:
                    print(f"   {sheet}")
                
                sheet_choice = input("   أدخل اسم الورقة (افتراضي: all): ").strip()
                args.sheet = sheet_choice if sheet_choice else "all"
            else:
                args.sheet = sheet_names[0] if sheet_names else 0
            
            if not args.output:
                base_name = os.path.splitext(excel_file)[0]
                args.output = input(f"💾 اسم ملف الإخراج (افتراضي: {base_name}.json): ").strip()
                if not args.output:
                    args.output = f"{base_name}.json"
            
            # التحويل
            result = converter.convert_excel_to_json(args.file, args.sheet, args.output)
            
            if result:
                data = json.loads(result)
                if "sheets" in data:
                    total_records = sum(sheet["metadata"]["records_count"] for sheet in data["sheets"].values())
                    print(f"✅ تم التحويل بنجاح: {len(data['sheets'])} أوراق، {total_records} سجل")
                else:
                    print(f"✅ تم التحويل بنجاح: {data['file_info']['records_count']} سجل")
                    
        except Exception as e:
            print(f"❌ {e}")
            sys.exit(1)

if __name__ == "__main__":
    main()
