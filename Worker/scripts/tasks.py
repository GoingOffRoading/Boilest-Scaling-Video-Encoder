from celery import Celery
from pathlib import Path
import json, subprocess, os, shutil

app = Celery('tasks', backend = 'rpc://test:test@192.168.1.110:31672/celery', broker = 'amqp://test:test@192.168.1.110:31672/celery')

@app.task
def ffinder(json_template):
    # Need to change this line to be a variable passed to the function
    # I.E. Invoke the search based on feeding it a JSON
    #f = open(json_template)
    # returns JSON object as
    # a dictionary
    #data = json.load(f)
    print ('================= json template =================')
    print (json.dumps(json_template, indent=3, sort_keys=True))
    print ('================ starting search ================')
    #print (data)
    # Get the folder to scan
    directory = (json_template['watch_folder'])
    print ('Will now search the directory ' + directory + ' and provide the relevant config flags:')
    # traverse whole directory
    for root, dirs, files in os.walk(directory):
        # select file name
        for file in files:
            # check the extension of files
            if file.endswith('.mkv') or file.endswith('.mp4'):
                # append the desired fields to the original json
                print ('================ media file located ================')
                ffinder_json = {'file_path':root, 'file_name':file}
                ffinder_json.update(json_template)      
                if (json_template["show_diagnostic_messages"]) == 'yes':
                    print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> DIAGNOSTICS <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')
                    print(json.dumps(ffinder_json, indent=3, sort_keys=True))
                    print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> DIAGNOSTICS <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')
                fprober.delay(ffinder_json)

@app.task
def fprober(ffinder_json):
    
    # Uncomment to see the incoming JSON
    #print(json.dumps(filename, indent=3, sort_keys=True))
    
    # Need to assemble the full filepath to pass to FFprobe
    file_path = (ffinder_json["file_path"])
    file_name = (ffinder_json["file_name"])
    ffprobe_path = os.path.join(file_path,file_name)
    print ('================= Executing FFprobe =================')
    print ('Going to execute FFprobe on: ' + ffprobe_path + 'using:')
    
    # Using subprocess to call FFprobe, get JSON back    
    cmnd = [f'ffprobe', '-loglevel', 'quiet', '-show_entries', 'format:stream=index,stream,codec_type,codec_name', '-of', 'json', ffprobe_path]
    print (cmnd)
    p = subprocess.run(cmnd, capture_output=True).stdout
    d = json.loads(p)

    # Diagnostics
    if (ffinder_json["show_diagnostic_messages"]) == 'yes':
        print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> DIAGNOSTICS <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')
        print(json.dumps(d, indent=3, sort_keys=True))
        print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> DIAGNOSTICS <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')
    
    print ('================= Extracing Variables =================')
    # Get the container type from the FFProbe output
    original_container = (d['format']['format_name'])
    #print (original_container)
    
    # Get the video codec from the first video stream
    for stream in d['streams']:
        if stream['codec_type']=="video":
            original_video_codec = stream['codec_name']
            break
    #print(original_audio_codec)
    
     # Get the video codec from the first audio stream
    for stream in d['streams']:
        if stream['codec_type']=="audio":
            original_audio_codec = stream['codec_name']
            break
    #print(original_audio_codec)

    # Get the subtitle format from the first subtitle stream
    for stream in d['streams']:
        if stream['codec_type']=="subtitle":
            original_subtitle_format = stream['codec_name']
            break
    #print(original_audio_codec)
    
    # Here we check the output of ffprobe against the configurations for the library
    # See the template.json
    
    # Part 1 (bellow) checks the container, codecs, formats and builds the relevant ffmpeg string 
    
    print ('================= Building FFMpeg String =================')

    # Create an empty string variable that will become our FFmpeg variables
    encode = str()

    # Determine if the container needs to be changed
    if original_container != (ffinder_json["ffmpeg_container_string"]):
        print (ffprobe_path + ' is using ' + original_container + ', not ' + (ffinder_json["ffmpeg_container_string"]))

    # Determine if the video needs to be re-encoded
    if original_video_codec != (ffinder_json["ffmpeg_video_codec"]):
        print (ffprobe_path + ' is using ' + original_video_codec + ', not ' + (ffinder_json["ffmpeg_video_codec"]))
        encode = encode + ' ' + (ffinder_json["ffmpeg_video_string"])
    
    # Determine if the audio needs to be re-encoded
    if original_audio_codec != (ffinder_json["ffmpeg_audio_codec"]):
        print (ffprobe_path + ' is using ' + original_audio_codec + ', not ' + (ffinder_json["ffmpeg_audio_codec"]))
        encode = encode + ' ' + (ffinder_json["ffmpeg_audio_string"])
        
    # Determine if the subtitles needs to be re-formatted
    if original_subtitle_format != (ffinder_json["ffmpeg_subtitle_format"]):
        print (ffprobe_path + ' is using ' + original_subtitle_format + ', not ' + (ffinder_json["ffmpeg_subtitle_format"]))
        encode = encode + ' ' + (ffinder_json["ffmpeg_subtitle_string"])  
    
    # Part 2 determines if the string is needed
    if original_container == (ffinder_json["ffmpeg_container_string"]) and original_video_codec == (ffinder_json["ffmpeg_video_codec"]) and original_audio_codec == (ffinder_json["ffmpeg_audio_codec"]) and original_subtitle_format == (ffinder_json["ffmpeg_subtitle_format"]): 
        print ('============== ' + file_name + ' does not need encoding ==============')
    else:
        print ('============== ' + file_name + ' needs encoding ==============')
        fprober_json = {'ffmpeg_encoding_string':encode, 'original_container':original_container, 'original_video_codec':original_video_codec, 'original_audio_codec':original_audio_codec, 'original_subtitle_format':original_subtitle_format}
        fprober_json.update(ffinder_json) 
        if (fprober_json["show_diagnostic_messages"]) == 'yes':
            print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> DIAGNOSTICS <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')
            print(json.dumps(fprober_json, indent=3, sort_keys=True))
            print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> DIAGNOSTICS <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')
        fencoder.delay(fprober_json)


