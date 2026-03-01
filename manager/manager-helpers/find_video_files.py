import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def find_video_files(directory_path, extensions=None):
    """Yield (directory, filename) tuples for video files under `directory_path`.

    `extensions` should be a list of extensions (with leading dot).
    If not provided a sensible default set will be used.
    """
    if extensions is None:
        extensions = ['.mp4', '.mkv', '.avi', '.mov', '.flv', '.wmv', '.ts']
    # Normalize to lowercase for comparison
    lower_exts = {e.lower() for e in extensions}

    directory_path = os.path.expanduser(directory_path)
    if not os.path.isdir(directory_path):
        logging.debug(f'Not a directory: {directory_path}')
        return

    for root, dirs, files in os.walk(directory_path):
        for file_name in files:
            _, ext = os.path.splitext(file_name)
            if ext.lower() in lower_exts:
                # Yield directory path (root) and filename separately
                yield root, file_name
