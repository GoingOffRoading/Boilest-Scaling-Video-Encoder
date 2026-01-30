#!/bin/sh
# docker-entrypoint.sh
# If the environment variable Manager is set (non-empty), run manager/start.sh
# Otherwise convert and run the ffmpeg worker notebook

set -e

# If Manager env var exists and is non-empty -> manager
if [ "${Role}" = "Manager" ]; then
    echo "[ENTRYPOINT] Manager mode detected (Role=${Role}). Running manager startup steps"
    
    # Check if database exists, if not copy from /Boil/Scripts
    if [ ! -f /Boil/App/boilest.db ]; then
        echo "[ENTRYPOINT] No /Boil/App/boilest.db found.  Copying template database from /Boil/Scripts/Manager/scripts/boilest.db"
        cp /Boil/Scripts/Manager/scripts/boilest.db /Boil/App/boilest.db
        chmod 664 /Boil/App/boilest.db
    else
        echo "[ENTRYPOINT] /Boil/App/boilest.db found"
    fi

    # Run start script (non-blocking expected)
    echo "[ENTRYPOINT] Running manager.py"
    if [-f /Boil/Scripts/Manager/scripts/manager.py ]; then
        echo "manager.py found"
    fi

    python -m /Boil/Scripts/Manager/scripts/manager.py || echo "[ENTRYPOINT] manager.py failed"

else
    echo "[ENTRYPOINT] Worker mode detected (Role=${Role}). Running worker.py"
    python /Boil/Scripts/worker.py || echo "[ENTRYPOINT] worker.py failed"
fi
