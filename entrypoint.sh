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
            python3 /Boil/Scripts/init_database.py /Boil/App/Boilest.db
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
