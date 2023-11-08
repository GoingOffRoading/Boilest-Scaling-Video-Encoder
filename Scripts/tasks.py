from celery import Celery
from pathlib import Path
from datetime import datetime
import json, subprocess, os, shutil, sqlite3, requests, sys, pathlib

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
    ffconfig_start_time = datetime.now()
    print ('>>>>>>>>>>>>>>>> ffconfigs with the arg: ' + arg + ' starting at ' + str(ffconfig_start_time) + '<<<<<<<<<<<<<<<<<<<')

    # First, we need to check the queue depth.  We don't want to add to queue, or add duplicate tasks, if there are already tasks in the queue 
    worker_queue = json.loads((requests.get('http://192.168.1.110:32311/api/queues/celery/worker', auth=('celery', 'celery'))).text)
    worker_queue_messages_unacknowledged = (worker_queue["messages_unacknowledged"])
    manager_queue = json.loads((requests.get('http://192.168.1.110:32311/api/queues/celery/manager', auth=('celery', 'celery'))).text)
    manager_queue_messages_unacknowledged = (manager_queue["messages_unacknowledged"])      
    tasks = worker_queue_messages_unacknowledged + manager_queue_messages_unacknowledged
    
    directory = '/Boilest/Configurations'
    # Searching for configurations
    if tasks == 0:
        print ('No tasks in sque, starting search for configs')
        for root, dirs, files in os.walk(directory):
            # select file name
            for file in files:
                # check the extension of files
                if file.endswith('.json'):
                    # append the desired fields to the original json
                    json_file = os.path.join(root,file)
                    print (json_file)
                    f = open(json_file)
                    json_template = json.load(f)
                    print (json.dumps(json_template, indent=3, sort_keys=True))
                    print ('sending ' + json_template["config_name"] + ' to ffinder')
                    ffinder.delay(json_template)
                else:
                    print('Did not find Configurations')
    elif tasks != 0:
        print ('Tasks in queue: ' + str(tasks) + ', not starting config scan')
    else:
        print ('Tasks in queue returned with an error')
    ffconfig_duration = (datetime.now() - ffconfig_start_time).total_seconds() / 60.0
    print ('>>>>>>>>>>>>>>>> ffconfigs ' + arg + ' complete, executed for ' + str(ffconfig_duration) + ' minutes <<<<<<<<<<<<<<<<<<<')



@app.task(queue='manager')
def ffinder(json_template):
    # The purpose of this function of to search a directory for files, filter for specific formats, and send those filtered results to the next function
    ffinder_start_time = datetime.now()
    print ('>>>>>>>>>>>>>>>> ffinder executing with config: ' + json_template["config_name"] + ' starting at ' + str(ffinder_start_time) + '<<<<<<<<<<<<<<<<<<<')

    # For fun/diagnostics
    print (json.dumps(json_template, indent=3, sort_keys=True))

    # Get the folder to scan
    directory = (json_template['watch_folder'])
    print ('Will now search the directory ' + directory + ' and provide the relevant config flags:')

    # traverse whole directory
    for root, dirs, files in os.walk(directory):
        # select file name
        for file in files:
            # check the extension of files
            if file.endswith('.mkv') or file.endswith('.mp4') or file.endswith('.avi'):
                # append the desired fields to the original json
                ffinder_json = {'file_path':root, 'file_name':file}
                ffinder_json.update(json_template)      
                print(json.dumps(ffinder_json, indent=3, sort_keys=True))
                fprober.delay(ffinder_json)

    ffinder_duration = (datetime.now() - ffinder_start_time).total_seconds() / 60.0
    print ('>>>>>>>>>>>>>>>> ffinder config: ' + json_template["config_name"] + ' complete, executed for ' + str(ffinder_duration) + ' minutes <<<<<<<<<<<<<<<<<<<')



