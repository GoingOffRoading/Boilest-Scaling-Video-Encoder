from celery import Celery
from pathlib import Path
from datetime import datetime
import json, subprocess, os, shutil, sqlite3, requests, sys, pathlib
from task_shared_services import task_start_time, task_duration_time, check_queue, find_files, celery_url_path

#backend_path = celery_url_path('rpc://') 
#print (backend_path)
#broker_path = celery_url_path('amqp://') 
#print (broker_path)
#app = Celery('tasks', backend = backend_path, broker = broker_path)

app = Celery('tasks', backend = 'rpc://celery:celery@192.168.1.110:31672/celery', broker = 'amqp://celery:celery@192.168.1.110:31672/celery')

@app.on_after_configure.connect
# Celery's scheduler.  Kicks off ffconfigs every hour
# https://docs.celeryq.dev/en/stable/userguide/periodic-tasks.html#entries
def setup_periodic_tasks(sender, **kwargs):
    # Calls ffconfigs('hello') every 10 seconds.
    sender.add_periodic_task(3600.0, ffconfigs.s('hit it'))

@app.task(queue='manager')
# Scan for condigurations, and post the to the next step
# Kicked off by the scheduler above, but started manually with start.py in /scripts
def ffconfigs(arg):
    function_start_time = task_start_time('ffconfigs')

    queue_depth = check_queue('worker')
    # Searching for configurations
    if queue_depth == 0:
        print ('No tasks in sque, starting search for configs')
        directory = '/Boilest/Configurations' 
        extensions = '.json'
        for i in find_files(directory,extensions):
            print (i)
            f = open(i)
            json_configuration = json.load(f)
            if json_configuration["enabled"] == 'true':
                print (json.dumps(json_configuration, indent=3, sort_keys=True))
                print ('sending ' + json_configuration["config_name"] + ' to ffinder')
                ffinder.delay(json_configuration)
            elif json_configuration["enabled"] == 'false':
                print ('Not condsidering ' + json_configuration["config_name"] + ' at this time') 
            else:
                print ('Did not find Configurations')
    elif queue_depth != 0:
        print ('Tasks in queue: ' + str(queue_depth) + ', not starting config scan')
    else:
        print ('Tasks in queue returned with an error')

    task_duration_time('ffconfigs',function_start_time)

@app.task(queue='manager')
def ffinder(json_configuration):
    # The purpose of this function of to search a directory for files, filter for specific formats, and send those filtered results to the next function
    function_start_time = task_start_time('ffinder')

    # For fun/diagnostics
    print (json.dumps(json_configuration, indent=3, sort_keys=True))

    # Get the folder to scan
    directory = (json_configuration['watch_folder'])
    extensions = '.mp4, .mkv, .avi'

    print ('Will now search the directory ' + directory + ' and provide the relevant config flags:')

    for i in find_files(directory,extensions):
        print (i)
        ffinder_json = {'file_path':i}
        ffinder_json.update(json_configuration)      
        print(json.dumps(ffinder_json, indent=3, sort_keys=True))
        fprober.delay(ffinder_json)

    task_duration_time('ffinder',function_start_time)



