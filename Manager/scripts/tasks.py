from celery import Celery
import os.path
from task_01_findmedia import findmedia
from task_02_ffprobe import ffprober
from task_03_process import ffencoder
from task_04_stats import ffstatrecorder
from subprocess import call


app = Celery('tasks', backend = 'rpc://test:test@192.168.1.110:31672/celery', broker = 'amqp://test:test@192.168.1.110:31672/celery')

@app.task
def add(x, y):
    return x + y

def fffind(DIRECTORY):
    findmedia(DIRECTORY)

def ffprobe(FILEPATH):
    ffprober(FILEPATH)

def ffencode(FILEPATH, ENCODESTRING):
    ffencoder(FILEPATH, ENCODESTRING)

def ffstatrecorde(FILEPATH, FILENAME, STARTSZIE, ENDSIZE, VMAF):
    ffstatrecorder(FILEPATH, FILENAME, STARTSZIE, ENDSIZE, VMAF)

def ffchain(DIRECTORY):
    # fetch_page -> parse_page -> store_page
    chain = fffind(DIRECTORY) | ffprobe(FILEPATH) 
    chain()


    


