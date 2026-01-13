# Use the official Python image based on Alpine
FROM python:3.9-alpine

# Install dependencies and supervisor
RUN apk update && \
    apk add --no-cache \
        build-base \
        linux-headers \
        supervisor \
        ffmpeg && \
    pip install --no-cache-dir celery requests mysql-connector-python pika jupyter nbconvert && \
    apk upgrade

# Create a non-root user and group
ARG UID=1000
ARG GID=1000
RUN addgroup -g $GID appgroup && \
    adduser -D -u $UID -G appgroup appuser

# Create additional directories without setting ownership
RUN mkdir -p /tv /anime /moviles /boil_hold

# Create application directory and set ownership
WORKDIR /app
COPY . /app
RUN chown -R appuser:appgroup /app /boil_hold

# Create log directory and set ownership
RUN mkdir -p /app/logs && \
    mkdir -p /app/data && \
    chown -R appuser:appgroup /app/logs /app/data

# Environment variables
ENV TZ=US/Pacific
ENV Role=worker

# Run as non-root user
USER appuser

# Entrypoint will choose manager or worker based on the `Manager` environment variable
COPY docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD [""]