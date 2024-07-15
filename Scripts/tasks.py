from celery import Celery
import json, os, logging, subprocess
import celeryconfig
from shared_services import celery_url_path


# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>  
# >>>>>>>>>>>>>>> Celery Configurations >>>>>>>>>>>>>>>
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>  

app = Celery('worker', backend = celery_url_path('rpc://'), broker = celery_url_path('amqp://') )
app.config_from_object(celeryconfig)

def celery_url_path(thing):
    # https://docs.celeryq.dev/en/stable/getting-started/first-steps-with-celery.html#keeping-results
    user = os.environ.get('user', 'celery')
    password = os.environ.get('password', 'celery')
    celery_host = os.environ.get('celery_host', '192.168.1.110')
    celery_port = os.environ.get('celery_port', '31672')
    celery_vhost = os.environ.get('celery_vhost', 'celery')
    thing = thing + user + ':' + password + '@' + celery_host + ':' + celery_port + '/' + celery_vhost
    logging.debug('celery_url_path is: ' + thing)
    return thing

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# >>>>>>>>>>>>>>> Check queue depth >>>>>>>>>>>>>>>
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

@app.task(queue='worker', name='queue_workers_if_queue_empty')
def queue_workers_if_queue_empty(arg):
    try:
        queue_depth = check_queue('worker')
        
        logging.info(f'Current Worker queue depth is: {queue_depth}')
        print(f'Current Worker queue depth is: {queue_depth}')
        
        if queue_depth == 0:
            logging.debug('Starting locate_files')
            # >>>>>>>>>>><<<<<<<<<<<<<<<<
            # >>>>>>>>>>><<<<<<<<<<<<<<<<
            locate_files.apply_async(kwargs={'arg': arg}, priority=1)
            # >>>>>>>>>>><<<<<<<<<<<<<<<<
            # >>>>>>>>>>><<<<<<<<<<<<<<<<
        elif queue_depth > 0:
            logging.debug(f'{queue_depth} tasks in queue. No rescan needed at this time.')
        else:
            logging.error('Something went wrong checking the Worker Queue')
    
    except Exception as e:
        logging.error(f"Error in queue_workers_if_queue_empty: {e}")


def check_queue(queue_name):
    try:
        rabbitmq_host = 'http://' + os.environ.get('rabbitmq_host','192.168.1.110')
        rabbitmq_port = os.environ.get('rabbitmq_port','32311')
        user = os.environ.get('user','celery')
        password = os.environ.get('password','celery')
        celery_vhost = os.environ.get('celery_vhost','celery')

        url = f"{rabbitmq_host}:{rabbitmq_port}/api/queues/{celery_vhost}/{queue_name}"
        logging.debug(f'Checking RabbitMQ queue depth for: {queue_name}')

        response = requests.get(url, auth=(user, password))
        response.raise_for_status()  # Ensure we raise an exception for HTTP errors

        worker_queue = response.json()
        queue_depth = worker_queue.get("messages_unacknowledged", 0)

        logging.debug (f'check_queue queue depth is: ' + str(queue_depth))
        return queue_depth
    except Exception as e:
        logging.error(f"Error getting active tasks count: {e}")
        return -1 # Return -1 to indicate an error


# >>>>>>>>>>>>>>>>>>>>>> <<<<<<<<<<<<<<<<<<<<<< 
# This section starts the discovery of the files by searching directories
# >>>>>>>>>>>>>>>>>>>>>> <<<<<<<<<<<<<<<<<<<<<<

@app.task(queue='Worker', name='locate_files')
def locate_files(arg):
    directories = ['/anime', '/tv', '/movies']
    extensions = ['.mp4', '.mkv', '.avi']

    print(f'Searching directories: {directories}')
    print(f'File extensions: {extensions}')

    for file_located in find_files(directories, extensions):
        logging.debug('File located, sending to ffprobe function')
        try:
            file_located_data = json.loads(file_located)
            logging.debug(json.dumps(file_located_data, indent=3, sort_keys=True))
            print(json.dumps(file_located_data, indent=3, sort_keys=True))
            # >>>>>>>>>>><<<<<<<<<<<<<<<<
            # >>>>>>>>>>><<<<<<<<<<<<<<<<
            requires_encoding.apply_async(kwargs={'file_located_data': file_located_data}, priority=2)
            # >>>>>>>>>>><<<<<<<<<<<<<<<<
            # >>>>>>>>>>><<<<<<<<<<<<<<<<
        except json.JSONDecodeError as e:
            logging.error(f'Failed to decode JSON: {e}')
            continue

