from celery import Celery
import subprocess, os, shutil
from task_shared_services import celery_url_path, file_size_mb, task_start_time, task_duration_time

backend_path = celery_url_path('rpc://') 
broker_path = celery_url_path('amqp://') 
app = Celery('tasks', backend = backend_path, broker = broker_path)

@app.task(queue='worker')
def fencoder(ffmpeg_inputs):
    import sys
    sys.path.append("/Scripts")
    from tasks_manager import ffresults

    function_start_time = task_start_time('fencoder')
  
    ffmpeg_command = ffmpeg_inputs['ffmpeg_command']

    print ('Please hold')
    
    process = subprocess.Popen(ffmpeg_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,universal_newlines=True)

    for line in process.stdout:
        print(line)

    encode_outcome = str()
    stats = str()
    move = str()
    file_path = ffmpeg_inputs['file_path']
    temp_filepath = ffmpeg_inputs['temp_filepath']
    root = ffmpeg_inputs['root']

    if os.path.exists(file_path and temp_filepath):
        files_exist = 'yes'
    else:
        print('Something went wrong, a file is missing') 

    
    if files_exist == 'yes':
        old_file_size = file_size_mb(file_path)
        new_file_size = file_size_mb(temp_filepath)
        new_file_size_difference = old_file_size - new_file_size
        print ('Old file size is: ' + str(old_file_size))
        print ('New file size is: ' + str(new_file_size))
        print ('Space saved on this encode: ' + str(new_file_size_difference))
        stats = 'exist'
        if new_file_size_difference > 0:
            encode_outcome = 'success'
        elif new_file_size_difference < 0:
            encode_outcome = 'file_larger'
        elif new_file_size_difference == 0:
            encode_outcome = 'error'
        else:
            encode_outcome = 'unknown_outcome'
        print ('Encode Outcome: ' + encode_outcome)

    if stats == 'exist':
        if encode_outcome == 'error':
            os.remove(temp_filepath)
        else:
            destination_filepath = root + '/' + os.path.basename(temp_filepath)
            print('Moving ' + temp_filepath + ' to ' + destination_filepath)
            os.remove(file_path)
            shutil.move(temp_filepath, destination_filepath) 
            move = 'complete'
            print ('Move complete')

    if move == 'complete':
        ffresults = ffmpeg_inputs
        del ffmpeg_inputs['temp_filepath']
        ffmpeg_inputs.update({'new_file_size':new_file_size})
        ffmpeg_inputs.update({'old_file_size':old_file_size})
        ffmpeg_inputs.update({'new_file_size_difference':new_file_size_difference})
        ffmpeg_inputs.update({'encode_outcome':encode_outcome})
        ffresults.delay(ffmpeg_inputs)

        print ('ffresults called')

    task_duration_time('fencoder',function_start_time)
    