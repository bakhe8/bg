from __future__ import annotations

import json

from flask import Blueprint, jsonify, request

from main.api.logging_utils import log_event
from main.config import COLUMN_ALIASES_PATH
from transition.backend.reference_loader import load_column_aliases


@bp.route("/api/aliases", methods=["GET"])
def list_aliases():
    aliases = load_column_aliases()
    return jsonify({"aliases": aliases})


@bp.route("/api/aliases", methods=["POST"])
def add_alias():
    payload = request.get_json(force=True) or {}
    canonical = (payload.get("canonical") or "").strip()
    alias = (payload.get("alias") or "").strip()

    if not canonical or not alias:
        return jsonify({"error": "الرجاء اختيار الحقل القياسي وإدخال اسم العمود."}), 400

    aliases = load_column_aliases()
    if canonical not in aliases:
        return jsonify({"error": "الحقل القياسي المحدد غير معروف."}), 400

    alias_key = alias.lower().strip()
    existing = {value.lower().strip() for value in aliases.get(canonical, [])}
    if alias_key in existing:
        return jsonify({"status": "exists", "message": "العمود مضاف مسبقًا."}), 200

    raw_data = _load_raw_config()
    raw_aliases = raw_data.setdefault(canonical, [])
    raw_aliases.append(alias)
    _write_raw_config(raw_data)
    load_column_aliases.cache_clear()
    log_event(
        "add_alias",
        {"canonical": canonical, "alias": alias},
        log_file="aliases.log",
    )
    return jsonify({"status": "added", "canonical": canonical, "alias": alias}), 201


def _load_raw_config():
    if not COLUMN_ALIASES_PATH.exists():
        raise FileNotFoundError(f"لم يتم العثور على ملف الأعمدة المرجعي: {COLUMN_ALIASES_PATH}")
    with COLUMN_ALIASES_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def _write_raw_config(data):
    with COLUMN_ALIASES_PATH.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
