from celery import Celery
from datetime import datetime
import json, os, sqlite3, logging
from task_shared_services import task_start_time, task_duration_time, check_queue, find_files, celery_url_path, check_queue, ffmpeg_output_file, ffprober_function, get_active_tasks, get_file_size_bytes
import celeryconfig

app = Celery('tasks', backend = celery_url_path('rpc://'), broker = celery_url_path('amqp://') )
app.config_from_object(celeryconfig)

@app.task(queue='manager')
# Stuff
def container_check(file_located, ffprobe_results):
    import sys
    sys.path.append("/Scripts")
    from tasks_worker import fencoder

    function_start_time = task_start_time('container_check')

    logging.debug ('Checking contaienr type for: ' + file_located['file'])
    logging.debug ('In: ' + file_located['root'])

    if ffprobe_results['format']['format_name'] != 'matroska,webm' or file_located['extension'] != '.mkv':
        logging.debug (file_located['file'] + ' is not .MKV')
        logging.debug ('Sending to FFmpeg:')


        logging.debug ('Generating file size')
        # I started to evaluate getting an actual hash but the functions took too long
        # Using file size in bytes to valudate works as a tep solution
        file_hash = get_file_size_bytes(file_located['file_path'])    

        
        ffmpeg_command = 'ffmpeg ' + \
                        os.environ.get('ffmpeg_settings') + \
                        ' -i ' + \
                        '"' + file_located['file_path'] + '" ' + \
                        '"' + ffmpeg_output_file(file_located['file']) + '"'
        
        logging.debug (ffmpeg_command)

        ffmpeg_inputs = file_located    
        ffmpeg_inputs.update({'file_hash':file_hash})
        ffmpeg_inputs.update({'ffmpeg_command':ffmpeg_command})
        ffmpeg_inputs.update({'job':'container_check'})
        ffmpeg_inputs.update({'temp_filepath':ffmpeg_output_file(file_located['file'])})
        ffmpeg_inputs.update({'original_string':ffmpeg_inputs['extension']})
        del ffmpeg_inputs['extension']

        fencoder.delay(ffmpeg_inputs)
    else:
        logging.debug (file_located['file'] + ' is .MKV')
        logging.debug ('Sending ' + file_located['file'] + ' to the next step')
        ffprober_av1_check.delay(file_located,ffprobe_results)
        
    task_duration_time('container_check',function_start_time)

@app.task(queue='manager')
def ffprober_av1_check(file_located,ffprobe_results):
    import sys
    sys.path.append("/Scripts")
    from tasks_worker import fencoder

    function_start_time = task_start_time('ffprober_av1_check')

    logging.debug ('Checking video codec in: ' + file_located['file'])
    logging.debug ('In: ' + file_located['root'])

    if file_located['directory'] == '/anime':
        ffmpeg_string = "libsvtav1 -crf 25 -preset 4 -g 240 -pix_fmt yuv420p10le -svtav1-params filmgrain=20:film-grain-denoise=0:tune=0:enable-qm=1:qm-min=0:qm-max=15"
    elif file_located['directory'] == '/tv':
        ffmpeg_string = "libsvtav1 -crf 25 -preset 4 -g 240 -pix_fmt yuv420p10le -svtav1-params filmgrain=20:film-grain-denoise=0:tune=0:enable-qm=1:qm-min=0:qm-max=15"
    elif file_located['directory'] == '/movies':
        ffmpeg_string = "libsvtav1 -crf 20 -preset 4 -g 240 -pix_fmt yuv420p10le -svtav1-params filmgrain=20:film-grain-denoise=0:tune=0:enable-qm=1:qm-min=0:qm-max=15"
    else:
        logging.debug ('Directory configuration does not exist')

    ffmpeg_command = str()
    encode_decision = 'no'
    original_string = str()

    streams_count = ffprobe_results['format']['nb_streams']
    logging.debug ('there are ' + str(streams_count) + ' streams:')

    for i in range (0,streams_count): 
        codec_type = ffprobe_results['streams'][i]['codec_type']
        if codec_type == 'video':
            codec_name = ffprobe_results['streams'][i]['codec_name'] 
            if codec_name == 'av1':
                ffmpeg_command = ffmpeg_command + ' -map 0:' + str(i) + ' -c:v copy'
                # No need to change encode_decision as the video codec is in the desired format
                logging.debug ('Stream ' + str(i) + ' is already ' + codec_name + ', copying stream')
            elif codec_name == 'mjpeg':
                logging.debug ('Garbage mjpeg stream, ignoring')    
                # No use for this for now
            elif codec_name != 'av1':
                encode_decision = 'yes'
                ffmpeg_command = ffmpeg_command + ' -map 0:' + str(i) + ' -c:v ' + ffmpeg_string
                original_string = original_string + '{stream ' + str(i) + ' ' + ffprobe_results['streams'][i]['codec_type'] + ' = ' + codec_name + '}'
                logging.debug ('Stream ' + str(i) + ' is ' + codec_name + ', encoding stream')

                # encode_decision = yes as the video codec is not in the desired format
            else:
                logging.debug ('Something is broken with stream ' + str(i))
                # Catch all error state        
        else:
           if codec_type == 'audio':
               ffmpeg_command = ffmpeg_command + ' -map 0:' + str(i) + ' -c:a copy'
           elif codec_type == 'subtitle':
               ffmpeg_command = ffmpeg_command + ' -map 0:' + str(i) + ' -c:s copy'
           elif codec_type == 'attachment':
               ffmpeg_command = ffmpeg_command + ' -map 0:' + str(i) + ' -c:t copy'
           else:
            logging.ERROR ('unexpected codec type')
    
    ffmpeg_command = 'ffmpeg ' + \
                os.environ.get('ffmpeg_settings') + \
                ' -i ' + \
                '"' + file_located['file_path'] + '"' + \
                ffmpeg_command + \
                ' "' + ffmpeg_output_file(file_located['file']) + '"'
    
    if encode_decision == 'yes':       

        logging.info ('Sending: ' + file_located['file'] + ' for processing') 

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
            fencoder.apply_async(kwargs={'ffmpeg_inputs': ffmpeg_inputs}, priority=6)
            logging.debug ('celery_priority_value is 4')
        elif ffprobe_results['streams'][0]['codec_name'] == 'hevc':
            fencoder.apply_async(kwargs={'ffmpeg_inputs': ffmpeg_inputs}, priority=4)
            logging.debug ('celery_priority_value is 6')
        else:
            fencoder.apply_async(kwargs={'ffmpeg_inputs': ffmpeg_inputs}, priority=5)
            logging.debug ('celery_priority_value is 5')


    elif encode_decision == 'no':
        logging.debug ('Next task goes here')
    else:
        logging.ERROR ('Error state here')

    task_duration_time('ffprober_av1_check',function_start_time)

