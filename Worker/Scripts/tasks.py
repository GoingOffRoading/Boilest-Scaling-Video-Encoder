from celery import Celery
from pathlib import Path
from datetime import datetime
import json, subprocess, os, shutil, sqlite3, requests, sys

app = Celery('tasks', backend = 'rpc://celery:celery@192.168.1.110:31672/celery', broker = 'amqp://celery:celery@192.168.1.110:31672/celery')


# Schedule, kicks off a scan for configs ever 15 minutes (15 x 60 = 900 seconds)
# https://docs.celeryq.dev/en/stable/userguide/periodic-tasks.html#entries
@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Calls ffconfigs('hello') every 10 seconds.
    sender.add_periodic_task(3600.0, ffconfigs.s('hit it'))


# Scan for condigurations, and post the to the next step
@app.task(queue='manager')
def ffconfigs(arg):
    print (arg)
    worker_queue = json.loads((requests.get('http://192.168.1.110:32311/api/queues/celery/worker', auth=('celery', 'celery'))).text)
    worker_queue_messages_unacknowledged = (worker_queue["messages_unacknowledged"])
    manager_queue = json.loads((requests.get('http://192.168.1.110:32311/api/queues/celery/manager', auth=('celery', 'celery'))).text)
    manager_queue_messages_unacknowledged = (manager_queue["messages_unacknowledged"])    
    prober_queue = json.loads((requests.get('http://192.168.1.110:32311/api/queues/celery/prober', auth=('celery', 'celery'))).text)
    prober_queue_messages_unacknowledged = (prober_queue["messages_unacknowledged"])    
    tasks = worker_queue_messages_unacknowledged + manager_queue_messages_unacknowledged + prober_queue_messages_unacknowledged
    print ('Tasks in queue:')
    print(tasks)

    directory = '/Boilest/Configurations'
    # traverse whole directory
    if tasks == 0:
        for root, dirs, files in os.walk(directory):
            # select file name
            for file in files:
                # check the extension of files
                if file.endswith('.json'):
                    # append the desired fields to the original json
                    print ('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Configuration Located <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')
                    json_file = os.path.join(root,file)
                    print (json_file)
                    f = open(json_file)
                    json_template = json.load(f)
                    print (json.dumps(json_template, indent=3, sort_keys=True))
                    ffinder.delay(json_template)
                else:
                    print('Did not find Configurations')
    else:
        print ('Tasks in the queue.  Not adding more at this time')
    sys.stdout.flush()


@app.task(queue='worker')
def ffinder(json_template):
    # We feed this function a JSON string of configurations
    # Configurations are stored in the /Templates directory
    # The future state is that this is triggered as a Bloom/cron function, and configured in a UI
    # The purpose of this function of to search a directory for files, filter for specific formats, and send those filtered results to the next function
    print ('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> ffinder input json <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')
    print (json.dumps(json_template, indent=3, sort_keys=True))
    print ('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> starting file search <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')
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
                print ('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> media file located <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')
                ffinder_json = {'file_path':root, 'file_name':file}
                ffinder_json.update(json_template)      
                if (json_template["show_diagnostic_messages"]) == 'yes':
                    print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> DIAGNOSTICS <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')
                    print(json.dumps(ffinder_json, indent=3, sort_keys=True))
                    print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> DIAGNOSTICS <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')
                fprober.delay(ffinder_json)
                sys.stdout.flush()

