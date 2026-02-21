import sqlite3
import logging
from db_path import get_db_path

__all__ = ["get_failed_by_status_logic"]


def get_failed_by_status_logic(status_value):
    logging.info("\n" + "="*80)
    logging.info(f"[REQUEST] GET /api/v2/queue/failed?status={status_value}")
    logging.info("="*80)
    if not status_value:
        return {'success': False, 'error': 'Missing status parameter'}, 400
    try:
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        cur.execute(
            """
            SELECT file_guid, input_file_name, directory_path, datetime_pulled, status, worker
            FROM queue
            WHERE status = ?
            ORDER BY datetime_pulled DESC
            LIMIT 1000
            """,
            (status_value,)
        )
        rows = [dict(r) for r in cur.fetchall()]

        cur.close()
        conn.close()
        logging.info("="*80 + "\n")
        return {'success': True, 'data': rows}, 200
    except Exception as e:
        logging.error(f"[ERROR] Exception fetching failed rows: {e}")
        return {'success': False, 'error': str(e)}, 500
