# Use the official Python image based on Alpine
FROM python:3.13-alpine

# Install dependencies and supervisor
RUN apk update && \
    apk add --no-cache \
        build-base \
        linux-headers \
        ffmpeg \
        sqlite && \
    pip install --no-cache-dir flask requests && \
    apk upgrade

# Create a non-root user and group
ARG UID=1000
ARG GID=1000
RUN addgroup -g $GID appgroup && \
    adduser -D -u $UID -G appgroup appuser

# Create directories for the persisted application data
RUN mkdir -p /boil/app 

# Create directories for the unpersisted persisted application data
RUN mkdir -p /boil/manager
RUN mkdir -p /boil/local_worker
RUN mkdir -p /boil/cloud_worker
RUN mkdir -p /boil/boil_hold

# Create directories for media data
RUN mkdir -p /tv-unsorted && \
    mkdir -p /tv-live-action && \
    mkdir -p /tv-live-action-favorites && \
    mkdir -p /tv-animated && \
    mkdir -p /tv-animated-favorites && \
    mkdir -p /movies-unsorted && \
    mkdir -p /movies-live-action && \
    mkdir -p /movies-live-action-favorites && \
    mkdir -p /movies-animated && \
    mkdir -p /movies-animated-favorites && \
    mkdir -p /anime-unsorted && \
    mkdir -p /anime && \
    mkdir -p /anime-favorites && \
    mkdir -p /youtube && \
    mkdir -p /home-movies

# Create application directory and set ownership
COPY manager /boil/manager
COPY local_worker /boil/local_worker
COPY cloud_worker /boil/cloud_worker
COPY entrypoint.sh /boil/entrypoint.sh

# Create directories for unpersisted application data 
RUN chown -R appuser:appgroup /boil && \
    chown -R appuser:appgroup /tv-unsorted && \
    chown -R appuser:appgroup /tv-live-action && \
    chown -R appuser:appgroup /tv-live-action-favorites && \
    chown -R appuser:appgroup /tv-animated && \
    chown -R appuser:appgroup /tv-animated-favorites && \
    chown -R appuser:appgroup /movies-unsorted && \
    chown -R appuser:appgroup /movies-live-action && \
    chown -R appuser:appgroup /movies-live-action-favorites && \
    chown -R appuser:appgroup /movies-animated && \
    chown -R appuser:appgroup /movies-animated-favorites && \
    chown -R appuser:appgroup /anime-unsorted && \
    chown -R appuser:appgroup /anime && \
    chown -R appuser:appgroup /anime-favorites && \
    chown -R appuser:appgroup /youtube && \
    chown -R appuser:appgroup /home-movies

# Global Variables
ENV NODE_NAME=""

# Manager Variables
ENV FLASK_APP=Flask.py
ENV FLASK_ENV=development
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5000

# Worker Variables
ENV TZ=US/Pacific
ENV Role=Worker
ENV LOG_LEVEL=INFO
ENV FFMPEG_SETTINGS='ffmpeg -hide_banner -loglevel 16 -stats -stats_period 60 -y -i'
ENV MANAGER_BASE_URL='http://localhost:5000'

# Entrypoint will choose manager or worker based on the `Manager` environment variable
RUN chmod +x /boil/entrypoint.sh && \
    chown appuser:appgroup /boil/entrypoint.sh

# Run as non-root user (after permissions are set)
USER appuser

#Exposes port 5000 for Flask by default
EXPOSE 5000

ENTRYPOINT ["/boil/entrypoint.sh"]
CMD [""]