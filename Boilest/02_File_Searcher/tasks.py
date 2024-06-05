from celery import Celery
from datetime import datetime
import json, os, sqlite3, logging
from task_shared_services import task_start_time, task_duration_time, check_queue, find_files, celery_url_path, check_queue, ffmpeg_output_file, ffprober_function, get_active_tasks, get_file_size_bytes
import celeryconfig

app = Celery('tasks', backend = celery_url_path('rpc://'), broker = celery_url_path('amqp://') )
app.config_from_object(celeryconfig)

@app.task(queue='manager')
# Assuming we get an all clear from queue_workers_if_queue_empty, locate_files locates media file to be probed (probing is a dependency to determine if the file must be encoded)
def locate_files(arg):
    function_start_time = task_start_time('locate_files')
    directories = ['/anime', '/tv', '/movies']
    extensions = ['.mp4', '.mkv', '.avi']
    logging.debug ('Searching: ' + str(directories))
    logging.debug ('For: ' + str(extensions))
    for file_located in find_files(directories, extensions):
            logging.debug ('Send to ffprobe function')
            file_located = json.loads(file_located)
            logging.debug(json.dumps(file_located, indent=3, sort_keys=True))
            ffprober.delay(file_located)
    task_duration_time('locate_files',function_start_time)
