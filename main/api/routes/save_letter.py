from __future__ import annotations

from pathlib import Path
from flask import Blueprint, request, jsonify

bp = Blueprint('save_letter_route', __name__)
TARGET_DIR = Path('main/data/exports')
TARGET_DIR.mkdir(parents=True, exist_ok=True)


@bp.route('/api/v1/letters', methods=['POST'])
def save_letter():
    payload = request.get_json(force=True)
    filename = payload.get('filename', 'letter.json')
    target = TARGET_DIR / filename
    target.write_text(request.data.decode('utf-8'), encoding='utf-8')
    return jsonify({'status': 'saved', 'path': str(target)}), 201
