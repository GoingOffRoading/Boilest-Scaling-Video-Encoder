import sqlite3
import logging
from datetime import datetime
from db_path import get_db_path

__all__ = ["get_index_data"]


def get_index_data():
    """
    Get data for the index page
    
    Returns:
        dict: Dictionary containing metrics, queued items, encoding items, and recently encoded items
    """
    logging.info("[UI] Fetching index page data")
    
    queued_count = 0
    encoded_count = 0
    space_saved_gb = 0.0
    queued_items = []
    encoding_items = []
    encoded_items = []
    
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
                directory_path,
                input_file_name,
                before_file_size,
                output_file_name,
                ffmpeg_string,
                datetime_added
            FROM queue 
            WHERE status = 'queued'
            ORDER BY before_file_size DESC
        """)
        queued_items = [dict(row) for row in cur.fetchall()]
        # Convert queued item sizes from KB to MB for display
        for item in queued_items:
            try:
                bfs = item.get('before_file_size')
                if bfs is not None:
                    item['before_file_size_mb'] = round(bfs / 1024, 2)
                else:
                    item['before_file_size_mb'] = None
            except Exception:
                item['before_file_size_mb'] = None

        logging.debug(f"[UI] Retrieved {len(queued_items)} queued items")
        
        # Get currently encoding items sorted by datetime_pulled ascending
        cur.execute("""
            SELECT 
                file_guid,
                directory_path,
                input_file_name,
                before_file_size,
                output_file_name,
                ffmpeg_string,
                datetime_added,
                datetime_pulled
            FROM queue 
            WHERE status = 'pulled'
            ORDER BY datetime_pulled ASC
        """)
        encoding_items = [dict(row) for row in cur.fetchall()]
        # Convert encoding item sizes from KB to MB for display
        for item in encoding_items:
            try:
                bfs = item.get('before_file_size')
                if bfs is not None:
                    item['before_file_size_mb'] = round(bfs / 1024, 2)
                else:
                    item['before_file_size_mb'] = None
            except Exception:
                item['before_file_size_mb'] = None

        logging.debug(f"[UI] Retrieved {len(encoding_items)} currently encoding items")
        
        # Get recently encoded items sorted by datetime_encoded descending
        cur.execute("""
            SELECT 
                output_file_name,
                directory_path,
                before_file_size - after_file_size as space_saved,
                datetime_pulled,
                datetime_encoded
            FROM queue 
            WHERE status = 'encoded'
            ORDER BY datetime_encoded DESC
            LIMIT 100
        """)
        encoded_items = [dict(row) for row in cur.fetchall()]

        # Compute encoding duration in minutes for each encoded item
        for item in encoded_items:
            dp = item.get('datetime_pulled')
            de = item.get('datetime_encoded')
            duration_minutes = None
            if dp and de:
                try:
                    dt_pulled = datetime.fromisoformat(dp)
                    dt_encoded = datetime.fromisoformat(de)
                    delta = dt_encoded - dt_pulled
                    duration_minutes = round(delta.total_seconds() / 60, 2)
                except Exception:
                    duration_minutes = None
            item['duration_minutes'] = duration_minutes

            # Convert space_saved from KB to MB for display
            try:
                ss = item.get('space_saved')
                if ss is not None:
                    item['space_saved_mb'] = round(ss / 1024, 2)
                else:
                    item['space_saved_mb'] = None
            except Exception:
                item['space_saved_mb'] = None

        logging.debug(f"[UI] Retrieved {len(encoded_items)} recently encoded items")
        
        conn.close()
    except Exception as e:
        logging.error(f"[ERROR] Failed to get index data: {e}")
    
    return {
        'queued_count': queued_count,
        'encoded_count': encoded_count,
        'space_saved_gb': space_saved_gb,
        'queued_items': queued_items,
        'encoding_items': encoding_items,
        'encoded_items': encoded_items
    }
