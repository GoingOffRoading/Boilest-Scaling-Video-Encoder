from celery import Celery
from datetime import datetime
import json, os, sqlite3
from task_shared_services import task_start_time, task_duration_time, check_queue, find_files, celery_url_path, check_queue, ffmpeg_output_file, ffprober_function

app = Celery('tasks', backend = celery_url_path('rpc://'), broker = celery_url_path('amqp://') )

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
        locate_files.delay(arg)
    elif queue_depth != 0:
        print (str(queue_depth) + ' tasks in queue')
    else:
        print ('Something went wrong checking the Worker Queue')


@app.task(queue='manager')
def locate_files(arg):
    function_start_time = task_start_time('locate_files')
    directories = ['/anime', '/tv', '/movies']
    extensions = ['.mp4', '.mkv', '.avi']
    print ('Searching: ' + str(directories))
    print ('For: ' + str(extensions))
    for file_located in find_files(directories, extensions):
            print ('Send to ffprobe function')
            file_located = json.loads(file_located)
            print(json.dumps(file_located, indent=3, sort_keys=True))
            ffprober.delay(file_located)
    task_duration_time('locate_files',function_start_time)


@app.task(queue='manager')
def ffprober(file_located):
    function_start_time = task_start_time('ffprober')    
    ffprobe_results = ffprober_function(file_located) 
    print(json.dumps(ffprobe_results, indent=3, sort_keys=True))
    container_check.delay(file_located,ffprobe_results)
    task_duration_time('ffprober',function_start_time)


@app.task(queue='manager')
def container_check(file_located, ffprobe_results):
    import sys
    sys.path.append("/Scripts")
    from tasks_worker import fencoder

    function_start_time = task_start_time('container_check')

    print ('Checking contaienr type for: ' + file_located['file'])
    print ('In: ' + file_located['root'])

    if ffprobe_results['format']['format_name'] != 'matroska,webm' or file_located['extension'] != '.mkv':
        print (file_located['file'] + ' is not .MKV')
        print ('Sending to FFmpeg:')
        
        ffmpeg_command = 'ffmpeg ' + \
                        os.environ.get('ffmpeg_settings') + \
                        ' -i ' + \
                        '"' + file_located['file_path'] + '" ' + \
                        '"' + ffmpeg_output_file(file_located['file']) + '"'
        
        print (ffmpeg_command)

        ffmpeg_inputs = file_located        
        ffmpeg_inputs.update({'ffmpeg_command':ffmpeg_command})
        ffmpeg_inputs.update({'job':'container_check'})
        ffmpeg_inputs.update({'temp_filepath':ffmpeg_output_file(file_located['file'])})
        ffmpeg_inputs.update({'original_string':ffmpeg_inputs['extension']})
        del ffmpeg_inputs['extension']

        fencoder.delay(ffmpeg_inputs)
    else:
        print (file_located['file'] + ' is .MKV')
        print ('Sending ' + file_located['file'] + ' to the next step')
        ffprober_av1_check.delay(file_located,ffprobe_results)
        
    task_duration_time('container_check',function_start_time)

