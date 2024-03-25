from celery import Celery
from datetime import datetime
import json, os, sqlite3
from task_shared_services import task_start_time, task_duration_time, check_queue, find_files, celery_url_path, check_queue, ffprober, ffprober2


backend_path = celery_url_path('rpc://') 
broker_path = celery_url_path('amqp://') 
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

    task_duration_time('ffinder',function_start_time)

@app.task(queue='manager')
def ffprober_container(json_configuration):
    import sys
    sys.path.append("/Scripts")
    from tasks_worker import fencoder

    function_start_time = task_start_time('ffprober_container')

    output_filename = os.path.splitext(json_configuration["file"])[0] + json_configuration["format_extension"]

    ffmpeg_command = '-c copy'
    original_string = os.path.splitext(json_configuration["file"])[1]

    json_configuration.update({'output_filename':output_filename,'ffmpeg_command':ffmpeg_command,'original_string':original_string})
    fencoder.delay(json_configuration)
    print ('fencoder called')

    task_duration_time('ffprober_container',function_start_time)

@app.task(queue='manager')
def ffprober_video_stream(json_configuration):
    import sys
    sys.path.append("/Scripts")
    from tasks_worker import fencoder

    function_start_time = task_start_time('ffprober_video_stream')

    output_filename = json_configuration["file"]
    ffmpeg_command = str()
    encode_decision = 'no'
    original_string = str()
    
    print ('json_configuration["ffprobe_string"] is: ' + json_configuration["ffprobe_string"])
    print ('json_configuration["file_path"] is: ' + json_configuration["file_path"])

    ffprobe_results = ffprober2(json_configuration["ffprobe_string"],json_configuration["file_path"]) 
        
    # Stream Loop: We need to loop through each of the streams, and make decisions based on the codec in the stream
    streams_count = ffprobe_results['format']['nb_streams']
    print ('there are ' + str(streams_count) + ' streams:')
    for i in range (0,streams_count): 
        codec_type = ffprobe_results['streams'][i]['codec_type']
        if codec_type == json_configuration["ffmpeg_codec_type"]:
            codec_name = ffprobe_results['streams'][i]['codec_name'] 
            original_string = original_string + '{stream ' + str(i) + ' ' + ffprobe_results['streams'][i]['codec_type'] + ' = ' + codec_name + '}'
            if codec_name == (json_configuration["ffmpeg_codec_name"]):
                ffmpeg_command = ffmpeg_command + ' -map 0:' + str(i) + ' -c:v copy'
                # No need to change encode_decision as the video codec is in the desired format
                print ('Stream ' + str(i) + ' is already ' + codec_name + ', copying stream')
            elif codec_name == 'mjpeg':
                print ('Garbage mjpeg stream, ignoring')    
                # No use for this for now
            elif codec_name != (json_configuration["ffmpeg_codec_name"]):
                encode_decision = 'yes'
                ffmpeg_command = ffmpeg_command + ' -map 0:' + str(i) + ' -c:v ' + (json_configuration["ffmpeg_string"])
                print ('Stream ' + str(i) + ' is ' + codec_name + ', encoding stream')
                # encode_decision = yes as the video codec is not in the desired format
            else:
                print ('Something is broken with stream ' + str(i))
                # Catch all error state        
        else:
           if codec_type == 'video':
               ffmpeg_command = ffmpeg_command + ' -map 0:' + str(i) + ' -c:v copy'
           elif codec_type == 'audio':
               ffmpeg_command = ffmpeg_command + ' -map 0:' + str(i) + ' -c:a copy'
           elif codec_type == 'subtitle':
               ffmpeg_command = ffmpeg_command + ' -map 0:' + str(i) + ' -c:s copy'
           elif codec_type == 'attachment':
               ffmpeg_command = ffmpeg_command + ' -map 0:' + str(i) + ' -c:t copy'
           else:
            print ('unexpected codec type')

    del json_configuration['ffmpeg_codec_name']
    del json_configuration['ffmpeg_codec_type']
    del json_configuration['ffmpeg_string']
    del json_configuration['ffprobe_string']
    del json_configuration['format_extension']
    del json_configuration['format_name']

