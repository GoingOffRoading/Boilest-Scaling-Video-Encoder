from pathlib import Path
import logging


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
