from celery import Celery
import os
import subprocess
import shlex
import json
import time
from pathlib import Path

app = Celery('tasks', backend = 'rpc://test:test@192.168.1.110:31672/celery', broker = 'amqp://test:test@192.168.1.110:31672/celery')

@app.task
json_file = f'C:\\Users\\Chase\\media\\Newfolder\\AV1.json'
mygenerator = finder(json_file) 
for finder_data in mygenerator:
    print(finder_data)
        

@app.task
def ffprober(FILEPATH):
    filename = 'C:\\Users\\Chase\\media\\Newfolder\\boil_watch\\test.mkv'
    probe_file(filename)

    # Now lets determine how the file needs to be processed by ffmpeg
    encode = str()
    if vcodec != 'av1':
        print (FILEPATH + ' is using ' + vcodec + ', not AV1')
        encode = encode + ' -c:v libsvtav1 -crf 20 -preset 4 -g 240 -pix_fmt yuv420p10le'
    if acodec != 'opus':
        print (FILEPATH + ' is using ' + acodec + ', not OPUS')
        encode = encode + ' -c:a libopus'
    if scodec != 'subrip':
        print (FILEPATH + ' is using ' + scodec + ', not SRT')
        encode = encode + ' -c:s srt'
    
    # Now lets determine if we should pass a FILEPATH file to the next step, and what that step will cover
    if container == 'matroska,webm' and vcodec == 'av1' and acodec == 'opus' and scodec == 'subrip': 
        print (FILEPATH + ' is using all of the correct containers and codecs')
    else:
        job = {'file':FILEPATH, 'encode_string':encode}
        JOBJSON = json.dumps(job)
        print('JSON is as follows: '+ JOBJSON)
        ffencode.delay(JOBJSON)

@app.task
def ffencode(JOBJSON):
    d = json.loads(JOBJSON)

    input_file = (d["file"]) 
    #newinput_file = '"' + input_file + '"'
    print ('input file is: ' + input_file)

    ffmpeg_string = (d["encode_string"])
    ffmpeg_string = ffmpeg_string + ' '
    print ('ffmpeg string is: ' + ffmpeg_string)

    file_name = Path(input_file).stem
    print ('filename is currently: ' + file_name)
    file_name = '/boil_hold/' + file_name + '.mkv'
    #newfile_name = '"' + file_name + '"'
    print ('file name with path is:' + file_name)

    ffmpeg_string = 'ffmpeg -hide_banner -loglevel 8 -stats -i "' + input_file + '"' + ffmpeg_string + '"' + file_name + '"'
    print (ffmpeg_string)
    os.system(ffmpeg_string)

    # I think I would like to do this as a subprocess instead of an OS call, but ran into too many issues having to split the string
    # Specifically, ffmpeg_string... Splitting it created 'SyntaxError: invalid syntax'
    # Given that it's going to take an investment of time to figure that out, and there's no advantage to the subprocess call of ffmpeg, I am going to leave it as an OS call above
    #ffmpeg_string = ffmpeg_string.split()
    #ffmpeg_string = 'ffmpeg, -hide_banner, -loglevel, 16, -stats, -i, ' + input_file + ', ', ffmpeg_string, ', /boil_hold/' + file_name + '.mkv'
    # Inserting a list into a string
    # https://stackoverflow.com/questions/56313176/how-to-fix-typeerror-can-only-concatenate-str-not-list-to-str
    #print (ffmpeg_string)
    # Current issues with the subprocess.popen is this error "TypeError: expected str, bytes or os.PathLike object, not list"
    #process = subprocess.Popen(
    #    ffmpeg_string,
    #    stderr=subprocess.PIPE,
    #    text=True,
    #    bufsize=0)
    #print(process.stderr.read())

    # Going to redo this later
    # Need to add data validations
    # When we get to validations, we need to explore StatReport: https://gitlab.com/AOMediaCodec/SVT-AV1/-/blob/master/Docs/Parameters.md

    #    >>>>>>>>>>>>>>>>>>>> HERE <<<<<<<<<<<<<<<<<<<<<<<<<
    # Try this: https://stackoverflow.com/questions/3751900/create-file-path-from-variables

    file_name = '"' + file_name + '"'
    input_file = '"' + input_file + '"'

    print ('now going to check on the existance of ' + file_name + ' and ' + input_file)

    if os.path.exists(file_name):
        print (file_name + ' exists')
    else:
        print (file_name + ' does not exist')   
    if os.path.exists(input_file):
        print (input_file + ' exists')
    else:
        print (input_file + ' does not exist')

    if os.path.exists(file_name and input_file):
        print('Original and Encoded Files Exists')
        time.sleep(1)
        file_stats = os.stat(input_file)
        print(f'Original file Size in MegaBytes is {file_stats.st_size / (1024 * 1024)}') 
        file_stats2 = os.stat(file_name)
        print(f'Encoded file Size in MegaBytes is {file_stats2.st_size / (1024 * 1024)}') 
        print('Removing the original file from ' + input_file)
        os.remove(input_file) 
        time.sleep(1)
        print('Moving the encoded file')
        os.rename(file_name, input_file)
        print ('Done')    
    else:
         print("Something Broke")





















@app.task
def ffstatrecorde(FILEPATH, FILENAME, STARTSZIE, ENDSIZE, VMAF):
    ffstatrecorder(FILEPATH, FILENAME, STARTSZIE, ENDSIZE, VMAF)

@app.task
def ffchain(DIRECTORY):
    # fetch_page -> parse_page -> store_page
    chain = fffind(DIRECTORY) | ffprobe(FILEPATH) 
    chain()

