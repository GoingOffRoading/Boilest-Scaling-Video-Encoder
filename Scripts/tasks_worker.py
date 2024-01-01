from celery import Celery
import os, shutil, logging
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

    logging.info ('Running: ' + ffmpeg_command)

    if os.path.exists(ffmpeg_inputs['file_path']):
        ready_command = 'ready_to_validate_source'

    
    if ready_command == 'ready_to_validate_source':
        logging.debug ('Checking: ' + ffmpeg_inputs['file'])
        if validate_video(ffmpeg_inputs['file_path']) == 'Success':
            logging.debug (ffmpeg_inputs['file'] + ' passed validation')
            ready_command = 'input_validated'
        else:
            logging.debug (ffmpeg_inputs['file'] + ' fails validation')
    

    if ready_command == 'input_validated':
        logging.debug ('FFMpeg command for ' + ffmpeg_inputs['file'])
        logging.debug (ffmpeg_command)
        logging.debug ('Please hold') 
        exit_code = run_ffmpeg(ffmpeg_command)
        if exit_code == 'Success':
            logging.debug("Encoding was successful.")
            ready_command = 'encode_success'
        else:
            logging.debug(f"Encoding failed")
            ready_command = 'encode_failed'


    if ready_command == 'encode_failed':
        if os.path.exists(temp_filepath):
            logging.debug ('Removing: ' + ffmpeg_inputs['temp_filepath'])
            os.remove(temp_filepath)

    
    if ready_command == 'encode_success':
        if validate_video(ffmpeg_inputs['temp_filepath']) == 'Success':
            ready_command = 'ready_to_compare'

    
    if ready_command == 'ready_to_compare':
        old_file_size = file_size_mb(file_path)
        new_file_size = file_size_mb(temp_filepath)
        new_file_size_difference = old_file_size - new_file_size
        logging.debug ('Old file size is: ' + str(old_file_size) + ' MB')
        logging.debug ('New file size is: ' + str(new_file_size) + ' MB')
        logging.debug ('Space saved on this encode: ' + str(new_file_size_difference) + ' MB')
        ready_command = 'stats_exist'
        if new_file_size_difference >= 0:
            encode_outcome = 'success'
        elif new_file_size_difference < 0:
            encode_outcome = 'file_larger'
        else:
            encode_outcome = 'unknown_outcome'
        logging.error ('Encode Outcome: ' + encode_outcome)


    if ready_command == 'stats_exist' and encode_outcome in ['success','file_larger']:
        destination_filepath = root + '/' + os.path.basename(temp_filepath)
        logging.debug('Moving ' + temp_filepath + ' to ' + destination_filepath)
        os.remove(file_path)
        shutil.move(temp_filepath, destination_filepath) 
        ready_command = 'move_complete'
        logging.debug ('Move complete')
    else:
        logging.error ('Issue with: ' + ffmpeg_inputs['file'])


    if ready_command == 'move_complete':
        ffresults_input = ffmpeg_inputs
        del ffmpeg_inputs['temp_filepath']
        ffresults_input.update({'new_file_size':new_file_size})
        ffresults_input.update({'old_file_size':old_file_size})
        ffresults_input.update({'new_file_size_difference':new_file_size_difference})
        ffresults_input.update({'encode_outcome':encode_outcome})
        ffresults.delay(ffresults_input)

        logging.debug ('ffresults called')

    task_duration_time('fencoder',function_start_time)
    