@app.task(queue='prober')
def fprober(ffinder_json):
    # This function is kicked off from the individual file results from the ffinder function
    # fprober's functions are three:
    # 1) For each file, run ffprobe to get details on the file
    # 2) Loop through those the ffprobe results to determine if any changes need to be made to the video container or it's video, audio, or subtitle streams 
    # 3) Determine if the file needs to be encoded, and if yes, pass the changes to the fencoder function

    file_path = (ffinder_json["file_path"])
    file_name = (ffinder_json["file_name"])
    file_full_path = os.path.join(file_path,file_name)
    print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>><<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')
    print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> starting fprober step on <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')
    print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> ' + file_name + ' <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')
    print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>><<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')  
    # Using subprocess to call FFprobe, get JSON back on the video's container, and streams  
    # And displaying the outputs  
    cmnd = [f'ffprobe', '-loglevel', 'quiet', '-show_entries', 'format:stream=index,stream,codec_type,codec_name,channel_layout', '-of', 'json', file_full_path]
    print ("ffprobe's command on " + file_name + ":")
    print (cmnd)
    p = subprocess.run(cmnd, capture_output=True).stdout
    d = json.loads(p)
    print ("ffprobe's results on " + file_name + ":")
    print(json.dumps(d, indent=3, sort_keys=True))
    
    print ('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Evaluating Codecs In <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')
    print ('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> ' + file_name + ' <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')   
    # Now that we have FFProbe's output, we want to evaluate the container, video stream, audio stream, and subtitle formats
    # If those values don't match the input templte, then we flip encode_decision to yes, and transmit the results to fencoder
    encode_string = str()
    encode_decision = 'no'

    print ('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Stream Container <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')
    
    original_container = (d['format']['format_name'])
    # Determine if the container needs to be changed
    print ('Original Video container is: ' + original_container)

    if original_container != (ffinder_json["ffmpeg_container_string"]):
        file_name = (ffinder_json["file_name"])
        file_name = Path(file_name).stem 
        output_extension = (ffinder_json["ffmpeg_container_extension"])
        print (file_name + ' will need its container changed to: ' + output_extension)
        ffmpeg_output_file = file_name + '.' + output_extension
        encode_decision = 'yes'
    else:
        ffmpeg_output_file = file_name
        print (file_name + ' is already: ' + (ffinder_json["ffmpeg_container_string"]))
    
    
    print ('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Stream <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')

    streams_count = d['format']['nb_streams']
    print ('there are ' + str(streams_count) + ' streams:')
    
    for i in range (0,streams_count):
        if d['streams'][i]['codec_type'] == 'video':
            codec_name = d['streams'][i]['codec_name'] 
            if codec_name == 'av1':
                encode_string = encode_string + ' -map 0:' + str(i) + ' -c:v copy'
                # No need to change encode_decision as the video codec is in the desired format
                print ('Stream ' + str(i) + ' is already ' + codec_name + ', copying stream')
            elif codec_name == 'mjpeg':
                print ('Garbage mjpeg stream, ignoring')    
            elif codec_name != 'av1':
                encode_decision = 'yes'
                # encode_decision = yes as the video codec is not in the desired format
                encode_string = encode_string + ' -map 0:' + str(i) + ' -vcodec libsvtav1 -crf 25 -preset 4 -g 240 -pix_fmt yuv420p10le -svtav1-params filmgrain=20:film-grain-denoise=0:tune=0'
                print ('Stream ' + str(i) + ' is ' + codec_name + ', encoding stream')
            else:
                print ('Something is broken with stream ' + str(i))
        elif d['streams'][i]['codec_type'] == 'audio':
            codec_name = d['streams'][i]['codec_name'] 
            if codec_name == 'opus':
                encode_string = encode_string + ' -map 0:' + str(i) + ' -c:a copy'
                print ('Stream ' + str(i) + ' is already ' + codec_name + ': nothing to encode')
            elif codec_name != 'opus' and d['streams'][i]['channel_layout'] == '5.1(side)':
                encode_string = encode_string + ' -map 0:' + str(i) + ' -acodec libopus -af aformat=channel_layouts="7.1|5.1|stereo"'
                encode_decision = 'yes'
                print ('Stream ' + str(i) + ' is ' + codec_name + ' and, using ' + d['streams'][i]['channel_layout'] +', filtering, then encoding stream')
            elif codec_name != 'opus':
                encode_string = encode_string + ' -map 0:' + str(i) + ' -acodec libopus' 
                encode_decision = 'yes'
                print ('Stream ' + str(i) + ' is ' + codec_name + ', encoding stream')
            else:
                print ('Something is broken with stream ' + str(i))
        elif d['streams'][i]['codec_type'] == 'subtitle':
            codec_name = d['streams'][i]['codec_name'] 
            if codec_name == 'subrip':
                encode_string = encode_string + ' -map 0:' + str(i) + ' -c:s copy'
                # No need to change encode_decision as the subtitles are in the desired format
                print ('Stream ' + str(i) + ' is already ' + codec_name + ': nothing to encode')
            elif codec_name != 'subrip' and d['streams'][i]['codec_name'] == 'hdmv_pgs_subtitle':
                # These are image based subtitles, and can't be converted to text type
                encode_string = encode_string + ' -map 0:' + str(i) + ' -c:s copy' 
                # No need to change encode_decision as we can't change picture subtitles into text subtitles
                print ('Stream ' + str(i) + ' is ' + codec_name + ': a pain in the dick, and nothing we can do but encode')
            elif codec_name != 'subrip':
                encode_string = encode_string + ' -map 0:' + str(i) + ' -scodec subrip' 
                encode_decision = 'yes'
                print ('Stream ' + str(i) + ' is ' + codec_name + ', encoding stream')
            else:
                print ('Something is broken with stream ' + str(i))

        # No idea if attachments provide any value.  Sr far: no
        elif d['streams'][i]['codec_type'] == 'attachment':
            print ('Stream is attachment, ignore')
            
        else:
            print ('fuck')
            
    print ('encode_string is: ' + encode_string)
    print ('encode_decision is: ' + encode_decision)
    
    print ('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Passing FFMpeg String for <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')
    print ('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> ' + file_name + ' <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<') 
   
    # Part 2 determines if the string is needed
    if encode_decision == 'no': 
        print (file_name + ' does not need encoding')
    else:
        print (file_name + ' needs encoding')
        fprober_json = {'ffmpeg_encoding_string':encode_string, 'ffmpeg_output_file':ffmpeg_output_file}
        fprober_json.update(ffinder_json) 
        print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> fprober_json output <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')
        print(json.dumps(fprober_json, indent=3, sort_keys=True))
        print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>><<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')
        print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> fprober step complete <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')
        print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> ' + file_name + ' <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<') 
        print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>><<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')
        fencoder.delay(fprober_json)
    sys.stdout.flush()


