import sqlite3
import logging
from db_path import get_db_path

__all__ = ["get_index_data"]


def get_index_data():
    """
    Get data for the index page
    
    Returns:
        dict: Dictionary containing metrics and queued items
    """
    logging.info("[UI] Fetching index page data")
    
    queued_count = 0
    encoded_count = 0
    space_saved_gb = 0.0
    queued_items = []
    
    try:
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        # Get queued count
        cur.execute("SELECT COUNT(*) FROM queue WHERE status='queued'")
        queued_count = cur.fetchone()[0]
        logging.debug(f"[UI] Queued count: {queued_count}")
        
        # Get encoded count
        cur.execute("SELECT COUNT(*) FROM queue WHERE status='encoded'")
        encoded_count = cur.fetchone()[0]
        logging.debug(f"[UI] Encoded count: {encoded_count}")
        
        # Get space saved (in KB, convert to GB)
        cur.execute("SELECT SUM(before_file_size) - SUM(after_file_size) as space_saved FROM queue WHERE status='encoded'")
        space_saved_result = cur.fetchone()
        if space_saved_result and space_saved_result['space_saved'] is not None:
            space_saved_kb = space_saved_result['space_saved']
            space_saved_gb = round(space_saved_kb / (1024 * 1024), 2)
        logging.debug(f"[UI] Space saved: {space_saved_gb} GB")
        
        # Get queued items sorted by file size descending
        cur.execute("""
            SELECT 
                file_guid,
                input_file_name,
                before_file_size,
                output_file_name,
                datetime_added
            FROM queue 
            WHERE status = 'queued'
            ORDER BY before_file_size DESC
        """)
        queued_items = [dict(row) for row in cur.fetchall()]
        logging.debug(f"[UI] Retrieved {len(queued_items)} queued items")
        
        conn.close()
    except Exception as e:
        logging.error(f"[ERROR] Failed to get index data: {e}")
    
    return {
        'queued_count': queued_count,
        'encoded_count': encoded_count,
        'space_saved_gb': space_saved_gb,
        'queued_items': queued_items
    }
