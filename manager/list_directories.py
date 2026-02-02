"""Utilities for listing rows from the `directories` table in boilest.db."""
from typing import List, Dict, Union
import sqlite3
from db_path import get_db_path


def list_directories_rows(db_path: str = None) -> Union[List[Dict], Dict]:
    """Return all rows from the `directories` table as a list of dictionaries.

    If `db_path` is not provided, the function will use `get_db_path()` from
    `manager/db_path.py` to determine the database file location.

    On success: returns List[Dict] where each dict represents a row.
    On error: returns Dict containing an "error" key with the exception message.
    """
    
    db_path = get_db_path()

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM directories")
        rows = [dict(r) for r in cur.fetchall()]
    except sqlite3.Error as e:
        return {"error": str(e)}
    finally:
        try:
            conn.close()
        except Exception:
            pass

    return rows
