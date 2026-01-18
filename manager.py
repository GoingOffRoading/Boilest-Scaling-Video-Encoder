from flask import Flask, jsonify, request, render_template
from scripts.db_status import get_database_status
from scripts.flask_get_largest_queue import get_largest_queue_logic
from scripts.flask_post_completed_encode import post_completed_encode_logic
from scripts.flask_post_scan import scan_logic
from scripts.flask_post_toggle_database import toggle_database_logic

app = Flask(__name__)

# Global flag to disable database operations
DB_DISABLED = False


@app.route('/', methods=['GET'])
def index():
    """Serve the main UI page"""
    print("[UI] Serving main page")
    return render_template('index.html')


@app.route('/api/queue/largest', methods=['GET'])
def get_largest_queue():
    """
    Query the queue table and return one row sorted by before_file_size DESC limit 1
    """
    response_data, status_code = get_largest_queue_logic(DB_DISABLED)
    return jsonify(response_data), status_code


@app.route('/api/completed', methods=['POST'])
def post_completed_encode():
    """
    Write a new record to the completed table
    Expects JSON body with: guid, after_file_size
    """
    data = request.get_json()
    response_data, status_code = post_completed_encode_logic(data)
    return jsonify(response_data), status_code


@app.route('/api/scan', methods=['POST'])
def scan():
    """
    Scan directories for video files and probe them to populate queue table
    Uses the scan_db_directories_and_write function from queue.py
    """
    global DB_DISABLED
    db_disabled_ref = {'value': DB_DISABLED}
    response_data, status_code = scan_logic(db_disabled_ref)
    DB_DISABLED = db_disabled_ref['value']
    return jsonify(response_data), status_code


@app.route('/api/db/toggle', methods=['POST'])
def toggle_database():
    """
    Toggle the database operations on/off
    Expects JSON body with: enabled (boolean)
    """
    global DB_DISABLED
    data = request.get_json()
    db_disabled_ref = {'value': DB_DISABLED}
    response_data, status_code = toggle_database_logic(data, db_disabled_ref)
    DB_DISABLED = db_disabled_ref['value']
    return jsonify(response_data), status_code


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
    app.run(debug=True, host='0.0.0.0', port=5000)