@app.task(queue='worker')
def fencoder(fprober_json):
    print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')
    print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> fencoder for' + (fprober_json["file_name"]) + ' <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')
    print (json.dumps(fprober_json, indent=3, sort_keys=True))
    print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')

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
    print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> FFmpeg for' + (fprober_json["file_name"]) + ' <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')
    ffmpeg_command = 'ffmpeg ' + ffmpeg_settings + ' -i "' + ffmeg_input_file + '"' + ffmpeg_encoding_settings + ' "' + ffmpeg_output_file + '"'
    print (ffmpeg_command)    

    # We need to determine if this is a production run and run the function like normal
    if (fprober_json["production_run"]) == 'yes':
        print ('Please hold')
        #os.system(ffmpeg_command)
        process = subprocess.Popen(ffmpeg_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,universal_newlines=True)
        for line in process.stdout:
            print(line)
    else:
        print ('This is a test run, so lets maybe not polute production')
        input_file_stats = float(31.44148)
        output_file_stats = float(34.31477626)
        new_file_size_difference = float(2.873836)

    print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Checking on the output for' + (fprober_json["file_name"]) + ' <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')
    
    if os.path.exists(ffmeg_input_file and ffmpeg_output_file):
        print (ffmeg_input_file + ' and ' + ffmpeg_output_file + ' Files Exists')
        input_file_stats = os.stat(ffmeg_input_file)
        input_file_stats = input_file_stats.st_size / (1024 * 1024)
        print (f'Original file Size in MegaBytes is: ' + str(input_file_stats)) 
        output_file_stats = os.stat(ffmpeg_output_file)
        output_file_stats = output_file_stats.st_size / (1024 * 1024)
        print (f'Encoded file Size in MegaBytes is: ' + str(output_file_stats)) 
        new_file_size_difference = input_file_stats - output_file_stats
        print (f'Total Space savings is:' + str(new_file_size_difference))
        print ('Removing ' + ffmeg_input_file)
        # We're checking for to things:
        # 1) If this is a production run, and we intend to delete source
        # 2) Don't delete sourec if the ffmpeg encode failed
        if (fprober_json["production_run"]) == 'yes' and output_file_stats != 0.0:
            os.remove(ffmeg_input_file) 
            print('Moving ' + ffmpeg_output_file + ' to ' + ffmeg_input_file)
            shutil.move(ffmpeg_output_file, ffmeg_input_file)
            print ('Done')
            fencoder_json = {'old_file_size':input_file_stats, 'new_file_size':output_file_stats, 'new_file_size_difference':new_file_size_difference}
            fencoder_json.update(fprober_json) 
            print(json.dumps(fencoder_json, indent=3, sort_keys=True))
            fresults.delay(fencoder_json)
        elif output_file_stats == 0.0:
            print ('Something went wrong, and the output file size is 0.0 KB')
            print ('Deleting: ' + ffmpeg_output_file)
            os.remove(ffmpeg_output_file) 
        else:
            print ('Something went wrong, and neither source nor encoded were deleted ')
    else:
        print("Either source or encoding is missing, so exiting")

    print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> DIAGNOSTICS <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')
    print('>>>>>>>>>>>>>>>>>>DONE<<<<<<<<<<<<<')
    print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> DIAGNOSTICS <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')
    sys.stdout.flush()


@app.task(queue='manager')
def fresults(fencoder_json):

    print ('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> fresults ' + (fencoder_json["file_name"]) + '<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')
    config_name = (fencoder_json["config_name"])
    ffmpeg_encoding_string = (fencoder_json["ffmpeg_encoding_string"])
    file_name = (fencoder_json["file_name"])
    file_path = (fencoder_json["file_path"])
    new_file_size = (fencoder_json["new_file_size"])
    new_file_size_difference = (fencoder_json["new_file_size_difference"])
    old_file_size = (fencoder_json["old_file_size"])
    watch_folder = (fencoder_json["watch_folder"])

    recorded_date = datetime.now()
    print (recorded_date)
    print("Current microsecond =" + str(recorded_date.microsecond))
    unique_identifier = file_name + str(recorded_date.microsecond)
    print (unique_identifier)

    print ('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> fresults db part <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')

    database = r"/Boilest/DB/Boilest.db"
    conn = sqlite3.connect(database)
    c = conn.cursor()
    c.execute(
        "INSERT INTO ffencode_results"
        " VALUES (?,?,?,?,?,?,?,?,?,?)",
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
        )
    )
    conn.commit()

    c.execute("select sum(new_file_size_difference) from ffencode_results")
    print ("We have saved so far:")
    print (c.fetchone())

    conn.close()
    print ('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> fresults db part done <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')
    sys.stdout.flush()