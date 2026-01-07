from celery import Celery
import json, os, logging, subprocess, shutil, mysql.connector
from mysql.connector import Error
from datetime import datetime
from scripts.01_file_finder import find_files
from scripts.02_file_prober import process_file_for_encoding
from scripts.03_ffmpeg_processor import process_ffmpeg_steps
from scripts.04_database_writer import write_results
from scripts.celery_config import configure_celery

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>  
# >>>>>>>>>>>>>>> Celery Configurations >>>>>>>>>>>>>>>
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>  

# create logger
logger = logging.getLogger('boilest_logs')
logger.setLevel(logging.INFO)

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)


def celery_url_path(thing):
    # https://docs.celeryq.dev/en/stable/getting-started/first-steps-with-celery.html#keeping-results
    celery_user = os.environ.get('user', 'celery')
    celery_password = os.environ.get('password', 'celery')
    celery_host = os.environ.get('celery_host', '192.168.1.110')
    celery_port = os.environ.get('celery_port', '31672')
    celery_vhost = os.environ.get('celery_vhost', 'celery')
    thing = thing + celery_user + ':' + celery_password + '@' + celery_host + ':' + celery_port + '/' + celery_vhost
    logger.debug('celery_url_path is: ' + thing)
    return thing

app = Celery('worker_queue', broker = celery_url_path('amqp://') )

configure_celery(app)

# >>>>>>>>>>>>>>>>>>>>>> <<<<<<<<<<<<<<<<<<<<<< 
# This section starts the discovery of the files by searching directories
# >>>>>>>>>>>>>>>>>>>>>> <<<<<<<<<<<<<<<<<<<<<<

@app.task
def locate_files(arg):
    directories = ['/anime', '/tv', '/movies']
    extensions = ['.mp4', '.mkv', '.avi']

    logger.info(f'Searching directories: {directories}')
    logger.info(f'File extensions: {extensions}')

    for file_located in find_files(directories, extensions):
        logger.debug('File located, sending to ffprobe function')
        try:
            file_located_data = json.loads(file_located)
            logger.debug(json.dumps(file_located_data, indent=3, sort_keys=True))
            # >>>>>>>>>>><<<<<<<<<<<<<<<<
            # >>>>>>>>>>><<<<<<<<<<<<<<<<
            requires_encoding.apply_async(kwargs={'file_located_data': file_located_data}, priority=1)
            # >>>>>>>>>>><<<<<<<<<<<<<<<<
            # >>>>>>>>>>><<<<<<<<<<<<<<<<
        except json.JSONDecodeError as e:
            logger.error(f'Failed to decode JSON: {e}')
            continue

# >>>>>>>>>>>>>>>>>>>>>> <<<<<<<<<<<<<<<<<<<<<< 
# This section starts the discovery of the file meta data, and determing what processing may need to occure
# >>>>>>>>>>>>>>>>>>>>>> <<<<<<<<<<<<<<<<<<<<<<

@app.task
def requires_encoding(file_located_data):
    file_name = file_located_data['file']
    logger.info(file_name + ' started requires_encoding')
    encoding_decision, ffmpeg_command, ffmepg_output_file_name, processing_priority = process_file_for_encoding(file_located_data)
    if encoding_decision == True:
        logger.info (file_located_data['file'] + ' requires encoding')
        file_located_data['ffmpeg_command'] = ffmpeg_command
        file_located_data['ffmepg_output_file_name'] = ffmepg_output_file_name
        file_located_data['old_file_size'] = file_size_kb(file_located_data['file_path'])
        logger.debug(json.dumps(file_located_data, indent=4))
        process_ffmpeg.apply_async(kwargs={'file_located_data': file_located_data}, priority=processing_priority)
    else:
        logger.debug ('file does not need encoding')
    logger.debug (encoding_decision)
    logger.debug (ffmpeg_command)
    logger.info(file_name + ' ended requires_encoding')

def file_size_kb(file_path):
    # Returns the file size of the file_path on disk
    if os.path.isfile(file_path):
        file_size_bytes = os.path.getsize(file_path)
        file_size_kb = file_size_bytes / 1024
        return round(file_size_kb)
    else:
        return 0.0

# >>>>>>>>>>>>>>>>>>>>>> <<<<<<<<<<<<<<<<<<<<<< 
# This section starts the actual processing of media fules
# >>>>>>>>>>>>>>>>>>>>>> <<<<<<<<<<<<<<<<<<<<<<
 

@app.task()
def process_ffmpeg(file_located_data):
    file = file_located_data['file']
    result = process_ffmpeg_steps(file_located_data)
    if result:
        logger.info ('ffmpeg is done with: ' + file)
        write_results(result)
        logger.debug(json.dumps(result, indent=4))



    

# >>>>>>>>>>>>>>>>>>>>>> <<<<<<<<<<<<<<<<<<<<<< 
# This section starts the discovery of the files by searching directories
# >>>>>>>>>>>>>>>>>>>>>> <<<<<<<<<<<<<<<<<<<<<<

