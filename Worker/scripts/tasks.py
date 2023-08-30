from celery import Celery
import os
from subprocess import call
import subprocess as sp
import shlex
import json


app = Celery('tasks', backend = 'rpc://test:test@192.168.1.110:31672/celery', broker = 'amqp://test:test@192.168.1.110:31672/celery')

@app.task

# The firt task searches the directory looking for files
def fffinder(DIRECTORY):
    print('Going to start scanning ' + DIRECTORY)
    # traverse whole directory
    for root, dirs, files in os.walk(DIRECTORY):
        # select file name
        for file in files:
            # check the extension of files
            if file.endswith('.mkv') or file.endswith('.mp4'):
                # print whole path of files
                print(os.path.join(root, file))
                FILEPATH = os.path.join(root, file)
                ffprober.delay(FILEPATH)


def ffprober(FILEPATH):
    # Execute ffprobe and get the codec of the first FILEPATH, audio, and subtitle stream
   
    container = sp.run(shlex.split(f'ffprobe -v quiet -show_entries format=format_name -of default=noprint_wrappers=1:nokey=1 {FILEPATH}'), capture_output=True).stdout.decode('utf8').strip()       
    vcodec = sp.run(shlex.split(f'ffprobe -v error -select_streams v:0 -show_entries stream=codec_name -of default=noprint_wrappers=1:nokey=1 {FILEPATH}'), capture_output=True).stdout.decode('utf8').strip()
    acodec = sp.run(shlex.split(f'ffprobe -v error -select_streams a:0 -show_entries stream=codec_name -of default=noprint_wrappers=1:nokey=1 {FILEPATH}'), capture_output=True).stdout.decode('utf8').strip()
    scodec = sp.run(shlex.split(f'ffprobe -v error -select_streams s:0 -show_entries stream=codec_name -of default=noprint_wrappers=1:nokey=1 {FILEPATH}'), capture_output=True).stdout.decode('utf8').strip()

    # Same as above, but outputs a larger object as json
    # I abandoned this approach as it was too dificult to loop through the JSON to find the first stream of each codec type (vido, audio, subtitle)
    # This would be ideal, as it reduces the file calls from three to one, so lets call this a someday task
    #data = sp.run(shlex.split(f'ffprobe -loglevel error -show_streams -of json {FILEPATH}'), capture_output=True).stdout
    # Convert data from JSON string to dictionary
    #d = json.loads(data)
    # Uncoment these for diagnostics
    # Get codecs
    #FILEPATH_codec = ({d["streams"][0]["codec_name"]})
    #audio_codec = ({d["streams"][1]["codec_name"]})
    #subtitle_format = ({d["streams"][2]["codec_name"]})

    # Now lets determine how the file needs to be processed by ffmpeg
    encode = str()
    if vcodec != 'av1':
        print (FILEPATH + ' is using ' + vcodec + ', not AV1')
        encode = encode + '-c:v libsvtav1 -crf 20 -preset 4 -g 240 -pix_fmt yuv420p10le'
    if acodec != 'opus':
        print (FILEPATH + ' is using ' + acodec + ', not OPUS')
        encode = encode + '-c:a libopus'
    if scodec != 'subrip':
        print (FILEPATH + ' is using ' + scodec + ', not SRT')
        encode = encode + '-c:s srt'
    # Now lets determine if we should pass a FILEPATH file to the next step, and what that step will cover
    if container == 'matroska,webm' and vcodec == 'av1' and acodec == 'opus' and scodec == 'subrip': 
        print (FILEPATH + ' is using all of the correct containers and codecs')
    else:
        job = {'file':FILEPATH, 'encode_string':encode}
        jobjson = json.dumps(job)
        print(jobjson)
        

def ffencode(FILEPATH, ENCODESTRING):
    ffencoder(FILEPATH, ENCODESTRING)

def ffstatrecorde(FILEPATH, FILENAME, STARTSZIE, ENDSIZE, VMAF):
    ffstatrecorder(FILEPATH, FILENAME, STARTSZIE, ENDSIZE, VMAF)

def ffchain(DIRECTORY):
    # fetch_page -> parse_page -> store_page
    chain = fffind(DIRECTORY) | ffprobe(FILEPATH) 
    chain()

