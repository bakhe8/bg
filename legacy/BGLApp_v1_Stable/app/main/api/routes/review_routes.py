from __future__ import annotations

from flask import Blueprint, jsonify, request

from main.api.logging_utils import log_event
from main.api.review_store import (
    ignore_column,
    list_ignored_columns,
    load_unknown_columns,
    unignore_column,
)

bp = Blueprint("review_routes", __name__)


@bp.route("/api/review/unknown-columns", methods=["GET"])
def review_unknown_columns():
    columns = load_unknown_columns()
    return jsonify({"columns": columns, "ignored": list_ignored_columns()})


@bp.route("/api/review/ignore", methods=["POST"])
def review_ignore_column():
    payload = request.get_json(force=True) or {}
    label = (payload.get("label") or "").strip()
    if not label:
        return jsonify({"error": "الرجاء تحديد اسم العمود"}), 400
    ignore_column(label)
    log_event("review_ignore", {"label": label}, log_file="review.log")
    return jsonify({"status": "ignored", "label": label})


@bp.route("/api/review/ignore", methods=["DELETE"])
def review_unignore_column():
    payload = request.get_json(force=True) or {}
    label = (payload.get("label") or "").strip()
    if not label:
        return jsonify({"error": "الرجاء تحديد اسم العمود"}), 400
    unignore_column(label)
    log_event("review_unignore", {"label": label}, log_file="review.log")
    return jsonify({"status": "restored", "label": label})
