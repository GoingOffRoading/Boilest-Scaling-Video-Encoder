from celery import Celery
import subprocess, os, shutil
from task_shared_services import celery_url_path, file_size_mb, task_start_time, task_duration_time, validate_video, run_ffmpeg

app = Celery('tasks', backend = celery_url_path('rpc://'), broker = celery_url_path('amqp://') )

@app.task(queue='worker')
def fencoder(ffmpeg_inputs):
    import sys
    sys.path.append("/Scripts")
    from tasks_manager import ffresults

    function_start_time = task_start_time('fencoder')

    ffmpeg_command = ffmpeg_inputs['ffmpeg_command']
    ready_command = str()
    encode_outcome = str()
    file_path = ffmpeg_inputs['file_path']
    temp_filepath = ffmpeg_inputs['temp_filepath']
    root = ffmpeg_inputs['root']


    if os.path.exists(ffmpeg_inputs['file_path']):
        ready_command = 'ready_to_validate_source'

    
    if ready_command == 'ready_to_validate_source':
        print ('Checking: ' + ffmpeg_inputs['file'])
        if validate_video(ffmpeg_inputs['file_path']) == 'Success':
            print (ffmpeg_inputs['file'] + ' passed validation')
            ready_command = 'input_validated'
        else:
            print (ffmpeg_inputs['file'] + ' fails validation')
    

    if ready_command == 'input_validated':
        print ('FFMpeg command for ' + ffmpeg_inputs['file'])
        print (ffmpeg_command)
        print ('Please hold') 
        exit_code = run_ffmpeg(ffmpeg_command)
        if exit_code == 'Success':
            print("Encoding was successful.")
            ready_command = 'encode_success'
        else:
            print(f"Encoding failed")
            ready_command = 'encode_failed'


    if ready_command == 'encode_failed':
        if os.path.exists(temp_filepath):
            print ('Removing: ' + ffmpeg_inputs['temp_filepath'])
            os.remove(temp_filepath)

    
    if ready_command == 'encode_success':
        if validate_video(ffmpeg_inputs['temp_filepath']) == 'Success':
            ready_command = 'ready_to_compare'

    
    if ready_command == 'ready_to_compare':
        old_file_size = file_size_mb(file_path)
        new_file_size = file_size_mb(temp_filepath)
        new_file_size_difference = old_file_size - new_file_size
        print ('Old file size is: ' + str(old_file_size) + ' MB')
        print ('New file size is: ' + str(new_file_size) + ' MB')
        print ('Space saved on this encode: ' + str(new_file_size_difference) + ' MB')
        ready_command = 'stats_exist'
        if new_file_size_difference >= 0:
            encode_outcome = 'success'
        elif new_file_size_difference < 0:
            encode_outcome = 'file_larger'
        else:
            encode_outcome = 'unknown_outcome'
        print ('Encode Outcome: ' + encode_outcome)


    if ready_command == 'stats_exist' and encode_outcome in ['success','file_larger']:
        destination_filepath = root + '/' + os.path.basename(temp_filepath)
        print('Moving ' + temp_filepath + ' to ' + destination_filepath)
        os.remove(file_path)
        shutil.move(temp_filepath, destination_filepath) 
        ready_command = 'move_complete'
        print ('Move complete')
    else:
        print ('Issue with: ' + ffmpeg_inputs['file'])


    if ready_command == 'move_complete':
        ffresults_input = ffmpeg_inputs
        del ffmpeg_inputs['temp_filepath']
        ffresults_input.update({'new_file_size':new_file_size})
        ffresults_input.update({'old_file_size':old_file_size})
        ffresults_input.update({'new_file_size_difference':new_file_size_difference})
        ffresults_input.update({'encode_outcome':encode_outcome})
        ffresults.delay(ffresults_input)

        print ('ffresults called')

    task_duration_time('fencoder',function_start_time)
    