# ----------------------------------------

# Preflight Check Functions
# Ensures that the video about to be encoded hasn't changed since it was first scanned & has integrity

# ----------------------------------------

from pathlib import Path
import logging
import os
import subprocess
import shutil
import json
import re
import urllib.request
from urllib.error import URLError, HTTPError
import socket
import time


# ----------------------------------------

#API Configuration  

# ----------------------------------------
API_BASE_URL = os.environ.get("MANAGER_BASE_URL", "http://192.168.1.110:31500")  # Get from container env var
QUEUE_ENDPOINTS = {
    "LARGEST": f"{API_BASE_URL}/api/v2/queue/largest",
    "SMALLEST": f"{API_BASE_URL}/api/v2/queue/smallest",
    "FIFO": f"{API_BASE_URL}/api/v2/queue/fifo",
}


def normalize_queue_order(queue_order):
    if queue_order is None:
        return "FIFO"

    normalized = str(queue_order).strip().upper()
    if normalized in QUEUE_ENDPOINTS:
        return normalized
    return "FIFO"


def get_task_endpoint(queue_order=None):
    normalized_queue_order = normalize_queue_order(queue_order)
    return QUEUE_ENDPOINTS[normalized_queue_order]


def get_task(queue_order=None):
    worker_name = os.environ.get("NODE_NAME", socket.gethostname())
    endpoint = get_task_endpoint(queue_order)
    request_url = f"{endpoint}?worker={worker_name}"
    request = urllib.request.Request(request_url, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            status_code = response.getcode()
            body = response.read().decode("utf-8")
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                data = body
            return status_code, data
    except HTTPError as exc:
        return exc.code, exc.read().decode("utf-8")
    except URLError as exc:
        return None, f"Connection error: {exc}"


def get_largest_task():
    return get_task("LARGEST")

# ----------------------------------------

# validate_hash checks to see if the file hasn't changed since it was originally scanned

# ----------------------------------------


def get_file_size_kb(file_path):
    try:
        file_size_bytes = Path(file_path).stat().st_size
        file_size_kb = int(file_size_bytes / 1024)
        return file_size_kb
    except FileNotFoundError:
        logging.debug(f"✗ File not found: {file_path}")
        return 0
    except Exception as e:
        logging.debug(f"✗ Error getting file size: {e}")
        return 0


def format_duration(duration_seconds):
    total_seconds = float(duration_seconds)

    if total_seconds < 60:
        return f"{total_seconds:.2f}s"
    if total_seconds < 3600:
        return f"{(total_seconds / 60):.2f}m"
    return f"{(total_seconds / 3600):.2f}h"


def file_exists(file_path):
    """
    Check if a file exists at the specified path.
    
    Parameters:
      - file_path (str): The path to the file to check
    
    Returns:
      - bool: True if the file exists, False otherwise
    """
    return os.path.exists(file_path)
    

def validate_hash(before_file_path, before_file_size):
    current_size_kb = get_file_size_kb(before_file_path)
    if current_size_kb == before_file_size:
        logging.debug(f"✓ Preflight check passed: {current_size_kb} KB == {before_file_size} KB")
        return True
    else:
        logging.debug(f"✗ Preflight check failed: {current_size_kb} KB != {before_file_size} KB")
        return False


# ----------------------------------------

# validate_video checks video integrity using ffmpeg
# Used to validate the input file before encoding and the output file after encoding

# ----------------------------------------

# Patterns that should be ignored during video validation
# Not currently used as videos would pass this check and fail in encoding.  Will revisit.
IGNORED_PATTERNS = [
    r"non monotonically increasing",
    r"invalid pts",
    r"invalid dts",
]


def _contains_ignored_pattern(text):
    """
    Check if text contains any of the ignored patterns.
    
    Parameters:
      - text (str): The text to check
    
    Returns:
      - bool: True if an ignored pattern is found, False otherwise
    """
    for pattern in IGNORED_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


# We want to scruitinize the output of ffmpeg more closely after encoding to ensure that there aren't any critical errors that would cause the file to be unplayable, even if it is technically valid. So we use a more thorough validation function post-flight.
    
def validate_video(file_path, duration=None):
    try:
        if duration is not None:
            command = f'ffmpeg -v error -xerror -t {int(duration)} -i "{file_path}" -f null -'
        else:
            command = f'ffmpeg -v error -xerror -i "{file_path}" -f null -'
        result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        ffmpeg_output = "\n".join(
            part for part in [result.stdout.strip(), result.stderr.strip()] if part
        )
        if ffmpeg_output:
            logging.warning(f"FFmpeg validation output for {file_path}:\n{ffmpeg_output}")
            logging.debug('File failed video integrity check')
            return False
        else:
            logging.debug('File passed video integrity check')
            return True
    except Exception as e:
        logging.debug(f"Error during video integrity check: {e}")
        return False


def post_flight_validate_video_full(file_path):
    """
    Validate video after encoding and delete the file if validation fails.
    
    Parameters:
      - file_path (str): Path to the video file to validate
    
    Returns:
      - bool: True if validation passed, False if validation failed (file will be deleted)
    """
    if not validate_video(file_path):
        logging.debug(f"Post-flight validation failed for: {file_path}")
        delete_file(file_path)
        return False
    logging.debug(f"Post-flight validation passed for: {file_path}")
    return True


# ----------------------------------------

# Run FFMPEG Command

# ----------------------------------------

def run_ffmpeg(before_file_size_file_path, ffmpeg_command, templorary_file_path, file_guid=None):
    """
    Runs ffmpeg with the provided file paths and ffmpeg command.
    Returns True on success, False on failure.

    Parameters:
      - before_file_size_file_path: Full path to the input file
      - ffmpeg_command: FFmpeg command string (video/audio/subtitle codec specifications)
      - templorary_file_path: Full path to the output file (temporary location)
    """
    try:
        ffmpeg_settings = 'ffmpeg -hide_banner -loglevel 16 -stats -stats_period 60 -y -i'

        logging.debug(before_file_size_file_path)
        logging.debug(templorary_file_path)
        
        command = f"{ffmpeg_settings} \"{before_file_size_file_path}\" {ffmpeg_command} \"{templorary_file_path}\""

        logging.debug(command)

        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        # Read output line by line and check manager stop signal periodically
        try:
            for line in process.stdout:
                logging.info(line.rstrip())
                if file_guid:
                    try:
                        if file_should_stop(file_guid):
                            logging.info(f"Manager requested stop for file {file_guid}; terminating ffmpeg")
                            try:
                                process.terminate()
                                process.wait(timeout=10)
                            except Exception:
                                try:
                                    process.kill()
                                except Exception:
                                    pass
                            return False
                    except Exception:
                        # ignore errors checking manager to avoid killing ffmpeg unnecessarily
                        pass
            process.wait()
            return process.returncode == 0
        except Exception as exc:
            logging.error(f"Error while running ffmpeg: {exc}")
            try:
                process.kill()
            except Exception:
                pass
            return False
    except Exception as exc:
        logging.error(f"Error: {exc}")
        return False



# ----------------------------------------

# delete_file deletes a file from the specified directory
# Used to remove files after processing or if they fail validation

# ----------------------------------------

def delete_file(file_path):
    try:
        logging.debug(f"Deleting file: {file_path}")
        os.remove(file_path)
        logging.debug(f"✓ File deleted successfully: {file_path}")
        return True
    except FileNotFoundError:
        logging.debug(f"✗ File not found: {file_path}")
        return False
    except Exception as e:
        logging.debug(f"✗ Error deleting file: {e}")
        return False

# ----------------------------------------
# This function validates the video after encoding and deletes it if it fails validation

def validate_post_flight_video(after_file_path):
    if not validate_video(after_file_path):
        if not delete_file(after_file_path):
            return False
        return False
    return True

# ----------------------------------------
# This function validates the video after encoding and deletes it if it fails validation

def move_file(source_path, destination_path):
    try:
        logging.debug(f"Moving file from {source_path} to {destination_path}")
        shutil.move(source_path, destination_path)
        logging.debug(f"✓ File moved successfully: {source_path} -> {destination_path}")
        return True
    except FileNotFoundError:
        logging.debug(f"✗ File not found: {source_path}")
        return False
    except Exception as e:
        logging.debug(f"✗ Error moving file: {e}")
        return False

# ----------------------------------------
# This function calls the manager with findings

def report_encoding_completed(file_guid, status, after_file_size=None):
    """
    Call the /api/v2/completed endpoint to report that encoding is finished.
    Retries up to 10 times on failure with exponential backoff.
    
    Parameters:
      - file_guid (str): The unique identifier of the file that was encoded
      - status (str): The outcome status (e.g., 'encoded', 'failed', 'error')
      - after_file_size (int, optional): The file size in KB after encoding
    
    Returns:
      - tuple: (status_code, response_data)
    """
    endpoint = f"{API_BASE_URL}/api/v2/completed"
    
    # Prepare the request data
    request_data = {
        "file_guid": file_guid,
        "outcome": status
    }
    
    # Add after_file_size if provided
    if after_file_size is not None:
        request_data["after_file_size"] = after_file_size
    
    max_attempts = 10
    attempt = 0
    
    while attempt < max_attempts:
        attempt += 1
        
        if attempt == 1:
            logging.info(f"\n[REPORT] Calling {endpoint}")
        else:
            logging.info(f"\n[REPORT] Retry attempt {attempt}/{max_attempts} - Calling {endpoint}")
            
        logging.debug(f"[REPORT] File GUID: {file_guid}")
        logging.debug(f"[REPORT] Status: {status}")
        if after_file_size is not None:
            logging.debug(f"[REPORT] Encoded file size: {after_file_size} KB")
        
        try:
            # Create and send the POST request
            json_data = json.dumps(request_data).encode('utf-8')
            request = urllib.request.Request(
                endpoint,
                data=json_data,
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            
            with urllib.request.urlopen(request, timeout=10) as response:
                status_code = response.getcode()
                body = response.read().decode('utf-8')
                try:
                    response_data = json.loads(body)
                except json.JSONDecodeError:
                    response_data = body
                
                logging.info(f"[SUCCESS] Status: {status_code}")
                logging.debug(f"[RESPONSE] {json.dumps(response_data, indent=2)}")
                
                # Extract and report the new file size if available
                if isinstance(response_data, dict) and 'data' in response_data:
                    data = response_data['data']
                    if 'after_file_size' in data:
                        logging.debug(f"[RESULT] Encoded file size confirmed: {data['after_file_size']} KB")
                
                # Success - return immediately
                return status_code, response_data
                
        except HTTPError as exc:
            status_code = exc.code
            error_body = exc.read().decode('utf-8')
            logging.error(f"[ERROR] HTTP Error {status_code}: {error_body}")
            last_status_code = status_code
            last_response = error_body
        except URLError as exc:
            logging.error(f"[ERROR] Connection error: {exc}")
            last_status_code = None
            last_response = f"Connection error: {exc}"
        except Exception as e:
            logging.error(f"[ERROR] Exception: {type(e).__name__}: {str(e)}")
            last_status_code = None
            last_response = str(e)
        
        # If not the last attempt, wait before retrying (30 seconds between attempts)
        if attempt < max_attempts:
            wait_time = 60 * (2 ** (attempt - 1))  # Exponential backoff: 60s, 120s, 240s, etc.
            logging.info(f"[RETRY] Waiting {wait_time} seconds before retry...")
            time.sleep(wait_time)
    
    # All attempts failed
    logging.error(f"[FAILED] All {max_attempts} attempts failed")
    return last_status_code, last_response


def get_file_status_from_manager(file_guid):
    """
    Query the manager for the queue record for `file_guid` and return the `status` value.
    Returns the status string (e.g. 'queued','pulled','encoded','stop', etc.) or None on error.
    """
    if not file_guid:
        return None
    endpoint = f"{API_BASE_URL}/api/v2/queue/status?file_guid={file_guid}"
    request = urllib.request.Request(endpoint, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            body = response.read().decode('utf-8')
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                return None
            if isinstance(data, dict) and data.get('success') and data.get('data'):
                return data['data'].get('status')
            return None
    except Exception as exc:
        logging.debug(f"Failed to fetch file status from manager: {exc}")
        return None


def file_should_stop(file_guid):
    """Return True if manager reports the given file's status is 'stop'."""
    try:
        status = get_file_status_from_manager(file_guid)
        if isinstance(status, str) and status.lower() == 'stop':
            return True
    except Exception:
        pass
    return False


def sleep_with_file_check(total_seconds, file_guid):
    """
    Sleep for total_seconds but check the manager for file status every MANAGER_POLL_INTERVAL seconds.
    Returns True if completed without a stop signal; False if manager requested stop for this file.
    """
    check_interval = int(os.environ.get('MANAGER_POLL_INTERVAL', '60'))
    end_time = time.time() + float(total_seconds)
    last_check = 0
    while time.time() < end_time:
        time.sleep(1)
        now = time.time()
        if (now - last_check) >= check_interval:
            last_check = now
            if file_should_stop(file_guid):
                logging.info(f"Manager reported 'stop' for file {file_guid}")
                # best-effort report
                try:
                    report_encoding_completed(file_guid, 'stopped')
                except Exception:
                    pass
                return False
    return True
    