def find_files(directories, extensions):
    for directory in directories:
        logging.info ('Scanning: ' + directory)
        for root, dirs, files in os.walk(directory):
            for file in files:
                for ext in extensions:
                    if file.lower().endswith(ext.lower()):
                        file_path = os.path.join(root, file)
                        result_dict = {
                            'directory': directory,
                            'root': root,
                            'file': file,
                            'file_path': file_path,
                            'extension': ext
                        }
                        yield json.dumps(result_dict)

# >>>>>>>>>>>>>>>>>>>>>> <<<<<<<<<<<<<<<<<<<<<< 
# This section starts the discovery of the file meta data, and determing what processing may need to occure
# >>>>>>>>>>>>>>>>>>>>>> <<<<<<<<<<<<<<<<<<<<<<

@app.task(queue='worker', name='requires_encoding')
def requires_encoding(file_located_data):
    stream_info = ffprobe_function(file_located_data['file_path'])
    encoding_decision = False
    
    encoding_decision, ffmepg_output_file_name = check_container_type(stream_info, encoding_decision, file_located_data['file'])
    encoding_decision, ffmpeg_command = check_codecs(stream_info, encoding_decision)
    if encoding_decision == True:
        print ('file needs encoding')
        ffmpeg_command = build_ffmpeg_command(file_located_data['file_path'], ffmpeg_command, ffmepg_output_file_name)
    else:
        print ('file does not need encoding')
    print (encoding_decision)
    print (ffmpeg_command)


def build_ffmpeg_command(file_path, ffmpeg_command, ffmepg_output_file_name):
    ffmpeg_settings = 'ffmpeg -hide_banner -loglevel 16 -stats -stats_period 10'
    ffmpeg_command = ffmpeg_settings + ' -i ' + file_path + ' ' + ffmpeg_command + ' ' + ffmepg_output_file_name
    return ffmpeg_command


