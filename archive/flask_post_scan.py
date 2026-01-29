import sqlite3
from ..scripts.manager.db.db_path import get_db_path
from .queue import scan_db_directories_and_write

__all__ = ["scan_logic", "check_queue_completion"]


def check_queue_completion(db_path=None):
    """
    Check if all queue items have been completed.
    Returns False if there are queue items not in completed table, True otherwise.
    """
    if db_path is None:
        db_path = get_db_path()
    
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        
        # LEFT JOIN to find queue items that don't have a matching completed entry
        query = """
            SELECT COUNT(*) 
            FROM queue q
            LEFT JOIN completed c ON q.guid = c.queued_file_guid
            WHERE c.guid IS NULL
        """
        
        cur.execute(query)
        uncompleted_count = cur.fetchone()[0]
        conn.close()
        
        # Return False if there are uncompleted items, True otherwise
        return uncompleted_count == 0
        
    except Exception as e:
        print(f"[ERROR] Error checking queue completion: {e}")
        return False


def scan_logic(db_disabled_ref):
    """
    Scan directories for video files and probe them to populate queue table
    Uses the scan_db_directories_and_write function from queue.py
    
    Args:
        db_disabled_ref (dict): Dictionary with 'value' key containing current DB_DISABLED state
        
    Returns:
        tuple: (response_data: dict, status_code: int)
    """
    print("\n" + "="*80)
    print("[REQUEST] POST /api/scan")
    print("="*80)

    db_path = str(get_db_path())

    # Only proceed if queue is already cleared/completed
    if not check_queue_completion(db_path):
        print("[SCAN] Queue still has uncompleted items; aborting scan.")
        return {
            'success': False,
            'error': 'Queue contains items not yet completed. Finish current queue before scanning again.'
        }, 409

    prev_db_disabled = db_disabled_ref['value']
    db_disabled_ref['value'] = True
    print("[DB] Database operations temporarily disabled for scan")

    try:
        # Scan directories and write to queue
        print("[SCAN] Scanning directories and processing files...")
        total_files = scan_db_directories_and_write(db_path)

        print(f"[SCAN] Complete: {total_files} files processed")

        return {
            'success': True,
            'message': 'Scan and queue completed',
            'results': {
                'files_processed': total_files
            }
        }, 200

    except Exception as e:
        print(f"[ERROR] Exception occurred: {type(e).__name__}")
        print(f"[ERROR] Error message: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }, 500

    finally:
        db_disabled_ref['value'] = prev_db_disabled
        state = 'disabled' if db_disabled_ref['value'] else 'enabled'
        print(f"[DB] Database operations restored to {state}")
        print("="*80 + "\n")
