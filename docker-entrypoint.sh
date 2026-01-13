#!/bin/sh
# docker-entrypoint.sh
# If the environment variable Manager is set (non-empty), run manager/start.sh
# Otherwise convert and run the ffmpeg worker notebook

set -e

# If Manager env var exists and is non-empty -> manager
if [ "${Role}" = "Manager" ]; then
    echo "[ENTRYPOINT] Manager mode detected (Role=${Role}). Running manager startup steps"
    # Restore DB if missing
    if [ ! -f /app/data/boilest.db ]; then
        if [ -f /boil_hold/boilest.db ]; then
            echo "[ENTRYPOINT] Restoring boilest.db to /app/data/"
            cp /boil_hold/boilest.db /app/data/
        else
            echo "[ENTRYPOINT] No /boil_hold/boilest.db to restore"
        fi
    fi

    # Run start script (non-blocking expected)
    echo "[ENTRYPOINT] Running start.py"
    python start.py || echo "[ENTRYPOINT] start.py failed"

else
    echo "[ENTRYPOINT] Worker mode detected. Converting and running 04_ffmpeg_worker.ipynb"
    # Convert notebook to script
    jupyter nbconvert --to script /app/04_ffmpeg_worker.ipynb --output /app/04_ffmpeg_worker.py || {
        echo "[ENTRYPOINT] Failed to convert notebook to script"
        exec /bin/sh
    }

    # Ensure executable permissions
    chmod +x /app/04_ffmpeg_worker.py || true

    # Run the generated script (it should start the worker loop)
    exec python /app/04_ffmpeg_worker.py
fi
