from __future__ import annotations

from pathlib import Path
from pydantic import BaseSettings


ROOT_DIR = Path(__file__).resolve().parents[1]
WEB_DIR = ROOT_DIR / "bg_ui"
TEMPLATES_DIR = WEB_DIR / "templates"
ASSETS_DIR = WEB_DIR / "assets"
DATA_DIR = ROOT_DIR / "data"
ARCHIVES_DIR = DATA_DIR / "archives"
EXPORTS_DIR = DATA_DIR / "exports"
LOGS_DIR = DATA_DIR / "logs"
REVIEW_DIR = DATA_DIR / "review"

REFERENCE_DIR = ROOT_DIR.parent / "transition" / "backend" / "config"
COLUMN_ALIASES_PATH = REFERENCE_DIR / "column_aliases.json"

for path in (ARCHIVES_DIR, EXPORTS_DIR, LOGS_DIR, REVIEW_DIR):
    path.mkdir(parents=True, exist_ok=True)


class Settings(BaseSettings):
    monitor_user: str | None = None
    monitor_pass: str | None = None
    alert_webhook: str | None = None
    alert_timeout: float = 5.0

    class Config:
        env_prefix = "BGLAPP_"
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
