from flask import Flask, jsonify, request, render_template
import sqlite3
from pathlib import Path
from scripts.db_status import get_database_status
from scripts.queue import scan_db_directories_and_write

app = Flask(__name__)

# Global flag to disable database operations
DB_DISABLED = False

def get_db_path():
    """Get the path to the boilest.db database"""
    return Path.cwd() / 'boilest.db'


@app.route('/', methods=['GET'])
def index():
    """Serve the main UI page"""
    print("[UI] Serving main page")
    return render_template('index.html')


@app.route('/api/encode/largest', methods=['GET'])
def get_largest_encode():
    """
    Query the encode table and return one row sorted by before_file_size DESC limit 1
    """
    print("\n" + "="*80)
    print("[REQUEST] GET /api/encode/largest")
    print("="*80)

    # Check if database operations are disabled
    if DB_DISABLED:
        print("[DB] Database operations are currently disabled")
        print("="*80 + "\n")
        return jsonify({
            'success': False,
            'error': 'Database operations are temporarily disabled'
        }), 503

    try:
        db_path = get_db_path()
        print(f"[DB] Database path: {db_path}")
        print(f"[DB] Database exists: {db_path.exists()}")

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # This allows accessing columns by name
        cur = conn.cursor()
        print("[DB] Connected to database successfully")

        # Query the encode table sorted by before_file_size descending, limit 1
        query = """
            SELECT 
                guid,
                directory_path,
                input_file_name,
                output_file_name,
                before_file_size,
                decision,
                ffmpeg_string,
                date_added
            FROM encode
            ORDER BY before_file_size DESC
            LIMIT 1
        """
        print("[QUERY] Executing query to fetch largest encode by before_file_size...")
        cur.execute(query)

        row = cur.fetchone()
        print(f"[QUERY] Query executed successfully")
        print(f"[RESULT] Row found: {row is not None}")

        conn.close()
        print("[DB] Connection closed")

        if row:
            # Convert row to dictionary
            result = dict(row)
            print(f"[RESULT] Returning encode record with before_file_size: {result['before_file_size']} bytes")
            print("="*80 + "\n")
            return jsonify({
                'success': True,
                'data': result
            }), 200
        else:
            print("[RESULT] No records found in encode table")
            print("="*80 + "\n")
            return jsonify({
                'success': True,
                'data': None,
                'message': 'No records found in encode table'
            }), 200

    except Exception as e:
        print(f"[ERROR] Exception occurred: {type(e).__name__}")
        print(f"[ERROR] Error message: {str(e)}")
        print("="*80 + "\n")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/encoded', methods=['POST'])
def create_encoded():
    """
    Write a new record to the encoded table
    Expects JSON body with: guid, after_file_size
    date_added is automatically set by the database
    """
    print("\n" + "="*80)
    print("[REQUEST] POST /api/encoded")
    print("="*80)

    # Check if database operations are disabled
    if DB_DISABLED:
        print("[DB] Database operations are currently disabled")
        print("="*80 + "\n")
        return jsonify({
            'success': False,
            'error': 'Database operations are temporarily disabled'
        }), 503

    try:
        # Get JSON data from request
        data = request.get_json()
        print(f"[REQUEST] Received data: {data}")

        # Validate required fields
        if not data:
            print("[ERROR] No JSON data provided")
            return jsonify({
                'success': False,
                'error': 'No JSON data provided'
            }), 400

        guid = data.get('guid')
        after_file_size = data.get('after_file_size')

        if not guid:
            print("[ERROR] Missing required field: guid")
            return jsonify({
                'success': False,
                'error': 'Missing required field: guid'
            }), 400

        if after_file_size is None:
            print("[ERROR] Missing required field: after_file_size")
            return jsonify({
                'success': False,
                'error': 'Missing required field: after_file_size'
            }), 400

        # Connect to database
        db_path = get_db_path()
        print(f"[DB] Database path: {db_path}")
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        print("[DB] Connected to database successfully")

        # Insert into encoded table
        # date_added will be set automatically by DEFAULT CURRENT_TIMESTAMP
        query = """
            INSERT INTO encoded (guid, after_file_size)
            VALUES (?, ?)
        """
        print(f"[INSERT] Inserting record - guid: {guid}, after_file_size: {after_file_size}")
        cur.execute(query, (guid, after_file_size))
        conn.commit()

        # Get the inserted record to return it
        cur.execute("SELECT guid, after_file_size, date_added FROM encoded WHERE guid = ?", (guid,))
        row = cur.fetchone()

        conn.close()
        print("[DB] Record inserted successfully")
        print("[DB] Connection closed")
        print("="*80 + "\n")

        if row:
            result = {
                'guid': row[0],
                'after_file_size': row[1],
                'date_added': row[2]
            }
            return jsonify({
                'success': True,
                'message': 'Record created successfully',
                'data': result
            }), 201
        else:
            return jsonify({
                'success': False,
                'error': 'Record created but could not be retrieved'
            }), 500

    except sqlite3.IntegrityError as e:
        print(f"[ERROR] Integrity error: {str(e)}")
        print("="*80 + "\n")
        return jsonify({
            'success': False,
            'error': f'Database integrity error: {str(e)} (guid may already exist)'
        }), 409
    except Exception as e:
        print(f"[ERROR] Exception occurred: {type(e).__name__}")
        print(f"[ERROR] Error message: {str(e)}")
        print("="*80 + "\n")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def check_queue_completion(db_path='boilest.db'):
    """
    Check if all queue items have been completed.
    Returns False if there are queue items not in completed table, True otherwise.
    """
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


