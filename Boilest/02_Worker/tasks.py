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

# Global variables to track processing state and store strings
process_file = False
original_string = str()
ffmpeg_command = str()

def check_media_file(file_path):
    global process_file, original_string, ffmpeg_string
    process_file = False  # Initialize the flag to False
    original_string = "original"  # Set initial value for original_string
    ffmpeg_command = "ffmpeg"  # Set initial value for ffmpeg_string

    # Initial ffmpeg check
    if initial_ffmpeg_check(file_path) == "Success":
        result = full_workflow(file_path)


def initial_ffmpeg_check(file_path):
    ffmpeg_command = f'ffmpeg -v error -i "{file_path}" -f null -'
    try:
        result = subprocess.run(ffmpeg_command, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        if result.stdout or result.stderr:
            print (file_path + " file is invalid")          
            return "Failure"
        else:
            print (file_path + " file is valid") 
            return "Success"
    except subprocess.CalledProcessError as e:
        print(result.stdout)
        return "Error"


def full_workflow(file_path):
    ffprobe_command = f'ffprobe -loglevel quiet -show_entries format:stream=index,stream,codec_type,codec_name,channel_layout,format=nb_streams -of json "{file_path}"'
    try:
        result = subprocess.run(ffprobe_command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stream_info = json.loads(result.stdout)
        streams_count = stream_info['format']['nb_streams']
        for i in range(streams_count):
            process_stream(stream_info['streams'][i], i)
        print ("original_string is: " + original_string)
        print ("ffmpeg_command is: " + ffmpeg_command)
        print ("process_file is:" + str(process_file))
    except subprocess.CalledProcessError as e:
        print(result.stdout)

def process_stream(stream, index):
    global original_string
    
    codec_type = stream.get('codec_type')
    print ("codec_type is: " + codec_type)
    codec_name = stream.get('codec_name')
    channel_layout = stream.get('channel_layout')

    original_string = original_string + " 0:" + str(index) + " " + codec_type + ":" + codec_name
    
    if codec_type == 'video':
        process_video_stream(codec_name, index)
    elif codec_type == 'audio':
        process_audio_stream(codec_name, channel_layout, index)
    elif codec_type == 'subtitle':
        process_subtitle_stream(codec_name, index)
    elif codec_type == 'attachment':
        process_attachment_stream(codec_name, index)
    else:
        print(f"Other stream type: codec_name={codec_name}, codec_type={codec_type}")

def process_video_stream(codec_name, index):
    global process_file, ffmpeg_command
    print ("codec_name is: " + codec_name)
    if codec_name == 'av1':
        #print(f"Video stream {index}: codec_name=av1")
        ffmpeg_command = ffmpeg_command + ' -map 0:' + str(index) + ' -c:v stuff'
        print (process_file)
        print (ffmpeg_command)
    else:
        #print(f"Video stream {index}: codec_name={codec_name}")
        ffmpeg_command = ffmpeg_command + ' -map 0:' + str(index) + ' -c:a copy'
        process_file = True
        print (process_file)
        print (ffmpeg_command)

def process_audio_stream(codec_name, channel_layout, index):
    global process_file, ffmpeg_command
    #print(f"Audio stream: codec_name={codec_name}, channel_layout={channel_layout}")
    ffmpeg_command = ffmpeg_command + ' -map 0:' + str(index) + ' -c:a copy'
    
def process_subtitle_stream(codec_name, index):
    global process_file, ffmpeg_command
    #print(f"Subtitle stream: codec_name={codec_name}")
    ffmpeg_command = ffmpeg_command + ' -map 0:' + str(index) + ' -c:s copy'

def process_attachment_stream(codec_name, index):
    global process_file, ffmpeg_command
    #print(f"Attachment stream: codec_name={codec_name}")
    ffmpeg_command = ffmpeg_command + ' -map 0:' + str(index) + ' -c:t copy'
