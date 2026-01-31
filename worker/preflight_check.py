# ----------------------------------------

# Preflight Check Functions
# Ensures that the video about to be encoded hasn't changed since it was first scanned & has integrity

# ----------------------------------------

from pathlib import Path
import logging
import os
import subprocess


# ----------------------------------------

# validate_hash checks to see if the file hasn't changed since it was originally scanned

# ----------------------------------------


def get_file_size_kb(directory_path, input_file_name):
    try:
        file_path = os.path.join(directory_path, input_file_name)
        file_size_bytes = Path(file_path).stat().st_size
        file_size_kb = int(file_size_bytes / 1024)
        return file_size_kb
    except FileNotFoundError:
        logging.debug(f"✗ File not found: {file_path}")
        return 0
    except Exception as e:
        logging.debug(f"✗ Error getting file size: {e}")
        return 0
    

def validate_hash(directory_path, input_file_name, before_file_size):
    current_size_kb = get_file_size_kb(directory_path, input_file_name)
    if current_size_kb == before_file_size:
        logging.debug(f"✓ Preflight check passed: {current_size_kb} KB == {before_file_size} KB")
        return True
    else:
        logging.debug(f"✗ Preflight check failed: {current_size_kb} KB != {before_file_size} KB")
        return False


# ----------------------------------------

# validate_video checks video integrity using ffmpeg

# ----------------------------------------

def validate_video(directory_path, input_file_name):
    try:
        file_path = os.path.join(directory_path, input_file_name)
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

# validate_preflight runs both video and hash validations

# ----------------------------------------

def validate_preflight(directory_path, input_file_name, before_file_size):
    video_ok = validate_video(directory_path, input_file_name)
    hash_ok = validate_hash(directory_path, input_file_name, before_file_size)

    if video_ok and hash_ok:
        logging.debug("✓ Preflight validation passed (video + hash)")
        return True

    logging.debug("✗ Preflight validation failed (video + hash)")
    return False
