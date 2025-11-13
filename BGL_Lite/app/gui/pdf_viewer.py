from __future__ import annotations

import os
from pathlib import Path

from ttkbootstrap.dialogs import Messagebox

try:
    import webview
except ImportError:  # pragma: no cover - optional dependency
    webview = None  # type: ignore[assignment]

_WEBVIEW_AVAILABLE: bool | None = None


def can_use_webview() -> bool:
    """
    نحاول إنشاء نافذة WebView صغيرة للتأكد أن الـ runtime موجود.
    إذا فشلنا نرجع False ونستخدم العارض الخارجي.
    """
    global _WEBVIEW_AVAILABLE
    if webview is None:
        _WEBVIEW_AVAILABLE = False
        return False
    if _WEBVIEW_AVAILABLE is not None:
        return _WEBVIEW_AVAILABLE
    try:
        window = webview.create_window("probe", html="<html></html>", hidden=True)

        def _close():
            window.destroy()

        webview.start(func=_close, debug=False)
        _WEBVIEW_AVAILABLE = True
    except Exception:
        _WEBVIEW_AVAILABLE = False
    return _WEBVIEW_AVAILABLE


def show_pdf_in_app(pdf_path: Path):
    """
    عرض ملف PDF داخل نافذة WebView2 (إذا أمكن)،
    وإلا نفتح الملف في عارض النظام الافتراضي.
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        Messagebox.show_error(f"ملف PDF غير موجود:\n{pdf_path}", "خطأ")
        return

    if can_use_webview():
        try:
            uri = pdf_path.as_uri()
            window = webview.create_window(
                title=f"معاينة PDF — {pdf_path.name}",
                url=uri,
                width=900,
                height=700,
                resizable=True,
            )
            webview.start(debug=False)
            return
        except Exception:
            Messagebox.show_warning(
                "تعذّر استخدام WebView2، سيتم فتح الملف بالعارض الافتراضي.",
                "تنبيه",
            )

    try:
        os.startfile(str(pdf_path))
    except Exception as exc:  # noqa: BLE001
        Messagebox.show_error(f"تعذر فتح ملف PDF:\n{exc}", "خطأ")
