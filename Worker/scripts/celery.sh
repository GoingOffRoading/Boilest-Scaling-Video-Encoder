#!/bin/sh -ex

celery -A tasks worker -l info -c 1 
#celery -A app.tasks.celery worker -l info  -c 1 
#&
#celery -A tasks celery flower -l info -c 1
#tail -f /dev/null
