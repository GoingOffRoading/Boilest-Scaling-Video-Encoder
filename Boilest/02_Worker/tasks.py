from celery import Celery
import json, os, logging, subprocess
import celeryconfig
from shared_services import celery_url_path


app = Celery('tasks', backend = celery_url_path('rpc://'), broker = celery_url_path('amqp://') )
app.config_from_object(celeryconfig)


@app.task(queue='worker')
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
            ffprober.delay(file_located_data)  # Uncomment this line to send the task to ffprober
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

@app.task(queue='worker')
def ffprober(file_located_data):

    encode_string = str()
    encode_decision = 'no'
    original_string = str()







    def processfile(*args, **kwargs):
        if encode_decision == 'yes':
            fencoder.apply_async(kwargs={'ffmpeg_inputs': ffmpeg_inputs}, priority=5)
        else:
            print('No need to encode')


def encode_decision():










def ffprober_function(file_path):
    try:
             = "ffprobe -loglevel quiet -show_entries format:stream=index,stream,codec_type,codec_name,channel_layout -of json"
        file_path = file_path["file_path"]
        full_command = f'{ffprobe_string} "{file_path}"'
        result = subprocess.run(full_command, capture_output=True, text=True, shell=True, check=True)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        return {"error": f"Error running ffprobe: {e}"}


def validate_video(file_path):
    try:
        command = 'ffmpeg -v error -i "' + file_path + '" -f null -'
        logging.debug (command)
        # Run the shell command and capture both stdout and stderr
        result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # Check if there is any output (stdout or stderr)
        if result.stdout or result.stderr:
            return "Failure"
        else:
            return "Success"
    except Exception as e:
        return f"Error: {e}"




























@app.task
import subprocess
import json

def check_media_file(file_path):
    # Initial ffmpeg check
    if initial_ffmpeg_check(file_path) == "Failure":
        return "Failure"
    
    # Proceed with full workflow if initial check passes
    return full_workflow(file_path)

def initial_ffmpeg_check(file_path):
    ffmpeg_command = f'ffmpeg -v error -i "{file_path}" -f null -'
    try:
        result = subprocess.run(ffmpeg_command, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        if result.stdout or result.stderr:
            return "Failure1"
    except subprocess.CalledProcessError as e:
        return f"Error: Invalid media file. Details: {e.stderr.decode()}"
    return "Success"

def full_workflow(file_path):
    ffprobe_command = f'ffprobe -loglevel quiet -show_entries format:stream=index,stream,codec_type,codec_name,channel_layout -of json "{file_path}"'
    try:
        result = subprocess.run(ffprobe_command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.stdout or result.stderr:
            stream_info = json.loads(result.stdout)
            return stream_info
    except subprocess.CalledProcessError as e:
        return f"Error: Unable to run ffprobe. Details: {e.stderr.decode()}"

    # Process the stream information
    if 'streams' in stream_info:
        for stream in stream_info['streams']:
            process_stream(stream)

    return "Success2"

def process_stream(stream):
    codec_type = stream.get('codec_type')
    codec_name = stream.get('codec_name')
    channel_layout = stream.get('channel_layout')

    if codec_type == 'video':
        process_video_stream(codec_name)
    elif codec_type == 'audio':
        process_audio_stream(codec_name, channel_layout)
    elif codec_type == 'subtitle':
        process_subtitle_stream(codec_name)
    elif codec_type == 'attachment':
        process_subtitle_stream(codec_name)
    else:
        print(f"Other stream type: codec_name={codec_name}, codec_type={codec_type}")

def process_video_stream(codec_name):
    if codec_name == 'h264':
        print("Video stream: codec_name=h264")
    else:
        print(f"Video stream: codec_name={codec_name}")

def process_audio_stream(codec_name, channel_layout):
    if codec_name == 'aac':
        print(f"Audio stream: codec_name=aac, channel_layout={channel_layout}")
    else:
        print(f"Audio stream: codec_name={codec_name}, channel_layout={channel_layout}")

def process_subtitle_stream(codec_name):
    if codec_name == 'mov_text':
        print("Subtitle stream: codec_name=mov_text")
    else:
        print(f"Subtitle stream: codec_name={codec_name}")

def process_attachment_stream(codec_name):
    if codec_name == 'tff':
        print("Subtitle stream: codec_name=mov_text")
    else:
        print(f"Subtitle stream: codec_name={codec_name}")