@app.task(queue='manager')
def ffprober_av1_check(file_located,ffprobe_results):
    import sys
    sys.path.append("/Scripts")
    from tasks_worker import fencoder

    function_start_time = task_start_time('ffprober_av1_check')

    print ('Checking video codec in: ' + file_located['file'])
    print ('In: ' + file_located['root'])

    if file_located['directory'] == '/anime':
        ffmpeg_string = "libsvtav1 -crf 25 -preset 4 -g 240 -pix_fmt yuv420p10le -svtav1-params filmgrain=20:film-grain-denoise=0:tune=0:enable-qm=1:qm-min=0:qm-max=15"
    elif file_located['directory'] == '/tv':
        ffmpeg_string = "libsvtav1 -crf 30 -preset 4 -g 240 -pix_fmt yuv420p10le -svtav1-params filmgrain=20:film-grain-denoise=0:tune=0:enable-qm=1:qm-min=0:qm-max=15"
    elif file_located['directory'] == '/movies':
        ffmpeg_string = "libsvtav1 -crf 25 -preset 6 -g 240 -pix_fmt yuv420p10le -svtav1-params filmgrain=20:film-grain-denoise=0:tune=0:enable-qm=1:qm-min=0:qm-max=15"
    else:
        print ('Directory configuration does not exist')

    ffmpeg_command = str()
    encode_decision = 'no'
    original_string = str()

    streams_count = ffprobe_results['format']['nb_streams']
    print ('there are ' + str(streams_count) + ' streams:')

    for i in range (0,streams_count): 
        codec_type = ffprobe_results['streams'][i]['codec_type']
        if codec_type == 'video':
            codec_name = ffprobe_results['streams'][i]['codec_name'] 
            if codec_name == 'av1':
                ffmpeg_command = ffmpeg_command + ' -map 0:' + str(i) + ' -c:v copy'
                # No need to change encode_decision as the video codec is in the desired format
                print ('Stream ' + str(i) + ' is already ' + codec_name + ', copying stream')
            elif codec_name == 'mjpeg':
                print ('Garbage mjpeg stream, ignoring')    
                # No use for this for now
            elif codec_name != 'av1':
                encode_decision = 'yes'
                ffmpeg_command = ffmpeg_command + ' -map 0:' + str(i) + ' -c:v ' + ffmpeg_string
                original_string = original_string + '{stream ' + str(i) + ' ' + ffprobe_results['streams'][i]['codec_type'] + ' = ' + codec_name + '}'
                print ('Stream ' + str(i) + ' is ' + codec_name + ', encoding stream')
                # encode_decision = yes as the video codec is not in the desired format
            else:
                print ('Something is broken with stream ' + str(i))
                # Catch all error state        
        else:
           if codec_type == 'audio':
               ffmpeg_command = ffmpeg_command + ' -map 0:' + str(i) + ' -c:a copy'
           elif codec_type == 'subtitle':
               ffmpeg_command = ffmpeg_command + ' -map 0:' + str(i) + ' -c:s copy'
           elif codec_type == 'attachment':
               ffmpeg_command = ffmpeg_command + ' -map 0:' + str(i) + ' -c:t copy'
           else:
            print ('unexpected codec type')
    
    ffmpeg_command = 'ffmpeg ' + \
                os.environ.get('ffmpeg_settings') + \
                ' -i ' + \
                '"' + file_located['file_path'] + '"' + \
                ffmpeg_command + \
                ' "' + ffmpeg_output_file(file_located['file']) + '"'
    
    if encode_decision == 'yes':
        print ('Incoming FFMpeg command:')
        print (ffmpeg_command)
        ffmpeg_inputs = file_located        
        ffmpeg_inputs.update({'ffmpeg_command':ffmpeg_command})
        ffmpeg_inputs.update({'job':'ffprober_av1_check'})
        ffmpeg_inputs.update({'temp_filepath':ffmpeg_output_file(file_located['file'])})
        ffmpeg_inputs.update({'original_string':original_string})
        del ffmpeg_inputs['extension']

        fencoder.delay(ffmpeg_inputs)
    elif encode_decision == 'no':
        print('Next task goes here')
    else:
        print ('Error state here')

    task_duration_time('ffprober_av1_check',function_start_time)

@app.task(queue='manager')
def ffresults(ffresults_input):

    function_start_time = task_start_time('ffresults')

    print ('Encoding results for: ' + ffresults_input['file'])
    print ('From: ' + ffresults_input['root'])

    ffmpeg_command = ffresults_input["ffmpeg_command"]
    file_name = ffresults_input["file"]
    file_path = ffresults_input["file_path"]
    new_file_size = ffresults_input["new_file_size"]
    new_file_size_difference = ffresults_input["new_file_size_difference"]
    old_file_size = ffresults_input["old_file_size"]
    original_string = ffresults_input["original_string"]
    encode_outcome = ffresults_input["encode_outcome"]
    

    recorded_date = datetime.now()

    print ("File encoding recorded: " + str(recorded_date) + 'MB')
    unique_identifier = file_name + str(recorded_date.microsecond)
    print ('Primary key saved as: ' + unique_identifier)

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
            new_file_size, 
            new_file_size_difference, 
            old_file_size,
            ffmpeg_command,
            encode_outcome,
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


