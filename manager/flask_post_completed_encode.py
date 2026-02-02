import sqlite3
import logging
from datetime import datetime
from db_path import get_db_path

__all__ = ["post_completed_encode_logic"]


def post_completed_encode_logic(request_data):
    logging.info("\n" + "="*80)
    logging.info("[REQUEST] POST /api/completed")
    logging.info("="*80)

    try:
        # Get JSON data from request
        logging.debug(f"[REQUEST] Received data: {request_data}")

        # Validate required fields
        if not request_data:
            logging.error("[ERROR] No JSON data provided")
            return {
                'success': False,
                'error': 'No JSON data provided'
            }, 400

        file_guid = request_data.get('file_guid')
        after_file_size = request_data.get('after_file_size')
        outcome = request_data.get('outcome')
        datetime_encoded = datetime.now().isoformat()

        if not file_guid:
            logging.error("[ERROR] Missing required field: file_guid")
            return {
                'success': False,
                'error': 'Missing required field: file_guid'
            }, 400

        if not outcome:
            logging.error("[ERROR] Missing required field: outcome")
            return {
                'success': False,
                'error': 'Missing required field: outcome'
            }, 400

        # Connect to database
        db_path = get_db_path()
        logging.debug(f"[DB] Database path: {db_path}")
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        logging.info("[DB] Connected to database successfully")

        # Update queue table with encoded status and file size
        update_query = """
            UPDATE queue
            SET datetime_encoded = ?, after_file_size = COALESCE(?, after_file_size), status = ?
            WHERE file_guid = ?
        """
        logging.debug(f"[UPDATE] Updating queue - file_guid: {file_guid}, after_file_size: {after_file_size}, outcome: {outcome}, datetime_encoded: {datetime_encoded}")
        cur.execute(update_query, (datetime_encoded, after_file_size, outcome, file_guid))
        
        rows_affected = cur.rowcount
        conn.commit()

        # Get the updated record to return it
        cur.execute("SELECT file_guid, directory_path, input_file_name, output_file_name, before_file_size, after_file_size, datetime_encoded, status FROM queue WHERE file_guid = ?", (file_guid,))
        row = cur.fetchone()

        cur.close()
        conn.close()
        logging.info(f"[DB] Updated {rows_affected} row(s)")
        logging.debug("[DB] Connection closed")
        logging.info("="*80 + "\n")

        if row:
            result = {
                'file_guid': row[0],
                'directory_path': row[1],
                'input_file_name': row[2],
                'output_file_name': row[3],
                'before_file_size': row[4],
                'after_file_size': row[5],
                'datetime_encoded': row[6],
                'status': row[7]
            }
            return {
                'success': True,
                'message': 'Queue record updated successfully',
                'data': result
            }, 200
        else:
            return {
                'success': False,
                'error': f'No queue record found with file_guid: {file_guid}'
            }, 404

    except Exception as e:
        logging.error(f"[ERROR] Exception occurred: {type(e).__name__}")
        logging.error(f"[ERROR] Error message: {str(e)}")
        logging.error("="*80 + "\n"
        return {
            'success': False,
            'error': str(e)
        }, 500
