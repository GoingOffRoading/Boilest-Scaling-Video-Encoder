import sqlite3
import logging
from db_path import get_db_path

__all__ = ["get_encoding_queue_logic"]


def get_encoding_queue_logic():
    logging.info("\n" + "="*80)
    logging.info("[REQUEST] GET /api/v2/queue/encoding")
    logging.info("="*80)
    try:
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        cur.execute("""
            SELECT
                file_guid,
                directory_path,
                input_file_name,
                before_file_size,
                output_file_name,
                ffmpeg_string,
                datetime_added,
                datetime_pulled,
                worker
            FROM queue
            WHERE status = 'pulled'
            ORDER BY datetime_pulled ASC
        """)
        rows = [dict(r) for r in cur.fetchall()]
        # convert sizes to KB/MB consistency if needed
        for item in rows:
            try:
                bfs = item.get('before_file_size')
                if bfs is not None:
                    item['before_file_size_mb'] = round(bfs / 1024, 2)
                else:
                    item['before_file_size_mb'] = None
            except Exception:
                item['before_file_size_mb'] = None

        cur.close()
        conn.close()
        logging.info("="*80 + "\n")
        return {
            'success': True,
            'data': rows
        }, 200
    except Exception as e:
        logging.error(f"[ERROR] Exception fetching encoding queue: {e}")
        return {
            'success': False,
            'error': str(e)
        }, 500