@app.route('/api/scan', methods=['POST'])
def scan():
    """
    Scan directories for video files and probe them to populate queue table
    Uses the scan_db_directories_and_write function from queue.py
    """
    print("\n" + "="*80)
    print("[REQUEST] POST /api/scan")
    print("="*80)

    db_path = str(get_db_path())

    # Only proceed if queue is already cleared/completed
    if not check_queue_completion(db_path):
        print("[SCAN] Queue still has uncompleted items; aborting scan.")
        return jsonify({
            'success': False,
            'error': 'Queue contains items not yet completed. Finish current queue before scanning again.'
        }), 409

    global DB_DISABLED
    prev_db_disabled = DB_DISABLED
    DB_DISABLED = True
    print("[DB] Database operations temporarily disabled for scan")

    try:
        # Scan directories and write to queue
        print("[SCAN] Scanning directories and processing files...")
        total_files = scan_db_directories_and_write(db_path)

        print(f"[SCAN] Complete: {total_files} files processed")

        return jsonify({
            'success': True,
            'message': 'Scan and queue completed',
            'results': {
                'files_processed': total_files
            }
        }), 200

    except Exception as e:
        print(f"[ERROR] Exception occurred: {type(e).__name__}")
        print(f"[ERROR] Error message: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

    finally:
        DB_DISABLED = prev_db_disabled
        state = 'disabled' if DB_DISABLED else 'enabled'
        print(f"[DB] Database operations restored to {state}")
        print("="*80 + "\n")


@app.route('/api/db/toggle', methods=['POST'])
def toggle_database():
    """
    Toggle the database operations on/off
    Expects JSON body with: enabled (boolean)
    """
    global DB_DISABLED

    print("\n" + "="*80)
    print("[REQUEST] POST /api/db/toggle")
    print("="*80)

    try:
        data = request.get_json()

        if not data or 'enabled' not in data:
            print("[ERROR] Missing 'enabled' field in request")
            return jsonify({
                'success': False,
                'error': "Missing required field: 'enabled' (boolean)"
            }), 400

        enabled = data.get('enabled')

        if not isinstance(enabled, bool):
            print("[ERROR] 'enabled' field must be a boolean")
            return jsonify({
                'success': False,
                'error': "'enabled' field must be a boolean"
            }), 400

        # enabled=True means DB should be active (DB_DISABLED=False)
        # enabled=False means DB should be disabled (DB_DISABLED=True)
        DB_DISABLED = not enabled

        status = "enabled" if enabled else "disabled"
        print(f"[DB] Database operations {status}")
        print("="*80 + "\n")

        return jsonify({
            'success': True,
            'message': f'Database operations {status}',
            'db_enabled': enabled
        }), 200

    except Exception as e:
        print(f"[ERROR] Exception occurred: {type(e).__name__}")
        print(f"[ERROR] Error message: {str(e)}")
        print("="*80 + "\n")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/db/status', methods=['GET'])
def database_status():
    """
    Get the current status of database operations
    """
    print("[REQUEST] GET /api/db/status")

    status_data = get_database_status(DB_DISABLED)

    return jsonify(status_data), 200


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    print("[HEALTH CHECK] Endpoint called")
    return jsonify({'status': 'healthy'}), 200


if __name__ == '__main__':
    print("\n" + "="*80)
    print("Starting Encode API Server...")
    print("="*80)
    print("Available endpoints:")
    print("  - GET  /                    (Main UI page)")
    print("  - GET  /api/encode/largest  (Get largest encode by file size)")
    print("  - POST /api/encoded         (Create new encoded record)")
    print("  - POST /api/scan            (Scan directories and probe files)")
    print("  - POST /api/db/toggle       (Enable/disable database operations)")
    print("  - GET  /api/db/status       (Check database status)")
    print("  - GET  /health              (Health check)")
    print("="*80 + "\n")
    app.run(debug=False, port=5000)
