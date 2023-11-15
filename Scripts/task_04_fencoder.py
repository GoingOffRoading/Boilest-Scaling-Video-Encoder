from celery import Celery
from pathlib import Path
from datetime import datetime
import json, subprocess, os, shutil
from task_04_fresults import fresults

app = Celery('tasks', backend = 'rpc://celery:celery@192.168.1.110:31672/celery', broker = 'amqp://celery:celery@192.168.1.110:31672/celery')

@app.task(queue='worker')
def fencoder(fprober_json):
    # This is the step where we do the actual video encoding
    fencoder_start_time = datetime.now()
    print ('>>>>>>>>>>>>>>>> fencoder for ' + fprober_json["file_name"] + ' starting at ' + str(fencoder_start_time) + '<<<<<<<<<<<<<<<<<<<')

    print (json.dumps(fprober_json, indent=3, sort_keys=True))

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
    ffmpeg_command = 'ffmpeg ' + ffmpeg_settings + ' -i "' + ffmeg_input_file + '"' + ffmpeg_encoding_settings + ' "' + ffmpeg_output_file + '"'
    print ('ffmpeg command:')
    print (ffmpeg_command)    

    print ('Please hold')
        #os.system(ffmpeg_command)
    process = subprocess.Popen(ffmpeg_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,universal_newlines=True)
    for line in process.stdout:
        print(line)
    
    fencoder_duration = (datetime.now() - fencoder_start_time).total_seconds() / 60.0
    encode_outcome = 'unset'
    
    if os.path.exists(ffmeg_input_file and ffmpeg_output_file):
        print (ffmeg_input_file + ' and ' + ffmpeg_output_file + ' Files Exists')
        input_file_stats = os.stat(ffmeg_input_file)
        input_file_stats = round(input_file_stats.st_size / (1024 * 1024))
        print (f'Original file Size in MegaBytes is: ' + str(input_file_stats)) 
        output_file_stats = (os.stat(ffmpeg_output_file))
        output_file_stats = round(output_file_stats.st_size / (1024 * 1024))
        print (f'Encoded file Size in MegaBytes is: ' + str(output_file_stats)) 
        new_file_size_difference = input_file_stats - output_file_stats
        print (f'Total Space savings is: ' + str(new_file_size_difference))
        print ('Removing ' + ffmeg_input_file)
        # We're checking for to things:
        # 1) If this is a production run, and we intend to delete source
        # 2) Don't delete sourec if the ffmpeg encode failed

        if output_file_stats != 0.0 and (new_file_size_difference >= 0 or fprober_json["override"] == 'true'):
            # This is the use-case where the newly encoded file is small than the old file, which is what we want
            os.remove(ffmeg_input_file) 
            ffmpeg_destination = fprober_json["file_path"] + '/' + fprober_json["ffmpeg_output_file"]
            print('Moving ' + ffmpeg_output_file + ' to ' + ffmpeg_destination)
            shutil.move(ffmpeg_output_file, ffmpeg_destination)
            print ('Done')
            encode_outcome = 'success'
        elif output_file_stats != 0.0 and new_file_size_difference < 0:
            # This is the use-case where the newly encoded file is larger than the old file
            # Usually this means that the ffmpeg command requires tweaking
            print ('New file not compressed, removing ' + ffmpeg_output_file)
            os.remove(ffmpeg_output_file)
            print (ffmpeg_output_file + ' file deleted')
            encode_outcome = 'file_size_failed'
        elif output_file_stats == 0.0:
            # Sometimes FFMPEG can fail, and the output file exists, but it's 0 kb
            print ('Something went wrong, and the output file size is 0.0 KB')
            print ('Deleting: ' + ffmpeg_output_file)
            encode_outcome = 'failed_encode'
            os.remove(ffmpeg_output_file) 
        else:
            print ('Something else went wrong, and neither source nor encoded were deleted ')
            encode_outcome = 'error'

        fencoder_json = {'old_file_size':input_file_stats, 'new_file_size':output_file_stats, 'new_file_size_difference':new_file_size_difference, 'fencoder_duration':fencoder_duration, 'encode_outcome':encode_outcome}
        fencoder_json.update(fprober_json) 
        print(json.dumps(fencoder_json, indent=3, sort_keys=True))
        #fresults.delay(fencoder_json)
    else:
        print("Either source or encoding is missing, so exiting")
    
    print ('>>>>>>>>>>>>>>>> fencoder ' + fprober_json["file_name"] + ' complete, executed for ' + str(fencoder_duration) + ' minutes <<<<<<<<<<<<<<<<<<<')

