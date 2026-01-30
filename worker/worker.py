"""
FFmpeg Worker Loop

This worker implements a loop that:
1. Fetches encoding tasks from `/api/queue/largest`
2. Builds and executes the ffmpeg command
3. Reports results back to `/api/encoded`
"""

import requests
import subprocess
import time
import os
from pathlib import Path
from .file_exists import file_exists
from .worker_validate_video import validate_video
from .get_file_size_kb import get_file_size_kb
from .worker_output_path import get_output_path


# API Configuration
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:5000')  # Update this to match your Flask server
GET_TASK_ENDPOINT = f"{API_BASE_URL}/api/queue/largest"
POST_RESULT_ENDPOINT = f"{API_BASE_URL}/api/encoded"

# Worker Configuration
POLL_INTERVAL = int(os.getenv('POLL_INTERVAL', 60))  # Seconds to wait between polls when no task is available
ffmpeg_settings = os.getenv('FFMPEG_SETTINGS', 'ffmpeg -hide_banner -loglevel 16 -stats -stats_period 10 -y -i')


def fetch_encoding_task():
    """
    Fetch the largest encoding task from the API
    Returns: tuple (success, data/error_message)
    """
    try:
        print(f"[FETCH] Requesting task from {GET_TASK_ENDPOINT}")
        response = requests.get(GET_TASK_ENDPOINT, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        
        if result.get('success') and result.get('data'):
            print(f"[FETCH] Task received - GUID: {result['data'].get('guid')}")
            print(f"[FETCH] File: {result['data'].get('input_file_name')}")
            print(f"[FETCH] Size: {result['data'].get('before_file_size')} bytes")
            return True, result['data']
        else:
            print("[FETCH] No tasks available")
            return False, result.get('message', 'No tasks available')
            
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Failed to fetch task: {e}")
        return False, str(e)


def validate_hash(filepath, before_file_size):
    """
    Validate file hasn't changed since scan
    It's possible other processes have modified the file since it was first scanned by the manager.
    This function checks the file size to ensure it matches what was originally recorded.
    Returns: True if the file size matches from the original scan
    """
    try:
        current_file_size = get_file_size_kb(filepath)
        if current_file_size == before_file_size:
            print("File passed expected size check")
            return True
        else:
            print(f"File mismatch: expected {before_file_size} KB, got {current_file_size} KB")
            return False
    except Exception as e:
        print(f"Error during hash validation: {e}")
        return False


def pre_launch_checks(filepath, before_file_size):
    """
    Run all pre-launch validation checks
    Pulls everything together
    """
    exists_check = file_exists(filepath)
    video_check = validate_video(filepath) 
    hash_check = validate_hash(filepath, before_file_size)
     
    if exists_check and video_check and hash_check:
        print("\n✓ All pre-launch validation checks PASSED!")
        return True
    else:
        print("\n✗ One or more pre-launch validation checks FAILED!")
        return False


def build_ffmpeg_command(ffmpeg_settings, filepath, ffmpeg_string, temp_file):
    """
    Build ffmpeg command in correct order: ffmpeg [global_options] -i input_file [encoding_options] output_file
    """
    ffmpeg_cmd = f'ffmpeg {ffmpeg_settings} -i "{filepath}" {ffmpeg_string} "{temp_file}"'
    return ffmpeg_cmd


def execute_ffmpeg(ffmpeg_settings, filepath, ffmpeg_string, temp_file):
    """
    Execute the FFmpeg command
    Returns: tuple (success, result_dict)
    """
    try:
        ffmpeg_cmd = build_ffmpeg_command(ffmpeg_settings, filepath, ffmpeg_string, temp_file)

        print(f"[FFMPEG] Executing: {ffmpeg_cmd}")
        print("[FFMPEG] Starting encoding...")
        
        # Run ffmpeg command
        result = subprocess.run(
            ffmpeg_cmd,
            shell=True,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"[ERROR] FFmpeg failed with return code {result.returncode}")
            print(f"[ERROR] stderr: {result.stderr[:500]}")
            return False, {
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
        
        print("[FFMPEG] Encoding complete!")
        return True, {
            'returncode': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr
        }
        
    except Exception as e:
        print(f"[ERROR] Exception during ffmpeg execution: {e}")
        return False, {'error': str(e)}


def post_launch_checks(temp_file):
    """
    Run all post-launch validation checks
    Pulls everything together
    """
    exists_check = file_exists(temp_file)
    video_check = validate_video(temp_file) 
     
    if exists_check and video_check:
        print("\n✓ All post launch validation checks PASSED!")
        return True
    else:
        print("\n✗ One or more post launch validation checks FAILED!")
        return False


def delete_file(filepath):
    """
    Delete a file from the filesystem
    Returns: True if successful, False otherwise
    """
    try:
        os.remove(filepath)
        print(f"[CLEANUP] Deleted file: {filepath}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to delete file: {e}")
        return False


def generate_destination_path(temp_file, filepath):
    """
    Generate destination path by combining directory from filepath and filename from temp_file
    Returns: destination path string
    """
    # Get directory from filepath
    source_dir = os.path.dirname(filepath)
    # Get filename from temp_file
    temp_filename = os.path.basename(temp_file)
    # Combine them to create destination
    destination = os.path.join(source_dir, temp_filename)
    return destination


def move_temp_to_source(temp_file, filepath):
    """
    Move the temp file to the source file location
    Gets directory path from filepath and filename from temp_file to create destination
    Then deletes the original filepath
    Returns: True if successful, False otherwise
    """
    try:
        # Generate destination path
        destination = generate_destination_path(temp_file, filepath)
        
        print(f"[MOVE] Destination: {destination}")

        if delete_file(filepath) == True:
            os.rename(temp_file, destination)
            print(f"[MOVE] Moved {temp_file} to {destination}")
            return True
        else:
            print('Failed to delete original file')
            return False      
            
    except Exception as e:
        print(f"[ERROR] Failed to move temp file: {e}")
        return False


def report_results(queued_file_guid, after_file_size):
    """
    Report encoding results back to the API
    Returns: tuple (success, response_data/error_message)
    """
    try:
        payload = {
            'queued_file_guid': queued_file_guid,
            'after_file_size': after_file_size
        }
        
        print(f"[REPORT] Posting results to {POST_RESULT_ENDPOINT}")
        print(f"[REPORT] Queued File GUID: {queued_file_guid}, After size: {after_file_size} bytes")
        
        response = requests.post(
            POST_RESULT_ENDPOINT,
            json=payload,
            timeout=10
        )
        response.raise_for_status()
        
        result = response.json()
        
        if result.get('success'):
            print(f"[REPORT] Results reported successfully!")
            return True, result
        else:
            print(f"[ERROR] API returned error: {result.get('error')}")
            return False, result.get('error', 'Unknown error')
            
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Failed to report results: {e}")
        return False, str(e)


def worker_loop():
    """
    Main worker loop that processes encoding tasks
    """
    print("="*80)
    print("FFmpeg Worker Started")
    print("="*80)
    print(f"API Base URL: {API_BASE_URL}")
    print(f"Poll Interval: {POLL_INTERVAL}s")
    print("="*80)

    try:
        while True:
            print(f"{'='*80}")
            print('Starting Loop')
            print(f"{'='*80}")
            
            # Step 1: Fetch a task
            task_retrieval_status, task_data = fetch_encoding_task()

            print(task_data)
           
            queue_file_guid = task_data['guid']
            file_path = task_data['file_path']
            output_file_name = task_data['output_file_name']
            before_file_size = task_data['before_file_size']
            ffmpeg_string = task_data['ffmpeg_string']

            print(queue_file_guid)
            print(file_path)
            print(output_file_name)
            print(before_file_size)
            print(ffmpeg_string)

            if task_retrieval_status == True:
                print('Step 1: Task Retrieved Successfully')
                if pre_launch_checks(file_path, before_file_size) == True:
                    print('Step 2: Pre-launch checks passed successfully')
                    if execute_ffmpeg(ffmpeg_settings, file_path, ffmpeg_string, get_output_path(file_path, output_file_name)) == True:
                        print('Step 3: FFmpeg executed successfully')
                        if post_launch_checks(get_output_path(file_path, output_file_name)) == True:
                            print('Step 4: Post-launch checks passed successfully')
                            if move_temp_to_source(get_output_path(file_path, output_file_name), file_path) == True:
                                print('Step 5: Moved temp file to source location successfully')
                            after_file_size = get_file_size_kb(get_output_path(file_path, output_file_name))
                            report_status, report_data = report_results(queue_file_guid, after_file_size)
                            if report_status == True:
                                print('Step 5: Results reported successfully')
                            else:
                                print('Step 5: Failed to report results')
                        else:
                            print('Step 4: Post-launch checks failed')
                    else:
                        print('Step 3: FFmpeg execution failed')
                else:
                    print("Pre-launch checks failed, skipping this task.")
            else:
                print("No task retrieved, waiting for next poll.")            

            print('Loop completed')
            time.sleep(POLL_INTERVAL)
    except KeyboardInterrupt:
        print("\n[WORKER] Interrupted by user, shutting down...")
    finally:
        print("[WORKER] Worker stopped")


if __name__ == "__main__":
    worker_loop()