@app.task(queue='manager')
def fprober(ffinder_json):
    # This function is kicked off from the individual file results from the ffinder function, and then do three functions:
    # 1) For each file, run ffprobe to get details on the file
    # 2) Loop through those the ffprobe results to determine if any changes need to be made to the video container or it's video, audio, or subtitle streams 
    # 3) Determine if the file needs to be encoded, and if yes, pass the changes to the fencoder function

    fprober_start_time = datetime.now()
    print ('>>>>>>>>>>>>>>>> fprober for ' + ffinder_json["file_name"] + ' starting at ' + str(fprober_start_time) + '<<<<<<<<<<<<<<<<<<<')

    # Using subprocess to call FFprobe, get JSON back on the video's container, and streams, then display the outputs  
    file_path = (ffinder_json["file_path"])
    file_name = (ffinder_json["file_name"])
    file_full_path = os.path.join(file_path,file_name)    
    cmnd = [f'ffprobe', '-loglevel', 'quiet', '-show_entries', 'format:stream=index,stream,codec_type,codec_name,channel_layout', '-of', 'json', file_full_path]
    print ("ffprobe's command on " + file_name + ":")
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
    if original_container != 'matroska,webm' or pathlib.Path(ffinder_json["file_name"]).suffix != '.mkv':
        file_name = (ffinder_json["file_name"])
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
    fprober_duration = (datetime.now() - fprober_start_time).total_seconds() / 60.0
    print ('>>>>>>>>>>>>>>>> fprober ' + ffinder_json["file_name"] + ' complete, executed for ' + str(fprober_duration) + ' minutes <<<<<<<<<<<<<<<<<<<')


@app.task(queue='worker')
def fencoder(fprober_json):
    # This is the step where we do the actual video encoding
    fencoder_start_time = datetime.now()
    print ('>>>>>>>>>>>>>>>> fencoder for ' + fprober_json["file_name"] + ' starting at ' + str(fencoder_start_time) + '<<<<<<<<<<<<<<<<<<<')

    print (json.dumps(fprober_json, indent=3, sort_keys=True))

    # Need to get the ffmpeg settings
    ffmpeg_settings = (fprober_json["ffmpeg_settings"])
    #print ('ffmpeg settings are: ' + ffmpeg_settings)
        
    # Need to get the input filepath
    file_path = (fprober_json["file_path"])
    file_name = (fprober_json["file_name"])
    ffmeg_input_file = os.path.join(file_path,file_name)
    #print ('input file is: ' + ffmeg_input_file)
    
    # Need to get the encoding settings     
    ffmpeg_encoding_settings = (fprober_json["ffmpeg_encoding_string"])
    #print ('encoding settings are: ' + ffmpeg_encoding_settings)
    
    # Need to get the output filepath   
    #file_name = Path(file_name).stem
    #output_extension = (fprober_json["ffmeg_container_extension"])
    
    #print ('filename is currently: ' + file_name)
    
    ffmpeg_output_file = (fprober_json["ffmpeg_output_file"])
    ffmpeg_output_file = '/boil_hold/' + ffmpeg_output_file
    
    # All together now
    ffmpeg_command = 'ffmpeg ' + ffmpeg_settings + ' -i "' + ffmeg_input_file + '"' + ffmpeg_encoding_settings + ' "' + ffmpeg_output_file + '"'
    print ('ffmpeg command:')
    print (ffmpeg_command)    

    print ('Please hold')
        #os.system(ffmpeg_command)
    process = subprocess.Popen(ffmpeg_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,universal_newlines=True)
    for line in process.stdout:
        print(line)
    
    if os.path.exists(ffmeg_input_file and ffmpeg_output_file):
        print (ffmeg_input_file + ' and ' + ffmpeg_output_file + ' Files Exists')
        input_file_stats = os.stat(ffmeg_input_file)
        input_file_stats = round(input_file_stats.st_size / (1024 * 1024))
        print (f'Original file Size in MegaBytes is: ' + str(input_file_stats)) 
        output_file_stats = (os.stat(ffmpeg_output_file))
        output_file_stats = round(output_file_stats.st_size / (1024 * 1024))
        print (f'Encoded file Size in MegaBytes is: ' + str(output_file_stats)) 
        new_file_size_difference = input_file_stats - output_file_stats
        print (f'Total Space savings is: ' + str(new_file_size_difference))
        print ('Removing ' + ffmeg_input_file)
        # We're checking for to things:
        # 1) If this is a production run, and we intend to delete source
        # 2) Don't delete sourec if the ffmpeg encode failed

        fencoder_duration = (datetime.now() - fencoder_start_time).total_seconds() / 60.0

        if output_file_stats != 0.0 and (new_file_size_difference > 0 or fprober_json["override"] == 'true'):
            # This is the use-case where the newly encoded file is small than the old file, which is what we want
            os.remove(ffmeg_input_file) 
            ffmpeg_destination = fprober_json["file_path"] + '/' + fprober_json["ffmpeg_output_file"]
            print('Moving ' + ffmpeg_output_file + ' to ' + ffmpeg_destination)
            shutil.move(ffmpeg_output_file, ffmpeg_destination)
            print ('Done')
            encode_outcome = 'success'
        elif output_file_stats != 0.0 and new_file_size_difference < 0:
            # This is the use-case where the newly encoded file is larger than the old file
            # Usually this means that the ffmpeg command requires tweaking
            print ('New file not compressed, removing')
            os.remove(ffmpeg_output_file)
            print ('Output file deleted')
            encode_outcome = 'failed'
        elif output_file_stats == 0.0:
            # Sometimes FFMPEG can fail, and the output file exists, but it's 0 kb
            print ('Something went wrong, and the output file size is 0.0 KB')
            print ('Deleting: ' + ffmpeg_output_file)
            os.remove(ffmpeg_output_file) 
        else:
            print ('Something else went wrong, and neither source nor encoded were deleted ')

        fencoder_json = {'old_file_size':input_file_stats, 'new_file_size':output_file_stats, 'new_file_size_difference':new_file_size_difference, 'fencoder_duration':fencoder_duration, 'encode_outcome':encode_outcome}
        fencoder_json.update(fprober_json) 
        print(json.dumps(fencoder_json, indent=3, sort_keys=True))
        fresults.delay(fencoder_json)
    else:
        print("Either source or encoding is missing, so exiting")
    
    print ('>>>>>>>>>>>>>>>> fencoder ' + fprober_json["file_name"] + ' complete, executed for ' + str(fencoder_duration) + ' minutes <<<<<<<<<<<<<<<<<<<')


