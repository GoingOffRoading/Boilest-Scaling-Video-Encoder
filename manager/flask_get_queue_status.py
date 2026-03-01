import sqlite3
import logging
from db_path import get_db_path

__all__ = ["get_queue_status_logic"]


def get_queue_status_logic(file_guid):
    logging.info("="*80 + "\n")
    logging.info("[REQUEST] GET /api/v2/queue/status")

    if not file_guid:
        logging.error("[ERROR] Missing required query parameter: file_guid")
        return {
            'success': False,
            'error': 'Missing required parameter: file_guid'
        }, 400

    try:
        db_path = get_db_path()
        logging.debug(f"[DB] Database path: {db_path}")

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        cur.execute("SELECT file_guid, directory_path, input_file_name, output_file_name, before_file_size, after_file_size, datetime_pulled, datetime_encoded, status FROM queue WHERE file_guid = ?", (file_guid,))
        row = cur.fetchone()

        cur.close()
        conn.close()
        logging.debug("[DB] Connection closed")
        logging.info("\n" + "="*80)

        if row:
            result = {
                'file_guid': row[0],
                'directory_path': row[1],
                'input_file_name': row[2],
                'output_file_name': row[3],
                'before_file_size': row[4],
                'after_file_size': row[5],
                'datetime_pulled': row[6],
                'datetime_encoded': row[7],
                'status': row[8]
            }
            return {
                'success': True,
                'data': result
            }, 200
        else:
            return {
                'success': True,
                'data': None,
                'message': 'No record found with that file_guid'
            }, 200

    except Exception as e:
        logging.error(f"[ERROR] Exception occurred: {type(e).__name__}")
        logging.error(f"[ERROR] Error message: {str(e)}")
        logging.error("="*80)
        return {
            'success': False,
            'error': str(e)
        }, 500
