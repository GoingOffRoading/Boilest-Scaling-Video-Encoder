import os

start_celery = 'celery -A tasks worker -l INFO -c 1'
os.system(start_celery)
print ("stuff")

devnull = 'tail -f /dev/null'
os.system(devnull)