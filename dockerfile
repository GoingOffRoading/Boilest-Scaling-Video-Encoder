# Use the official Python image based on Alpine
FROM python:3.13-alpine

# Install dependencies and supervisor
RUN apk update && \
    apk add --no-cache \
        build-base \
        linux-headers \
        ffmpeg && \
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
RUN mkdir -p /boil/worker
RUN mkdir -p /boil/boil_hold
RUN mkdir -p /boil/templates

# Create directories for media data
RUN mkdir -p /boilmedia

# Create application directory and set ownership
COPY manager /boil/manager
COPY worker /boil/worker
COPY templates /boil/templates
COPY entrypoint.sh /boil/entrypoint.sh

# Create directories for unpersisted application data 
RUN chown -R appuser:appgroup /boil 

# Used in Flask
ENV FLASK_APP=Flask.py
ENV FLASK_ENV=development
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5000

# Environment variables
ENV TZ=US/Pacific
ENV Role=Worker
ENV FFMPEG_SETTINGS='ffmpeg -hide_banner -loglevel 16 -stats -stats_period 10 -y -i'
ENV POLL_INTERVAL=60

# Entrypoint will choose manager or worker based on the `Manager` environment variable
RUN chmod +x /boil/entrypoint.sh && \
    chown appuser:appgroup /boil/entrypoint.sh

# Run as non-root user (after permissions are set)
USER appuser

#Exposes port 5000 for Flask by default
EXPOSE 5000

ENTRYPOINT ["/boil/entrypoint.sh"]
CMD [""]