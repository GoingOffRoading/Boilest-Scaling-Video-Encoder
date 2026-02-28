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

# API Configuration  

# ----------------------------------------


API_BASE_URL = os.environ.get("MANAGER_BASE_URL", "http://192.168.1.110:31500")  # Get from container env var


def get_task():
    """
    Parameters:
        - None
    Description:
        - Fetches the next task from the manager for this worker node.
    Returns:
        - (status_code, data) or (None, error message)
    """
    worker_name = os.environ.get("NODE_NAME", socket.gethostname())
    endpoint = f"{API_BASE_URL}/api/v2/queue/task"
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


# ----------------------------------------

# Helper functions - Used in Pre-Post Processes

# ----------------------------------------


def format_duration(duration_seconds):
    """
    Parameters:
        - duration_seconds (float)
    Description:
        - Formats a duration in seconds into a human-readable string with units (s, m, h).
    Returns:
        - str
    """
    total_seconds = float(duration_seconds)

    if total_seconds < 60:
        return f"{total_seconds:.2f}s"
    if total_seconds < 3600:
        return f"{(total_seconds / 60):.2f}m"
    return f"{(total_seconds / 3600):.2f}h"


def file_exists(file_path):
    """
    Parameters:
        - file_path (str)
    Description:
        - Checks if a file exists at the specified path.
    Returns:
        - bool: True if the file exists, False otherwise
        - str: A reason message
    """
    try:
        exists = os.path.exists(file_path)
        return exists, 'Success'
    except Exception as e:
        return False, str(e)



def get_file_size_kb(file_path):
    """
    Parameters:
        - file_path (str)
    Description:
        - Gets the size of a file in kilobytes.
    Returns:
        - int: The file size in KB
        - str: A reason message
    """
    try:
        file_size_bytes = Path(file_path).stat().st_size
        file_size_kb = int(file_size_bytes / 1024)
        return file_size_kb, 'success'
    except FileNotFoundError:
        logging.debug(f"✗ File not found: {file_path}")
        return 0, 'FileNotFoundError'
    except Exception as e:
        logging.debug(f"✗ Error getting file size: {e}")
        return 0, str(e)



def validate_video(file_path, duration=None):
    """
    Parameters:
        - file_path (str)
        - duration (float, optional)
    Description:
        - Validates a video file using ffmpeg. If duration is provided, only checks that duration of video can be processed without error.
    Returns:
        - bool: True if the video is valid, False otherwise
        - str: A reason message
    """
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
            return False, ffmpeg_output
        else:
            logging.debug('File passed video integrity check')
            return True, 'success'
    except Exception as e:
        logging.debug(f"Error during video integrity check: {e}")
        return False, str(e)



def delete_file(file_path):
    """
    Parameters:
        - file_path (str)
    Description:
        - Deletes a file at the specified path.
    Returns:
        - bool: True if the file was deleted successfully, False otherwise
        - str: A reason message
    """
    try:
        logging.debug(f"Deleting file: {file_path}")
        os.remove(file_path)
        logging.debug(f"✓ File deleted successfully: {file_path}")
        return True, 'success'
    except FileNotFoundError:
        logging.debug(f"✗ File not found: {file_path}")
        return False, 'FileNotFoundError'
    except Exception as e:
        logging.debug(f"✗ Error deleting file: {e}")
        return False, str(e)


