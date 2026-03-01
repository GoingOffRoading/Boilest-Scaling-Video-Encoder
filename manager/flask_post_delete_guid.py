from flask import Blueprint, request, jsonify
from db_path import get_db_path
import sqlite3

bp = Blueprint('delete_guid', __name__)

@bp.route('/api/v2/queue/delete-guid', methods=['POST'])
def delete_guid():
    data = request.get_json()
    guid = data.get('guid')
    if not guid:
        return jsonify({'error': 'No GUID provided'}), 400
    db_path = get_db_path()
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute('DELETE FROM queue WHERE guid = ?', (guid,))
        deleted_count = cur.rowcount
        conn.commit()
        conn.close()
        return jsonify({'deleted_count': deleted_count}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
