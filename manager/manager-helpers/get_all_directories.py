import sqlite3
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def get_all_directories(db_path):
    """Return all rows from the `directories` table as a list of (guid, path, ffmpeg_video, desired_video_codec)."""
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT guid, path, ffmpeg_video, desired_video_codec FROM directories WHERE active = 'active'")
        rows = cur.fetchall()
        conn.close()
        return rows
    except Exception as e:
        logging.debug(f"✗ Error reading directories table: {e}")
        try:
            if conn:
                conn.close()
        except:
            pass
        return []
