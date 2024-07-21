# Use the official Python image based on Alpine
FROM python:3.9-alpine

# Install dependencies and supervisor
RUN apk update && \
    apk add --no-cache \
        build-base \
        linux-headers \
        supervisor \
        ffmpeg && \
    pip install --no-cache-dir celery requests mysql-connector-python && \
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
    chown -R appuser:appgroup /app/logs

# Environment variables
ENV TZ=US/Pacific

# Used in celery and rabbitmq
ENV user celery
ENV password celery
ENV celery_host 192.168.1.110
ENV celery_port 31672
ENV celery_vhost celery
ENV rabbitmq_host 192.168.1.110
ENV rabbitmq_port 32311

# Used in celery and rabbitmq
ENV sql_host 192.168.1.110
ENV sql_port 32053
ENV sql_database boilest
ENV sql_user boilest
ENV sql_pswd boilest

# Run as non-root user
USER appuser

# Start supervisord
#CMD ["supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
CMD ["celery", "-A", "tasks", "worker"]