from celery import Celery
import subprocess, os, shutil
from task_shared_services import celery_url_path, file_size_mb, task_start_time, task_duration_time

app = Celery('tasks', backend = celery_url_path('rpc://'), broker = celery_url_path('amqp://') )

@app.task(queue='worker')
def fencoder(ffmpeg_inputs):
    import sys
    sys.path.append("/Scripts")
    from tasks_manager import ffresults

    function_start_time = task_start_time('fencoder')
  
    ffmpeg_command = ffmpeg_inputs['ffmpeg_command']

    print ('FFMpeg command for ' + ffmpeg_inputs['file'])
    print (ffmpeg_command)

    print ('Please hold')
    
    process = subprocess.Popen(ffmpeg_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,universal_newlines=True)

    for line in process.stdout:
        print(line)

    files_exist = str()
    encode_outcome = str()
    stats = str()
    move = str()
    file_path = ffmpeg_inputs['file_path']
    temp_filepath = ffmpeg_inputs['temp_filepath']
    root = ffmpeg_inputs['root']

    if os.path.exists(file_path and temp_filepath):
        files_exist = 'yes'
    elif os.path.exists(temp_filepath):
        os.remove(temp_filepath)
    else:
        print ('Issue with: ' + ffmpeg_inputs['file'])

    
    if files_exist == 'yes':
        old_file_size = file_size_mb(file_path)
        new_file_size = file_size_mb(temp_filepath)
        new_file_size_difference = old_file_size - new_file_size
        print ('Old file size is: ' + str(old_file_size) + ' MB')
        print ('New file size is: ' + str(new_file_size) + ' MB')
        print ('Space saved on this encode: ' + str(new_file_size_difference) + ' MB')
        stats = 'exist'
        if new_file_size_difference >= 0:
            encode_outcome = 'success'
        elif new_file_size_difference < 0:
            encode_outcome = 'file_larger'
        else:
            encode_outcome = 'unknown_outcome'
        print ('Encode Outcome: ' + encode_outcome)
    else:
        print ('Issue with: ' + ffmpeg_inputs['file'])

    if stats == 'exist' and encode_outcome in ['success','file_larger']:
        destination_filepath = root + '/' + os.path.basename(temp_filepath)
        print('Moving ' + temp_filepath + ' to ' + destination_filepath)
        os.remove(file_path)
        shutil.move(temp_filepath, destination_filepath) 
        move = 'complete'
        print ('Move complete')
    else:
        print ('Issue with: ' + ffmpeg_inputs['file'])

    if move == 'complete':
        ffresults_input = ffmpeg_inputs
        del ffmpeg_inputs['temp_filepath']
        ffresults_input.update({'new_file_size':new_file_size})
        ffresults_input.update({'old_file_size':old_file_size})
        ffresults_input.update({'new_file_size_difference':new_file_size_difference})
        ffresults_input.update({'encode_outcome':encode_outcome})

        ffresults.delay(ffresults_input)

        print ('ffresults called')

    task_duration_time('fencoder',function_start_time)
    