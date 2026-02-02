import sqlite3
from datetime import datetime
from db_path import get_db_path

__all__ = ["get_largest_queue_logic"]


def get_largest_queue_logic(db_disabled):
    import logging
    logging.info("\n" + "="*80)
    logging.info("[REQUEST] GET /api/queue/largest")
    logging.info("="*80)

    # Check if database operations are disabled
    if db_disabled:
        logging.error("[DB] Database operations are currently disabled")
        logging.error("="*80 + "\n")
        return {
            'success': False,
            'error': 'Database operations are temporarily disabled'
        }, 503

    try:
        db_path = get_db_path()
        logging.debug(f"[DB] Database path: {db_path}")

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # This allows accessing columns by name
        cur = conn.cursor()
        logging.debug("[DB] Connected to database successfully")

        # Query the encode table sorted by before_file_size descending, limit 1
        query = """
            SELECT 
                file_guid,
                directory_path,
                input_file_name,
                output_file_name,
                before_file_size,
                ffmpeg_string
            FROM queue q
            WHERE status = 'queued'
            ORDER BY before_file_size DESC
            LIMIT 1
        """
        logging.debug("[QUERY] Executing query to fetch largest queue by before_file_size...")
        cur.execute(query)

        row = cur.fetchone()
        logging.debug(f"[QUERY] Query executed successfully")
        logging.debug(f"[RESULT] Row found: {row is not None}")

        if row:
            update_query = """
                UPDATE queue
                SET datetime_pulled = ?, status = 'pulled'
                WHERE file_guid = ?
            """
            current_time = datetime.now()
            cur.execute(update_query, (current_time, row["file_guid"]))
            conn.commit()

        conn.close()
        logging.debug("[DB] Connection closed")

        if row:
            # Convert row to dictionary
            result = dict(row)
            logging.info(f"[RESULT] Queued for encoding: {result['input_file_name']} ")
            logging.info("="*80 + "\n")
            return {
                'success': True,
                'data': result
            }, 200
        else:
            logging.info("[RESULT] No records found in queue table")
            logging.info("="*80 + "\n")
            return {
                'success': True,
                'data': None,
                'message': 'No records found in queue table'
            }, 200

    except Exception as e:
        logging.error(f"[ERROR] Exception occurred: {type(e).__name__}")
        logging.error(f"[ERROR] Error message: {str(e)}")
        logging.error("="*80 + "\n")
        return {
            'success': False,
            'error': str(e)
        }, 500
