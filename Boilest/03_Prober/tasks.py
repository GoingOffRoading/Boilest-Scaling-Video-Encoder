from celery import Celery
from datetime import datetime
import json, os, sqlite3, logging
from task_shared_services import task_start_time, task_duration_time, check_queue, find_files, celery_url_path, check_queue, ffmpeg_output_file, ffprober_function, get_active_tasks, get_file_size_bytes
import celeryconfig

app = Celery('tasks', backend = celery_url_path('rpc://'), broker = celery_url_path('amqp://') )
app.config_from_object(celeryconfig)

@app.task(queue='manager')
# Nothing special...  ffprober, on getting a media file from locate_files, runs ffprobe and ships the combined payloads to container_check
def ffprober(file_located):
    function_start_time = task_start_time('ffprober')    
    ffprobe_results = ffprober_function(file_located) 
    logging.debug(json.dumps(ffprobe_results, indent=3, sort_keys=True))
    container_check.delay(file_located,ffprobe_results)
    task_duration_time('ffprober',function_start_time)

