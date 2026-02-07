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


# ----------------------------------------

#API Configuration  

# ----------------------------------------
API_BASE_URL = os.environ.get("MANAGER_BASE_URL", "http://192.168.1.110:31500")  # Get from container env var
GET_TASK_ENDPOINT = f"{API_BASE_URL}/api/queue/largest"


def get_largest_task():
    request = urllib.request.Request(GET_TASK_ENDPOINT, method="GET")
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


def validate_video_lite(file_path):
    try:
        command = 'ffmpeg -v error -fflags +genpts -t 300 -i "' + file_path + '" -f null -'
        result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Check stdout for actual errors (not in ignored patterns)
        combined_output = result.stdout + result.stderr
        
        if combined_output:
            # If output contains only ignored patterns, pass validation
            if _contains_ignored_pattern(combined_output):
                logging.debug('File passed video integrity check (ignored non-critical errors)')
                return True
            else:
                logging.debug('File failed video integrity check')
                logging.debug(f'FFmpeg output: {combined_output}')
                return False
        else:
            logging.debug('File passed video integrity check')
            return True
    except Exception as e:
        logging.debug(f"Error during video integrity check: {e}")
        return False
    
# We want to scruitinize the output of ffmpeg more closely after encoding to ensure that there aren't any critical errors that would cause the file to be unplayable, even if it is technically valid. So we use a more thorough validation function post-flight.
    
def validate_video_full(file_path):
    try:
        command = 'ffmpeg -v error -i "' + file_path + '" -f null -'
        result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.stdout or result.stderr:
            logging.debug('File failed video integrity check')
            return False
        else:
            logging.debug('File passed video integrity check')
            return True
    except Exception as e:
        logging.debug(f"Error during video integrity check: {e}")
        return False




# ----------------------------------------

# Run FFMPEG Command

# ----------------------------------------

def run_ffmpeg(before_file_size_file_path, ffmpeg_command, templorary_file_path):
    """
    Runs ffmpeg with the provided file paths and ffmpeg command.
    Returns True on success, False on failure.

    Parameters:
      - before_file_size_file_path: Full path to the input file
      - ffmpeg_command: FFmpeg command string (video/audio/subtitle codec specifications)
      - templorary_file_path: Full path to the output file (temporary location)
    """
    try:
        ffmpeg_settings = 'ffmpeg -hide_banner -loglevel 16 -stats -stats_period 10 -y -i'

        logging.debug(before_file_size_file_path)
        logging.debug(templorary_file_path)
        
        command = f"{ffmpeg_settings} \"{before_file_size_file_path}\" {ffmpeg_command} \"{templorary_file_path}\""

        logging.debug(command)

        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        for line in process.stdout:
            logging.debug(line.rstrip())
        return True
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
    Call the /api/completed endpoint to report that encoding is finished.
    
    Parameters:
      - file_guid (str): The unique identifier of the file that was encoded
      - status (str): The outcome status (e.g., 'encoded', 'failed', 'error')
      - after_file_size (int, optional): The file size in KB after encoding
    
    Returns:
      - tuple: (status_code, response_data)
    """
    # Get API base URL from environment variable
    api_base_url = os.environ.get("API_BASE_URL", "http://192.168.1.110:31500")
    endpoint = f"{api_base_url}/api/completed"
    
    # Prepare the request data
    request_data = {
        "file_guid": file_guid,
        "outcome": status
    }
    
    # Add after_file_size if provided
    if after_file_size is not None:
        request_data["after_file_size"] = after_file_size
    
    logging.info(f"\n[REPORT] Calling {endpoint}")
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
            
            return status_code, response_data
            
    except HTTPError as exc:
        status_code = exc.code
        error_body = exc.read().decode('utf-8')
        logging.error(f"[ERROR] HTTP Error {status_code}: {error_body}")
        return status_code, error_body
    except URLError as exc:
        logging.error(f"[ERROR] Connection error: {exc}")
        return None, f"Connection error: {exc}"
    except Exception as e:
        logging.error(f"[ERROR] Exception: {type(e).__name__}: {str(e)}")
        return None, str(e)
    

