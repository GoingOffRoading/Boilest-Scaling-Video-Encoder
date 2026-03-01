import sqlite3


def is_file_unpulled_in_queue(input_file_name: str, directory_path: str, db_path: str) -> bool:
    """Check if file is already in queue."""
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT 1 FROM queue WHERE input_file_name = ? AND directory_path = ? LIMIT 1",
            (input_file_name, directory_path),
        )
        return cur.fetchone() is not None
    finally:
        conn.close()
