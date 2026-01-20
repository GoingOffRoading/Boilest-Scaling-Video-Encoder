#!/usr/bin/env python3
"""
Initialize the Boilest database with required tables.
Creates the database file if it doesn't exist and sets up the schema.
"""
import sqlite3
import sys
from pathlib import Path


def create_database(db_path):
    """Create the database and all required tables."""
    try:
        db_path = Path(db_path)
        
        # Create parent directory if it doesn't exist
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        print(f"[INIT_DB] Creating database at {db_path}")
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        # Create directories table
        cur.execute("""CREATE TABLE IF NOT EXISTS directories (
            guid TEXT PRIMARY KEY,
            path TEXT NOT NULL UNIQUE,
            added_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );""")
        print("[INIT_DB] Created 'directories' table")

        # Create queue table
        cur.execute("""CREATE TABLE IF NOT EXISTS queue (
            guid TEXT PRIMARY KEY,
            directory_guid TEXT NOT NULL,
            file_path TEXT NOT NULL,
            output_file_name TEXT,
            before_file_size INTEGER NOT NULL,
            ffmpeg_string TEXT,
            date_added TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );""")
        print("[INIT_DB] Created 'queue' table")

        # Create completed table
        cur.execute("""CREATE TABLE IF NOT EXISTS completed (
            guid TEXT PRIMARY KEY,
            queued_file_guid TEXT NOT NULL,
            after_file_size INTEGER NOT NULL,
            date_added TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );""")
        print("[INIT_DB] Created 'completed' table")

        # Create error table
        cur.execute("""CREATE TABLE IF NOT EXISTS error (
            guid TEXT PRIMARY KEY,
            queued_file_guid TEXT NOT NULL,
            reason TEXT NOT NULL,
            additional_detail TEXT,
            date_added TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );""")
        print("[INIT_DB] Created 'error' table")

        # Populate default directories
        default_directories = [
            ('1ae5df46-7d84-44ec-8174-73f1d12170c5', '/Boil/Media/Anime', '2026-01-16 19:24:25'),
            ('eb120fd2-5860-409d-9c47-534cefd0dc9b', '/Boil/Media/TV', '2026-01-16 19:24:28'),
            ('1a2c2141-cc92-43a2-8c41-9ce95f0864dd', '/Boil/Media/Movies', '2026-01-16 19:24:34'),
        ]
        
        for guid, path, added_at in default_directories:
            try:
                cur.execute(
                    "INSERT OR IGNORE INTO directories (guid, path, added_at) VALUES (?, ?, ?)",
                    (guid, path, added_at)
                )
                if cur.rowcount > 0:
                    print(f"[INIT_DB] Added directory: {path}")
            except Exception as e:
                print(f"[INIT_DB] Warning: Could not add directory {path}: {e}")

        conn.commit()
        conn.close()
        
        print("[INIT_DB] Database created successfully")
        return True
        
    except Exception as e:
        print(f"[INIT_DB] Error creating database: {e}", file=sys.stderr)
        return False


if __name__ == '__main__':
    # Get database path from command line argument or use default
    db_path = sys.argv[1] if len(sys.argv) > 1 else '/Boil/App/Boilest.db'
    
    success = create_database(db_path)
    sys.exit(0 if success else 1)
