#!/bin/sh
# docker-entrypoint.sh
# If the environment variable Manager is set (non-empty), run manager/start.sh
# Otherwise convert and run the ffmpeg worker notebook

set -e

# If Manager env var exists and is non-empty -> manager
if [ "${Role}" = "Manager" ]; then
    echo "[ENTRYPOINT] Manager mode detected (Role=${Role}). Running manager startup steps"
    # Restore DB if missing
    if [ ! -f /boil/app/boilest.db ]; then
        echo "[ENTRYPOINT] No /boil/app/boilest.db found"
        cp /boil/scripts/boilest.db /boil/app/boilest.db
    fi

    # Run start script (non-blocking expected)
    echo "[ENTRYPOINT] Running manager.py"
    python /boil/manager.py || echo "[ENTRYPOINT] manager.py failed"

else
    echo "[ENTRYPOINT] Worker mode detected. Converting and running 04_ffmpeg_worker.ipynb"
    # Convert notebook to script
    jupyter nbconvert --to script /boil/04_ffmpeg_worker.ipynb --output /boil/04_ffmpeg_worker.py || {
        echo "[ENTRYPOINT] Failed to convert notebook to script"
        exec /bin/sh
    }

    # Ensure executable permissions
    chmod +x /boil/04_ffmpeg_worker.py || true

    # Run the generated script (it should start the worker loop)
    exec python /boil/04_ffmpeg_worker.py
fi
