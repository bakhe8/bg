#!/usr/bin/env python3
"""
Portable updater for BGLApp.
Checks remote manifest and applies updates automatically when configured.
"""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path

import requests


def parse_version(value: str) -> tuple[int, ...]:
    parts = []
    for token in value.split("."):
        try:
            parts.append(int(token))
        except ValueError:
            parts.append(0)
    return tuple(parts)


@dataclass
class PortableUpdater:
    base_dir: Path = Path(__file__).resolve().parent.parent

    def __post_init__(self):
        self.manifest_path = self.base_dir / "release_manifest.json"
        self.app_dir = self.base_dir / "app"
        self.main_dir = self.app_dir / "main"
        self.runtime_dir = self.app_dir / "portable_runtime"
        self.remote_manifest_url = os.environ.get("BGLAPP_UPDATE_MANIFEST_URL")
        self.remote_package_url = os.environ.get("BGLAPP_UPDATE_PACKAGE_URL")

    def run(self, auto: bool = False):
        if not self.remote_manifest_url or not self.remote_package_url:
            if not auto:
                print("⚠️  لم يتم ضبط متغيرات البيئة BGLAPP_UPDATE_MANIFEST_URL و BGLAPP_UPDATE_PACKAGE_URL.")
            return
        local_manifest = self._load_local_manifest()
        remote_manifest = self._fetch_remote_manifest()
        if not remote_manifest:
            print("⚠️  تعذر تحميل ملف الإصدار البعيد.")
            return
        local_version = parse_version(local_manifest.get("version", "0.0.0"))
        remote_version = parse_version(remote_manifest.get("version", "0.0.0"))
        if remote_version <= local_version:
            if not auto:
                print(f"✅ النسخة الحالية ({local_manifest.get('version')}) هي الأحدث.")
            return
        if not auto:
            print(f"✨ إصدار جديد متوفر: {remote_manifest.get('version')} (الحالي {local_manifest.get('version')})")
        self._download_and_apply(remote_manifest)
        self._write_manifest(remote_manifest)
        print("✅ تم تحديث التطبيق بنجاح.")

    def _load_local_manifest(self) -> dict:
        if not self.manifest_path.exists():
            return {}
        try:
            import json

            return json.loads(self.manifest_path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            return {}

    def _write_manifest(self, data: dict):
        import json

        self.manifest_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _fetch_remote_manifest(self) -> dict | None:
        try:
            response = requests.get(self.remote_manifest_url, timeout=15)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            print(f"⚠️  تعذر تحميل ملف الإصدار البعيد: {exc}")
            return None

    def _download_and_apply(self, remote_manifest: dict):
        try:
            response = requests.get(self.remote_package_url, timeout=60)
            response.raise_for_status()
        except requests.RequestException as exc:
            print(f"⚠️  تعذر تحميل حزمة التحديث: {exc}")
            return
        with tempfile.TemporaryDirectory() as tmp_dir:
            zip_path = Path(tmp_dir) / "update.zip"
            zip_path.write_bytes(response.content)
            extract_dir = Path(tmp_dir) / "extracted"
            extract_dir.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(extract_dir)
            main_candidate = self._find_main_directory(extract_dir)
            if not main_candidate:
                print("⚠️  الحزمة لا تحتوي على مجلد main صالح.")
                return
            backup_dir = self.main_dir.with_suffix(".backup")
            if backup_dir.exists():
                shutil.rmtree(backup_dir)
            if self.main_dir.exists():
                self.main_dir.rename(backup_dir)
            shutil.copytree(main_candidate, self.main_dir)

    @staticmethod
    def _find_main_directory(root: Path) -> Path | None:
        candidates = list(root.rglob("main"))
        for candidate in candidates:
            if (candidate / "api").exists() and (candidate / "bg_ui").exists():
                return candidate
        return None


if __name__ == "__main__":
    PortableUpdater().run()
