# Use the official Python image based on Alpine
FROM python:3.13-alpine

# Install dependencies and supervisor
RUN apk update && \
    apk add --no-cache \
        build-base \
        linux-headers \
        ffmpeg && \
    pip install --no-cache-dir flask && \
    apk upgrade

# Create a non-root user and group
ARG UID=1000
ARG GID=1000
RUN addgroup -g $GID appgroup && \
    adduser -D -u $UID -G appgroup appuser

# Create directories for the persisted application data
RUN mkdir -p /boil/app 

# Create directories for the unpersisted persisted application data
RUN mkdir -p /boil/scripts

# Create directories for media files
RUN mkdir -p /boil/tv && \
    mkdir -p /boil/anime && \
    mkdir -p /boil/moviles && \
    mkdir -p /boil/media && \
    mkdir -p /boil/boil_hold

# Create application directory and set ownership
COPY . /boil/scripts

# Create directories for unpersisted application data 
RUN chown -R appuser:appgroup /boil 

# Create log directory and set ownership
#WORKDIR /boil

# Environment variables
ENV TZ=US/Pacific
ENV Role=Worker

# Entrypoint will choose manager or worker based on the `Manager` environment variable
RUN chmod +x /boil/scripts/entrypoint.sh && \
    chown appuser:appgroup /boil/scripts/entrypoint.sh

# Run as non-root user (after permissions are set)
USER appuser

ENTRYPOINT ["/boil/scripts/entrypoint.sh"]
CMD [""]