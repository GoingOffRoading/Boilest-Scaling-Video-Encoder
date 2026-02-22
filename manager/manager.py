import os
import logging
from flask import Flask, jsonify, request, render_template
from db_status import get_database_status
from flask_get_index import get_index_data
from flask_get_largest_queue import get_largest_queue_logic
from flask_get_smalled_queue import get_smallest_queue_logic
from flask_get_fifo_queue import get_fifo_queue_logic
from flask_post_completed_encode import post_completed_encode_logic
from flask_get_queue_status import get_queue_status_logic
from flask_post_queue import run_queue_workflow
from flask_post_toggle_database import toggle_database_logic
from flask_post_delete_errors import delete_errors_logic
from flask_post_delete_queue import delete_queue_logic
from flask_directories import create_directory_logic, update_directory_logic, delete_directory_logic
from flask_get_encoding_queue import get_encoding_queue_logic
from flask_get_failed_by_status import get_failed_by_status_logic

# Get log level from environment variable (default: INFO)
log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, log_level), format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

# Global flag to disable database operations
DB_DISABLED = False


@app.route('/', methods=['GET'])
def index():
    """Serve the main UI page"""
    logging.info("[UI] Serving main page")
    index_data = get_index_data()
    return render_template('index.html', **index_data)

@app.route('/api/v2/queue/fifo', methods=['GET'])
def get_fifo_queue():
    """
    Query the queue table and return one row using FIFO order by table ROWID
    """
    worker = request.args.get('worker')
    response_data, status_code = get_fifo_queue_logic(DB_DISABLED, worker)
    return jsonify(response_data), status_code


@app.route('/api/v2/completed', methods=['POST'])
def post_completed_encode():
    """
    Write a new record to the completed table
    Expects JSON body with: guid, after_file_size
    """
    data = request.get_json()
    response_data, status_code = post_completed_encode_logic(data)
    return jsonify(response_data), status_code


@app.route('/api/v2/scan', methods=['POST'])
def scan():
    """
    Scan directories for video files and probe them to populate queue table
    Uses the scan_db_directories_and_write function from queue.py
    """
    global DB_DISABLED
    data = request.get_json(silent=True) or {}
    selected_paths = data.get('paths')

    if selected_paths is not None and not isinstance(selected_paths, list):
        return jsonify({"error": "'paths' must be a list of directory paths"}), 400

    DB_DISABLED = True
    try:
        run_queue_workflow(selected_paths=selected_paths)
    finally:
        DB_DISABLED = False
    return jsonify({"status": "scan_completed", "db_disabled": DB_DISABLED}), 200


@app.route('/api/v2/db/toggle', methods=['POST'])
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


@app.route('/api/v2/queue/delete', methods=['POST'])
def delete_queued():
    """
    Delete all queued items from the queue table
    """
    response_data, status_code = delete_queue_logic()
    return jsonify(response_data), status_code


@app.route('/api/v2/queue/delete-errors', methods=['POST'])
def delete_error_records():
    """
    Delete all error records from the queue table (status starts with 'Failed')
    """
    data = request.get_json(silent=True) or {}
    status_value = data.get('status')
    guids = data.get('guids')
    response_data, status_code = delete_errors_logic(status_value, guids=guids)
    return jsonify(response_data), status_code


@app.route('/api/v2/directories', methods=['POST'])
def create_directory():
    data = request.get_json(silent=True) or {}
    response_data, status_code = create_directory_logic(data)
    return jsonify(response_data), status_code


@app.route('/api/v2/directories/<guid>', methods=['PATCH'])
def update_directory(guid):
    data = request.get_json(silent=True) or {}
    response_data, status_code = update_directory_logic(guid, data)
    return jsonify(response_data), status_code


@app.route('/api/v2/directories/<guid>', methods=['DELETE'])
def delete_directory(guid):
    response_data, status_code = delete_directory_logic(guid)
    return jsonify(response_data), status_code


@app.route('/api/v2/db/status', methods=['GET'])
def database_status():
    """
    Get the current status of database operations
    """
    logging.info("[REQUEST] GET /api/v2/db/status")
    status_data = get_database_status(DB_DISABLED)
    return jsonify(status_data), 200


@app.route('/api/v2/queue/status', methods=['GET'])
def get_queue_status():
    file_guid = request.args.get('file_guid')
    response_data, status_code = get_queue_status_logic(file_guid)
    return jsonify(response_data), status_code

@app.route('/api/v2/queue/encoding', methods=['GET'])
def get_encoding_queue():
    response_data, status_code = get_encoding_queue_logic()
    return jsonify(response_data), status_code


@app.route('/api/v2/queue/failed', methods=['GET'])
def get_failed_by_status():
    status_value = request.args.get('status')
    response_data, status_code = get_failed_by_status_logic(status_value)
    return jsonify(response_data), status_code


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    logging.info("[HEALTH CHECK] Endpoint called")
    return jsonify({'status': 'healthy'}), 200


if __name__ == '__main__':
    logging.info("\n" + "="*80)
    logging.info("Starting Encode API Server...")
    logging.info("="*80)
    logging.info("Available endpoints:")
    logging.info("  - GET  /                    (Main UI page)")
    logging.info("  - GET  /api/v2/queue/largest   (Get largest queued item by file size)")
    logging.info("  - GET  /api/v2/queue/smallest  (Get smallest queued item by file size)")
    logging.info("  - GET  /api/v2/queue/fifo      (Get queued item by FIFO row order)")
    logging.info("  - POST /api/v2/completed       (Create new completed record)")
    logging.info("  - POST /api/v2/scan            (Scan directories and probe files)")
    logging.info("  - POST /api/v2/queue/delete    (Delete all queued items)")
    logging.info("  - POST /api/v2/queue/delete-errors (Delete failed records by status)")
    logging.info("  - POST /api/v2/directories     (Create directory)")
    logging.info("  - PATCH /api/v2/directories/<guid> (Update directory)")
    logging.info("  - DELETE /api/v2/directories/<guid> (Delete directory)")
    logging.info("  - POST /api/v2/db/toggle       (Enable/disable database operations)")
    logging.info("  - GET  /api/v2/db/status       (Check database status)")
    logging.info("  - GET  /health              (Health check)")
    logging.info("="*80 + "\n")
    app.run(debug=True, use_reloader=False, host='0.0.0.0', port=5000)
