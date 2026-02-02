"""CLI to add or remove directory paths from the `directories` table.

Usage examples:
  python manage_directories.py add /path/to/videos
  python manage_directories.py remove /path/to/videos

The script checks that the filesystem directory exists before adding, and
verifies the row exists in the database before removing.
"""
import argparse
import os
import sqlite3
import uuid
import sys
from typing import Optional, Dict, Any

from db_path import get_db_path


def add_directory(path: str, db_path: Optional[str] = None) -> Dict[str, Any]:
    if db_path is None:
        db_path = get_db_path()

    path = os.path.expanduser(path)
    if not os.path.isdir(path):
        return {"error": f"Filesystem path does not exist or is not a directory: {path}"}

    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        # Check for existing entry
        cur.execute("SELECT 1 FROM directories WHERE path = ? LIMIT 1", (path,))
        if cur.fetchone() is not None:
            return {"status": "exists", "message": "Directory already present in database", "path": path}

        new_guid = str(uuid.uuid4())
        cur.execute("INSERT INTO directories (guid, path) VALUES (?, ?)", (new_guid, path))
        conn.commit()
        return {"status": "added", "guid": new_guid, "path": path}

    except sqlite3.Error as e:
        return {"error": str(e)}
    finally:
        try:
            conn.close()
        except Exception:
            pass


def remove_directory(path: str, db_path: Optional[str] = None) -> Dict[str, Any]:
    if db_path is None:
        db_path = get_db_path()

    path = os.path.expanduser(path)

    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        # Verify row exists
        cur.execute("SELECT guid FROM directories WHERE path = ? LIMIT 1", (path,))
        row = cur.fetchone()
        if row is None:
            return {"status": "missing", "message": "Directory not found in database", "path": path}

        guid = row[0]
        cur.execute("DELETE FROM directories WHERE guid = ?", (guid,))
        conn.commit()
        return {"status": "removed", "guid": guid, "path": path}

    except sqlite3.Error as e:
        return {"error": str(e)}
    finally:
        try:
            conn.close()
        except Exception:
            pass


def main(argv=None):
    parser = argparse.ArgumentParser(description="Add or remove directory paths in boilest.db directories table")
    parser.add_argument("operator", choices=["add", "remove"], help="Operation to perform")
    parser.add_argument("path", help="Directory path to add or remove")
    parser.add_argument("--db", dest="db_path", help="Optional path to database file")

    args = parser.parse_args(argv)

    if args.operator == "add":
        result = add_directory(args.path, args.db_path)
    else:
        result = remove_directory(args.path, args.db_path)

    # Print JSON-like dict result for easy parsing
    print(result)

    # Exit with non-zero code on error
    if isinstance(result, dict) and "error" in result:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