def ffprobe_function(file_path):
    # Subprocess call to ffprobe to retrieve video info in JSON format
    ffprobe_command = f'ffprobe -loglevel quiet -show_entries format:stream=index,stream,codec_type,codec_name,channel_layout,format=nb_streams -of json "{file_path}"'
    result = subprocess.run(ffprobe_command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stream_info = json.loads(result.stdout)
    return stream_info


def check_container_type(stream_info, encoding_decision, file):
    # Desired container is MKV so we check for that, and pass True for all other container types
    format_name = stream_info['format'].get('format_name')
    print ('format is: ' + format_name)
    if format_name != 'matroska,webm':
        encoding_decision = True
    encoding_decision, ffmepg_output_file = check_container_extension(file, encoding_decision)
    print ('>>>check_container_type<<<  Container is: ' + format_name + ' so, encoding_decision is: ' + str(encoding_decision))
    return encoding_decision, ffmepg_output_file
    

def check_container_extension(file, encoding_decision):
    base, ext = os.path.splitext(file)
    if ext.lower() != '.mkv':
        # Change the extension to .mkv
        file = base + '.mkv'
        encoding_decision = True
    ffmepg_output_file = '/boil_hold/' + file
    return encoding_decision, ffmepg_output_file


def check_codecs(stream_info, encoding_decision):
    # Loops through the streams in stream_info from requires_encoding, then
    # calls functions to determine if the steam needs encoding based on stream type conditions 
    streams_count = stream_info['format']['nb_streams']
    ffmpeg_command = str()
    print ('There are : ' + str(streams_count) + ' streams')
    for i in range (0,streams_count):
        codec_type = stream_info['streams'][i]['codec_type'] 
        if codec_type == 'video':
            encoding_decision, ffmpeg_command = check_video_stream(encoding_decision, i, stream_info, ffmpeg_command)
        elif codec_type == 'audio':
            encoding_decision, ffmpeg_command = check_audio_stream(encoding_decision, i, stream_info, ffmpeg_command)
        elif codec_type == 'subtitle':
            encoding_decision, ffmpeg_command = check_subtitle_stream(encoding_decision, i, stream_info, ffmpeg_command)
        elif codec_type == 'attachment':
            encoding_decision, ffmpeg_command = check_attachmeent_stream(encoding_decision, i, stream_info, ffmpeg_command)        
    return encoding_decision, ffmpeg_command


def check_video_stream(encoding_decision, i, stream_info, ffmpeg_command):
    # Checks the video stream from check_codecs to determine if the stream needs encoding
    codec_name = stream_info['streams'][i]['codec_name'] 
    desired_video_codec = 'av1'
    print('Steam ' + str(i) + ' codec is: ' + codec_name)
    if codec_name == desired_video_codec:
        ffmpeg_command = ffmpeg_command + ' -map 0:' + str(i) + ' -c:v copy'
    elif codec_name == 'mjpeg':
        ffmpeg_command = ffmpeg_command + ' -map 0:' + str(i) + ' -c:v copy'
    elif codec_name != desired_video_codec: 
        encoding_decision = True
        svt_av1_string = "libsvtav1 -crf 25 -preset 4 -g 240 -pix_fmt yuv420p10le -svtav1-params filmgrain=20:film-grain-denoise=0:tune=0:enable-qm=1:qm-min=0:qm-max=15"
        ffmpeg_command = ffmpeg_command + ' -map 0:' + str(i) + ' -c:v ' + svt_av1_string
    else:
        print ('ignoring for now')
    return encoding_decision, ffmpeg_command


def check_audio_stream(encoding_decision, i, stream_info, ffmpeg_command):
    # Checks the audio stream from check_codecs to determine if the stream needs encoding
    codec_name = stream_info['streams'][i]['codec_name'] 
    # This will be populated at a later date
    #desired_audio_codec = 'aac'
    #if codec_name != desired_video_codec:
    #    encoding_decision = True
    print('Steam ' + str(i) + ' codec is: ' + codec_name)
    ffmpeg_command = ffmpeg_command + ' -map 0:' + str(i) + ' -c:a copy'
    return encoding_decision, ffmpeg_command
    

def check_subtitle_stream(encoding_decision, i, stream_info, ffmpeg_command):
    # Checks the subtitle stream from check_codecs to determine if the stream needs encoding
    codec_name = stream_info['streams'][i]['codec_name'] 
    # This will be populated at a later date
    #desired_subtitle_codec = 'srt'
    #if codec_name != desired_subtitle_codec:
    #    encoding_decision = True
    print('Steam ' + str(i) + ' codec is: ' + codec_name)
    ffmpeg_command = ffmpeg_command + ' -map 0:' + str(i) + ' -c:s copy'
    return encoding_decision, ffmpeg_command


def check_attachmeent_stream(encoding_decision, i, stream_info, ffmpeg_command):
    # Checks the attachment stream from check_codecs to determine if the stream needs encoding
    codec_name = stream_info['streams'][i]['codec_name'] 
    # This will be populated at a later date
    #desired_attachment_codec = '???'
    #if codec_name != desired_attachment_codec:
    #    encoding_decision = True
    print('Steam ' + str(i) + ' codec is: ' + codec_name)
    ffmpeg_command = ffmpeg_command + ' -map 0:' + str(i) + ' -c:t copy'
    return encoding_decision, ffmpeg_command


# >>>>>>>>>>>>>>>>>>>>>> <<<<<<<<<<<<<<<<<<<<<< 
# This section starts the actual processing of media fules
# >>>>>>>>>>>>>>>>>>>>>> <<<<<<<<<<<<<<<<<<<<<<
 