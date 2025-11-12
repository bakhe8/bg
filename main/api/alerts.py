from __future__ import annotations

from typing import Any, Dict

import requests

from main.config import settings


def notify_failure(event: str, metadata: Dict[str, Any]) -> None:
    """Send a lightweight webhook notification when critical failures happen."""
    webhook_url = settings.alert_webhook
    if not webhook_url:
        return
    payload = {
        "text": f"[BGLApp] حدث خطأ في {event}",
        "event": event,
        "metadata": metadata,
    }
    try:
        requests.post(
            webhook_url,
            json=payload,
            timeout=settings.alert_timeout,
            headers={"Content-Type": "application/json"},
        )
    except requests.RequestException:
        # نتجاهل فشل التنبيه حتى لا يوقف المسار الأساسي
        pass
