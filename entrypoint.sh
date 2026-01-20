#!/bin/sh
# docker-entrypoint.sh
# If the environment variable Manager is set (non-empty), run manager/start.sh
# Otherwise convert and run the ffmpeg worker notebook

set -e

# If Manager env var exists and is non-empty -> manager
if [ "${Role}" = "Manager" ]; then
    echo "[ENTRYPOINT] Manager mode detected (Role=${Role}). Running manager startup steps"
    # Restore DB if missing
    if [ ! -f /Boil/App/Boilest.db ]; then
        echo "[ENTRYPOINT] No /Boil/App/Boilest.db found"
        if [ -f /Boil/Scripts/Boilest.db ]; then
            echo "[ENTRYPOINT] Copying template database from /Boil/Scripts/Boilest.db"
            cp /Boil/Scripts/Boilest.db /Boil/App/Boilest.db
        else
            echo "[ENTRYPOINT] No template database found, creating new database"
            python3 << 'EOF'
import sqlite3
from pathlib import Path

db_path = Path('/Boil/App/Boilest.db')
conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.execute("""CREATE TABLE IF NOT EXISTS directories (
    guid TEXT PRIMARY KEY,
    path TEXT NOT NULL UNIQUE,
    added_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);""")

cur.execute("""CREATE TABLE IF NOT EXISTS queue (
    guid TEXT PRIMARY KEY,
    directory_guid TEXT NOT NULL,
    file_path TEXT NOT NULL,
    output_file_name TEXT,
    before_file_size INTEGER NOT NULL,
    ffmpeg_string TEXT,
    date_added TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);""")

cur.execute("""CREATE TABLE IF NOT EXISTS completed (
    guid TEXT PRIMARY KEY,
    queued_file_guid TEXT NOT NULL,
    after_file_size INTEGER NOT NULL,
    date_added TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);""")

cur.execute("""CREATE TABLE IF NOT EXISTS error (
    guid TEXT PRIMARY KEY,
    queued_file_guid TEXT NOT NULL,
    reason TEXT NOT NULL,
    additional_detail TEXT,
    date_added TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);""")

conn.commit()
conn.close()
print("[ENTRYPOINT] Database created successfully")
EOF
        fi
        # Ensure proper permissions on the database file
        chmod 664 /Boil/App/Boilest.db
        echo "[ENTRYPOINT] Database permissions set"
    else
        echo "[ENTRYPOINT] /Boil/App/Boilest.db found"
    fi

    # Run start script (non-blocking expected)
    echo "[ENTRYPOINT] Running manager.py"
    python /Boil/Scripts/manager.py || echo "[ENTRYPOINT] manager.py failed"

else
    echo "[ENTRYPOINT] Worker mode detected (Role=${Role}). Running worker.py"
    python /Boil/Scripts/worker.py || echo "[ENTRYPOINT] worker.py failed"
fi
