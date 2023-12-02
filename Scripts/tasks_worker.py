from celery import Celery
import subprocess, os, shutil
from task_shared_services import celery_url_path, file_size_mb, task_start_time, task_duration_time

backend_path = celery_url_path('rpc://') 
broker_path = celery_url_path('amqp://') 
app = Celery('tasks', backend = backend_path, broker = broker_path)

@app.task(queue='worker')
def fencoder(json_configuration):
    import sys
    sys.path.append("/Scripts")
    from tasks_manager import ffresults

    function_start_time = task_start_time('fencoder')

    ffmpeg_settings = os.environ.get('ffmpeg_settings','-hide_banner -loglevel 16 -stats -stats_period 10')

    file_path = json_configuration["file_path"]
    output_file = json_configuration["output_filename"]
    root = json_configuration["root"]
    temp_filepath = '/boil_hold/' +  output_file
    ffmpeg_command = json_configuration["ffmpeg_command"]

    
    ffmpeg_command = 'ffmpeg ' + ffmpeg_settings + ' -i "' + file_path + '" ' + ffmpeg_command + ' "' + temp_filepath + '"'
    print (ffmpeg_command)

    print ('Please hold')
    
    process = subprocess.Popen(ffmpeg_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,universal_newlines=True)

    for line in process.stdout:
        print(line)

    encode_outcome = str()
    stats = str()
    move = str()

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
        if new_file_size_difference >= 0:
            encode_outcome = 'success'
        elif new_file_size_difference < 0:
            encode_outcome = 'file_larger'
        else:
            encode_outcome = 'unknown_outcome'
        print ('Encode Outcome: ' + encode_outcome)

    if stats == 'exist':
        if new_file_size != 0.0 and (new_file_size_difference > 0 or json_configuration["override"] == 'true'):
            destination_filepath = root + '/' + output_file
            print('Moving ' + temp_filepath + ' to ' + destination_filepath)
            os.remove(file_path)
            shutil.move(temp_filepath, destination_filepath) 
            move = 'complete'
            print ('Move complete')
        elif new_file_size == 0.0:
            print('Problem with the output')
            os.remove(new_file_size)
        else:
            print ('Saving conditions were note met')

    if move == 'complete':
        json_configuration.update({'new_file_size':new_file_size, 'old_file_size':old_file_size, 'new_file_size_difference':new_file_size_difference, 'encode_outcome':encode_outcome,'ffmpeg_command':ffmpeg_command})
        ffresults.delay(json_configuration)
        print ('ffresults called')

    task_duration_time('fencoder',function_start_time)
    