def report_encoding_completed(file_guid, status, after_file_size=None, notes=None):
    """
    Parameters:
        - file_guid (str): The unique identifier of the file that was encoded
        - status (str): The outcome status (e.g., 'encoded', 'failed', 'error')
        - after_file_size (int, optional): The file size in KB after encoding
        - notes (str, optional): Notes or exception details to record
    Description:
        - Calls the manager's /api/v2/completed endpoint to report that encoding is finished, along with status, file size, and notes.
        - Implements retry logic with exponential backoff (up to 10 attempts) in case of failures or connection issues.
    Returns:
        - tuple: (status_code, response_data)
    """

    endpoint = f"{API_BASE_URL}/api/v2/completed"
    request_data = {
        "file_guid": file_guid,
        "status": status
    }
    if after_file_size is not None:
        request_data["after_file_size"] = after_file_size
    if notes is not None:
        request_data["notes"] = notes

    max_attempts = 10
    last_status_code = None
    last_response = None
    for attempt in range(1, max_attempts + 1):
        try:
            data_bytes = json.dumps(request_data).encode("utf-8")
            request = urllib.request.Request(
                endpoint,
                data=data_bytes,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(request, timeout=10) as response:
                status_code = response.getcode()
                body = response.read().decode("utf-8")
                try:
                    response_data = json.loads(body)
                except json.JSONDecodeError:
                    response_data = body
                logging.debug(f"[RESPONSE] {json.dumps(response_data, indent=2)}")
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

        # If not the last attempt, wait before retrying (exponential backoff)
        if attempt < max_attempts:
            wait_time = 60 * (2 ** (attempt - 1))  # 60s, 120s, 240s, etc.
            logging.info(f"[RETRY] Waiting {wait_time} seconds before retry...")
            time.sleep(wait_time)

    # All attempts failed
    logging.error(f"[FAILED] All {max_attempts} attempts failed")
    return last_status_code, last_response




def get_file_status_from_manager(file_guid):
    """
    Parameters:
        - file_guid (str)
    Description:
        - Queries the manager for the queue record for file_guid and returns the status value.
    Returns:
        - status string or None
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
    """
    Parameters:
        - file_guid (str)
    Description:
        - Checks if the manager reports the given file's status as 'Stopped'.
    Returns:
        - bool
    """
    try:
        status = get_file_status_from_manager(file_guid)
        if isinstance(status, str) and status == 'Stopped':
            return True
    except Exception:
        pass
    return False


def sleep_with_file_check(total_seconds, file_guid, check='yes'):
    """
    Parameters:
        - total_seconds (float)
        - file_guid (str)
        - check (str)
    Description:
        - Sleeps for total_seconds but checks the manager for file status every MANAGER_POLL_INTERVAL seconds if check=='yes'.
    Returns:
        - bool
    """
    check_interval = 60
    end_time = time.time() + float(total_seconds)
    last_check = 0
    while time.time() < end_time:
        time.sleep(1)
        now = time.time()
        if (now - last_check) >= check_interval:
            last_check = now
            if check == 'yes':
                if file_should_stop(file_guid):
                    logging.info(f"Manager reported 'stop' for file {file_guid}")
                    # best-effort report
                    try:
                        report_encoding_completed(file_guid, 'Stopped')
                    except Exception:
                        pass
                    return False
    return True


# ----------------------------------------

# Preflgiht Specific Functions

# ----------------------------------------


def validate_hash(before_file_path, before_file_size):
    """
    Parameters:
        - before_file_path (str)
        - before_file_size (int)
    Description:
        - Checks if the file size matches the expected size for integrity validation.
    Returns:
        - (bool, reason)
    """
    current_size_kb, reason = get_file_size_kb(before_file_path)
    if current_size_kb == before_file_size:
        logging.debug(f"✓ Preflight check passed: {current_size_kb} KB == {before_file_size} KB")
        return True, reason
    else:
        logging.debug(f"✗ Preflight check failed: {current_size_kb} KB != {before_file_size} KB")
        return False, reason


# ----------------------------------------

# Run FFMPEG Command

# ----------------------------------------



def run_ffmpeg(before_file_size_file_path, ffmpeg_command, templorary_file_path, file_guid=None):
    """
    Parameters:
        - before_file_size_file_path (str)
        - ffmpeg_command (str)
        - templorary_file_path (str)
        - file_guid (str, optional)
    Description:
        - Runs ffmpeg with the provided file paths and command. Monitors for manager stop signal if file_guid is provided.
    Returns:
        - bool: true if ffmpeg succeeded, false if it failed or was stopped
        - str: A reason message 
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
                            logging.info(f"Manager requested stop for file {file_guid}; attempting to terminate ffmpeg")
                            try:
                                process.terminate()
                                try:
                                    process.wait(timeout=10)
                                    logging.info(f"ffmpeg terminated gracefully for file {file_guid}")
                                except subprocess.TimeoutExpired:
                                    logging.warning(f"ffmpeg did not terminate gracefully, force killing for file {file_guid}")
                                    process.kill()
                                    process.wait(timeout=5)
                                    logging.info(f"ffmpeg killed for file {file_guid}")
                            except Exception as kill_exc:
                                logging.error(f"Failed to terminate/kill ffmpeg for file {file_guid}: {kill_exc}")
                                return False, str(kill_exc)
                            return False, 'Stopped by Manager'
                    except Exception as check_exc:
                        logging.error(f"Error checking manager stop signal: {check_exc}")
                        pass
            process.wait()
            if process.returncode == 0:
                return True, 'success'
            else:
                return False, f'ffmpeg exited with code {process.returncode}'
        except Exception as exc:
            logging.error(f"Error while running ffmpeg: {exc}")
            try:
                process.kill()
            except Exception as kill_exc:
                logging.error(f"Failed to kill ffmpeg after error: {kill_exc}")
                return False, str(kill_exc)
            return False, str(exc)
    except Exception as exc:
        logging.error(f"Error: {exc}")
        return False, str(exc)


# ----------------------------------------

# Postflight Specific Functions

# ----------------------------------------


def post_flight_validate_video_full(file_path):
        """   
        Parameters:
            - file_path (str): Path to the video file to validate
        Description:
            - Validate video after encoding and delete the file if validation fails.
        Returns:
            - (bool, reason): True if validation passed, False if validation failed (file will be deleted), with reason string
        """
        is_valid, reason = validate_video(file_path)
        if not is_valid:
                logging.debug(f"Post-flight validation failed for: {file_path}")
                deleted = delete_file(file_path)
                if not deleted:
                        return False, f"Validation failed: {reason}; File deletion failed"
                return False, f"Validation failed: {reason}; File deleted"
        logging.debug(f"Post-flight validation passed for: {file_path}")
        return True, 'success'



def move_file(source_path, destination_path):
    """
    Parameters:
        - source_path (str)
        - destination_path (str)
    Description:
        - Moves a file from the source path to the destination path. Logs the operation and handles errors.
    Returns:
        - (bool, reason)
    """
    try:
        logging.debug(f"Moving file from {source_path} to {destination_path}")
        shutil.move(source_path, destination_path)
        logging.debug(f"✓ File moved successfully: {source_path} -> {destination_path}")
        return True, 'success'
    except FileNotFoundError:
        logging.debug(f"✗ File not found: {source_path}")
        return False, 'FileNotFoundError'
    except Exception as e:
        logging.debug(f"✗ Error moving file: {e}")
        return False, str(e)

