import sqlite3
import uuid
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def write_to_queue(directory_guid, directory_path, input_file_name, output_file_name, before_file_size, ffmpeg_string, priority, db_path):
    """Write a row into `queue` using the updated schema, including priority.

    Schema columns inserted:
      directory_guid, file_guid, directory_path, input_file_name,
      output_file_name, before_file_size, after_file_size, ffmpeg_string,
      datetime_added, datetime_pulled, datetime_encoded, status, priority

    Parameters:
      - directory_guid (str)
      - directory_path (str)
      - input_file_name (str)
      - output_file_name (str)
      - before_file_size (int)
      - ffmpeg_string (str)
      - priority (int)
      - after_file_size (int|None) optional
      - db_path (str|None) optional DB path; falls back to global `db_path` variable
    """
    try:
        file_guid = str(uuid.uuid4())
        datetime_added = datetime.now().isoformat()
        after_file_size = None
        datetime_pulled = None
        datetime_encoded = None
        status = 'queued'

        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO queue (directory_guid, file_guid, directory_path, input_file_name, output_file_name, before_file_size, after_file_size, ffmpeg_string, datetime_added, datetime_pulled, datetime_encoded, status, priority) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                directory_guid,
                file_guid,
                directory_path,
                input_file_name,
                output_file_name,
                before_file_size,
                after_file_size,
                ffmpeg_string,
                datetime_added,
                datetime_pulled,
                datetime_encoded,
                status,
                priority,
            ),
        )
        conn.commit()
        conn.close()

        logging.debug(f"✓ Wrote queue entry {file_guid} for {input_file_name}")
        return file_guid

    except Exception as e:
        logging.debug(f"✗ Error writing to queue: {e}")
        try:
            conn.close()
        except Exception:
            pass
        return None
