<<<<<<< HEAD
#!/bin/sh

celery -A tasks celery beat -l debug &
celery -A tasks celery worker -l info &
celery -A tasks celery flower -l info 

#&
#tail -f /dev/null


=======
#!/bin/sh -ex

celery -A app.tasks.celery beat -l debug &
celery -A app.tasks.celery worker -l info &
celery -A app.tasks.celery flower -l info &
tail -f /dev/null
>>>>>>> 674c8c6bb5ebf8ea61f7bbff40b5ab64508bf20e
