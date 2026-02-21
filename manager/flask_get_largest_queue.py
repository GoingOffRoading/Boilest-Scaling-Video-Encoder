import sqlite3
from datetime import datetime
from db_path import get_db_path

__all__ = ["get_largest_queue_logic"]


def get_largest_queue_logic(db_disabled, worker):
    import logging
    logging.info("="*80)
    logging.info("[REQUEST] GET /api/v2/queue/largest")
    logging.info("="*80)

    # Check if database operations are disabled
    if db_disabled:
        logging.error("[DB] Database operations are currently disabled")
        logging.error("="*80)
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

        # First, check if this worker already has an assigned task
        if worker:
            check_existing_query = """
                SELECT 
                    file_guid,
                    directory_path,
                    input_file_name,
                    output_file_name,
                    before_file_size,
                    ffmpeg_string
                FROM queue q
                WHERE worker = ? AND status = 'pulled'
                LIMIT 1
            """
            logging.debug(f"[QUERY] Checking for existing task assigned to worker: {worker}")
            cur.execute(check_existing_query, (worker,))
            existing_row = cur.fetchone()
            
            if existing_row:
                logging.debug(f"[RESULT] Found existing task for worker: {worker}")
                conn.close()
                logging.debug("[DB] Connection closed")
                
                result = dict(existing_row)
                logging.info(f"[RESULT] Returning existing task for worker {worker}: {result['input_file_name']}")
                logging.info("="*80)
                return {
                    'success': True,
                    'data': result
                }, 200

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
                SET datetime_pulled = ?, status = 'pulled', worker = ?
                WHERE file_guid = ?
            """
            current_time = datetime.now()
            cur.execute(update_query, (current_time, worker, row["file_guid"]))
            conn.commit()

        conn.close()
        logging.debug("[DB] Connection closed")

        if row:
            # Convert row to dictionary
            result = dict(row)
            logging.info(f"[RESULT] Queued for encoding: {result['input_file_name']} ")
            logging.info("="*80)
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
