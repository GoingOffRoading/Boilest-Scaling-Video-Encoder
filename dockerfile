# Use the official Python image based on Alpine
FROM python:3.9-alpine

# Install dependencies and supervisor
RUN apk update && \
    apk add --no-cache \
        build-base \
        linux-headers \
        supervisor \
        ffmpeg && \
    pip install --no-cache-dir celery requests mysql-connector-python pika && \
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
RUN chown -R appuser:appgroup /app /boil_hold && \
    chmod +x /app/start.sh

# Create log directory and set ownership
RUN mkdir -p /app/logs && \
    mkdir -p /app/data && \
    chown -R appuser:appgroup /app/logs /app/data

# Environment variables
ENV TZ=US/Pacific
ENV ROLE=worker

# Used in celery and rabbitmq
ENV user celery
ENV password celery
ENV celery_host 192.168.1.110
ENV celery_port 31672
ENV celery_vhost celery
ENV rabbitmq_host 192.168.1.110
ENV rabbitmq_port 32311

# Run as non-root user
USER appuser

# Start the application
CMD ["/app/start.sh"]