<<<<<<< Updated upstream
    print ('ffmpeg_command is: ' + ffmpeg_command)
    print ('encode_decision is: ' + encode_decision)
    print ('original_string is: ' + original_string)
       
    # Part 2 determines if the string is needed
    if encode_decision == 'no': 
        print (json_configuration["file"] + ' does not need encoding')
    elif encode_decision == 'yes':
        print (json_configuration["file"] + ' needs encoding')
        json_configuration.update({'ffmpeg_command':ffmpeg_command, 'output_filename':output_filename, 'original_string':original_string})
        print(json.dumps(json_configuration, indent=3, sort_keys=True))
        fencoder.delay(json_configuration)
        print ('fencoder called')
=======
        logging.debug ('Generating file size')
        # I started to evaluate getting an actual hash but the functions took too long
        # Using file size in bytes to valudate works as a tep solution
        file_hash = get_file_size_bytes(file_located['file_path'])    

        logging.debug ('Incoming FFMpeg command:')
        logging.debug (ffmpeg_command)
        ffmpeg_inputs = file_located
        ffmpeg_inputs.update({'file_hash':file_hash})        
        ffmpeg_inputs.update({'ffmpeg_command':ffmpeg_command})
        ffmpeg_inputs.update({'job':'ffprober_av1_check'})
        ffmpeg_inputs.update({'temp_filepath':ffmpeg_output_file(file_located['file'])})
        ffmpeg_inputs.update({'original_string':original_string})
        del ffmpeg_inputs['extension']

        #fencoder.delay(ffmpeg_inputs)
        #fencoder.apply_async(args=(ffmpeg_inputs, ), priority=celery_priority_value)
        
        if ffprobe_results['streams'][0]['codec_name'] == 'h264':
            fencoder.apply_async(kwargs={'ffmpeg_inputs': ffmpeg_inputs}, priority=7)
            logging.debug ('celery_priority_value is 4')
        elif ffprobe_results['streams'][0]['codec_name'] == 'hevc':
            fencoder.apply_async(kwargs={'ffmpeg_inputs': ffmpeg_inputs}, priority=3)
            logging.debug ('celery_priority_value is 6')
        else:
            fencoder.apply_async(kwargs={'ffmpeg_inputs': ffmpeg_inputs}, priority=5)
            logging.debug ('celery_priority_value is 5')


    elif encode_decision == 'no':
        logging.debug ('Next task goes here')
>>>>>>> Stashed changes
    else:
        print('Something went wrong')

    
    task_duration_time('fprober',function_start_time)


@app.task(queue='manager')
def ffresults(json_configuration):

    function_start_time = task_start_time('ffresults')

    config_name = json_configuration["config_name"]
    ffmpeg_encoding_string = json_configuration["ffmpeg_command"]
    file_name = json_configuration["file"]
    file_path = json_configuration["root"]
    new_file_size = json_configuration["new_file_size"]
    new_file_size_difference = json_configuration["new_file_size_difference"]
    old_file_size = json_configuration["old_file_size"]
    original_string = json_configuration["original_string"]
    notes = json_configuration["notes"]
    override = json_configuration["override"]
    encode_outcome = json_configuration["encode_outcome"]
    

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
            ffmpeg_encoding_string,
            override,
            encode_outcome,
            notes,
            original_string
        )
    )
    conn.commit()

    c.execute("select round(sum(new_file_size_difference)) from ffencode_results")
    total_space_saved = c.fetchone()
    conn.close()

    print ('The space delta on ' + file_name + ' was: ' + str(new_file_size_difference) + ' MB')
    print ('We have saved so far: ' + str(total_space_saved) + ' MB.')

    task_duration_time('ffresults',function_start_time)