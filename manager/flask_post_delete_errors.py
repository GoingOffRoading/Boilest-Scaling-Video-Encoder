import sqlite3
import logging
from db_path import get_db_path

__all__ = ["delete_errors_logic"]


def delete_errors_logic():
    """
    Delete all error records from the queue table (status starts with 'Failed')
    
    Returns:
        tuple: (response_dict, status_code)
    """
    logging.info("[REQUEST] POST /api/queue/delete-errors")
    
    try:
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        
        # Delete all rows with status starting with 'Failed'
        cur.execute("DELETE FROM queue WHERE status LIKE 'Failed%'")
        deleted_count = cur.rowcount
        conn.commit()
        conn.close()
        
        logging.info(f"[SUCCESS] Deleted {deleted_count} failed records")
        return {
            'success': True,
            'deleted_count': deleted_count,
            'message': f'Successfully deleted {deleted_count} failed records'
        }, 200
        
    except Exception as e:
        logging.error(f"[ERROR] Failed to delete failed records: {e}")
        return {
            'success': False,
            'error': str(e)
        }, 500
