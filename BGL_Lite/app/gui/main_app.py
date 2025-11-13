from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path
from tkinter import filedialog

import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Messagebox, Querybox

from app.core.pdf_generator import PDFGenerator, generate_pdf
from app.core.processor import process_file, save_output
from app.gui.pdf_viewer import show_pdf_in_app
from app.gui.pages.export_page import ExportPage
from app.gui.pages.home_page import HomePage
from app.gui.pages.learning_page import LearningPage
from app.gui.pages.review_page import ReviewPage

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

OUTPUT_DIR = ROOT_DIR / "data" / "output"
CONFIG_DIR = ROOT_DIR / "config"
BANKS_PATH = CONFIG_DIR / "banks_dict.json"
SUPPLIERS_PATH = CONFIG_DIR / "suppliers_dict.json"
APPROVED_FILE = OUTPUT_DIR / "approved.json"
REVIEW_FILE = OUTPUT_DIR / "review_report.json"


def ensure_json(path: Path, default):
    if not path.exists():
        path.write_text(json.dumps(default, ensure_ascii=False, indent=2), encoding="utf-8")


def load_json(path: Path, default=None):
    ensure_json(path, default if default is not None else {})
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, payload):
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


class MainApp(ttk.Window):
    def __init__(self):
        super().__init__(themename="minty")
        self.title("BGL_Lite — Smart Excel Processor")
        self.geometry("1100x720")

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        ensure_json(BANKS_PATH, {})
        ensure_json(SUPPLIERS_PATH, {})
        ensure_json(APPROVED_FILE, [])
        ensure_json(REVIEW_FILE, {})

        self.records: list[dict] = []
        self.learnable_items: list[dict] = []
        self.last_pdf_path: Path | None = None
        self.last_preview_record: dict | None = None
        self.current_page = "HomePage"

        self._build_layout()
        self._build_pages()
        self._build_sidebar_actions()
        home_page: HomePage = self.pages["HomePage"]  # type: ignore[assignment]
        home_page.update_stats(0, 0)

        self.show_page("HomePage")

    @property
    def output_dir(self) -> Path:
        return OUTPUT_DIR

    def _build_layout(self):
        root = ttk.Frame(self)
        root.pack(fill="both", expand=True)

        # الحاوية اليسرى (المحتوى)
        self.container = ttk.Frame(root)
        self.container.pack(side="left", fill="both", expand=True)
        self.container.columnconfigure(0, weight=1)
        self.container.rowconfigure(0, weight=1)

        # القائمة اليمنى الديناميكية
        self.sidebar = ttk.Frame(root, padding=(15, 20), width=240)
        self.sidebar.pack(side="right", fill="y")

        ttk.Label(self.sidebar, text="لوحة التحكم", font=("Segoe UI", 14, "bold")).pack(anchor="center", pady=(0, 10))

        nav_frame = ttk.Labelframe(self.sidebar, text="الصفحات")
        nav_frame.pack(fill="x", pady=(0, 10))
        nav_buttons = [
            ("🏠 الرئيسية", "HomePage"),
            ("👁️ مراجعة", "ReviewPage"),
            ("🧩 التعلّم", "LearningPage"),
            ("🖨️ التصدير", "ExportPage"),
        ]
        for text, page in nav_buttons:
            ttk.Button(nav_frame, text=text, command=lambda p=page: self.show_page(p)).pack(fill="x", pady=2)

        self.action_frame = ttk.Labelframe(self.sidebar, text="الإجراءات")
        self.action_frame.pack(fill="both", expand=True, pady=(0, 10))

        ttk.Button(
            self.sidebar,
            text="↩ العودة للرئيسية",
            bootstyle="secondary",
            command=lambda: self.show_page("HomePage"),
        ).pack(fill="x")

    def _build_pages(self):
        self.pages: dict[str, ttk.Frame] = {}
        for Page in (HomePage, ReviewPage, LearningPage, ExportPage):
            page = Page(parent=self.container, controller=self)
            name = Page.__name__
            self.pages[name] = page
            page.grid(row=0, column=0, sticky="nsew")

        self.page_actions = {
            "HomePage": [
                ("📂 تحميل ملف Excel", self.choose_excel_file),
                ("🧹 تنظيف المخرجات", self.clean_outputs),
                ("👁️ فتح صفحة المراجعة", lambda: self.show_page("ReviewPage")),
                ("🧩 فتح صفحة التعلّم", lambda: self.show_page("LearningPage")),
                ("📄 عرض آخر PDF", self.open_pdf_viewer),
            ],
            "ReviewPage": [
                ("✅ اعتماد الصفوف المحددة", self.review_approve_selected),
                ("👁️ معاينة PDF", self.review_preview_selected),
                ("📄 فتح سجل الموافقات", self.review_open_log),
                ("🖨️ تصدير السجلات المعتمدة", self.review_export_pdf),
            ],
            "LearningPage": [
                ("➕ إضافة العنصر المحدد", self.learning_add_selected),
                ("🗑️ إزالة من القائمة", self.learning_remove_selected),
                ("🔄 تحديث العناصر", self._update_learning_page),
            ],
            "ExportPage": [
                ("🖨️ توليد PDF النهائي", self.export_bulk),
                ("📄 تصدير سجل واحد", self.export_single_prompt),
                ("👁️ عرض آخر PDF", self.open_pdf_viewer),
            ],
        }

    def _build_sidebar_actions(self):
        for child in self.action_frame.winfo_children():
            child.destroy()
        actions = self.page_actions.get(self.current_page, [])
        if not actions:
            ttk.Label(self.action_frame, text="لا توجد إجراءات لهذه الصفحة.", bootstyle="secondary").pack(
                anchor="w", padx=10, pady=10
            )
            return
        for text, handler in actions:
            ttk.Button(self.action_frame, text=text, command=handler).pack(fill="x", pady=3)

    def show_page(self, name: str):
        self.current_page = name
        page = self.pages[name]
        if hasattr(page, "on_show"):
            page.on_show()
        page.tkraise()
        self._build_sidebar_actions()

    def choose_excel_file(self):
        file_path = filedialog.askopenfilename(
            title="اختر ملف Excel",
            filetypes=[("Excel Files", "*.xlsx *.xls")],
        )
        if not file_path:
            return
        self.process_excel(Path(file_path))

    def process_excel(self, file_path: Path):
        try:
            home_page: HomePage = self.pages["HomePage"]  # type: ignore[assignment]
            home_page.set_status("جاري معالجة الملف...", file_path)
            payload = process_file(file_path)
            save_output(payload)
            self.records = payload.get("records", [])
            self.learnable_items = payload.get("learnable_items", [])
            self.last_preview_record = self.records[0] if self.records else None
            home_page.set_status(f"تم تحميل {file_path} — {len(self.records)} صفوف.", file_path)
            home_page.update_stats(len(self.records), len(self.learnable_items))
            self._update_learning_page()
            self.pages["ExportPage"].update_summary()  # type: ignore[attr-defined]
            self._notify_pages()
        except Exception as exc:  # noqa: BLE001
            Messagebox.show_error(f"حدث خطأ أثناء قراءة الملف:\n{exc}", "خطأ")

    def clean_outputs(self):
        removed = 0
        for path in OUTPUT_DIR.iterdir():
            try:
                if path.is_file():
                    path.unlink()
                    removed += 1
                elif path.is_dir():
                    shutil.rmtree(path)
                    removed += 1
            except OSError as exc:
                Messagebox.show_error(f"تعذر حذف {path.name}: {exc}", "خطأ")
                return
        save_json(APPROVED_FILE, [])
        save_json(REVIEW_FILE, {})
        self.records = []
        self.learnable_items = []
        self.last_pdf_path = None
        self.last_preview_record = None
        home_page: HomePage = self.pages["HomePage"]  # type: ignore[assignment]
        home_page.update_stats(0, 0, alert="تم تنظيف مجلد المخرجات بالكامل.")
        self._update_learning_page()
        self.pages["ExportPage"].update_summary()  # type: ignore[attr-defined]
        self._notify_pages()
        Messagebox.ok(f"تم تنظيف المخرجات ({removed} عنصر).", "تنظيف")

    def _notify_pages(self):
        for page in self.pages.values():
            if hasattr(page, "on_show"):
                page.on_show()

    # ===== Review actions =====
    def review_page(self) -> ReviewPage:
        return self.pages["ReviewPage"]  # type: ignore[return-value]

    def review_approve_selected(self):
        self.review_page().approve_selected()

    def review_preview_selected(self):
        self.review_page().preview_selected()

    def review_open_log(self):
        self.review_page().open_approved_folder()

    def review_export_pdf(self):
        self.review_page().export_pdf()

    # ===== Learning actions =====
    def learning_page(self) -> LearningPage:
        return self.pages["LearningPage"]  # type: ignore[return-value]

    def learning_add_selected(self):
        item = self.learning_page().get_selected_item()
        if not item:
            Messagebox.show_warning("اختر عنصرًا أولًا.", "تنبيه")
            return
        if self.add_learnable_item(item["type"], item["value"]):
            self.remove_learnable_item(item["type"], item["value"])
            self.learning_page().remove_item(item["iid"])

    def learning_remove_selected(self):
        item = self.learning_page().get_selected_item()
        if not item:
            Messagebox.show_warning("اختر عنصرًا لإزالته.", "تنبيه")
            return
        self.remove_learnable_item(item["type"], item["value"])
        self.learning_page().remove_item(item["iid"])

    def _update_learning_page(self):
        learning_page = self.pages.get("LearningPage")  # type: ignore[assignment]
        if learning_page:
            learning_page.refresh_items()

    # ===== Export actions =====
    def export_page(self) -> ExportPage:
        return self.pages["ExportPage"]  # type: ignore[return-value]

    def export_bulk(self):
        approved = load_json(APPROVED_FILE, [])
        target = approved or self.records
        if not target:
            Messagebox.show_warning("لا توجد بيانات كافية للتصدير.", "تنبيه")
            self.export_page().status_var.set("لا توجد سجلات معتمدة. راجع صفحة المراجعة أولًا.")
            return
        files = generate_pdf(target)
        if files:
            self.last_pdf_path = files[-1]
            self.last_preview_record = target[-1]
            Messagebox.ok("تم إنشاء ملفات PDF بنجاح.", "تم")
            self.export_page().status_var.set(f"تم إنشاء {len(files)} ملف PDF في مجلد data/output/.")
        else:
            Messagebox.show_warning("تعذر إنشاء ملفات PDF.", "تنبيه")

    def export_single_prompt(self):
        approved = load_json(APPROVED_FILE, [])
        records = approved or self.records
        if not records:
            Messagebox.show_warning("لا توجد سجلات متاحة.", "تنبيه")
            return
        options = [
            (idx, f"{rec.get('guarantee_number', 'N/A')} — {rec.get('supplier_name') or rec.get('contractor_name', '')}")
            for idx, rec in enumerate(records)
        ]
        labels = [label for _, label in options]
        selected = Querybox.get_item(title="تصدير سجل واحد", prompt="اختر سجلًا للتصدير:", items=labels, parent=self)
        if selected is None:
            return
        index = labels.index(selected)
        record = records[options[index][0]]
        pdf_path = self.export_pdf_single(record)
        if pdf_path:
            Messagebox.ok("تم إنشاء ملف PDF واحد.", "تم")
            self.open_pdf_viewer(record, pdf_path)
        else:
            Messagebox.show_warning("تعذر إنشاء ملف PDF.", "تنبيه")

    def reload_pdf_viewer(self):
        if not (self.last_preview_record or self.last_pdf_path):
            Messagebox.show_warning("لا توجد بيانات متاحة للعرض.", "تنبيه")
            return
        self.open_pdf_viewer(self.last_preview_record, self.last_pdf_path)

    # ===== Learnable items helpers =====
    def add_learnable_item(self, item_type: str, value: str) -> bool:
        value = value.strip()
        if not value:
            return False
        if item_type == "bank":
            if not any("\u0600" <= ch <= "\u06FF" for ch in value):
                Messagebox.show_warning("يرجى إدخال اسم البنك بالعربية.", "تنبيه")
                return False
            db = load_json(BANKS_PATH, {})
            if value in db:
                Messagebox.show_info("تنبيه", f"البنك '{value}' موجود مسبقًا.")
                return False
            en_name = Querybox.get_string("الترجمة الإنجليزية", f"أدخل الاسم الإنجليزي للبنك '{value}':", parent=self)
            if en_name is None or not en_name.strip():
                Messagebox.show_warning("لم يتم حفظ البنك لعدم إدخال اسم إنجليزي صالح.", "تنبيه")
                return False
            db[value] = {"en": en_name.strip()}
            save_json(BANKS_PATH, db)
        else:
            if not any("\u0600" <= ch <= "\u06FF" for ch in value):
                Messagebox.show_warning("لا يمكن حفظ المورد إلا إذا كان الاسم بالعربية.", "تنبيه")
                return False
            db = load_json(SUPPLIERS_PATH, {})
            if value in db:
                Messagebox.show_info("تنبيه", f"المورّد '{value}' موجود مسبقًا.")
                return False
            db[value] = {"normalized": value}
            save_json(SUPPLIERS_PATH, db)
        Messagebox.ok(f"✅ تمت إضافة '{value}' إلى قاعدة بيانات {item_type}.", "تم")
        return True

    def remove_learnable_item(self, item_type: str, value: str):
        key = value.lower()
        self.learnable_items = [
            item for item in self.learnable_items if not (item["type"] == item_type and item["value"].lower() == key)
        ]

    # ===== PDF helpers =====
    def export_pdf_single(self, record: dict) -> Path | None:
        files = generate_pdf([record])
        if files:
            self.last_pdf_path = files[-1]
            self.last_preview_record = record
            return files[-1]
        return None

    def open_pdf_viewer(self, record: dict | None = None, pdf_path: Path | None = None):
        record = record or self.last_preview_record
        pdf_path = pdf_path or self.last_pdf_path
        if not record and not pdf_path:
            Messagebox.show_warning("لا توجد بيانات متاحة للعرض.", "تنبيه")
            return
        if pdf_path is None and record is not None:
            preview_path = Path(tempfile.gettempdir()) / "BGL_Lite_preview.pdf"
            PDFGenerator().generate_letter(record, preview_path)
            pdf_path = preview_path
        if pdf_path is None:
            Messagebox.show_warning("تعذر إنشاء ملف المعاينة.", "تنبيه")
            return
        show_pdf_in_app(pdf_path)
        self.last_pdf_path = pdf_path
        if record:
            self.last_preview_record = record


def run():
    app = MainApp()
    app.mainloop()


if __name__ == "__main__":
    run()
