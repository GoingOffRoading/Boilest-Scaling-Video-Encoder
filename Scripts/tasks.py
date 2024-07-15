from celery import Celery
import json, os, logging, subprocess, requests
import celeryconfig


# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>  
# >>>>>>>>>>>>>>> Celery Configurations >>>>>>>>>>>>>>>
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>  


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

app = Celery('worker', backend = celery_url_path('rpc://'), broker = celery_url_path('amqp://') )
app.config_from_object(celeryconfig)

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# >>>>>>>>>>>>>>> Check queue depth >>>>>>>>>>>>>>>
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

@app.task
def queue_workers_if_queue_empty(arg):
    try:
        queue_depth = check_queue('Worker')        
        print(f'Current Worker queue depth is: {queue_depth}')
        print(f'Current Worker queue depth is: {queue_depth}')        
        if queue_depth == 0:
            print('Starting locate_files')
            # >>>>>>>>>>><<<<<<<<<<<<<<<<
            # >>>>>>>>>>><<<<<<<<<<<<<<<<
            locate_files.apply_async(kwargs={'arg': arg}, priority=2)
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

@app.task
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
            requires_encoding.apply_async(kwargs={'file_located_data': file_located_data}, priority=3)
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

@app.task
def requires_encoding(file_located_data):
    stream_info = ffprobe_function(file_located_data['file_path'])
    encoding_decision = False
    
    encoding_decision, ffmepg_output_file_name = check_container_type(stream_info, encoding_decision, file_located_data['file'])
    encoding_decision, ffmpeg_command = check_codecs(stream_info, encoding_decision)
    if encoding_decision == True:
        print ('file needs encoding')
        file_located_data['ffmpeg_command'] = ffmpeg_command
        file_located_data['ffmepg_output_file_name'] = ffmepg_output_file_name
        file_located_data['file_hash'] = file_size_kb(file_located_data['file_path'])
        print(json.dumps(file_located_data, indent=4))
        process_ffmpeg.apply_async(kwargs={'file_located_data': file_located_data}, priority=6)
    else:
        print ('file does not need encoding')
    print (encoding_decision)
    print (ffmpeg_command)


def file_size_kb(file_path):
    # Returns the file size of the file_path on disk
    if os.path.isfile(file_path):
        file_size_bytes = os.path.getsize(file_path)
        file_size_kb = file_size_bytes / 1024
        return round(file_size_kb)
    else:
        return 0.0


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
 

@app.task()
def process_ffmpeg(file_located_data):
    if delete_old_move_new(file_located_data) == True:
        print ('stuff')

def delete_old_move_new(file_located_data):
    if ffmpeg_postlaunch_checks(file_located_data) == True:
        moving_files = move_processed_file(file_located_data)
        if moving_files == True:
            print ('all done!')
            return True
        else:
            print ('delete_old_move_new failed')
            return False

def ffmpeg_postlaunch_checks(file_located_data):
    if encode_video(file_located_data) and file_exists(file_located_data['ffmepg_output_file_name']) and check_encode_output_size(file_located_data['ffmepg_output_file_name']) and validate_video(file_located_data['ffmepg_output_file_name']):
        print ('ffmpeg_postlaunch_checks succeeded')
        return True
    else:
        print ('ffmpeg_postlaunch_checks failed')
        return False


def encode_video(file_located_data):
    if ffmpeg_prelaunch_checks(file_located_data) == True:
        ffmpeg_command = build_ffmpeg_command(file_located_data['file_path'], file_located_data['ffmpeg_command'], file_located_data['ffmepg_output_file_name'])
        file_processed = run_ffmpeg(ffmpeg_command)
        return file_processed
    else:
        print('File failed to meet conditions, will not process')


def ffmpeg_prelaunch_checks(file_located_data):
    if file_exists(file_located_data['file_path']) and check_file_hash(file_located_data):
        print('file passed ffmpeg_prelaunch_checks')
        return True
    else:
        print('file failed ffmpeg_prelaunch_checks')
        return False


def file_exists(file_path):
    file_existance = os.path.isfile(file_path)
    # Returns true if the file that is about to be touched is in the expected location
    print (file_path + ' : ' + str(file_existance))
    return file_existance


def check_file_hash(file_located_data):
    original_file_hash = file_located_data['file_hash'] 
    print('original_file_hash: ' + str(original_file_hash))
    current_file_hash = file_size_kb(file_located_data['file_path'])
    print('current_file_hash: ' + str(current_file_hash))

    if original_file_hash == current_file_hash:
        print('Hashes match')
        return True
    else:
        print('Hashes do not match')
        return False


def check_encode_output_size(file_path):
    # Returns the file size of the file_path on disk
    if get_file_size_kb(file_path) > 0.0:
        return True
    else:
        return False
    

def get_file_size_kb(file_path):
    file_size_bytes = os.path.getsize(file_path)
    file_size_kb = round(file_size_bytes / 1024)
    return file_size_kb


def validate_video(file_path):
    # This function determines if a video is valid, or if the video contains errors
    # Returns:
    #       Failure if the shell command returns anything; i.e. one of the streams is bad
    #       Success if the shell command doesn't return anything; i.e. the streams are good
    #       Error if the shell command fails; this shouldn't happen
    try:
        command = 'ffmpeg -v error -i "' + file_path + '" -f null -'
        result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.stdout or result.stderr:
            print ('File failed validation')
            return False
        else:
            print ('File passed validation')
            return True
    except Exception as e:
        return f"Error: {e}"
    
def run_ffmpeg(ffmpeg_command):
    print ('running ffmpeg now')
    try:
        process = subprocess.Popen(ffmpeg_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,universal_newlines=True)
        for line in process.stdout:
            print(line)
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False  # Return a non-zero exit code to indicate an error
    
def move_processed_file (file_located_data):
    # Delete the original file, replace it with the processed file
    file_path = file_located_data['file_path']
    ffmepg_output_file_name = file_located_data['ffmepg_output_file_name']
    new_file_destination = os.path.join(os.path.dirname(file_path), os.path.basename(ffmepg_output_file_name))
    print('new_file_destination: ' + str(new_file_destination))
    try:
        print('removing: ' + str(file_path))
        os.remove(file_path)
        print('moving: ' + str(ffmepg_output_file_name) + ' to: ' + str(new_file_destination))
        shutil.move(ffmepg_output_file_name, new_file_destination) 
        return True
    except Exception as e:
        print(f"An error occurred: {e}")
        return False

def build_ffmpeg_command(file_path, ffmpeg_command, ffmepg_output_file_name):
    ffmpeg_settings = 'ffmpeg -hide_banner -loglevel 16 -stats -stats_period 10'
    ffmpeg_command = ffmpeg_settings + ' -y -i "' + file_path + '" ' + ffmpeg_command + ' "' + ffmepg_output_file_name + '"'
    print ('ffmpeg_command is: ' + ffmpeg_command)
    return ffmpeg_command