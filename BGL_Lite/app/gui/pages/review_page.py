from __future__ import annotations

import json
import os
import tempfile
import tkinter as tk
from pathlib import Path
from tkinter import messagebox

import ttkbootstrap as ttk

from app.core.pdf_generator import PDFGenerator, generate_pdf


class ReviewPage(ttk.Frame):
    """صفحة مراجعة النتائج واعتمادها."""

    COLUMNS = [
        ("bank_name", "البنك"),
        ("guarantee_number", "رقم الضمان"),
        ("contract_number", "رقم العقد"),
        ("amount", "المبلغ"),
        ("validity_date", "تاريخ الانتهاء"),
        ("contractor_name", "اسم الشركة"),
    ]

    def __init__(self, parent: ttk.Frame, controller):
        super().__init__(parent)
        self.controller = controller
        self.output_dir: Path = controller.output_dir
        self.approved_path = self.output_dir / "approved.json"

        self.records: list[dict] = []
        self.tree_records: dict[str, dict] = {}
        self.approved_records = self.load_approved()

        self.detail_var = tk.StringVar(value="اختر صفًا لعرض التفاصيل.")
        self.status_var = tk.StringVar()

        self.configure(padding=15)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        header = ttk.Label(self, text="👁️ مراجعة النتائج", font=("Segoe UI", 16, "bold"))
        header.grid(row=0, column=0, sticky="w", pady=(0, 10))

        status_strip = ttk.Frame(self, padding=12, bootstyle="light")
        status_strip.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        status_strip.columnconfigure((0, 1, 2), weight=1)
        ttk.Label(status_strip, text="حالة الجدول", font=("Segoe UI", 11, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(status_strip, textvariable=self.status_var).grid(row=1, column=0, sticky="w")

        self.preview_hint = tk.StringVar(value="اختر سجلًا لتفعيل زر المعاينة في القائمة اليمنى.")
        self.export_hint = tk.StringVar(value="اختر سجلًا أو اعتمد بياناتك لتفعيل التصدير.")

        ttk.Label(status_strip, text="👁️ معاينة PDF", bootstyle="secondary").grid(row=0, column=1, sticky="w")
        ttk.Label(status_strip, textvariable=self.preview_hint, wraplength=180).grid(row=1, column=1, sticky="w")

        ttk.Label(status_strip, text="🖨️ التصدير", bootstyle="secondary").grid(row=0, column=2, sticky="w")
        ttk.Label(status_strip, textvariable=self.export_hint, wraplength=180).grid(row=1, column=2, sticky="w")

        tree_frame = ttk.Frame(self)
        tree_frame.grid(row=2, column=0, sticky="nsew")
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        columns = [col for col, _ in self.COLUMNS]
        self.tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            selectmode="extended",
            height=15,
        )
        for col, label in self.COLUMNS:
            self.tree.heading(col, text=label)
            self.tree.column(col, width=150, anchor="center")
        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        self.tree.grid(row=0, column=0, sticky="nsew")

        scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        scroll.grid(row=0, column=1, sticky="ns")

        detail = ttk.Labelframe(self, text="التفاصيل")
        detail.grid(row=3, column=0, sticky="ew", pady=10)
        ttk.Label(detail, textvariable=self.detail_var, anchor="w", justify="right").pack(fill="x", padx=10, pady=10)

    def load_records(self) -> list[dict]:
        output = self.output_dir / "output.json"
        if output.exists():
            try:
                data = json.loads(output.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    return data
                if isinstance(data, dict):
                    return data.get("records", [])
            except json.JSONDecodeError:
                pass
        return []

    def load_approved(self) -> list[dict]:
        if self.approved_path.exists():
            try:
                data = json.loads(self.approved_path.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    return data
            except json.JSONDecodeError:
                pass
        return []

    def populate_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.tree_records.clear()
        for idx, record in enumerate(self.records):
            iid = f"rec_{idx}"
            values = [record.get(col, "") for col, _ in self.COLUMNS]
            self.tree.insert("", "end", iid=iid, values=values)
            self.tree_records[iid] = record

    def on_select(self, _event=None):
        selection = self.tree.selection()
        if not selection:
            self.detail_var.set("اختر صفًا لعرض تفاصيله.")
            self.preview_hint.set("اختر صفًا لتفعيل زر المعاينة في القائمة اليمنى.")
            return
        iid = selection[0]
        record = self.tree_records.get(iid, {})
        lines = [f"{label}: {record.get(col, '')}" for col, label in self.COLUMNS]
        self.detail_var.set("\n".join(lines))
        self.preview_hint.set("جاهز للمعاينة. استخدم زر \"معاينة PDF\" من القائمة اليمنى.")

    def approve_selected(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("تنبيه", "اختر سجلًا واحدًا على الأقل لاعتماده.")
            return
        newly_approved = []
        for iid in selection:
            record = self.tree_records.pop(iid, None)
            if record:
                newly_approved.append(record)
                self.tree.delete(iid)
        if not newly_approved:
            messagebox.showinfo("تم", "لا توجد سجلات جديدة لاعتمادها.")
            return
        self.approved_records.extend(newly_approved)
        self.approved_path.write_text(json.dumps(self.approved_records, ensure_ascii=False, indent=2), encoding="utf-8")
        self.update_status()
        messagebox.showinfo("تم", f"تم اعتماد {len(newly_approved)} سجل/سجلات.")

    def open_approved_folder(self):
        if not self.approved_path.exists():
            messagebox.showinfo("معلومة", "لم يتم اعتماد أي سجلات بعد.")
            return
        os.startfile(self.approved_path)

    def export_pdf(self):
        target_records = self.approved_records or list(self.tree_records.values())
        if not target_records:
            messagebox.showwarning("تنبيه", "لا توجد بيانات لتصديرها.")
            return
        files = generate_pdf(target_records)
        if files and target_records:
            self.controller.last_pdf_path = files[-1]
            self.controller.last_preview_record = target_records[-1]
            self.controller.open_pdf_viewer(target_records[-1], files[-1])
        messagebox.showinfo("PDF", f"تم إنشاء {len(files)} ملف داخل data/output/.")

    def preview_selected(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("تنبيه", "اختر سجلًا واحدًا لمعاينته.")
            return
        record = self.tree_records.get(selection[0])
        if not record:
            messagebox.showwarning("تنبيه", "تعذر العثور على السجل المحدد.")
            return
        preview_path = Path(tempfile.gettempdir()) / "BGL_Lite_preview.pdf"
        generator = PDFGenerator()
        generator.generate_letter(record, preview_path)
        self.controller.last_pdf_path = preview_path
        self.controller.last_preview_record = record
        self.controller.open_pdf_viewer(record, preview_path)

    def update_status(self):
        total = len(self.records)
        remaining = len(self.tree_records)
        approved = len(self.approved_records)
        self.status_var.set(f"إجمالي السجلات: {total} | المتبقي للمراجعة: {remaining} | المعتمد: {approved}")
        if approved or remaining:
            self.export_hint.set("يمكنك الآن استخدام زر التصدير في القائمة اليمنى.")
        else:
            self.export_hint.set("لا توجد بيانات جاهزة للتصدير بعد.")

    def on_show(self):
        self.records = self.load_records()
        self.approved_records = self.load_approved()
        self.populate_table()
        self.update_status()
