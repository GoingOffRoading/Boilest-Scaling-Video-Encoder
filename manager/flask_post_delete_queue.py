import sqlite3
import logging
from db_path import get_db_path

__all__ = ["delete_queue_logic"]


def delete_queue_logic():
    """
    Delete all queued items from the queue table
    
    Returns:
        tuple: (response_dict, status_code)
    """
    logging.info("[REQUEST] POST /api/v2/queue/delete")
    
    try:
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        
        # Delete all rows with status = 'queued'
        cur.execute("DELETE FROM queue WHERE status = 'queued'")
        deleted_count = cur.rowcount
        conn.commit()
        conn.close()
        
        logging.info(f"[SUCCESS] Deleted {deleted_count} queued items")
        return {
            'success': True,
            'deleted_count': deleted_count,
            'message': f'Successfully deleted {deleted_count} queued items'
        }, 200
        
    except Exception as e:
        logging.error(f"[ERROR] Failed to delete queued items: {e}")
        return {
            'success': False,
            'error': str(e)
        }, 500
