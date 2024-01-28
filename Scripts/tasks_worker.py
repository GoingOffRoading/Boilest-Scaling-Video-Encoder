from celery import Celery
import os, shutil, logging
from task_shared_services import celery_url_path, file_size_mb, task_start_time, task_duration_time, validate_video, run_ffmpeg, get_file_size_bytes

# Get log level from environment variable, defaulting to INFO if not set
#log_level = os.getenv('LOG_LEVEL', 'INFO')
#
#print ('log_level is: ' + log_level)
#
# Configure basic logging
##logging.basicConfig(
#    level=log_level,
#    format='%(asctime)s - %(levelname)s - %(message)s'
#)

app = Celery('tasks', backend = celery_url_path('rpc://'), broker = celery_url_path('amqp://') )

app.conf.update(
    worker_log_level='WARNING'
)


@app.task(queue='worker')
def fencoder(ffmpeg_inputs):
    import sys
    sys.path.append("/Scripts")
    from tasks_manager import ffresults

    function_start_time = task_start_time('fencoder')

    ffmpeg_command = ffmpeg_inputs['ffmpeg_command']
    encode_outcome = str()
    exit_code = str()
    file_path = ffmpeg_inputs['file_path']
    temp_filepath = ffmpeg_inputs['temp_filepath']
    root = ffmpeg_inputs['root']
    

    # Lets check to see if the file still exists

    File_Exists = os.path.exists(ffmpeg_inputs['file_path'])
    logging.debug ('File_Exists : ' + str(File_Exists))
    Current_File_Size = get_file_size_bytes(ffmpeg_inputs['file_path'])
    logging.debug ('Scanned size hash : ' + str(ffmpeg_inputs['file_hash']))
    logging.debug ('Current size hash : ' + str(Current_File_Size))
    Video_Validation = validate_video(ffmpeg_inputs['file_path'])
    logging.debug ('Video_Validation : ' + str(Video_Validation))


    if (File_Exists == True and
        Current_File_Size == ffmpeg_inputs['file_hash'] and
        Video_Validation == 'Success'
        ):
        logging.debug ('FFMpeg command for ' + ffmpeg_inputs['file'])
        logging.debug (ffmpeg_command)
        logging.info ('Running: ' + ffmpeg_command)
        logging.debug ('Please hold') 
        exit_code = run_ffmpeg(ffmpeg_command)
    elif File_Exists == False:
        logging.error (ffmpeg_inputs['file_path'] + ' no longer exists') 
    elif Current_File_Size != ffmpeg_inputs['file_hash']:
        logging.error (ffmpeg_inputs['file_path'] + ' is not the same file from the scan')
    elif Video_Validation == 'Failure':
        logging.error (ffmpeg_inputs['file_path'] + ' is not a valid video file')
    else:
        logging.error ('Unknown error processing: ' + ffmpeg_inputs['file_path'])

    
    logging.debug ('exit_code : ' + str(exit_code))


    if (exit_code == 'Success' and 
        validate_video(ffmpeg_inputs['temp_filepath']) == 'Success'):
        logging.debug("Encoding was successful.")

        old_file_size = file_size_mb(file_path)
        new_file_size = file_size_mb(temp_filepath)
        new_file_size_difference = old_file_size - new_file_size
        logging.debug ('Old file size is: ' + str(old_file_size) + ' MB')
        logging.debug ('New file size is: ' + str(new_file_size) + ' MB')
        logging.debug ('Space saved on this encode: ' + str(new_file_size_difference) + ' MB')
        if new_file_size_difference >= 0:
            encode_outcome = 'success'
        elif new_file_size_difference < 0:
            encode_outcome = 'file_larger'
        else:
            encode_outcome = 'unknown_outcome'
        logging.error ('Encode Outcome: ' + encode_outcome)

        if encode_outcome in ['success','file_larger']:
            destination_filepath = root + '/' + os.path.basename(temp_filepath)
            logging.debug('Moving ' + temp_filepath + ' to ' + destination_filepath)
            os.remove(file_path)
            shutil.move(temp_filepath, destination_filepath) 
            logging.debug ('Move complete')
            ffresults_input = ffmpeg_inputs
            del ffmpeg_inputs['temp_filepath']
            ffresults_input.update({'new_file_size':new_file_size})
            ffresults_input.update({'old_file_size':old_file_size})
            ffresults_input.update({'new_file_size_difference':new_file_size_difference})
            ffresults_input.update({'encode_outcome':encode_outcome})
            ffresults.delay(ffresults_input)
            logging.debug ('ffresults called')
        else:
            logging.error ('Issue with: ' + ffmpeg_inputs['file'])

    elif (exit_code != 'Success' and
          os.path.exists(temp_filepath)):
        logging.debug ('Removing: ' + ffmpeg_inputs['temp_filepath'])
        os.remove(temp_filepath)
    else:
        logging.debug('No idea')       

    task_duration_time('fencoder',function_start_time)
    