@app.task(queue='manager')
def fprober(ffinder_json):
    # This function is kicked off from the individual file results from the ffinder function, and then do three functions:
    # 1) For each file, run ffprobe to get details on the file
    # 2) Loop through those the ffprobe results to determine if any changes need to be made to the video container or it's video, audio, or subtitle streams 
    # 3) Determine if the file needs to be encoded, and if yes, pass the changes to the fencoder function

    function_start_time = task_start_time('fprober')

    # Using subprocess to call FFprobe, get JSON back on the video's container, and streams, then display the outputs  
    file_full_path = (ffinder_json["file_path"])
    cmnd = [f'ffprobe', '-loglevel', 'quiet', '-show_entries', 'format:stream=index,stream,codec_type,codec_name,channel_layout', '-of', 'json', file_full_path]
    print ("ffprobe's command on " + file_full_path + ":")
    print (cmnd)
    p = subprocess.run(cmnd, capture_output=True).stdout
    d = json.loads(p)
    print ("ffprobe's results on " + file_name + ":")
    print(json.dumps(d, indent=3, sort_keys=True))
     
    # Now that we have FFProbe's output, we want to evaluate the container, video stream, audio stream, and subtitle formats
    # If those values don't match the input templte, then we flip encode_decision to yes, and transmit the results to fencoder

    # Setting starter variables.  These are revisited throughout the loop.
    encode_string = str()
    encode_decision = 'no'
    original_string = str()
    
    # Determine if the container needs to be changed
    original_container = (d['format']['format_name'])
    print ('Original Video container is: ' + original_container)

    # herheherhehrhre
    if original_container != 'matroska,webm' or pathlib.Path(ffinder_json["file_name"]).suffix != '.mkv':
        file_path = root, extension = os.path.splitext(ffinder_json["file_path"])
        file_name = Path(file_name).stem 
        ffmpeg_output_file = file_name + '.mkv'
        encode_decision = 'yes'
        print ('Container is not MKV, converting container')
    else:
        ffmpeg_output_file = file_name
        print (file_name + ' is already .mkv, no need to change container')
    
    # Stream Loop: We need to loop through each of the streams, and make decisions based on the codec in the stream
    streams_count = d['format']['nb_streams']
    print ('there are ' + str(streams_count) + ' streams:')
    for i in range (0,streams_count):
        if d['streams'][i]['codec_type'] == 'video':
            codec_name = d['streams'][i]['codec_name'] 
            original_string = original_string + '{' + str(i) + d['streams'][i]['codec_type'] + '=' + codec_name + '}'
            if codec_name == (ffinder_json["ffmpeg_video_codec"]):
                encode_string = encode_string + ' -map 0:' + str(i) + ' -c:v copy'
                # No need to change encode_decision as the video codec is in the desired format
                print ('Stream ' + str(i) + ' is already ' + codec_name + ', copying stream')
            elif codec_name == 'mjpeg':
                print ('Garbage mjpeg stream, ignoring')    
                # No use for this for now
            elif codec_name != (ffinder_json["ffmpeg_video_codec"]):
                encode_decision = 'yes'
                encode_string = encode_string + ' -map 0:' + str(i) + ' ' + (ffinder_json["ffmpeg_video_string"])
                print ('Stream ' + str(i) + ' is ' + codec_name + ', encoding stream')
                # encode_decision = yes as the video codec is not in the desired format
            else:
                print ('Something is broken with stream ' + str(i))
                # Catch all error state
        elif d['streams'][i]['codec_type'] == 'audio':
            codec_name = d['streams'][i]['codec_name'] 
            original_string = original_string + '{' + str(i) + d['streams'][i]['codec_type'] + '=' + codec_name + '}'
            if codec_name == (ffinder_json["ffmpeg_audio_codec"]):
                encode_string = encode_string + ' -map 0:' + str(i) + ' -c:a copy'
                print ('Stream ' + str(i) + ' is already ' + codec_name + ': nothing to encode')
                # No need to change encode_decision as the audio codec is in the desired format
            elif codec_name != 'opus' and d['streams'][i]['channel_layout'] == '5.1(side)':
                encode_string = encode_string + ' -map 0:' + str(i) + ' -acodec libopus -af aformat=channel_layouts="7.1|5.1|stereo"'
                encode_decision = 'yes'
                print ('Stream ' + str(i) + ' is ' + codec_name + ' and, using ' + d['streams'][i]['channel_layout'] +', filtering, then encoding stream')
                # encode_decision = yes as the audio codec is not in the desired format... libopus has problems with 5.1(side) channel layout in ffmpeg so we catch it here.  Unclear if we can combine this step with the next one
            elif codec_name != (ffinder_json["ffmpeg_audio_codec"]):
                #encode_string = encode_string + ' -map 0:' + str(i) + ' -acodec libopus' 
                encode_string = encode_string + ' -map 0:' + str(i) + ' ' + (ffinder_json["ffmpeg_audio_string"])
                encode_decision = 'yes'
                print ('Stream ' + str(i) + ' is ' + codec_name + ', encoding stream')
                # encode_decision = yes as the audio codec is not in the desired format
            else:
                print ('Something is broken with stream ' + str(i))
                # Catch all error state
        elif d['streams'][i]['codec_type'] == 'subtitle':
            codec_name = d['streams'][i]['codec_name'] 
            original_string = original_string + '{' + str(i) + d['streams'][i]['codec_type'] + '=' + codec_name + '}'
            if codec_name == (ffinder_json["ffmpeg_subtitle_format"]):
                encode_string = encode_string + ' -map 0:' + str(i) + ' -c:s copy'
                # No need to change encode_decision as the subtitles are in the desired format
                print ('Stream ' + str(i) + ' is already ' + codec_name + ': nothing to encode')
            elif d['streams'][i]['codec_name'] == 'hdmv_pgs_subtitle':
                # These are image based subtitles, and can't be converted to text type
                encode_string = encode_string + ' -map 0:' + str(i) + ' -c:s copy' 
                # No need to change encode_decision as we can't change picture subtitles into text subtitles
                print ('Stream ' + str(i) + ' is ' + codec_name + ': a pain in the dick, and nothing we can do but copy the stream')
            elif codec_name != (ffinder_json["ffmpeg_subtitle_format"]):
                #encode_string = encode_string + ' -map 0:' + str(i) + ' -scodec subrip' 
                encode_string = encode_string + ' -map 0:' + str(i) + ' ' + (ffinder_json["ffmpeg_subtitle_string"]) 
                encode_decision = 'yes'
                print ('Stream ' + str(i) + ' is ' + codec_name + ', encoding stream')
            else:
                print ('Something is broken with stream ' + str(i))

        # No idea if attachments provide any value.  Sr far: no
        elif d['streams'][i]['codec_type'] == 'attachment':
            original_string = original_string + '{' + str(i) + d['streams'][i]['codec_type']
            print ('Stream is attachment, ignore')
            # Progably not a great idea to ditch these, but whatever.  So far in discovery, the attachments have been font files.         
        else:
            print ('fuck')
            
    print ('encode_string is: ' + encode_string)
    print ('encode_decision is: ' + encode_decision)
    print ('original_string is: ' + original_string)
       
    # Part 2 determines if the string is needed
    if encode_decision == 'no': 
        print (file_name + ' does not need encoding')
    else:
        print (file_name + ' needs encoding')
        fprober_json = {'ffmpeg_encoding_string':encode_string, 'ffmpeg_output_file':ffmpeg_output_file, 'original_string':original_string}
        fprober_json.update(ffinder_json) 

        print(json.dumps(fprober_json, indent=3, sort_keys=True))
        fencoder.delay(fprober_json)
    
    task_duration_time('fprober',function_start_time)


