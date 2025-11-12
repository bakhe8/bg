from __future__ import annotations

from pathlib import Path
from flask import Blueprint, request, jsonify

from main.api.api_gateway import ApiGateway

bp = Blueprint('convert_excel_route', __name__)

gateway = ApiGateway(Path('main/data/archives'))


@bp.route('/api/v1/convert', methods=['POST'])
def convert_endpoint():
    uploaded = request.files.get('file')
    if not uploaded:
        return jsonify({'error': 'no file supplied'}), 400
    temp_path = Path('main/data/archives') / uploaded.filename
    uploaded.save(temp_path)
    try:
        payload = gateway.converter.convert_excel_to_json(str(temp_path), sheet_name=0, output_file=None)
        return jsonify({'data': payload})
    finally:
        if temp_path.exists():
            temp_path.unlink()
