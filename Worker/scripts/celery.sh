
#!/bin/sh

celery -A tasks celery beat -l debug &
celery -A tasks celery worker -l info &
celery -A tasks celery flower -l info &
tail -f /dev/null
