#!/bin/sh -ex

celery -A tasks worker --detach -l info -c 1 &
celery -A tasks flower -l debug &
tail -f /dev/null
