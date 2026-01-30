#!/bin/sh
# docker-entrypoint.sh
# If the environment variable Manager is set (non-empty), run manager/start.sh
# Otherwise convert and run the ffmpeg worker notebook

set -e

# If Manager env var exists and is non-empty -> manager
if [ "${Role}" = "Manager" ]; then
    echo "[ENTRYPOINT] Manager mode detected (Role=${Role}). Running manager startup steps"
    
    # Check if database exists, if not copy from /boil/manager
    if [ ! -f /boil/app/boilest.db ]; then
        echo "[ENTRYPOINT] No /boil/app/boilest.db found.  Copying template database from /boil/manager/boilest.db"
        cp /boil/manager/boilest.db /boil/app/boilest.db
        chmod 664 /boil/app/boilest.db
    else
        echo "[ENTRYPOINT] /boil/app/boilest.db found"
    fi

    # Run start script (non-blocking expected)
    echo "[ENTRYPOINT] Running manager.py"
    if [-f /boil/manager/manager.py ]; then
        echo "manager.py found"
    fi

    python /boil/manager/manager.py || echo "[ENTRYPOINT] manager.py failed"
else
    echo "[ENTRYPOINT] Worker mode detected (Role=${Role}). Running worker.py"
    python /boil/worker/worker.py || echo "[ENTRYPOINT] worker.py failed"
fi
