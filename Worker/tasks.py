from celery import Celery
import os.path
from subprocess import call

app = Celery('tasks', backend = 'rpc://test:test@192.168.1.110:31672/celery', broker = 'amqp://test:test@192.168.1.110:31672/celery')

@app.task
def add(x, y):
    return x + y


