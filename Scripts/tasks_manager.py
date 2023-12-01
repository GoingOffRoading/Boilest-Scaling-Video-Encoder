from celery import Celery
from pathlib import Path
from datetime import datetime
import json, subprocess, os, shutil, sqlite3, requests, sys, pathlib
from task_shared_services import task_start_time, task_duration_time, check_queue, find_files, celery_url_path, check_queue, ffprober

backend_path = celery_url_path('rpc://') 
print (backend_path)
broker_path = celery_url_path('amqp://') 
print (broker_path)
app = Celery('tasks', backend = backend_path, broker = broker_path)

#app = Celery('tasks', backend = 'rpc://celery:celery@192.168.1.110:31672/celery', broker = 'amqp://celery:celery@192.168.1.110:31672/celery')

@app.on_after_configure.connect
# Celery's scheduler.  Kicks off ffconfigs every hour
# https://docs.celeryq.dev/en/stable/userguide/periodic-tasks.html#entries
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(3600.0, queue_workers_if_queue_empty.s('hit it'))

@app.task(queue='manager')
def queue_workers_if_queue_empty(arg):
    queue_depth = check_queue('worker')
    print ('Current Worker queue depth is: ' + str(queue_depth))
    if queue_depth == 0:
        print ('Starting Configurations Discovery')
        ffconfigs.delay(arg)
    elif queue_depth != 0:
        print (str(queue_depth) + ' tasks in queue')
    else:
        print ('Something went wrong checking the Worker Queue')

@app.task(queue='manager')
def ffconfigs(arg):
    function_start_time = task_start_time('ffconfigs')

    print (arg)

    directory = '/Boilest/Configurations' 
    extensions = '.json'

    for root, file, file_path in find_files(directory,extensions):
        print (file_path)
        f = open(file_path)
        json_configuration = json.load(f)
        if json_configuration["enabled"] == 'true':
            print (json.dumps(json_configuration, indent=3, sort_keys=True))
            del json_configuration['enabled']            
            print ('sending ' + json_configuration["config_name"] + ' to ffinder')
            ffinder.delay(json_configuration)
        elif json_configuration["enabled"] == 'false':
            print ('Not condsidering ' + json_configuration["config_name"] + ' at this time') 
        else:
            print ('Did not find Configurations')

    task_duration_time('ffconfigs',function_start_time)

@app.task(queue='manager')
def ffinder(json_configuration):
    # The purpose of this function of to search a directory for files, filter for specific formats, and send those filtered results to the next function
    function_start_time = task_start_time('ffinder')

    # For fun/diagnostics
    print (json.dumps(json_configuration, indent=3, sort_keys=True))

    # Get the folder to scan
    directory = (json_configuration['watch_folder'])
    if json_configuration["ffmpeg_codec_type"] == 'container':
        extensions = [".mp4", ".mkv", ".avi"]
        extensions.remove(json_configuration['format_extension'])
    else:
        extensions = json_configuration["ffmpeg_codec_type"]

    print ('Will now search the directory ' + directory + ' and provide the relevant config flags:')
    
    for root, file, file_path in find_files(json_configuration["watch_folder"], extensions):
        json_configuration.update({'root':root,'file':file,'file_path':file_path})
        if json_configuration["ffmpeg_codec_type"] == 'container':
            ffprober_container.delay(json_configuration)
        else:
            ffprober_video_stream.delay(json_configuration)

@app.task(queue='manager')
def ffprober_container(json_configuration):
    output_filename = os.path.splitext(json_configuration["file"])[0] + json_configuration["format_extension"]
    json_configuration.update({'output_filename':output_filename})

@app.task(queue='manager')
def ffprober_video_stream(json_configuration):

    output_filename = json_configuration["file_path"]
    ffmpeg_command = str()
    encode_decision = 'no'
    original_string = str()
    
    print ('json_configuration["ffprobe_string"] is: ' + json_configuration["ffprobe_string"])
    print ('json_configuration["file_path"] is: ' + json_configuration["file_path"])

    ffprobe_results = ffprober(json_configuration["ffprobe_string"],json_configuration["file_path"]) 
        
    # Stream Loop: We need to loop through each of the streams, and make decisions based on the codec in the stream
    streams_count = ffprobe_results['format']['nb_streams']
    print ('there are ' + str(streams_count) + ' streams:')
    for i in range (0,streams_count):
        if ffprobe_results['streams'][i]['codec_type'] == json_configuration["ffmpeg_codec_type"]:
            codec_name = ffprobe_results['streams'][i]['codec_name'] 
            ffmpeg_command = ffmpeg_command + '{' + str(i) + d['streams'][i]['codec_type'] + '=' + codec_name + '}'
            if codec_name == (json_configuration["ffmpeg_codec_name"]):
                ffmpeg_command = ffmpeg_command + ' -map 0:' + str(i) + ' -c:v copy'
                # No need to change encode_decision as the video codec is in the desired format
                print ('Stream ' + str(i) + ' is already ' + codec_name + ', copying stream')
            elif codec_name == 'mjpeg':
                print ('Garbage mjpeg stream, ignoring')    
                # No use for this for now
            elif codec_name != (json_configuration["ffmpeg_codec_name"]):
                encode_decision = 'yes'
                ffmpeg_command = ffmpeg_command + ' -map 0:' + str(i) + ' ' + (json_configuration["ffmpeg_string"])
                print ('Stream ' + str(i) + ' is ' + codec_name + ', encoding stream')
                # encode_decision = yes as the video codec is not in the desired format
            else:
                print ('Something is broken with stream ' + str(i))
                # Catch all error state
        
        else:
            ffmpeg_command = ffmpeg_command + ' -map 0:' + str(i) + ' -c copy'   
       
    print ('ffmpeg_command is: ' + ffmpeg_command)
    print ('encode_decision is: ' + encode_decision)
    print ('original_string is: ' + original_string)
       
    # Part 2 determines if the string is needed
    if encode_decision == 'no': 
        print (file_name + ' does not need encoding')
    else:
        print (file_name + ' needs encoding')
        json_configuration.update({'ffmpeg_command':ffmpeg_command, 'output_filename':output_filename, 'original_string':original_string})
        print(json.dumps(fprober_json, indent=3, sort_keys=True))
        #fencoder.delay(fprober_json)
    
    task_duration_time('fprober',function_start_time)


