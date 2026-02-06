import sqlite3
import logging
from db_path import get_db_path

__all__ = ["get_index_data"]


def get_index_data():
    """
    Get data for the index page
    
    Returns:
        dict: Dictionary containing queued_count and other metrics
    """
    logging.info("[UI] Fetching index page data")
    
    # Get count of queued items
    queued_count = 0
    try:
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM queue WHERE status='queued'")
        queued_count = cur.fetchone()[0]
        conn.close()
        logging.debug(f"[UI] Queued count: {queued_count}")
    except Exception as e:
        logging.error(f"[ERROR] Failed to get queued count: {e}")
    
    return {
        'queued_count': queued_count
    }