@app.task
def fencoder(fprober_json):
    if (fprober_json["show_diagnostic_messages"]) == 'yes':
        print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> DIAGNOSTICS <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')
        print ('================= ffmpeger JSON inputs =================')
        print (json.dumps(fprober_json, indent=3, sort_keys=True))
        print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> DIAGNOSTICS <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')
        
    # ffmpeg is ffmpeg + settings + input file + encoding settings + output file
    # So we're going to grab each of those pieces

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
    file_name = Path(file_name).stem
    output_extension = (fprober_json["ffmeg_container_extension"])
    #print ('filename is currently: ' + file_name)
    ffmpeg_output_file = '/boil_hold/' + file_name + '.' + output_extension
    #print ('file name with path is: ' + ffmpeg_output_file)
    
    # All together now
    print ('=============== Assembled ffmpeg command ===============')
    ffmpeg_command = 'ffmpeg ' + ffmpeg_settings + ' -i "' + ffmeg_input_file + '"' + ffmpeg_encoding_settings + ' "' + ffmpeg_output_file + '"'
    print (ffmpeg_command)    
    print ('=============== Executing ffmpeg =======================')

    # We need to determine if this is a production run and run the function like normal
    if (fprober_json["production_run"]) == 'yes':
        print ('Please hold')
        os.system(ffmpeg_command)
    else:
        print ('This is a test run, so lets maybe not polute production')
    
    # Would love to revisit this as a subprocess, but was having issues getting everything to slice as desired
    #print ('=============== assembled ffmpeg command ===============')
    #ffmpeg_settings = ffmpeg_settings.split()
    #ffmpeg_settings = ', '.join(ffmpeg_settings)
    #ffmpeg_encoding_settings = ffmpeg_encoding_settings.split()
    #ffmeg_input_file = '"' + ffmeg_input_file + '"'
    #ffmpeg_output_file = '"' + ffmpeg_output_file + '"'
    #ffmpeg_command = 'ffmpeg', ffmpeg_settings, '-i', ffmeg_input_file, ffmpeg_encoding_settings,ffmpeg_output_file
    #print (ffmpeg_command)    
    #print ('=============== executing ffmpeg =======================')
    
    #p = subprocess.run(cmnd, capture_output=True).stdout
    #d = json.loads(p)

    print ('=============== Checking output =======================')
    
    if os.path.exists(ffmeg_input_file and ffmpeg_output_file):
        print( ffmeg_input_file + ' and ' + ffmpeg_output_file + ' Files Exists')
        input_file_stats = os.stat(ffmeg_input_file)
        print(f'Original file Size in MegaBytes is {input_file_stats.st_size / (1024 * 1024)}') 
        output_file_stats = os.stat(ffmpeg_output_file)
        print(f'Encoded file Size in MegaBytes is {output_file_stats.st_size / (1024 * 1024)}') 
        print('Removing ' + ffmeg_input_file)
        if (fprober_json["production_run"]) == 'yes':
            os.remove(ffmeg_input_file) 
            print('Moving ' + ffmpeg_output_file + ' to ' + ffmeg_input_file)
            shutil.move(ffmpeg_output_file, ffmeg_input_file)
            print ('Done')
            fencoder_json = {'old_file_size':input_file_stats, 'new_file_size':output_file_stats}
            fencoder_json.update(fprober_json) 
            if (fprober_json["show_diagnostic_messages"]) == 'yes':
                print(json.dumps(fencoder_json, indent=3, sort_keys=True))
            #fencoder.delay(fencoder_json)
        else:
            print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> DIAGNOSTICS <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')
            print('In test mode, not moving files')
            print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> DIAGNOSTICS <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')
                    
    else:
         print("Either source or encoding is missing, so exiting")




