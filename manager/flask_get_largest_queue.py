import sqlite3
from db_path import get_db_path

__all__ = ["get_largest_queue_logic"]


def get_largest_queue_logic(db_disabled):
    print("\n" + "="*80)
    print("[REQUEST] GET /api/queue/largest")
    print("="*80)

    # Check if database operations are disabled
    if db_disabled:
        print("[DB] Database operations are currently disabled")
        print("="*80 + "\n")
        return {
            'success': False,
            'error': 'Database operations are temporarily disabled'
        }, 503

    try:
        db_path = get_db_path()
        print(f"[DB] Database path: {db_path}")

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # This allows accessing columns by name
        cur = conn.cursor()
        print("[DB] Connected to database successfully")

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
            WHERE datetime_pulled IS NULL AND datetime_encoded IS NULL
            ORDER BY before_file_size DESC
            LIMIT 1
        """
        print("[QUERY] Executing query to fetch largest queue by before_file_size...")
        cur.execute(query)

        row = cur.fetchone()
        print(f"[QUERY] Query executed successfully")
        print(f"[RESULT] Row found: {row is not None}")

        if row:
            update_query = """
                UPDATE queue
                SET datetime_pulled = CURRENT_TIMESTAMP
                WHERE file_guid = ?
            """
            cur.execute(update_query, (row["file_guid"],))
            conn.commit()

        conn.close()
        print("[DB] Connection closed")

        if row:
            # Convert row to dictionary
            result = dict(row)
            print(f"[RESULT] Returning queue record with before_file_size: {result['before_file_size']} bytes")
            print("="*80 + "\n")
            return {
                'success': True,
                'data': result
            }, 200
        else:
            print("[RESULT] No records found in queue table")
            print("="*80 + "\n")
            return {
                'success': True,
                'data': None,
                'message': 'No records found in queue table'
            }, 200

    except Exception as e:
        print(f"[ERROR] Exception occurred: {type(e).__name__}")
        print(f"[ERROR] Error message: {str(e)}")
        print("="*80 + "\n")
        return {
            'success': False,
            'error': str(e)
        }, 500
