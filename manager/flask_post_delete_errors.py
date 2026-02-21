import sqlite3
import logging
from db_path import get_db_path

__all__ = ["delete_errors_logic"]


def delete_errors_logic(status_value, guids=None):
    """
    Delete all error records from the queue table matching the given status.
    
    Returns:
        tuple: (response_dict, status_code)
    """
    logging.info("[REQUEST] POST /api/v2/queue/delete-errors")

    if not status_value and not guids:
        return {'success': False, 'error': 'Missing required status value or guids'}, 400
    
    try:
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        
        deleted_count = 0
        if guids:
            # Delete only specific GUIDs
            placeholders = ','.join('?' for _ in guids)
            query = f"DELETE FROM queue WHERE file_guid IN ({placeholders})"
            cur.execute(query, tuple(guids))
            deleted_count = cur.rowcount
        else:
            # Delete all rows with the provided status
            cur.execute("DELETE FROM queue WHERE status = ?", (status_value,))
            deleted_count = cur.rowcount
        conn.commit()
        conn.close()
        
        logging.info(f"[SUCCESS] Deleted {deleted_count} records for status: {status_value}")
        return {
            'success': True,
            'deleted_count': deleted_count,
            'message': f'Successfully deleted {deleted_count} records'
        }, 200
        
    except Exception as e:
        logging.error(f"[ERROR] Failed to delete records for status {status_value}: {e}")
        return {
            'success': False,
            'error': str(e)
        }, 500
