import sqlite3
from datetime import datetime
from db_path import get_db_path

__all__ = ["post_completed_encode_logic"]


def post_completed_encode_logic(request_data):
    print("\n" + "="*80)
    print("[REQUEST] POST /api/completed")
    print("="*80)

    try:
        # Get JSON data from request
        print(f"[REQUEST] Received data: {request_data}")

        # Validate required fields
        if not request_data:
            print("[ERROR] No JSON data provided")
            return {
                'success': False,
                'error': 'No JSON data provided'
            }, 400

        queued_file_guid = request_data.get('queued_file_guid')
        after_file_size = request_data.get('after_file_size')
        date_added = datetime.now().isoformat()

        if not queued_file_guid:
            print("[ERROR] Missing required field: queued_file_guid")
            return {
                'success': False,
                'error': 'Missing required field: queued_file_guid'
            }, 400

        if after_file_size is None:
            print("[ERROR] Missing required field: after_file_size")
            return {
                'success': False,
                'error': 'Missing required field: after_file_size'
            }, 400

        # Connect to database
        db_path = get_db_path()
        print(f"[DB] Database path: {db_path}")
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        print("[DB] Connected to database successfully")

        # Insert into completed table with current datetime
        query = """
            INSERT INTO completed (queued_file_guid, after_file_size, date_added)
            VALUES (?, ?, ?)
        """
        print(f"[INSERT] Inserting record - queued_file_guid: {queued_file_guid}, after_file_size: {after_file_size}, date_added: {date_added}")
        cur.execute(query, (queued_file_guid, after_file_size, date_added))
        
        conn.commit()

        # Get the inserted record to return it
        cur.execute("SELECT guid, queued_file_guid, after_file_size, date_added FROM completed WHERE queued_file_guid = ?", (queued_file_guid,))
        row = cur.fetchone()

        conn.close()
        print("[DB] Record inserted successfully")
        print("[DB] Connection closed")
        print("="*80 + "\n")

        if row:
            result = {
                'guid': row[0],
                'queued_file_guid': row[1],
                'after_file_size': row[2],
                'date_added': row[3]
            }
            return {
                'success': True,
                'message': 'Record created successfully',
                'data': result
            }, 201
        else:
            return {
                'success': False,
                'error': 'Record created but could not be retrieved'
            }, 500

    except sqlite3.IntegrityError as e:
        print(f"[ERROR] Integrity error: {str(e)}")
        print("="*80 + "\n")
        return {
            'success': False,
            'error': f'Database integrity error: {str(e)} (queued_file_guid may already exist)'
        }, 409
    except Exception as e:
        print(f"[ERROR] Exception occurred: {type(e).__name__}")
        print(f"[ERROR] Error message: {str(e)}")
        print("="*80 + "\n")
        return {
            'success': False,
            'error': str(e)
        }, 500
