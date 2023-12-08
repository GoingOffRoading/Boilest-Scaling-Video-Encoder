from celery import Celery
from datetime import datetime
import json, os, sqlite3
from task_shared_services import task_start_time, task_duration_time, check_queue, find_files, celery_url_path, check_queue, ffprober, ffmpeg_output_file


backend_path = celery_url_path('rpc://') 
broker_path = celery_url_path('amqp://') 
app = Celery('tasks', backend = backend_path, broker = broker_path)

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
    for file_located in find_files(directories, extensions):
        if file_located['extension'] in ['.avi','.mp4']:
            print ('Send to AVI function')
            ffprober_not_mkv.delay(file_located)
        elif file_located['extension'] == '.mkv':
            print ('Send to ffprobe function')
            ffprober(file_located)
        else:
            print ('No logic match for extension: ' + file_located['extension'])
    task_duration_time('locate_files',function_start_time)


@app.task(queue='manager')
def ffprober(file_located):
    function_start_time = task_start_time('ffprober')
    ffprobe_results = ffprober("ffprobe -loglevel quiet -show_entries format:stream=index,stream,codec_type,codec_name,channel_layout -of json",file_located["file_path"]) 
    container_check.delay(file_located,ffprobe_results)
    task_duration_time('ffprober',function_start_time)


@app.task(queue='manager')
def container_check(file_located):
    import sys
    sys.path.append("/Scripts")
    from tasks_worker import fencoder

    function_start_time = task_start_time('ffprober_not_mkv')

    change_container = 'no'
    if original_container != 'matroska,webm' or pathlib.Path(ffinder_json["file_name"]).suffix != '.mkv':
        change_container = 'yes'        

    if change_container == 'yes':
        ffmpeg_command = "ffmpeg -hide_banner -loglevel 16 -stats -stats_period 10 -i " + file_located['file_path'] + ' ' + ffmpeg_output_file(file_located['file'])

        ffmpeg_inputs = {
            'directory':file_located['directory'], 
            'job':'ffprober_not_mkv', 
            'ffmpeg_command':ffmpeg_command,
            'original_file':'not an MKV',
            'root':file_located['root'], 
            'dirs':file_located['dirs'], 
            'file':file_located['file'], 
            'file_path':file_located['file_path']
            }

        fencoder.delay(ffmpeg_inputs)
    else:
        ffprober_video_stream.delay(ffmpeg_inputs)
        
    task_duration_time('ffprober_not_mkv',function_start_time)




    streams_count = ffprobe_results['format']['nb_streams']
    print ('there are ' + str(streams_count) + ' streams:')

    
    for i in range (0,streams_count):         
        if ffprobe_results['streams'][i]['codec_type'] == 'video':
            if ffprobe_results['streams'][i]['codec_name'] != 'av1':
                video_requires_encoding = 'yes'
        elif ffprobe_results['streams'][i]['codec_type'] == 'audio':
            if ffprobe_results['streams'][i]['codec_name'] != 'aac':
                audio_requires_encoding = 'yes'
        elif ffprobe_results['streams'][i]['codec_type'] == 'subtitles':
            if ffprobe_results['streams'][i]['codec_name'] != 'subrip':
                subtitles_requires_encoding = 'yes'
        elif ffprobe_results['streams'][i]['codec_type'] == 'attachment':
            attachments_requires_encoding = 'yes'
        else:
            print ('Unknown stream type')

    if video_requires_encoding == 'yes':
        ffprober_video_stream.delay(file_located)
    elif audio_requires_encoding == 'yes':
        print ('Placeholder for future state audio encoding')
    elif subtitles_requires_encoding == 'yes':
        print ('Placeholder for future state subtitles encoding')
    elif attachments_requires_encoding == 'yes':
        print ('Placeholder for future state attachment encoding')
        

    task_duration_time('fprober',function_start_time)



def ffprober_video_stream(file_located,ffprobe_results):
    import sys
    sys.path.append("/Scripts")
    from tasks_worker import fencoder

    streams_count = ffprobe_results['format']['nb_streams']
    print ('there are ' + str(streams_count) + ' streams:')
    for i in range (0,streams_count): 
        codec_type = ffprobe_results['streams'][i]['codec_type']
        if codec_type == 'video':
            codec_name = ffprobe_results['streams'][i]['codec_name'] 
            original_file = original_file + '{stream ' + str(i) + ' ' + ffprobe_results['streams'][i]['codec_type'] + ' = ' + codec_name + '}'
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








    ffmpeg_inputs = {
            'directory':file_located['directory'], 
            'job':'ffprober_not_mkv', 
            'ffmpeg_command':ffmpeg_command,
            'original_file':'not an MKV',
            'root':file_located['root'], 
            'dirs':file_located['dirs'], 
            'file':file_located['file'], 
            'file_path':file_located['file_path']
            }

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

    ffprobe_results = ffprober(json_configuration["ffprobe_string"],json_configuration["file_path"]) 
        
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