@app.task(queue='manager')
def fresults(fencoder_json):
    # Last but not least, record the results of ffencode
    fresults_start_time = datetime.now()
    print ('>>>>>>>>>>>>>>>> fresults for ' + fencoder_json["file_name"] + ' starting at ' + str(fresults_start_time) + '<<<<<<<<<<<<<<<<<<<')
    config_name = fencoder_json["config_name"]
    ffmpeg_encoding_string = fencoder_json["ffmpeg_encoding_string"]
    file_name = fencoder_json["file_name"]
    file_path = fencoder_json["file_path"]
    new_file_size = fencoder_json["new_file_size"]
    new_file_size_difference = fencoder_json["new_file_size_difference"]
    old_file_size = fencoder_json["old_file_size"]
    watch_folder = fencoder_json["watch_folder"]
    fencoder_duration = fencoder_json["fencoder_duration"]
    original_string = fencoder_json["original_string"]
    notes = fencoder_json["notes"]
    override = fencoder_json["override"]
    encode_outcome = fencoder_json["encode_outcome"]

    recorded_date = datetime.now()

    print ("File encoding recorded: " + str(recorded_date))
    unique_identifier = file_name + str(recorded_date.microsecond)
    print ('Primary key saved as: ' + unique_identifier)

    database = r"/Boilest/DB/Boilest.db"
    conn = sqlite3.connect(database)
    c = conn.cursor()
    c.execute(
        "INSERT INTO ffencode_results"
        " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            unique_identifier,
            recorded_date,
            file_name, 
            file_path, 
            config_name,
            new_file_size, 
            new_file_size_difference, 
            old_file_size,
            watch_folder,
            ffmpeg_encoding_string,
            fencoder_duration,
            original_string,
            notes,
            override,
            encode_outcome
        )
    )
    conn.commit()

    c.execute("select round(sum(new_file_size_difference)) from ffencode_results")
    total_space_saved = c.fetchone()
    c.execute("select round(sum(fencoder_duration)) from ffencode_results")
    total_processing_time = c.fetchone()
    conn.close()

    print ('The space delta on ' + file_name + ' was: ' + str(new_file_size_difference) + ' MB and required ' + str(fencoder_duration) + ' minutes of encoding')
    print ('We have saved so far: ' + str(total_space_saved) + ' MB, which required a total processing time of ' + str(total_processing_time) + ' minutes')
      
    fresults_duration = (datetime.now() - fresults_start_time).total_seconds() / 60.0   
    print ('>>>>>>>>>>>>>>>> fencoder ' + fencoder_json["file_name"] + ' complete, executed for ' + str(fresults_duration) + ' minutes <<<<<<<<<<<<<<<<<<<')