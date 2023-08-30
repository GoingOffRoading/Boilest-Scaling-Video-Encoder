#!/bin/sh -ex

celery -A app.tasks.celery beat -l debug &
celery -A app.tasks.celery worker -l info &
celery -A app.tasks.celery flower -l info &
tail -f /dev/null